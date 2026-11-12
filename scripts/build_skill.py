#!/usr/bin/env python3
"""Build the installable skill from the template and the current guidance.

Writes skill/SKILL.md and sharpen.zip. The skill carries a copy of the
guidance so it still works when it cannot reach the web.
"""
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "skill" / "SKILL.template.md"
GUIDANCE = ROOT / "guidance" / "guidance.md"
OUT = ROOT / "skill" / "SKILL.md"
ZIP = ROOT / "sharpen.zip"
MARKER = "{{GUIDANCE}}"


def render(guidance_text):
    template = TEMPLATE.read_text()
    if template.count(MARKER) != 1:
        raise SystemExit("the template needs exactly one {{GUIDANCE}} marker")
    # Push the guidance headings down one level so they sit inside the skill.
    lines = [("#" + line) if line.startswith("#") else line
             for line in guidance_text.strip().splitlines()]
    return template.replace(MARKER, "\n".join(lines))


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(GUIDANCE.read_text()))
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo("sharpen/SKILL.md", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, OUT.read_text())
    print(f"built {OUT.relative_to(ROOT)} and {ZIP.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
