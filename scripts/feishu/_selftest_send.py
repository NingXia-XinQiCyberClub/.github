#!/usr/bin/env python3
"""发送环节测试：拦截 urlopen，检查签名、地址校验与错误码处理，不产生真实请求。

用法：python _selftest_send.py
"""

import base64
import hashlib
import hmac
import io
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import notify  # noqa: E402

HOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/00000000-0000-0000-0000-000000000000"
MESSAGE = {"msg_type": "text", "content": {"text": "hi"}}
captured = {}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def ok(req, timeout=0):
    captured["url"] = req.full_url
    captured["body"] = json.loads(req.data.decode("utf-8"))
    return FakeResponse(json.dumps({"code": 0, "msg": "success"}).encode())


def rejected(req, timeout=0):
    return FakeResponse(json.dumps({"code": 9499, "msg": "Bad Request"}).encode())


def main():
    failed = 0

    def check(name, condition, detail=""):
        nonlocal failed
        if condition:
            print(f"[通过] {name}")
        else:
            print(f"[失败] {name} {detail}")
            failed += 1

    urllib.request.urlopen = ok
    captured.clear()
    check("无密钥发送成功", notify.send(HOOK, "", MESSAGE) == 0)
    check("无密钥不带签名字段", "sign" not in captured["body"], captured["body"])
    check("原文不被改写", captured["body"]["msg_type"] == "text")

    captured.clear()
    check("有密钥发送成功", notify.send(HOOK, "demo", MESSAGE) == 0)
    body = captured["body"]
    expected = base64.b64encode(
        hmac.new(f"{body['timestamp']}\ndemo".encode(), b"", hashlib.sha256).digest()
    ).decode()
    check("签名字段存在", "sign" in body)
    check("时间戳为字符串", isinstance(body["timestamp"], str))
    check("签名与独立实现一致", body["sign"] == expected, body.get("sign"))

    # 固定向量，防止后续改动签名算法而无人察觉。取值与飞书官方示例一致：
    # secret=demo，timestamp=1599360473
    check(
        "签名固定向量",
        notify.sign("demo", "1599360473") == "l1N0gAcBjdwBvGm1xMjOF0XSyaLRpR7tuO5dHfhAYc8=",
        notify.sign("demo", "1599360473"),
    )

    check("拦截非飞书域名", notify.send("https://evil.example.com/open-apis/bot/v2/hook/x", "", MESSAGE) == 1)
    check("拦截 http 明文", notify.send("http://open.feishu.cn/open-apis/bot/v2/hook/x", "", MESSAGE) == 1)
    check("拦截错误路径", notify.send("https://open.feishu.cn/other/path", "", MESSAGE) == 1)

    urllib.request.urlopen = rejected
    check("飞书错误码视为失败", notify.send(HOOK, "", MESSAGE) == 1)

    def boom(req, timeout=0):
        raise urllib.error.URLError("connection refused")

    urllib.request.urlopen = boom
    check("网络异常视为失败", notify.send(HOOK, "", MESSAGE) == 1)

    failed += check_app_bot()

    print("\n全部通过" if failed == 0 else f"\n失败 {failed} 项")
    return 1 if failed else 0


CARD_MESSAGE = {
    "msg_type": "interactive",
    "card": {
        "config": {"wide_screen_mode": True},
        "header": {"template": "blue", "title": {"tag": "plain_text", "content": "测试"}},
        "elements": [],
    },
}


def check_app_bot():
    """应用机器人路径：换 token、发消息、以及两种投递方式的优先级。"""
    failed = 0
    calls = []

    def check(name, condition, detail=""):
        nonlocal failed
        if condition:
            print(f"[通过] {name}")
        else:
            print(f"[失败] {name} {detail}")
            failed += 1

    def router(req, timeout=0):
        url = req.full_url
        body = json.loads(req.data.decode("utf-8"))
        calls.append({"url": url, "body": body, "auth": req.get_header("Authorization")})
        if "tenant_access_token" in url:
            return FakeResponse(
                json.dumps({"code": 0, "tenant_access_token": "t-demo", "expire": 7140}).encode()
            )
        return FakeResponse(json.dumps({"code": 0, "data": {"message_id": "om_x"}}).encode())

    urllib.request.urlopen = router

    original_env = dict(notify.os.environ)
    notify.os.environ.clear()
    notify.os.environ.update(
        {
            "FEISHU_APP_ID": "cli_demo",
            "FEISHU_APP_SECRET": "s3cret",
            "FEISHU_CHAT_ID": "oc_demo",
        }
    )

    calls.clear()
    code = notify.deliver(CARD_MESSAGE, "main")
    check("应用机器人发送成功", code == 0)
    token_call = calls[0]
    check("先换 token", token_call["url"].endswith("/auth/v3/tenant_access_token/internal"))
    check("token 请求带应用凭据", token_call["body"].get("app_id") == "cli_demo")
    send_call = calls[-1] if len(calls) > 1 else {}
    check(
        "消息接口使用 chat_id",
        "receive_id_type=chat_id" in (send_call.get("url") or "")
        and send_call["body"].get("receive_id") == "oc_demo",
        send_call.get("url"),
    )
    check("以 Bearer 传递 token", send_call.get("auth") == "Bearer t-demo")
    check(
        "content 为卡片 JSON 字符串",
        json.loads(send_call["body"]["content"]).get("header", {}).get("template") == "blue",
    )

    # 同时配置 webhook 时，webhook 优先，不调用应用接口
    calls.clear()
    notify.os.environ["FEISHU_WEBHOOK"] = HOOK
    code = notify.deliver(CARD_MESSAGE, "main")
    check("webhook 优先于应用机器人", code == 0 and len(calls) == 1 and calls[0]["url"] == HOOK)

    # 招新群缺失时降级到主群 webhook
    calls.clear()
    notify.os.environ["FEISHU_WEBHOOK_RECRUIT"] = ""
    notify.os.environ["FEISHU_CHAT_ID_RECRUIT"] = ""
    code = notify.deliver(CARD_MESSAGE, "recruit")
    check("招新群缺失时回落主群", code == 0 and calls and calls[0]["url"] == HOOK)

    # 主群配多个机器人时逐个发送
    calls.clear()
    notify.os.environ["FEISHU_WEBHOOK"] = f"{HOOK},{HOOK.replace('0000-0000-0000-0000', '1111-1111-1111-1111')}"
    code = notify.deliver(CARD_MESSAGE, "main")
    check("多机器人逐个发送", code == 0 and len(calls) == 2, len(calls))

    # 其中一个失败要判定为失败，便于在 Actions 里发现
    def flaky(req, timeout=0):
        if "1111-1111" in req.full_url:
            return FakeResponse(json.dumps({"code": 9499, "msg": "Bad Request"}).encode())
        return FakeResponse(json.dumps({"code": 0, "msg": "success"}).encode())

    urllib.request.urlopen = flaky
    check("多机器人部分失败判定为失败", notify.deliver(CARD_MESSAGE, "main") == 1)

    # 应用机器人也可以配多个 chat_id
    urllib.request.urlopen = router
    notify.os.environ.clear()
    notify.os.environ.update(
        {
            "FEISHU_APP_ID": "cli_demo",
            "FEISHU_APP_SECRET": "s3cret",
            "FEISHU_CHAT_ID": "oc_one,oc_two",
        }
    )
    calls.clear()
    check("应用机器人多群发送", notify.deliver(CARD_MESSAGE, "main") == 0)
    sent = [c for c in calls if "receive_id_type" in (c["url"] or "")]
    check(
        "应用机器人多群各发一次",
        [c["body"]["receive_id"] for c in sent] == ["oc_one", "oc_two"],
        [c["body"]["receive_id"] for c in sent],
    )

    # 企业接口返回错误码
    def denied(req, timeout=0):
        return FakeResponse(json.dumps({"code": 230013, "msg": "Bot has NO availability"}).encode())

    urllib.request.urlopen = denied
    notify.os.environ.pop("FEISHU_WEBHOOK", None)
    check("应用接口错误码视为失败", notify.deliver(CARD_MESSAGE, "main") == 1)

    notify.os.environ.clear()
    notify.os.environ.update(original_env)
    return failed


if __name__ == "__main__":
    sys.exit(main())
