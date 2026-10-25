#!/usr/bin/env python3
"""飞书群播报：把 GitHub 事件渲染成消息卡片，发送到群自定义机器人。

由 workflows/feishu-broadcast.yml 调用。事件数据从 GITHUB_EVENT_PATH 读取，
因此本脚本不访问 GitHub API，也不依赖第三方库，Python 3.9 以上可直接运行。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

# 只允许向飞书官方的机器人地址发送，避免误配把消息发往其他站点
HOOK_HOSTS = {"open.feishu.cn", "open.larksuite.com"}

MAX_COMMITS_DEFAULT = 5

# lark_md 中会触发加粗、链接等语法的字符，写入前替换为全角。
# 只处理成对标记的左半部分即可阻断语法，例如 [ 被替换后就不再构成链接，
# 因此保留英文括号，避免 fix(login) 之类的提交信息被改写。
_ESCAPES = str.maketrans(
    {
        "*": "＊",
        "_": "＿",
        "[": "［",
        "]": "］",
        "~": "～",
        "`": "＇",
    }
)


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, "")
    value = value.strip()
    return value if value else default


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def md_escape(text: object, limit: int = 100) -> str:
    """压缩空白、截断，并转义 lark_md 的控制字符。"""
    value = " ".join(str(text or "").split())
    if len(value) > limit:
        value = value[: limit - 1] + "…"
    return value.translate(_ESCAPES)


def plain_trim(text: object, limit: int = 120) -> str:
    """用于 plain_text 元素，只压缩与截断，不做转义。"""
    value = " ".join(str(text or "").split())
    if len(value) > limit:
        value = value[: limit - 1] + "…"
    return value


def local_time(iso: str) -> str:
    """把 ISO 8601 时间转换为北京时间，返回 MM-DD HH:MM。"""
    if not iso:
        return ""
    try:
        stamp = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    return stamp.astimezone(CST).strftime("%m-%d %H:%M")


def now_text() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M")


# --------------------------------------------------------------------------
# 卡片构造
# --------------------------------------------------------------------------


def md_block(text: str) -> dict:
    return {"tag": "div", "text": {"tag": "lark_md", "content": text}}


def plain_block(text: str) -> dict:
    return {"tag": "div", "text": {"tag": "plain_text", "content": text}}


def build_card(title: str, template: str, blocks: list, buttons: list = None) -> dict:
    elements = list(blocks)
    if buttons:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": label},
                        "url": url,
                        "type": "default" if index else "primary",
                    }
                    for index, (label, url) in enumerate(buttons)
                ],
            }
        )
    elements.append(
        plain_block(f"宁夏大学鑫启网安俱乐部 · {now_text()}")
    )
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": elements,
        },
    }


# --------------------------------------------------------------------------
# 各事件类型的渲染
# --------------------------------------------------------------------------

_SQUASH_MARK = re.compile(r"\(#[0-9]+\)\s*$")


def is_squash_artifact(message: str) -> bool:
    """判断提交是否只是变更请求合入后留下的痕迹。"""
    text = (message or "").strip()
    if not text:
        return False
    if _SQUASH_MARK.search(text):
        return True
    return text.startswith("Merge pull request #") or text.startswith("Merge branch ")


def render_push(payload: dict) -> dict | None:
    if payload.get("deleted"):
        return None

    repository = payload.get("repository") or {}
    repo = repository.get("full_name", "")
    short = repo.split("/")[-1] if repo else "仓库"
    ref = payload.get("ref", "")
    commits = payload.get("commits") or []
    compare_url = payload.get("compare", "") or repository.get("html_url", "")

    if not commits:
        return None

    if truthy(env("SKIP_SQUASH_ONLY", "true")) and all(
        is_squash_artifact(item.get("message", "")) for item in commits
    ):
        print("推送仅含合入痕迹，已跳过播报")
        return None

    try:
        limit = max(1, int(env("MAX_COMMITS", str(MAX_COMMITS_DEFAULT))))
    except ValueError:
        limit = MAX_COMMITS_DEFAULT

    is_tag = ref.startswith("refs/tags/")
    branch = ref.split("/", 2)[-1] if ref.count("/") >= 2 else ref
    actor = (payload.get("pusher") or {}).get("name") or (payload.get("sender") or {}).get("login", "")

    if is_tag:
        title = f"标签 · {short}"
        template = "purple"
        meta = [f"**标签** {md_escape(branch)}", f"**推送者** {md_escape(actor)}"]
    else:
        title = f"提交 · {short}"
        template = "blue"
        meta = [
            f"**分支** {md_escape(branch)}",
            f"**提交** {len(commits)} 个",
            f"**推送者** {md_escape(actor)}",
        ]

    blocks = [md_block("　·　".join(meta))]

    lines = []
    for item in commits[:limit]:
        head = (item.get("message") or "").splitlines()[0]
        author = plain_trim((item.get("author") or {}).get("name", ""), 24)
        suffix = f"（{author}）" if author else ""
        lines.append(f"{plain_trim(head, 100)}{suffix}")
    if len(commits) > limit:
        lines.append(f"… 另有 {len(commits) - limit} 个提交")

    # 提交标题用纯文本块，避免标题中的 Markdown 语法被飞书解析
    blocks.append(plain_block("\n".join(lines)))

    buttons = [("查看对比", compare_url)] if compare_url else []
    return build_card(title, template, blocks, buttons)


def render_pull_request(payload: dict) -> dict | None:
    action = payload.get("action", "")
    pr = payload.get("pull_request") or {}
    repository = payload.get("repository") or {}
    short = (repository.get("full_name", "") or "仓库").split("/")[-1]

    state = {
        "opened": ("新开变更请求", "green"),
        "reopened": ("重新打开变更请求", "orange"),
        "ready_for_review": ("变更请求转为待评审", "blue"),
        "converted_to_draft": ("变更请求转为草稿", "grey"),
    }
    if action == "closed":
        merged = bool(pr.get("merged"))
        state["closed"] = ("变更请求已合入" if merged else "变更请求已关闭", "violet" if merged else "grey")

    if action not in state:
        return None

    label, template = state[action]
    author = md_escape((pr.get("user") or {}).get("login", ""))
    head = md_escape((pr.get("head") or {}).get("ref", ""))
    base = md_escape((pr.get("base") or {}).get("ref", ""))

    meta = [f"**标题** {md_escape(pr.get('title', ''), 80)}"]
    second = [f"**作者** {author}", f"**分支** {head} → {base}"]
    if pr.get("draft") and action == "opened":
        second.append("**状态** 草稿")
    meta.append("　·　".join(second))
    meta.append(
        f"**改动** +{pr.get('additions', 0)} −{pr.get('deletions', 0)} · "
        f"{pr.get('changed_files', 0)} 个文件"
    )
    if action == "closed":
        meta.append(f"**关闭于** {local_time(pr.get('closed_at') or pr.get('merged_at') or '')}")

    blocks = [md_block("\n".join(meta))]
    buttons = [("查看变更请求", pr.get("html_url", ""))] if pr.get("html_url") else []
    return build_card(f"{label} · {short}", template, blocks, buttons)


def render_issue(payload: dict) -> dict | None:
    action = payload.get("action", "")
    issue = payload.get("issue") or {}
    repository = payload.get("repository") or {}
    short = (repository.get("full_name", "") or "仓库").split("/")[-1]

    if issue.get("pull_request"):
        return None

    labels = [item.get("name", "") for item in issue.get("labels") or []]

    # 入会工单单独处理：只在正式成为组织成员后播报，见 membership.py
    if "membership" in labels:
        print("入会工单由成员播报流程处理，此处跳过")
        return None

    state = {
        "opened": ("新开工单", "orange"),
        "reopened": ("重新打开工单", "orange"),
        "closed": ("关闭工单", "grey"),
    }
    if action not in state:
        return None

    label, template = state[action]
    author = md_escape((issue.get("user") or {}).get("login", ""))

    meta = [f"**标题** {md_escape(issue.get('title', ''), 80)}", f"**作者** {author}"]
    if labels:
        meta.append(f"**标签** {md_escape('、'.join(labels), 60)}")

    blocks = [md_block("\n".join(meta))]
    buttons = [("查看工单", issue.get("html_url", ""))] if issue.get("html_url") else []
    return build_card(f"{label} · {short}", template, blocks, buttons)


def render_discussion(payload: dict) -> dict | None:
    """讨论区动态。

    GitHub 的 discussion 事件只在开启了 Discussions 的仓库触发。
    讨论下的回复刻意不播报：自我介绍一类的帖子每多一条回复就发一张卡片，
    会把真正的代码动态挤掉。
    """
    action = payload.get("action", "")
    discussion = payload.get("discussion") or {}
    repository = payload.get("repository") or {}
    short = (repository.get("full_name", "") or "仓库").split("/")[-1]

    if not discussion:
        return None

    state = {
        "created": ("新开讨论", "green"),
        "reopened": ("讨论重新打开", "orange"),
        "closed": ("讨论已关闭", "grey"),
        "answered": ("讨论已采纳答案", "green"),
    }
    if action not in state:
        return None

    label, template = state[action]
    author = md_escape((discussion.get("user") or {}).get("login", ""))
    category = md_escape(((discussion.get("category") or {}) or {}).get("name", ""), 30)
    body = plain_trim(discussion.get("body") or "", 160)

    meta = [f"**标题** {md_escape(discussion.get('title', ''), 80)}"]
    second = [f"**发起人** {author}"]
    if category:
        second.append(f"**分类** {category}")
    meta.append("　·　".join(second))

    blocks = [md_block("\n".join(meta))]
    if body and action == "created":
        blocks.append({"tag": "hr"})
        blocks.append(plain_block(body))

    if discussion.get("answer_html_url") and action != "closed":
        blocks.append(plain_block("该讨论已采纳答案，可直接查看结论。"))

    url = discussion.get("html_url", "")
    buttons = [("查看讨论", url)] if url else []
    return build_card(f"{label} · {short}", template, blocks, buttons)


# --------------------------------------------------------------------------
# 新成员公告
# --------------------------------------------------------------------------

# 工单表单渲染为正文后形如「### 中文姓名\n\n张三」，按标题取下一行
_SECTION = re.compile(r"###[ \t]*([^\r\n]+?)[ \t]*\r?\n+([\s\S]*?)(?=\r?\n###[ \t]|$)")


def form_fields(body: str) -> dict:
    """把工单表单正文解析为 {标题: 值}，仅取首行的简短值。"""
    fields = {}
    for match in _SECTION.finditer(body or ""):
        name = match.group(1).strip()
        value = match.group(2).strip()
        first = next((line.strip() for line in value.splitlines() if line.strip()), "")
        if name and first and not first.startswith("- [") and not first.startswith("[x]"):
            fields[name] = first
    return fields


def mask_student_id(value: str) -> str:
    """学号属于个人信息，公告中只保留前 4 位与后 3 位。

    掩码用全角星号：半角 ``****`` 会被飞书按加粗语法解析，破坏排版。
    """
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 8:
        return ""
    return f"{digits[:4]}＊＊＊＊{digits[-3:]}"


def render_invite_result(payload: dict) -> dict | None:
    """公布新成员。

    仅在组织邀请已发出（即审核通过、正式批准加入）时播报；已有待接受邀请、
    申请账号已是成员、邀请失败三种情形都不发公告，避免重复与误导。
    申请人信息取自工单正文，因此调用方必须传入 issues 事件负载。
    """
    if env("INVITE_STATUS") != "invited":
        return None

    issue = payload.get("issue") or {}
    fields = form_fields(issue.get("body") or "")

    login = md_escape(env("INVITE_LOGIN") or (issue.get("user") or {}).get("login", ""), 39)
    name = md_escape(fields.get("中文姓名", ""), 20) or login
    grade = md_escape(fields.get("年级", ""), 20)
    major = md_escape(fields.get("学院与专业", ""), 40)
    interest = md_escape(fields.get("研究兴趣", ""), 80)
    student_id = mask_student_id(fields.get("学号", ""))

    meta = [f"**姓名** {name}", f"**GitHub** {login}"]
    line = []
    if grade:
        line.append(f"**年级** {grade}")
    if student_id:
        line.append(f"**学号** {student_id}")
    if line:
        meta.append("　".join(line))
    if major:
        meta.append(f"**学院专业** {major}")
    if interest:
        meta.append(f"**研究兴趣** {interest}")

    blocks = [md_block("\n".join(meta))]
    blocks.append({"tag": "hr"})
    blocks.append(
        plain_block(
            "欢迎加入宁夏大学鑫启网安俱乐部。组织邀请已发至其 GitHub 注册邮箱，"
            "需本人点击接受后生效，邀请 7 天内有效；接受后默认获得公开仓库只读权限。"
        )
    )

    url = issue.get("html_url") or env("INVITE_ISSUE_URL")
    buttons = [("查看申请工单", url)] if url else []
    return build_card("新成员加入", "green", blocks, buttons)



def render_test() -> dict:
    blocks = [
        md_block(
            "**状态** 配置已生效\n"
            "**说明** 本消息由手动触发发送，后续提交、变更请求与工单将自动播报"
        )
    ]
    return build_card("播报测试", "turquoise", blocks)


def build_card_for(event_name: str, payload: dict) -> dict | None:
    if event_name == "push":
        return render_push(payload)
    if event_name in {"pull_request", "pull_request_target"}:
        return render_pull_request(payload)
    if event_name == "issues":
        return render_issue(payload)
    if event_name == "discussion":
        return render_discussion(payload)
    if event_name == "invite_result":
        return render_invite_result(payload)
    if event_name == "workflow_dispatch":
        return render_test()
    print(f"未处理的触发类型：{event_name}")
    return None


# --------------------------------------------------------------------------
# 发送
# --------------------------------------------------------------------------


def sign(secret: str, timestamp: str) -> str:
    """飞书自定义机器人签名：以 timestamp\\nsecret 为密钥，对空串做 HMAC-SHA256。"""
    key = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(key, b"", digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def send(webhook: str, secret: str, message: dict) -> int:
    """通过群自定义机器人的 Webhook 发送。"""
    parsed = urllib.parse.urlparse(webhook)
    if parsed.scheme != "https" or parsed.hostname not in HOOK_HOSTS:
        print(f"Webhook 地址不合法：{parsed.netloc}", file=sys.stderr)
        return 1
    if "/open-apis/bot/v2/hook/" not in (parsed.path or ""):
        print("Webhook 路径不符合自定义机器人格式", file=sys.stderr)
        return 1

    body = dict(message)
    if secret:
        timestamp = str(int(time.time()))
        body["timestamp"] = timestamp
        body["sign"] = sign(secret, timestamp)

    request = urllib.request.Request(
        webhook,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            text = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        print(f"发送失败：HTTP {error.code} {error.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"发送失败：{error.reason}", file=sys.stderr)
        return 1

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        print(f"响应不是 JSON：{text[:200]}", file=sys.stderr)
        return 1

    # 新版返回 code/msg，旧版返回 StatusCode/StatusMessage
    code = result.get("code", result.get("StatusCode", 0))
    if code not in (0, None):
        print(f"发送被拒绝：{result}", file=sys.stderr)
        return 1
    if result.get("StatusCode") not in (0, None):
        print(f"发送被拒绝：{result}", file=sys.stderr)
        return 1

    print("已发送")
    return 0


# --------------------------------------------------------------------------
# 应用机器人：不走 Webhook，用自建应用的 tenant_access_token 调消息接口
# --------------------------------------------------------------------------

API_BASE = "https://open.feishu.cn/open-apis"


def _post_json(url: str, payload: dict, token: str = "") -> dict | None:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as error:
        print(f"请求失败：HTTP {error.code} {error.reason}", file=sys.stderr)
        return None
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"请求失败：{error}", file=sys.stderr)
        return None


def tenant_access_token(app_id: str, app_secret: str) -> str:
    """换取 tenant_access_token，有效期约 2 小时，需在每次运行内重新获取。"""
    result = _post_json(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
    )
    if not result or result.get("code") != 0:
        print(f"获取 tenant_access_token 失败：{result}", file=sys.stderr)
        return ""
    return result.get("tenant_access_token", "")


def send_app(app_id: str, app_secret: str, chat_id: str, message: dict) -> int:
    """以应用机器人身份向群发送消息。消息体取自卡片的 card 字段。"""
    card = message.get("card")
    if card is None:
        print("应用机器人只支持卡片消息", file=sys.stderr)
        return 1

    token = tenant_access_token(app_id, app_secret)
    if not token:
        return 1

    result = _post_json(
        f"{API_BASE}/im/v1/messages?receive_id_type=chat_id",
        {
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        },
        token,
    )
    if not result or result.get("code") != 0:
        print(f"发送被拒绝：{result}", file=sys.stderr)
        return 1

    print("已发送（应用机器人）")
    return 0


def channel_config(channel: str) -> tuple[str, str]:
    """返回 (webhook, chat_id)。招新群未配置时降级到主群，避免公告丢失。"""
    if channel == "recruit":
        webhook = env("FEISHU_WEBHOOK_RECRUIT")
        chat_id = env("FEISHU_CHAT_ID_RECRUIT")
        if webhook or chat_id:
            return webhook, chat_id
        print("未配置招新群机器人，改发主群")
    return env("FEISHU_WEBHOOK"), env("FEISHU_CHAT_ID")


def deliver(message: dict, channel: str = "main") -> int:
    """按配置选择投递方式：优先群自定义机器人，其次应用机器人。

    两者都没有配置时静默跳过，不把流水线判为失败。
    """
    webhook, chat_id = channel_config(channel)
    if webhook:
        return send(webhook, env("FEISHU_WEBHOOK_SECRET"), message)

    app_id = env("FEISHU_APP_ID")
    app_secret = env("FEISHU_APP_SECRET")
    if app_id and app_secret and chat_id:
        return send_app(app_id, app_secret, chat_id, message)

    print("未配置飞书机器人，跳过播报", file=sys.stderr)
    return 0


def load_event() -> dict:
    path = env("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def is_membership_issue(event_name: str, payload: dict) -> bool:
    """判断本次事件是否为加入社团申请，用于选择招新群。"""
    if event_name != "issues":
        return event_name == "invite_result"
    issue = payload.get("issue") or {}
    if issue.get("pull_request"):
        return False
    labels = [item.get("name", "") for item in issue.get("labels") or []]
    return "membership" in labels


def main() -> int:
    payload = load_event()
    # FEISHU_SCENE 允许调用方覆盖事件类型，用于邀请结果这类非 GitHub 原生事件
    event_name = env("FEISHU_SCENE") or env("GITHUB_EVENT_NAME")

    message = build_card_for(event_name, payload)
    if message is None:
        print("事件不需要播报")
        return 0

    if truthy(env("DRY_RUN")):
        print(json.dumps(message, ensure_ascii=False, indent=2))
        return 0

    # 新成员公告发招新群，其余发主群
    channel = "recruit" if is_membership_issue(event_name, payload) else "main"
    return deliver(message, channel)


if __name__ == "__main__":
    sys.exit(main())
