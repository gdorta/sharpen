#!/usr/bin/env python3
"""Fixed safety checks on guidance.md. No model calls.

The guidance file is read by other people's assistants, so before any update
ships it has to pass these checks. They are deliberately simple and strict.
"""
import json
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_CHARS = 24_000
MIN_CHARS = 3_000
REQUIRED = ["# Sharpen guidance", "## Every prompt, every model", "## Remove on sight",
            "## Prompt types", "## Claude models", "## OpenAI models", "## Choosing a model"]
BANNED = ["ignore previous", "ignore all previous", "ignore the above", "disregard your",
          "curl ", "wget ", "api key", "password", "<script", "base64", "rm -rf"]


def check(text, allowed):
    problems = []
    if not MIN_CHARS <= len(text) <= MAX_CHARS:
        problems.append(f"length is {len(text)} characters, expected {MIN_CHARS} to {MAX_CHARS}")
    if not re.search(r"(?m)^Verified: \d{4}-\d{2}-\d{2}$", text):
        problems.append("missing a 'Verified: YYYY-MM-DD' line")
    place = -1
    for heading in REQUIRED:
        found = text.find("\n" + heading + "\n") if place >= 0 else (0 if text.startswith(heading) else -1)
        if found < 0:
            problems.append(f"missing heading, or heading out of order: {heading}")
        elif found < place:
            problems.append(f"heading out of order: {heading}")
        else:
            place = found
    for url in re.findall(r"https?://[^\s)>\]\"']+", text):
        parts = urllib.parse.urlparse(url)
        if parts.scheme != "https" or parts.hostname not in allowed:
            problems.append(f"link outside the allowed sites: {url}")
    lowered = text.lower()
    for phrase in BANNED:
        if phrase in lowered:
            problems.append(f"contains a banned phrase: {phrase.strip()}")
    if re.search(r"```(bash|sh|shell|zsh|powershell|python|js|javascript)\b", lowered):
        problems.append("contains a runnable code block")
    if "—" in text:
        problems.append("contains an em dash")
    return problems


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "guidance" / "guidance.md"
    allowed = set(json.loads((ROOT / "guidance" / "sources.json").read_text())["allowed_domains"])
    problems = check(path.read_text(), allowed)
    for problem in problems:
        print(f"FAIL  {problem}")
    if not problems:
        print(f"OK    {path.name} passes every check")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
