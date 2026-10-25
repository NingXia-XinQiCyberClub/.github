#!/usr/bin/env python3
"""周报渲染测试：用构造的统计数据检查卡片结构，不联网。

用法：python _selftest_summary.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import summary  # noqa: E402
from _selftest import check_lark_md, walk_lark_md, walk_urls  # noqa: E402

EMPTY_PR = {"opened": 0, "merged": 0, "closed": 0, "open": 0}
EMPTY_ISSUE = {"opened": 0, "closed": 0, "open": 0}
EMPTY_DISC = {"opened": 0, "items": [], "unanswered": 0}


def base_stats(**overrides):
    stats = {
        "since": "2026-10-18",
        "until": "2026-10-25",
        "days": 7,
        "commits": {"guide": 9, "site": 4},
        "members": {"zhangsan": 8, "lisi": 5},
        "commit_total": 13,
        "pr": {"opened": 3, "merged": 2, "closed": 1, "open": 5},
        "issue": {"opened": 4, "closed": 2, "open": 7},
        "discussion": {
            "opened": 2,
            "unanswered": 1,
            "items": [
                {
                    "number": 5,
                    "title": "新人如何入门 Web 安全？",
                    "url": "https://github.com/NingXia-XinQiCyberClub/guide/discussions/5",
                    "author": "wangwu",
                    "category": "问答",
                    "comments": 4,
                    "answered": True,
                }
            ],
        },
        "pending": [
            {
                "title": "docs: 补充 0.9 节",
                "number": 12,
                "url": "https://github.com/NingXia-XinQiCyberClub/guide/pull/12",
                "repo": "guide",
                "age": 3,
            }
        ],
        "untriaged": [
            {
                "title": "[加入] 张三",
                "number": 7,
                "url": "https://github.com/NingXia-XinQiCyberClub/.github/issues/7",
            }
        ],
    }
    stats.update(overrides)
    return stats


CASES = [
    ("正常一周", base_stats(), [], ""),
    (
        "无活动",
        base_stats(
            commits={},
            members={},
            commit_total=0,
            pr=EMPTY_PR,
            issue=EMPTY_ISSUE,
            discussion=EMPTY_DISC,
            pending=[],
            untriaged=[],
        ),
        [],
        "",
    ),
    (
        "统计失败不算无活动",
        base_stats(commit_total=0, commits={}, members={}, pr={"opened": None, "merged": None, "closed": None, "open": None}, issue=EMPTY_ISSUE, discussion=EMPTY_DISC, pending=[], untriaged=[]),
        ["/orgs/x/repos 返回 403（令牌权限不足或失效）"],
        "",
    ),
    (
        "讨论区统计失败",
        base_stats(discussion={"opened": None, "items": [], "unanswered": None}),
        ["讨论区统计需要令牌，已跳过"],
        "",
    ),
    ("有积压", base_stats(), [], ""),
    (
        "超长标题",
        base_stats(
            pending=[
                {"title": "很长的标题" * 30, "number": 1, "url": "https://github.com/a/b/pull/1", "repo": "b", "age": 9}
            ]
            * 8,
        ),
        [],
        "使用默认令牌统计，跨仓库数据可能不完整",
    ),
    (
        "恶意语法",
        base_stats(
            untriaged=[{"title": "[点我](http://evil) **粗** `x`", "number": 2, "url": "https://github.com/a/b/issues/2"}],
            discussion={
                "opened": 1,
                "unanswered": 1,
                "items": [
                    {
                        "number": 9,
                        "title": "[点我](http://evil) ~~删~~",
                        "url": "https://github.com/a/b/discussions/9",
                        "author": "**坏**",
                        "category": "问答",
                        "comments": 0,
                        "answered": False,
                    }
                ],
            },
        ),
        [],
        "",
    ),
]


def main():
    failed = 0
    for name, stats, warnings, note in CASES:
        card = summary.build_message(stats, warnings, note)
        json.dumps(card, ensure_ascii=False)
        header = card["card"]["header"]

        for path, content in walk_lark_md(card):
            problem = check_lark_md(content)
            if problem:
                print(f"[失败] {name}：{path} {problem}\n       {content}")
                failed += 1

        for url in walk_urls(card):
            if "evil" in url:
                print(f"[失败] {name}：出现非 GitHub 链接 {url}")
                failed += 1

        text = json.dumps(card, ensure_ascii=False)
        if "很长的标题" in text and len(text) > 4000:
            print(f"[失败] {name}：卡片体积 {len(text)} 字节，超出飞书限制")
            failed += 1

        body = card["card"]["elements"][0]["text"]["content"].replace("\n", " / ")
        print(f"[通过] {name} → {header['title']['content']} [{header['template']}] | {body[:60]}")
        print(f"       {len(text)} 字节，{len(card['card']['elements'])} 个元素")

    print("\n全部通过" if failed == 0 else f"\n失败 {failed} 项")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
