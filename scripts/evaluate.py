#!/usr/bin/env python3
"""Compare the old and new guidance on a fixed set of draft prompts.

For each draft in evals/cases.jsonl, the skill rewrites it twice: once with
the guidance on the main branch and once with the proposed guidance. A judge
scores both without knowing which is which.

Both labs take part equally. Half the drafts are rewritten by a Claude model
and half by an OpenAI model. Each pair is judged by the other lab's model, so
neither lab grades its own work. With only one lab's key present, that lab
does both jobs.

The update passes when the new guidance does no harm:
  - overall, its average score is within 0.3 of the old one, or higher,
  - for each lab's half, it is within 0.6, and
  - it loses badly (3 points or more) on at most 2 drafts.

This test catches an update that makes rewrites worse. It does not check
facts. review.py does that.
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
from llm import ask, available, other_lab  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases.jsonl"
RUBRIC = ROOT / "evals" / "rubric.md"
REPORT = ROOT / ".work" / "eval_report.md"
MODELS = {
    "anthropic": {"writer": os.environ.get("SHARPEN_EVAL_MODEL", "claude-sonnet-5-5"),
                  "judge": os.environ.get("SHARPEN_JUDGE_MODEL", "claude-opus-5-5")},
    "openai": {"writer": os.environ.get("SHARPEN_EVAL_MODEL_OPENAI", "gpt-6.1-sol"),
               "judge": os.environ.get("SHARPEN_JUDGE_MODEL_OPENAI", "gpt-6-astra")},
}
MEAN_SLACK = 0.3
LAB_SLACK = 0.6  # each lab's half is only ten drafts, so its average moves more by chance
BAD_LOSS = 3
MAX_BAD_LOSSES = 2


def old_guidance():
    if "--old" in sys.argv:
        return pathlib.Path(sys.argv[sys.argv.index("--old") + 1]).read_text()
    return subprocess.run(["git", "show", "HEAD:guidance/guidance.md"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout


def rewrite(model, guidance, case):
    system = (render(guidance)
              + "\n\nNo web tools are available in this run. Use the guidance snapshot above.")
    target = f"for {case['target']} " if case.get("target") else ""
    return ask(model, system, f"sharpen {target}{case['draft']}")


def judge(model, case, old_text, new_text):
    flip = random.Random(case["id"]).random() < 0.5
    a, b = (new_text, old_text) if flip else (old_text, new_text)
    system = (RUBRIC.read_text()
              + '\n\nReply with JSON only, in this shape: {"a": 7, "b": 6, "note": "one short sentence"}')
    user = (f"<draft>\n{case['draft']}\n</draft>\n"
            f"<target_model>{case.get('target') or 'not named'}</target_model>\n"
            f"<rewrite_a>\n{a}\n</rewrite_a>\n<rewrite_b>\n{b}\n</rewrite_b>")
    reply = ask(model, system, user)
    scores = json.loads(re.search(r"\{.*\}", reply, re.S).group(0))
    sa, sb = float(scores["a"]), float(scores["b"])
    old_score, new_score = (sb, sa) if flip else (sa, sb)
    return old_score, new_score, str(scores.get("note", ""))


def run(case, writer_lab, judge_lab, old, new):
    writer, grader = MODELS[writer_lab]["writer"], MODELS[judge_lab]["judge"]
    old_text, new_text = rewrite(writer, old, case), rewrite(writer, new, case)
    old_score, new_score, note = judge(grader, case, old_text, new_text)
    return {"id": case["id"], "lab": writer_lab, "writer": writer, "judge": grader,
            "old": old_score, "new": new_score, "note": note}


def main():
    cases = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    old, new = old_guidance(), (ROOT / "guidance" / "guidance.md").read_text()

    labs = [lab for lab in ("anthropic", "openai") if available(lab)]
    if not labs:
        print("no model key was found, so the test cannot run")
        return 1
    plan = []
    for index, case in enumerate(cases):
        writer_lab = labs[index % len(labs)]
        judge_lab = other_lab(writer_lab) if len(labs) == 2 else writer_lab
        plan.append((case, writer_lab, judge_lab))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda item: run(*item, old, new), plan))

    def means(rows):
        return statistics.mean(r["old"] for r in rows), statistics.mean(r["new"] for r in rows)

    old_mean, new_mean = means(results)
    bad = [r for r in results if r["new"] <= r["old"] - BAD_LOSS]
    passed = new_mean >= old_mean - MEAN_SLACK and len(bad) <= MAX_BAD_LOSSES

    lines = [f"# Guidance test: {'passed' if passed else 'did not pass'}", "",
             f"All drafts: current {old_mean:.2f}, proposed {new_mean:.2f}"]
    for lab in labs:
        rows = [r for r in results if r["lab"] == lab]
        lab_old, lab_new = means(rows)
        if lab_new < lab_old - LAB_SLACK:
            passed = False
        lines.append(f"Rewritten by {MODELS[lab]['writer']} ({len(rows)} drafts): "
                     f"current {lab_old:.2f}, proposed {lab_new:.2f}")
    lines[0] = f"# Guidance test: {'passed' if passed else 'did not pass'}"
    lines += [f"Drafts where the proposed guidance lost by {BAD_LOSS} or more: {len(bad)}", "",
              "| Draft | Rewritten by | Judged by | Current | Proposed | Judge's note |",
              "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['id']} | {r['writer']} | {r['judge']} | {r['old']:g} | {r['new']:g} "
                     f"| {r['note'].replace('|', '/')} |")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as out:
            out.write(f"passed={'true' if passed else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
