#!/usr/bin/env python3
"""
fetch_news.py — 财经新闻批量抓取脚本

用法：
  python3 fetch_news.py [--sources all|intl|cn|crypto|tech] [--limit 10]

输出：标准输出，每条新闻一行，格式：[来源] 标题 | URL
"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

# ── 数据源定义 ─────────────────────────────────────────────

RSS_SOURCES = {
    "intl": [
        ("WSJ Markets",    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
        ("FT",             "https://www.ft.com/rss/home"),
        ("Economist",      "https://www.economist.com/finance-and-economics/rss.xml"),
        ("Benzinga",       "https://www.benzinga.com/feed"),
        ("MarketWatch",    "https://feeds.marketwatch.com/marketwatch/topstories/"),
        ("CNBC",           "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
        ("Fed Press",      "https://www.federalreserve.gov/feeds/press_all.xml"),
    ],
    "cn": [
        ("澎湃新闻",        "https://feedx.net/rss/thepaper.xml"),
        ("FT中文",          "https://feedx.net/rss/ftchinese.xml"),
        ("36氪",            "https://36kr.com/feed"),
    ],
    "crypto": [
        ("CoinDesk",       "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph",  "https://cointelegraph.com/rss"),
    ],
    "tech": [
        ("TechCrunch",     "https://techcrunch.com/feed/"),
        ("Hacker News",    "https://hnrss.org/best"),
    ],
}

# ── 工具函数 ──────────────────────────────────────────────

def curl(url: str, timeout: int = 8) -> str:
    """HTTP GET via curl."""
    result = subprocess.run(
        ["curl", "-sL", url, "--max-time", str(timeout), "-A",
         "Mozilla/5.0 (compatible; financial-data-skill/1.0)"],
        capture_output=True, text=True
    )
    return result.stdout


def parse_rss(source_name: str, xml_text: str, limit: int) -> list[dict]:
    """解析标准 RSS XML，返回文章列表。"""
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link") or "").strip()
            desc  = (item.findtext("description") or "").strip()[:160]
            if title:
                items.append({"source": source_name, "title": title,
                               "url": link, "summary": desc})
    except ET.ParseError as e:
        print(f"[WARN] {source_name} parse error: {e}", file=sys.stderr)
    return items


def fetch_cailian(limit: int) -> list[dict]:
    """财联社电报（JSON API）。"""
    url = ("https://www.cls.cn/nodeapi/updateTelegraphList"
           "?app=CailianpressWeb&os=web&sv=8.4.6&rn=30")
    raw = curl(url)
    items = []
    try:
        data = json.loads(raw)
        for item in data["data"]["roll_data"][:limit]:
            title = (item.get("title") or item.get("content", ""))[:120]
            items.append({"source": "财联社", "title": title,
                           "url": f"https://www.cls.cn/detail/{item.get('id','')}", "summary": ""})
    except Exception as e:
        print(f"[WARN] 财联社 fetch error: {e}", file=sys.stderr)
    return items


def fetch_sina(limit: int) -> list[dict]:
    """新浪财经滚动（JSON API）。"""
    url = ("https://feed.mix.sina.com.cn/api/roll/get"
           "?pageid=153&lid=2516&k=&num=20&page=1")
    raw = curl(url)
    items = []
    try:
        data = json.loads(raw)
        for item in data["result"]["data"][:limit]:
            items.append({"source": "新浪财经", "title": item["title"],
                           "url": item.get("url", ""), "summary": ""})
    except Exception as e:
        print(f"[WARN] 新浪财经 fetch error: {e}", file=sys.stderr)
    return items

# ── 主逻辑 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="财经新闻抓取工具")
    parser.add_argument("--sources", default="all",
                        choices=["all", "intl", "cn", "crypto", "tech"],
                        help="新闻源分类（默认 all）")
    parser.add_argument("--limit", type=int, default=8,
                        help="每个来源最多条数（默认 8）")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出")
    args = parser.parse_args()

    # 确定要抓取的 RSS 源
    if args.sources == "all":
        rss_groups = list(RSS_SOURCES.values())
    else:
        rss_groups = [RSS_SOURCES.get(args.sources, [])]

    all_items = []

    # 抓取 RSS
    for group in rss_groups:
        for name, url in group:
            xml_text = curl(url)
            items = parse_rss(name, xml_text, args.limit)
            all_items.extend(items)

    # 抓取中文 JSON 源（当 sources 是 all 或 cn 时）
    if args.sources in ("all", "cn"):
        all_items.extend(fetch_cailian(args.limit))
        all_items.extend(fetch_sina(args.limit))

    # 输出
    if args.json:
        print(json.dumps(all_items, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"财经新闻抓取结果 — {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
        print(f"共 {len(all_items)} 条 | 来源筛选: {args.sources} | 每源限 {args.limit} 条")
        print(f"{'='*60}\n")
        for item in all_items:
            print(f"[{item['source']}] {item['title']}")
            if item.get("url"):
                print(f"  {item['url']}")
            if item.get("summary"):
                print(f"  {item['summary']}")
            print()


if __name__ == "__main__":
    main()
