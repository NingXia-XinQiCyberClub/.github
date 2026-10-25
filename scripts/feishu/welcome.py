#!/usr/bin/env python3
"""新成员提醒：发现飞书群里的新面孔，@ 他先去 GitHub 填加入工单。

群自定义机器人只能发消息，读不到成员名单，因此本脚本走企业自建应用：
用 tenant_access_token 拉群成员列表，与上一次的快照对比，新增的成员即为新人。

快照存放在本仓库的 feishu-state 分支（不在 main 上），首次运行只记录名单、
不发提醒，避免把现有成员全部 @ 一遍。

用法：
    python welcome.py --dry-run      # 只打印差异，不发消息、不写快照
    python welcome.py                # 正常执行
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notify import (  # noqa: E402
    API_BASE,
    CST,
    build_card,
    env,
    md_block,
    md_escape,
    plain_block,
    send_app,
    tenant_access_token,
)

STATE_BRANCH = "feishu-state"
STATE_PATH = "feishu-members.json"
MAX_NEW_PER_RUN = 20

JOIN_URL = (
    "https://github.com/NingXia-XinQiCyberClub/.github/issues/new?template=join.yml"
)


# --------------------------------------------------------------------------
# 快照读写：借 GitHub Contents API 存到独立分支，避免污染 main
# --------------------------------------------------------------------------


def gh_call(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    token = env("GITHUB_TOKEN")
    repo = env("GITHUB_REPOSITORY")
    if not token or not repo:
        return 0, {}

    url = f"https://api.github.com/repos/{repo}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "xinqi-new-member",
        "Authorization": f"Bearer {token}",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, {}
        print(f"GitHub 接口返回 {error.code}：{path}", file=sys.stderr)
        return error.code, {}
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"GitHub 接口请求失败：{error}", file=sys.stderr)
        return 0, {}


def ensure_state_branch() -> bool:
    """快照分支不存在时从默认分支创建。分支已存在则直接返回成功。"""
    repo = env("GITHUB_REPOSITORY")
    if not repo:
        return False

    status, _ = gh_call("GET", f"/branches/{STATE_BRANCH}")
    if status == 200:
        return True

    status, body = gh_call("GET", "/git/ref/heads/main")
    base_sha = ((body.get("object") or {}).get("sha")) or ""
    if status != 200 or not base_sha:
        print("读取默认分支失败，无法创建快照分支", file=sys.stderr)
        return False

    status, _ = gh_call(
        "POST", "/git/refs", {"ref": f"refs/heads/{STATE_BRANCH}", "sha": base_sha}
    )
    if status in (200, 201):
        print(f"已创建快照分支 {STATE_BRANCH}")
        return True

    # 并发创建时可能已由另一实例建好，再确认一次
    status, _ = gh_call("GET", f"/branches/{STATE_BRANCH}")
    return status == 200


def load_state() -> tuple[dict, str]:
    """返回 (成员快照, 文件 sha)。首次运行时快照为空、sha 为空串。"""
    import base64

    query = urllib.parse.urlencode({"ref": STATE_BRANCH})
    status, body = gh_call("GET", f"/contents/{STATE_PATH}?{query}")
    if status != 200 or not body.get("content"):
        return {}, ""

    raw = base64.b64decode(body["content"]).decode("utf-8")
    try:
        members = json.loads(raw).get("members") or {}
    except json.JSONDecodeError:
        print("快照文件损坏，按首次运行处理", file=sys.stderr)
        return {}, ""
    return members, body.get("sha", "")


def save_state(members: dict, sha: str) -> bool:
    import base64

    content = json.dumps(
        {"updated": datetime.now(CST).isoformat(timespec="seconds"), "members": members},
        ensure_ascii=False,
        indent=2,
    )
    payload = {
        "message": f"chore(state): 更新飞书群成员快照（{len(members)} 人）",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": STATE_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    status, _ = gh_call("PUT", f"/contents/{STATE_PATH}", payload)
    if status in (200, 201):
        print(f"已保存快照：{len(members)} 人")
        return True
    print(f"保存快照失败，状态码 {status}", file=sys.stderr)
    return False


# --------------------------------------------------------------------------
# 群成员
# --------------------------------------------------------------------------


def fetch_members(app_id: str, app_secret: str, chat_id: str) -> dict | None:
    token = tenant_access_token(app_id, app_secret)
    if not token:
        return None

    members: dict = {}
    page_token = ""
    while True:
        query = {"member_id_type": "open_id", "page_size": 100}
        if page_token:
            query["page_token"] = page_token
        url = f"{API_BASE}/im/v1/chats/{chat_id}/members?" + urllib.parse.urlencode(query)

        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "xinqi-new-member",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            hint = "（应用缺少 im:chat.members:read 权限，或机器人不在该群）"
            print(f"读取群成员失败：HTTP {error.code}{hint}", file=sys.stderr)
            return None
        except (urllib.error.URLError, json.JSONDecodeError) as error:
            print(f"读取群成员失败：{error}", file=sys.stderr)
            return None

        if result.get("code") != 0:
            print(f"读取群成员被拒绝：{result}", file=sys.stderr)
            return None

        data = result.get("data") or {}
        for item in data.get("items") or []:
            member_id = item.get("member_id")
            if member_id:
                members[member_id] = item.get("name") or ""
        if not data.get("has_more"):
            break
        page_token = data.get("page_token") or ""
        if not page_token:
            break

    return members


# --------------------------------------------------------------------------
# 提醒
# --------------------------------------------------------------------------


def build_reminder(newcomers: list[tuple[str, str]]) -> dict:
    """newcomers 为 [(open_id, 姓名)]。卡片里逐个 @ 到人。"""
    mentions = " ".join(f'<at id={open_id}></at>' for open_id, _ in newcomers)
    blocks = [
        md_block(f"{mentions} 欢迎加入宁夏大学鑫启网安俱乐部。"),
        md_block(
            "**第一步** 在 GitHub 填写加入申请工单，维护者审核通过后会向你的 GitHub 账号发出组织邀请\n"
            "**第二步** 查收 GitHub 注册邮箱，点击邮件里的接受链接\n"
            "**第三步** 按[第 0 章](https://github.com/NingXia-XinQiCyberClub/guide/blob/main/00-%E5%8A%A0%E5%85%A5%E7%A4%BE%E5%9B%A2%E6%B5%81%E7%A8%8B.md)完成入门任务"
        ),
        plain_block(
            "组织内的仓库、任务与赛事报名都在 GitHub 上，没有加入组织将无法查看。"
            "工单需要填写真实姓名与 11 位学号，请如实填写。"
        ),
    ]
    buttons = [("填写加入工单", JOIN_URL)]
    return build_card("请填写加入工单", "blue", blocks, buttons)


def describe(newcomers: list[tuple[str, str]]) -> str:
    names = [name or open_id[:12] for open_id, name in newcomers]
    return "、".join(md_escape(name, 20) for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(description="提醒新成员填写加入工单")
    parser.add_argument("--dry-run", action="store_true", help="只打印差异，不发消息")
    args = parser.parse_args()

    app_id = env("FEISHU_APP_ID")
    app_secret = env("FEISHU_APP_SECRET")
    chat_id = env("FEISHU_CHAT_ID_RECRUIT") or env("FEISHU_CHAT_ID")

    if not (app_id and app_secret and chat_id):
        print(
            "未配置 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_CHAT_ID，跳过新成员提醒",
            file=sys.stderr,
        )
        return 0

    current = fetch_members(app_id, app_secret, chat_id)
    if current is None:
        return 1

    if not args.dry_run and not ensure_state_branch():
        print("无法准备快照分支", file=sys.stderr)
        return 1

    known, sha = load_state()
    if not known:
        print(f"首次运行，仅记录现有 {len(current)} 名成员，不发提醒")
        if args.dry_run:
            return 0
        save_state(current, sha)
        return 0

    newcomers = [(open_id, name) for open_id, name in current.items() if open_id not in known]
    vanished = [open_id for open_id in known if open_id not in current]

    print(f"群成员 {len(current)} 人，新增 {len(newcomers)} 人，退出 {len(vanished)} 人")

    if vanished and not args.dry_run:
        # 退出的人从快照里移除，但不发任何消息
        print("已退出：" + "、".join(vanished))

    if len(newcomers) > MAX_NEW_PER_RUN:
        print(
            f"新增人数 {len(newcomers)} 超过上限 {MAX_NEW_PER_RUN}，"
            "疑似权限或快照异常，本次只更新快照不发提醒",
            file=sys.stderr,
        )
        if not args.dry_run:
            save_state(current, sha)
        return 1

    if newcomers:
        print("新增：" + describe(newcomers))
        if args.dry_run:
            print(json.dumps(build_reminder(newcomers), ensure_ascii=False, indent=2))
            return 0
        code = send_app(app_id, app_secret, chat_id, build_reminder(newcomers))
        if code != 0:
            # 发送失败不写快照，下次运行会重试，避免漏提醒
            return code
    elif args.dry_run:
        print("没有新成员")
        return 0

    if not args.dry_run:
        save_state(current, sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
