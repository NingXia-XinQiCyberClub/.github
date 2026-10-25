#!/usr/bin/env python3
"""本地渲染测试：构造各种 GitHub 事件负载，检查卡片结构与转义，不联网。

用法：python _selftest.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import notify  # noqa: E402

BASE_REPO = {
    "full_name": "NingXia-XinQiCyberClub/guide",
    "html_url": "https://github.com/NingXia-XinQiCyberClub/guide",
}


def push_payload(messages, ref="refs/heads/main"):
    commits = [
        {"id": f"{'a' * 39}{i}", "message": message, "author": {"name": "张三"}}
        for i, message in enumerate(messages)
    ]
    return {
        "ref": ref,
        "deleted": False,
        "compare": "https://github.com/NingXia-XinQiCyberClub/guide/compare/abc...def",
        "pusher": {"name": "张三"},
        "sender": {"login": "zhangsan"},
        "repository": BASE_REPO,
        "commits": commits,
    }


def pr_payload(action, merged=False, draft=False):
    return {
        "action": action,
        "repository": BASE_REPO,
        "pull_request": {
            "title": "docs: 补充 0.9 节飞书说明（含二维码）",
            "user": {"login": "lisi"},
            "head": {"ref": "docs/feishu-note"},
            "base": {"ref": "main"},
            "draft": draft,
            "merged": merged,
            "additions": 12,
            "deletions": 3,
            "changed_files": 2,
            "closed_at": "2026-10-24T18:00:00Z",
            "html_url": "https://github.com/NingXia-XinQiCyberClub/guide/pull/12",
        },
    }


def issue_payload(action, labels, body=""):
    return {
        "action": action,
        "repository": BASE_REPO,
        "issue": {
            "title": "[加入] 张三",
            "user": {"login": "zhangsan"},
            "labels": [{"name": name} for name in labels],
            "body": body,
            "html_url": "https://github.com/NingXia-XinQiCyberClub/.github/issues/7",
        },
    }


JOIN_BODY = """### 中文姓名

张三

### 英文名

Zhang San

### 学号

12024242193

### 年级

大二

### 学院与专业

信息工程学院 网络工程

### 研究兴趣

Web 安全,Pwn / 二进制

### 流程清单

- [x] 步骤 1：安装并配置 Git — 教程见[第 0 章 0.3 节](https://example.com)
- [x] 步骤 2：配置认证方式（SSH 或 GitHub CLI）
- [ ] 步骤 3：阅读贡献指南与行为准则

### 受阻环节

步骤 3 的链接打不开

### 承诺

- [x] 已阅读并同意行为准则
"""


def discussion_payload(action="created", body="想问问大家平时用什么靶场练手？", answer=None):
    return {
        "action": action,
        "repository": BASE_REPO,
        "discussion": {
            "number": 5,
            "title": "新人如何入门 Web 安全？",
            "body": body,
            "state": "open",
            "html_url": "https://github.com/NingXia-XinQiCyberClub/guide/discussions/5",
            "user": {"login": "wangwu"},
            "category": {"name": "问答"},
            "answer_html_url": answer,
        },
    }


def discussion_comment_payload(action="created"):
    payload = discussion_payload("created")
    payload["action"] = action
    payload["comment"] = {
        "body": "从[第 0 章](https://evil.example)开始，先**装好环境**。",
        "html_url": "https://github.com/NingXia-XinQiCyberClub/guide/discussions/5#discussioncomment-1",
        "user": {"login": "lisi"},
    }
    return payload


CASES = [
    ("push 普通提交", "push", push_payload(["docs: 补充 0.9 节", "fix(login): 修正越界判断"])),
    ("push 多条提交", "push", push_payload([f"feat: 变更 {i}" for i in range(8)])),
    ("push 标签", "push", push_payload(["chore: 发布 v1.0.0"], ref="refs/tags/v1.0.0")),
    ("push 恶意标题", "push", push_payload(["**加粗**[点我](http://evil) `code` ~~del~~"])),
    ("push 纯合入痕迹", "push", push_payload(["docs: 补充说明 (#12)", "Merge pull request #13 from docs/x"])),
    ("PR 新开（草稿）", "pull_request", pr_payload("opened", draft=True)),
    ("PR 合入", "pull_request", pr_payload("closed", merged=True)),
    ("PR 关闭未合入", "pull_request", pr_payload("closed", merged=False)),
    ("PR 同步标签（应忽略）", "pull_request", pr_payload("synchronize")),
    ("Issue 新开", "issues", issue_payload("opened", [])),
    ("入会工单（不在此处播报）", "issues", issue_payload("opened", ["membership"], JOIN_BODY)),
    ("讨论新开", "discussion", discussion_payload()),
    ("讨论已采纳答案", "discussion", discussion_payload("answered", answer="https://github.com/x/y")),
    ("讨论含恶意正文", "discussion", discussion_payload(body="**加粗** [点我](http://evil) `x` <at id=all></at>")),
    ("讨论回复", "discussion_comment", discussion_comment_payload()),
    ("讨论回复编辑（应忽略）", "discussion_comment", discussion_comment_payload("edited")),
    ("手动测试", "workflow_dispatch", {}),
]


def walk_lark_md(node, path="card"):
    if isinstance(node, dict):
        if node.get("tag") == "lark_md":
            yield path, node.get("content", "")
        for key, value in node.items():
            yield from walk_lark_md(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_lark_md(value, f"{path}[{index}]")


def walk_urls(node, found=None):
    if found is None:
        found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "url" and isinstance(value, str):
                found.append(value)
            else:
                walk_urls(value, found)
    elif isinstance(node, list):
        for value in node:
            walk_urls(value, found)
    return found


import re

# 本脚本自行生成的链接形式：[#12](https://github.com/...)，其余方括号一律视为未转义
_LINK = re.compile(r"\[#[0-9]+\]\(https://github\.com/[^\s)]+\)")

# 脚本自行生成的 @ 提醒，飞书语法为 <at id=ou_xxx></at>
_MENTION = re.compile(r"<at id=ou_[A-Za-z0-9]+></at>")


def check_lark_md(content, allow=()):
    """检查内容除脚本自建的链接与 @ 之外，是否残留会破坏排版的未转义字符。

    allow 可传入额外的正则，用于脚本里写死的固定链接等本体可控的标记。
    """
    stripped = _LINK.sub("", content)
    stripped = _MENTION.sub("", stripped)
    for pattern in allow:
        stripped = re.sub(pattern, "", stripped)
    for char in "[]`~_<>":
        if char in stripped:
            return f"残留未转义字符 {char!r}"
    if stripped.replace("**", "").count("*"):
        return "星号未成对，可能破坏加粗"
    if "***" in stripped:
        return "星号连续出现"
    return ""


def main():
    failed = 0
    for name, event, payload in CASES:
        card = notify.build_card_for(event, payload)
        if card is None:
            print(f"[跳过] {name}")
            continue

        json.dumps(card, ensure_ascii=False)
        assert card["msg_type"] == "interactive", name
        title = card["card"]["header"]["title"]["content"]
        assert title, name

        for path, content in walk_lark_md(card):
            problem = check_lark_md(content)
            if problem:
                print(f"[失败] {name}：{path} {problem}")
                print(f"       {content}")
                failed += 1

        for url in walk_urls(card):
            if not url.startswith("https://github.com/"):
                print(f"[失败] {name}：链接不是 GitHub 地址 {url}")
                failed += 1

        first = card["card"]["elements"][0]["text"]["content"].replace("\n", " / ")
        print(f"[通过] {name} → {title} | {first[:64]}")

    failed += check_invite()
    failed += check_routing()

    print("\n全部通过" if failed == 0 else f"\n失败 {failed} 项")
    return 1 if failed else 0


# 邀请结果只在「已发出邀请」时公告，其余三种状态一律静默
INVITE_CASES = [
    ("invited", True),
    ("pending", False),
    ("already_member", False),
    ("failed", False),
]


def check_invite():
    failed = 0
    payload = issue_payload("labeled", ["membership"], JOIN_BODY)
    for status, should_send in INVITE_CASES:
        notify.os.environ["INVITE_STATUS"] = status
        notify.os.environ["INVITE_LOGIN"] = "zhangsan"
        notify.os.environ["FEISHU_SCENE"] = "invite_result"

        card = notify.build_card_for("invite_result", payload)
        if card is None:
            if should_send:
                print(f"[失败] 邀请结果 {status}：应当公告却未生成卡片")
                failed += 1
            else:
                print(f"[跳过] 邀请结果 {status}（按设计不公告）")
            continue

        text = json.dumps(card, ensure_ascii=False)
        title = card["card"]["header"]["title"]["content"]
        if "12024242193" in text:
            print(f"[失败] 邀请结果 {status}：学号未脱敏")
            failed += 1
        if "张三" not in text:
            print(f"[失败] 邀请结果 {status}：未取到申请人姓名")
            failed += 1
        for path, content in walk_lark_md(card):
            problem = check_lark_md(content)
            if problem:
                print(f"[失败] 邀请结果 {status}：{path} {problem}")
                failed += 1
        print(f"[通过] 邀请结果 {status} → {title}")

    for key in ("INVITE_STATUS", "INVITE_LOGIN", "FEISHU_SCENE"):
        notify.os.environ.pop(key, None)
    return failed


def check_routing():
    """验证入会公告进招新群、其他事件进主群，以及未配置时的降级行为。"""
    failed = 0
    original_send = notify.send
    original_env = dict(notify.os.environ)
    captured = []

    notify.send = lambda webhook, secret, message: (captured.append(webhook), 0)[1]

    main_hook = "https://open.feishu.cn/open-apis/bot/v2/hook/main"
    recruit_hook = "https://open.feishu.cn/open-apis/bot/v2/hook/recruit"

    def run(label, event, expected, extra=None):
        nonlocal failed
        captured.clear()
        notify.os.environ.clear()
        notify.os.environ.update(
            {
                "GITHUB_EVENT_NAME": event,
                "GITHUB_EVENT_PATH": "",
                "FEISHU_WEBHOOK": main_hook,
                "FEISHU_WEBHOOK_RECRUIT": recruit_hook,
            }
        )
        if extra:
            notify.os.environ.update(extra)
        code = notify.main()
        got = captured[0] if captured else None
        ok = code == 0 and got == expected
        print(f"[{'通过' if ok else '失败'}] 路由 {label} → {got or '未发送'}")
        if not ok:
            failed += 1

    # main 内部通过 load_event 读文件，这里替换为直接返回构造的负载
    notify.load_event = lambda: ROUTING_PAYLOAD

    ROUTING_PAYLOAD.clear()
    ROUTING_PAYLOAD.update(push_payload(["docs: 变更"]))
    run("推送进主群", "push", main_hook)

    ROUTING_PAYLOAD.clear()
    ROUTING_PAYLOAD.update(issue_payload("opened", ["membership"], JOIN_BODY))
    run("入会工单不在此处播报", "issues", None)

    ROUTING_PAYLOAD.clear()
    ROUTING_PAYLOAD.update(issue_payload("labeled", ["membership"], JOIN_BODY))
    run(
        "未配招新群时降级到主群",
        "issues",
        main_hook,
        {"FEISHU_SCENE": "invite_result", "INVITE_STATUS": "invited", "FEISHU_WEBHOOK_RECRUIT": ""},
    )

    captured.clear()
    notify.os.environ.clear()
    notify.os.environ.update({"GITHUB_EVENT_NAME": "push", "GITHUB_EVENT_PATH": ""})
    code = notify.main()
    ok = code == 0 and not captured
    print(f"[{'通过' if ok else '失败'}] 路由 未配置任何机器人时静默跳过")
    if not ok:
        failed += 1

    notify.send = original_send
    notify.os.environ.clear()
    notify.os.environ.update(original_env)
    return failed


ROUTING_PAYLOAD: dict = {}


if __name__ == "__main__":
    sys.exit(main())
