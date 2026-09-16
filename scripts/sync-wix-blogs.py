#!/usr/bin/env python3
"""Pull Wix blog posts from RSS into writing/catalog.json."""

from __future__ import annotations

import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = "https://pournimacsm.wixsite.com/qapournima/blog-feed.xml"
OUT = ROOT / "writing" / "catalog.json"

MEDIUM = [
    {
        "id": "ai-driven-testing",
        "title": "AI-Driven Testing",
        "url": "https://medium.com/@qapournima/ai-driven-testing-revolutionizing-software-testing-with-automation-and-efficiency-4b5308362560",
        "date": "2024-01-01",
        "displayDate": "Medium",
        "excerpt": "Using automation and AI to test faster without losing quality.",
        "source": "medium",
    },
    {
        "id": "breaking-silos-in-agile-teams",
        "title": "Breaking Silos in Agile Teams",
        "url": "https://medium.com/@qapournima/breaking-silos-in-agile-teams-fostering-collaboration-and-alignment-863f5aea3f2c",
        "date": "2024-01-01",
        "displayDate": "Medium",
        "excerpt": "Collaboration and alignment across engineering and QA.",
        "source": "medium",
    },
]


def clean(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def slug_from(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def load_feed() -> list[dict]:
    req = urllib.request.Request(FEED, headers={"User-Agent": "QAPournima-blog-sync"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read()
    root = ET.fromstring(xml)
    posts = []
    for item in root.findall(".//item"):
        def tag(name: str) -> str:
            el = item.find(name)
            return (el.text or "").strip() if el is not None else ""

        title = clean(tag("title"))
        url = tag("link")
        raw_date = tag("pubDate")
        try:
            dt = parsedate_to_datetime(raw_date).astimezone(timezone.utc)
        except (TypeError, ValueError):
            dt = datetime.now(timezone.utc)
        excerpt = clean(tag("description"))
        if len(excerpt) > 220:
            excerpt = excerpt[:217].rstrip() + "…"
        posts.append(
            {
                "id": slug_from(url),
                "title": title,
                "url": url,
                "date": dt.date().isoformat(),
                "displayDate": dt.strftime("%-d %b %Y"),
                "excerpt": excerpt,
                "source": "wix",
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def main() -> None:
    wix = load_feed()
    wix_titles = {p["title"].lower() for p in wix}
    extra = [p for p in MEDIUM if p["title"].lower() not in wix_titles]
    catalog = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "posts": wix + extra}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(catalog['posts'])} posts to {OUT}")


if __name__ == "__main__":
    main()
