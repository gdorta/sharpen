#!/usr/bin/env python3
"""Compare the old and new guidance on a fixed set of draft prompts.

For each draft in evals/cases.jsonl, the skill rewrites it twice: once with
the guidance on the main branch and once with the proposed guidance. A judge
scores both without knowing which is which.

The update passes when the new guidance does no harm:
  - its average score is within 0.3 of the old one, or higher, and
  - it loses badly (3 points or more) on at most 2 drafts.

This test catches an update that makes rewrites worse. It cannot tell whether
a new fact is true. Truth rests on the sources being the vendors' own pages.
"""
import concurrent.futures
import json
import os
import pathlib
import random
import re
import statistics
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_skill import render  # noqa: E402
from llm import ask  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases.jsonl"
RUBRIC = ROOT / "evals" / "rubric.md"
REPORT = ROOT / ".work" / "eval_report.md"
REWRITE_MODEL = os.environ.get("SHARPEN_EVAL_MODEL", "claude-sonnet-5-5")
JUDGE_MODEL = os.environ.get("SHARPEN_JUDGE_MODEL", "claude-opus-5-5")
MEAN_SLACK = 0.3
BAD_LOSS = 3
MAX_BAD_LOSSES = 2


def old_guidance():
    if "--old" in sys.argv:
        return pathlib.Path(sys.argv[sys.argv.index("--old") + 1]).read_text()
    return subprocess.run(["git", "show", "HEAD:guidance/guidance.md"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout


def rewrite(guidance, case):
    system = (render(guidance)
              + "\n\nNo web tools are available in this run. Use the guidance snapshot above.")
    target = f"for {case['target']} " if case.get("target") else ""
    return ask(REWRITE_MODEL, system, f"sharpen {target}{case['draft']}", max_tokens=8000)


def judge(case, old_text, new_text):
    flip = random.Random(case["id"]).random() < 0.5
    a, b = (new_text, old_text) if flip else (old_text, new_text)
    system = (RUBRIC.read_text()
              + '\n\nReply with JSON only, in this shape: {"a": 7, "b": 6, "note": "one short sentence"}')
    user = (f"<draft>\n{case['draft']}\n</draft>\n"
            f"<target_model>{case.get('target') or 'not named'}</target_model>\n"
            f"<rewrite_a>\n{a}\n</rewrite_a>\n<rewrite_b>\n{b}\n</rewrite_b>")
    reply = ask(JUDGE_MODEL, system, user, max_tokens=4000)
    scores = json.loads(re.search(r"\{.*\}", reply, re.S).group(0))
    sa, sb = float(scores["a"]), float(scores["b"])
    old_score, new_score = (sb, sa) if flip else (sa, sb)
    return old_score, new_score, str(scores.get("note", ""))


def run(case, old, new):
    old_text, new_text = rewrite(old, case), rewrite(new, case)
    return (case, *judge(case, old_text, new_text))


def main():
    cases = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    old, new = old_guidance(), (ROOT / "guidance" / "guidance.md").read_text()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda case: run(case, old, new), cases))

    old_mean = statistics.mean(r[1] for r in results)
    new_mean = statistics.mean(r[2] for r in results)
    bad = [r for r in results if r[2] <= r[1] - BAD_LOSS]
    passed = new_mean >= old_mean - MEAN_SLACK and len(bad) <= MAX_BAD_LOSSES

    lines = [f"# Guidance test: {'passed' if passed else 'did not pass'}", "",
             f"Average score with the current guidance: {old_mean:.2f}",
             f"Average score with the proposed guidance: {new_mean:.2f}",
             f"Drafts where the proposed guidance lost by {BAD_LOSS} or more: {len(bad)}", "",
             "| Draft | Current | Proposed | Judge's note |", "|---|---|---|---|"]
    for case, old_score, new_score, note in results:
        lines.append(f"| {case['id']} | {old_score:g} | {new_score:g} | {note.replace('|', '/')} |")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6]))

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as out:
            out.write(f"passed={'true' if passed else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
