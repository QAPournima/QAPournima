#!/usr/bin/env python3
"""Refresh the auto-generated featured projects block in README.md."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
START = "<!-- FEATURED-AUTO:START -->"
END = "<!-- FEATURED-AUTO:END -->"

USERNAME = "QAPournima"
EXCLUDE = {
    "QAPournima",
    "Portfolio",
    "Ridhaan-Namkaran-Glimpses",
    "MysticalMemoir",
    "Google_-Extensions",
}
# Already shown as curated cards in README.
CURATED = {
    "Zap-Prototype",
    "playwrightWithJavascript",
    "QAAutomationTest_Mobile",
}


def github_get(url: str) -> list | dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def list_public_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        data = github_get(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated&page={page}"
        )
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("private")
        and repo["name"] not in EXCLUDE
        and repo["name"] not in CURATED
    ]


def card(repo: dict) -> str:
    name = repo["name"].replace("_", " ").replace("-", " ")
    url = repo["html_url"]
    desc = (repo.get("description") or "GitHub project").strip()
    if len(desc) > 90:
        desc = desc[:87] + "..."
    lang = (repo.get("language") or "").strip()
    lang_bit = f"<br/><code>{lang}</code>" if lang else ""
    return (
        f'<td width="50%" valign="top">\n'
        f'<a href="{url}"><strong>{name}</strong></a><br/>\n'
        f"{desc}{lang_bit}\n"
        f"</td>"
    )


def render(repos: list[dict]) -> str:
    if not repos:
        return f"{START}\n{END}"
    rows = ["### More GitHub Projects", "", "<table>"]
    for i in range(0, len(repos), 2):
        chunk = repos[i : i + 2]
        rows.append("<tr>")
        rows.extend(card(repo) for repo in chunk)
        if len(chunk) == 1:
            rows.append("<td></td>")
        rows.append("</tr>")
    rows.append("</table>")
    return f"{START}\n" + "\n".join(rows) + f"\n{END}"


def main() -> None:
    text = README.read_text()
    if START not in text or END not in text:
        raise SystemExit("README.md is missing FEATURED-AUTO markers")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    block = render(list_public_repos())
    README.write_text(before + block + after)
    print("Updated featured projects in README.md")


if __name__ == "__main__":
    main()
