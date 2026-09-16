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
        if len(excerpt) > 140:
            excerpt = excerpt[:137].rstrip() + "…"
        enclosure = item.find("enclosure")
        image = (enclosure.get("url") or "").strip() if enclosure is not None else ""
        posts.append(
            {
                "id": slug_from(url),
                "title": title,
                "url": url,
                "date": dt.date().isoformat(),
                "displayDate": dt.strftime("%-d %b %Y"),
                "excerpt": excerpt,
                "image": image,
                "source": "wix",
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def main() -> None:
    wix = load_feed()
    catalog = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "posts": wix}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(catalog['posts'])} posts to {OUT}")


if __name__ == "__main__":
    main()
