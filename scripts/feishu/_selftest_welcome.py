#!/usr/bin/env python3
"""新成员提醒的测试：拦截所有网络，检查快照对比、首次运行、上限保护与卡片渲染。

用法：python _selftest_welcome.py
"""

import base64
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import welcome  # noqa: E402
from _selftest import check_lark_md, walk_lark_md, walk_urls  # noqa: E402


class FakeResponse(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


ENV = {
    "FEISHU_APP_ID": "cli_demo",
    "FEISHU_APP_SECRET": "s3cret",
    "FEISHU_CHAT_ID": "oc_main",
    "FEISHU_CHAT_ID_RECRUIT": "oc_recruit",
    "GITHUB_TOKEN": "ghs_demo",
    "GITHUB_REPOSITORY": "NingXia-XinQiCyberClub/.github",
}


def setup_env(**overrides):
    original = dict(welcome.os.environ)
    welcome.os.environ.clear()
    welcome.os.environ.update(ENV)
    welcome.os.environ.update(overrides)
    return original


def make_member_api(names):
    """names 为 {open_id: 姓名}，返回一个模拟群成员接口。"""

    def handler(req, timeout=0):
        url = req.full_url
        if "tenant_access_token" in url:
            return FakeResponse(
                json.dumps({"code": 0, "tenant_access_token": "t-demo"}).encode()
            )
        if "/members" in url:
            items = [
                {"member_id": open_id, "name": name, "member_id_type": "open_id"}
                for open_id, name in names.items()
            ]
            return FakeResponse(
                json.dumps(
                    {"code": 0, "data": {"items": items, "has_more": False, "page_token": ""}}
                ).encode()
            )
        return FakeResponse(json.dumps({"code": 0}).encode())

    return handler


def check(name, condition, detail=""):
    print(f"[{'通过' if condition else '失败'}] {name}" + ("" if condition else f" {detail}"))
    return 0 if condition else 1


def main():
    failed = 0
    original_urlopen = welcome.urllib.request.urlopen
    original_state = (welcome.load_state, welcome.save_state)
    original_branch = welcome.ensure_state_branch
    # 快照分支的创建在 check_branch 里单独验证，其余用例直接放行
    welcome.ensure_state_branch = lambda: True

    # ---------- 卡片渲染 ----------
    card = welcome.build_reminder([("ou_aaa", "张三"), ("ou_bbb", "李四")])
    json.dumps(card, ensure_ascii=False)
    blocks = card["card"]["elements"]
    first = blocks[0]["text"]["content"]
    failed += check("卡片 @ 到每个人", "<at id=ou_aaa></at>" in first and "<at id=ou_bbb></at>" in first, first)
    failed += check("标题正确", card["card"]["header"]["title"]["content"] == "请填写加入工单")
    failed += check(
        "按钮指向加入工单模板",
        any(
            a.get("url", "").endswith("issues/new?template=join.yml")
            for e in blocks
            if e["tag"] == "action"
            for a in e["actions"]
        ),
    )
    for path, content in walk_lark_md(card):
        # 卡片里写死的教程链接是脚本自身的常量，允许出现
        problem = check_lark_md(content, allow=[r"\[第 0 章\]\(https://github\.com/[^\s)]+\)"])
        if problem:
            failed += check(f"卡片转义 {path}", False, f"{problem} / {content}")
    bad = [u for u in walk_urls(card) if not u.startswith("https://github.com/")]
    failed += check("链接均为 GitHub 地址", not bad, str(bad))

    # ---------- 首次运行：只记录，不提醒 ----------
    sent = []
    welcome.send_app = lambda *a: (sent.append(a), 0)[1]
    welcome.load_state = lambda: ({}, "")
    saved = []
    welcome.save_state = lambda members, sha: (saved.append(len(members)), True)[1]

    welcome.urllib.request.urlopen = make_member_api({"ou_1": "老王", "ou_2": "老李"})
    original = setup_env()
    code = welcome.main()
    failed += check("首次运行返回成功", code == 0, str(code))
    failed += check("首次运行不发提醒", not sent, str(sent))
    failed += check("首次运行写快照", saved == [2], str(saved))

    # ---------- 有新人：提醒并更新快照 ----------
    sent.clear()
    saved.clear()
    welcome.load_state = lambda: ({"ou_1": "老王", "ou_2": "老李"}, "sha_abc")
    welcome.urllib.request.urlopen = make_member_api(
        {"ou_1": "老王", "ou_2": "老李", "ou_9": "新同学"}
    )
    code = welcome.main()
    failed += check("有新人时返回成功", code == 0, str(code))
    failed += check("只发一条提醒", len(sent) == 1, str(len(sent)))
    if sent:
        _, _, chat, card = sent[0]
        failed += check("发到招新群", chat == "oc_recruit", chat)
        text = json.dumps(card, ensure_ascii=False)
        failed += check("提醒里 @ 到新人", "<at id=ou_9></at>" in text)
        failed += check("提醒里不含老成员", "ou_1" not in text and "ou_2" not in text)
    failed += check("更新快照到 3 人", saved == [3], str(saved))

    # ---------- 无人变动：不发提醒 ----------
    sent.clear()
    saved.clear()
    welcome.load_state = lambda: ({"ou_1": "老王"}, "sha")
    welcome.urllib.request.urlopen = make_member_api({"ou_1": "老王"})
    code = welcome.main()
    failed += check("无变动时不发提醒", code == 0 and not sent, f"{code} {sent}")
    failed += check("无变动时仍写快照", saved == [1], str(saved))

    # ---------- 有成员退出 ----------
    sent.clear()
    saved.clear()
    welcome.load_state = lambda: ({"ou_1": "老王", "ou_2": "老李"}, "sha")
    welcome.urllib.request.urlopen = make_member_api({"ou_1": "老王"})
    welcome.main()
    failed += check("退出者不触发提醒", not sent, str(sent))
    failed += check("快照移除退出者", saved == [1], str(saved))

    # ---------- 超上限保护 ----------
    sent.clear()
    saved.clear()
    welcome.load_state = lambda: ({"ou_0": "老成员"}, "sha")
    many = {"ou_0": "老成员"}
    many.update({f"ou_{i}": f"新人{i}" for i in range(1, 30)})
    welcome.urllib.request.urlopen = make_member_api(many)
    code = welcome.main()
    failed += check("超上限时返回失败", code == 1, str(code))
    failed += check("超上限时不发提醒", not sent, str(len(sent)))
    failed += check("超上限时只更新快照", saved == [30], str(saved))

    # ---------- 发送失败不写快照 ----------
    sent.clear()
    saved.clear()
    welcome.load_state = lambda: ({"ou_1": "老王"}, "sha")
    welcome.urllib.request.urlopen = make_member_api({"ou_1": "老王", "ou_9": "新同学"})
    welcome.send_app = lambda *a: 1
    code = welcome.main()
    failed += check("发送失败时返回失败", code == 1, str(code))
    failed += check("发送失败不写快照，下次重试", not saved, str(saved))

    # ---------- 未配置应用时静默跳过 ----------
    welcome.send_app = lambda *a: 0
    welcome.os.environ.clear()
    welcome.os.environ.update({"FEISHU_WEBHOOK": "https://open.feishu.cn/open-apis/bot/v2/hook/x"})
    code = welcome.main()
    failed += check("只有 webhook 时静默跳过", code == 0, str(code))

    # ---------- 群成员接口报错 ----------
    welcome.os.environ.clear()
    welcome.os.environ.update(ENV)

    def denied(req, timeout=0):
        if "tenant_access_token" in req.full_url:
            return FakeResponse(json.dumps({"code": 0, "tenant_access_token": "t"}).encode())
        raise welcome.urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)

    welcome.urllib.request.urlopen = denied
    code = welcome.main()
    failed += check("权限不足时返回失败", code == 1, str(code))

    # 收尾
    welcome.urllib.request.urlopen = original_urlopen
    welcome.load_state, welcome.save_state = original_state
    welcome.ensure_state_branch = original_branch
    welcome.os.environ.clear()
    welcome.os.environ.update(original)

    failed += check_branch(original_urlopen)

    print("\n全部通过" if failed == 0 else f"\n失败 {failed} 项")
    return 1 if failed else 0


def check_branch(original_urlopen):
    """快照分支的创建逻辑：已存在则跳过，不存在则从 main 建。"""
    failed = 0
    calls = []

    def handler(req, timeout=0):
        calls.append((req.get_method(), req.full_url))
        if req.get_method() == "GET" and "/branches/feishu-state" in req.full_url:
            if handler.exists:
                return FakeResponse(json.dumps({}).encode())
            raise welcome.urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)
        if req.get_method() == "GET" and "/git/ref/heads/main" in req.full_url:
            return FakeResponse(json.dumps({"object": {"sha": "abc123"}}).encode())
        if req.get_method() == "POST" and req.full_url.endswith("/git/refs"):
            body = json.loads(req.data.decode())
            handler.created = body
            return FakeResponse(json.dumps({"ref": body["ref"]}).encode())
        return FakeResponse(json.dumps({}).encode())

    handler.exists = False
    handler.created = None
    welcome.urllib.request.urlopen = handler
    setup_env()

    ok = welcome.ensure_state_branch()
    failed += check("分支不存在时创建", ok and handler.created == {
        "ref": "refs/heads/feishu-state", "sha": "abc123"
    }, str(handler.created))

    handler.exists = True
    calls.clear()
    handler.created = None
    ok = welcome.ensure_state_branch()
    failed += check("分支已存在时不重复创建", ok and handler.created is None, str(handler.created))

    welcome.urllib.request.urlopen = original_urlopen
    return failed


if __name__ == "__main__":
    sys.exit(main())
