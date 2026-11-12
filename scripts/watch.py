#!/usr/bin/env python3
"""Check the official prompting pages for changes. Makes no model calls.

Reads guidance/sources.json, fetches each page, and compares its hash with
guidance/state.json. Every page read is saved under .work/sources/. update.py
reads the changed ones and review.py reads them all.

  python scripts/watch.py           normal weekly check
  python scripts/watch.py --init    record today's hashes, report no change
  python scripts/watch.py --force   treat every page as changed
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES = ROOT / "guidance" / "sources.json"
STATE = ROOT / "guidance" / "state.json"
WORK = ROOT / ".work"
MAX_BYTES = 2_000_000
MIN_CHARS = 500
USER_AGENT = "sharpen-guidance-watcher (+https://github.com/gdorta/sharpen)"


def fetch(url, allowed):
    """Return the page text. Only https, only allowed hosts, redirects included."""
    parts = urllib.parse.urlparse(url)
    if parts.scheme != "https" or parts.hostname not in allowed:
        raise ValueError(f"not an allowed address: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        landed = urllib.parse.urlparse(response.geturl())
        if landed.scheme != "https" or landed.hostname not in allowed:
            raise ValueError(f"redirected off the allowed hosts: {response.geturl()}")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("page is larger than expected")
    text = body.decode("utf-8", errors="replace")
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip() + "\n"
    if len(text) < MIN_CHARS:
        raise ValueError("page is shorter than expected")
    if text.lstrip()[:15].lower().startswith(("<!doctype", "<html")):
        raise ValueError("got a web page where markdown was expected")
    return text


def discover(rule, text):
    """Find per-model pages linked from a hub page, so new models are picked up."""
    paths = sorted(set(re.findall(rule["path_pattern"], text)))[: rule.get("max", 15)]
    found = []
    for path in paths:
        slug = path.rstrip("/").split("/")[-1]
        found.append({
            "id": f"{rule['vendor']}-{slug}",
            "vendor": rule["vendor"],
            "url": f"{rule['host']}{path}.md",
            "discovered": True,
        })
    return found


def main():
    init = "--init" in sys.argv
    force = "--force" in sys.argv
    today = datetime.date.today().isoformat()

    config = json.loads(SOURCES.read_text())
    allowed = set(config["allowed_domains"])
    state = json.loads(STATE.read_text()) if STATE.exists() else {"sources": {}}
    known = state.setdefault("sources", {})

    (WORK / "sources").mkdir(parents=True, exist_ok=True)
    queue = list(config["sources"])
    texts, changed, errors, everything = {}, [], {}, []

    index = 0
    while index < len(queue):
        source = queue[index]
        index += 1
        try:
            text = fetch(source["url"], allowed)
        except Exception as error:  # keep the old hash and try again next run
            errors[source["id"]] = str(error)
            print(f"could not read {source['id']}: {error}")
            continue
        texts[source["id"]] = text
        page = WORK / "sources" / f"{source['id']}.md"
        page.write_text(text)
        everything.append({"id": source["id"], "vendor": source["vendor"], "url": source["url"],
                           "file": str(page.relative_to(ROOT))})
        for rule in config.get("discover", []):
            if rule["from"] == source["id"]:
                have = {item["id"] for item in queue}
                queue.extend(item for item in discover(rule, text) if item["id"] not in have)

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        before = known.get(source["id"], {}).get("sha256")
        if digest != before or force:
            known[source["id"]] = {"url": source["url"], "vendor": source["vendor"],
                                   "sha256": digest, "last_changed": today}
            if not init:
                changed.append({"id": source["id"], "vendor": source["vendor"],
                                "url": source["url"], "file": str(page.relative_to(ROOT)),
                                "new": before is None})
        print(f"{'changed  ' if digest != before else 'unchanged'} {source['id']}")

    if not texts:
        print("no page could be read, so nothing was checked")
        return 1

    state["last_checked"] = today
    state["errors"] = errors
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    (WORK / "changed.json").write_text(json.dumps(changed, indent=2) + "\n")
    (WORK / "all_sources.json").write_text(json.dumps(everything, indent=2) + "\n")

    flag = "true" if changed else "false"
    print(f"\n{len(texts)} pages read, {len(changed)} changed, {len(errors)} unreadable")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as out:
            out.write(f"changed={flag}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
