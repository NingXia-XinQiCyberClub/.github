#!/usr/bin/env python3
"""每周汇总：统计组织内一周的提交、变更请求、工单与成员活跃度，生成播报卡片。

由 weekly-summary.yml 定时调用，也可以本地运行：

    set ORG_STATS_TOKEN=github_pat_xxx
    python summary.py --org NingXia-XinQiCyberClub --dry-run

统计口径默认取最近 7 天，可用 --days 调整。全部数据来自 GitHub REST API，
令牌只从环境变量读取，不打印、不落盘。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notify import CST, build_card, env, md_block, md_escape, plain_block, plain_trim  # noqa: E402

API = "https://api.github.com"
USER_AGENT = "xinqi-weekly-summary"

# 配额有限，次要指标设上限，宁可少统计也不要把整轮请求耗光
MAX_REPOS = 30
MAX_COMMIT_PAGES = 3
MAX_REVIEW_CHECKS = 10
SEARCH_LIMIT = 20


class Budget:
    """记录剩余额度，避免把配额耗尽在次要指标上。"""

    def __init__(self, remaining: int = 400):
        self.remaining = remaining

    def spend(self) -> bool:
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True


class Client:
    def __init__(self, token: str, budget: Budget):
        self.token = token
        self.budget = budget
        self.warnings: list[str] = []

    def get(self, path: str, params: dict | None = None):
        if not self.budget.spend():
            self.warn("接口额度不足，部分指标已跳过")
            return None

        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                remaining = response.headers.get("X-RateLimit-Remaining", "")
                if remaining.isdigit():
                    self.budget.remaining = min(self.budget.remaining, int(remaining))
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            hint = "（令牌权限不足或失效）" if error.code in (401, 403, 404) else ""
            self.warn(f"{path} 返回 {error.code}{hint}")
            return None
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as error:
            self.warn(f"{path} 请求失败：{error}")
            return None

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def search(self, query: str, limit: int = SEARCH_LIMIT) -> list:
        data = self.get("/search/issues", {"q": query, "per_page": limit, "sort": "updated"})
        return data.get("items") or [] if isinstance(data, dict) else []

    def count(self, query: str):
        data = self.get("/search/issues", {"q": query, "per_page": 1})
        if not isinstance(data, dict) or "total_count" not in data:
            return None
        return int(data["total_count"])


def day(offset: int) -> str:
    return (datetime.now(CST) - timedelta(days=offset)).strftime("%Y-%m-%d")


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def repo_of(item: dict) -> str:
    return (item.get("repository_url") or "").rstrip("/").split("/")[-1]


def collect(client: Client, org: str, days: int) -> dict:
    since, until = day(days), day(0)
    window = f"{since}..{until}"

    stats = {
        "since": since,
        "until": until,
        "days": days,
        "commits": Counter(),
        "members": Counter(),
        "commit_total": 0,
        "pr": {"opened": None, "merged": None, "closed": None, "open": None},
        "issue": {"opened": None, "closed": None, "open": None},
        "pending": [],
        "untriaged": [],
    }

    repos = client.get(
        f"/orgs/{org}/repos",
        {"per_page": MAX_REPOS, "sort": "pushed", "direction": "desc", "type": "public"},
    )
    if not isinstance(repos, list):
        client.warn("仓库列表读取失败，提交统计不完整")
        repos = []

    for repo in repos:
        name = repo.get("name") or ""
        pushed = repo.get("pushed_at") or ""
        branch = repo.get("default_branch") or "main"
        if not name or pushed < since:
            continue

        page = 1
        while page <= MAX_COMMIT_PAGES:
            data = client.get(
                f"/repos/{org}/{name}/commits",
                {
                    "since": f"{since}T00:00:00Z",
                    "sha": branch,
                    "per_page": 100,
                    "page": page,
                },
            )
            if not isinstance(data, list) or not data:
                break
            for commit in data:
                author = (commit.get("author") or {}).get("login")
                name_of = ((commit.get("commit") or {}).get("author") or {}).get("name") or "未知"
                stats["commits"][name] += 1
                stats["members"][author or name_of] += 1
                stats["commit_total"] += 1
            if len(data) < 100:
                break
            page += 1

    stats["pr"]["opened"] = client.count(f"org:{org} type:pr created:{window}")
    stats["pr"]["merged"] = client.count(f"org:{org} type:pr is:merged merged:{window}")
    stats["pr"]["closed"] = client.count(f"org:{org} type:pr is:unmerged closed:{window}")
    stats["pr"]["open"] = client.count(f"org:{org} type:pr is:open")

    stats["issue"]["opened"] = client.count(f"org:{org} type:issue created:{window}")
    stats["issue"]["closed"] = client.count(f"org:{org} type:issue closed:{window}")
    stats["issue"]["open"] = client.count(f"org:{org} type:issue is:open")

    # 待评审：已开启、非草稿、尚无他人批准。近 10 条逐条查评审状态，其余按未评审计。
    for index, item in enumerate(client.search(f"org:{org} type:pr is:open draft:false")):
        number, repo = item.get("number"), repo_of(item)
        approved = False
        if repo and index < MAX_REVIEW_CHECKS:
            reviews = client.get(f"/repos/{org}/{repo}/pulls/{number}/reviews", {"per_page": 100})
            if isinstance(reviews, list):
                author = (item.get("user") or {}).get("login")
                approved = any(
                    review.get("state") == "APPROVED"
                    and (review.get("user") or {}).get("login") != author
                    for review in reviews
                )
        if not approved:
            stats["pending"].append(
                {
                    "number": number,
                    "url": item.get("html_url", ""),
                    "title": item.get("title", ""),
                    "repo": repo,
                    "age": (datetime.now(timezone.utc) - parse_time(item.get("created_at"))).days,
                }
            )

    for item in client.search(f"org:{org} type:issue is:open no:label"):
        stats["untriaged"].append(
            {
                "number": item.get("number"),
                "url": item.get("html_url", ""),
                "title": item.get("title", ""),
            }
        )

    return stats


def is_quiet(stats: dict) -> bool:
    """三项指标都必须成功统计且为 0，才算真的没有活动。"""
    values = [
        stats["commit_total"],
        stats["pr"]["opened"],
        stats["pr"]["merged"],
        stats["issue"]["opened"],
    ]
    return all(value == 0 for value in values)


def fmt(value) -> str:
    return "—" if value is None else str(value)


def build_message(stats: dict, warnings: list[str], note: str = "") -> dict:
    since, until, days = stats["since"], stats["until"], stats["days"]
    span = f"{since} 至 {until}（{days} 天）"

    if is_quiet(stats):
        blocks = [md_block(f"**统计区间** {span}\n**本周动态** 无提交、无变更请求、无新工单")]
        if warnings:
            blocks.append(plain_block("统计提示：" + "；".join(warnings[:3])))
        return build_card("周报 · 无活动", "grey", blocks)

    pr, issue = stats["pr"], stats["issue"]
    lines = [f"**统计区间** {span}"]
    lines.append(
        f"**提交** {stats['commit_total']} 次 / {len(stats['commits'])} 个仓库"
    )
    lines.append(
        "**变更请求** 新开 {o} · 合入 {m} · 关闭未合入 {c} · 待处理 {p}".format(
            o=fmt(pr["opened"]), m=fmt(pr["merged"]), c=fmt(pr["closed"]), p=fmt(pr["open"])
        )
    )
    lines.append(
        "**工单** 新开 {o} · 关闭 {c} · 待处理 {p}".format(
            o=fmt(issue["opened"]), c=fmt(issue["closed"]), p=fmt(issue["open"])
        )
    )

    blocks = [md_block("\n".join(lines))]

    if stats["commits"]:
        ranking = sorted(stats["commits"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        body = "\n".join(f"{md_escape(name)}  {count} 次" for name, count in ranking)
        blocks.append({"tag": "hr"})
        blocks.append(md_block(f"**仓库提交排行**\n{body}"))

    if stats["members"]:
        ranking = sorted(stats["members"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        body = "　·　".join(f"{plain_trim(name, 24)}（{count}）" for name, count in ranking)
        blocks.append(md_block(f"**活跃成员** {body}"))

    if stats["pending"]:
        blocks.append({"tag": "hr"})
        shown = stats["pending"][:5]
        text = "**待评审变更请求**\n" + "\n".join(
            f"[#{item['number']}]({item['url']}) {md_escape(item['title'], 60)}"
            f"（{md_escape(item['repo'], 24)}，{item['age']} 天）"
            for item in shown
        )
        rest = len(stats["pending"]) - len(shown)
        if rest > 0:
            text += f"\n… 另有 {rest} 条"
        blocks.append(md_block(text))

    if stats["untriaged"]:
        shown = stats["untriaged"][:5]
        text = "**未分类工单**\n" + "\n".join(
            f"[#{item['number']}]({item['url']}) {md_escape(item['title'], 60)}" for item in shown
        )
        rest = len(stats["untriaged"]) - len(shown)
        if rest > 0:
            text += f"\n… 另有 {rest} 条"
        blocks.append(md_block(text))

    # 有积压时把卡片染成橙色，便于一眼看出需要处理
    template = "orange" if stats["pending"] or stats["untriaged"] else "blue"

    if warnings:
        blocks.append({"tag": "hr"})
        blocks.append(plain_block("统计提示：" + "；".join(warnings[:3])))
    if note:
        blocks.append(plain_block(note))

    return build_card(f"周报 · {span}", template, blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成组织周报卡片")
    parser.add_argument("--org", default=os.environ.get("ORG", ""), help="组织名")
    parser.add_argument(
        "--days", type=int, default=int(os.environ.get("DAYS", "7")), help="统计天数"
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印卡片 JSON，不发送")
    args = parser.parse_args()

    if not args.org:
        print("缺少组织名，使用 --org 或环境变量 ORG", file=sys.stderr)
        return 2

    token = os.environ.get("ORG_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    note = ""
    if not token:
        note = "未配置 ORG_STATS_TOKEN，本次仅能统计公开数据，额度上限为每小时 60 次"
    elif not os.environ.get("ORG_STATS_TOKEN"):
        note = "使用默认令牌统计，跨仓库数据可能不完整"

    client = Client(token, Budget())
    stats = collect(client, args.org, max(1, args.days))
    message = build_message(stats, client.warnings, note)

    if args.dry_run:
        print(json.dumps(message, ensure_ascii=False, indent=2))
        return 0

    from notify import deliver

    return deliver(message, "main")


if __name__ == "__main__":
    sys.exit(main())
