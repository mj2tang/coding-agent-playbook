#!/usr/bin/env python3
"""Detect new posts in RSS/Atom feeds listed in watch/sources.json.

  python3 scripts/watch_sources.py            # print new items as markdown, update watch/state.json
  python3 scripts/watch_sources.py --init     # record current items without reporting them
  python3 scripts/watch_sources.py --dry-run  # report without updating state

Exit 0 with no output when nothing is new. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "watch" / "sources.json"
STATE = ROOT / "watch" / "state.json"
ATOM = "{http://www.w3.org/2005/Atom}"


def parse_feed(xml_text: str) -> list[dict]:
    """Return [{title, link, date}] for RSS 2.0 or Atom feeds."""
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "date": (item.findtext("pubDate") or "").strip(),
        })
    for entry in root.iter(f"{ATOM}entry"):
        link = entry.find(f"{ATOM}link")
        items.append({
            "title": (entry.findtext(f"{ATOM}title") or "").strip(),
            "link": link.get("href", "") if link is not None else "",
            "date": (entry.findtext(f"{ATOM}updated") or "").strip(),
        })
    return [i for i in items if i["link"]]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "coding-agent-playbook-watcher/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def new_items(source: dict, items: list[dict], seen: set[str]) -> list[dict]:
    pattern = re.compile(source.get("include") or ".*")
    return [i for i in items if pattern.search(i["link"]) and i["link"] not in seen]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--init", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    sources = json.loads(SOURCES.read_text())["sources"]
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    report = []
    for src in sources:
        try:
            items = parse_feed(fetch(src["feed"]))
        except Exception as e:  # one broken feed shouldn't hide the others
            print(f"warning: {src['name']}: {e}", file=sys.stderr)
            continue
        seen = set(state.get(src["name"], []))
        fresh = new_items(src, items, seen)
        if fresh and not a.init:
            report.append(f"### {src['name']}\nSuggested doc to update: `{src.get('update', '-')}`\n")
            report += [f"- [{i['title']}]({i['link']}) {i['date']}" for i in fresh]
            report.append("")
        state[src["name"]] = sorted(seen | {i["link"] for i in items})
    if not a.dry_run:
        STATE.write_text(json.dumps(state, indent=2) + "\n")
    if report:
        print("\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
