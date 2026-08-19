#!/usr/bin/env python3
"""Validate this repository against the Agent Skills / skills.sh layout.

Checks, per skill directory under skills/:
  - a SKILL.md exists and opens with a YAML frontmatter block
  - required fields `name` and `description` are present and non-empty
  - `name` matches its directory and is lowercase-with-hyphens
  - `description` says when to use the skill, not only what it is
  - relative markdown links resolve on disk

Exits non-zero with a list of problems. No third-party dependencies.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MIN_DESCRIPTION = 40
MAX_DESCRIPTION = 1024


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return top-level scalar keys from a leading `---` block, or None."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line.startswith((" ", "\t", "#")):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def check_links(skill_md: Path, text: str, problems: list[str]) -> None:
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = (skill_md.parent / target.split("#", 1)[0]).resolve()
        if not path.exists():
            problems.append(f"{skill_md}: broken relative link -> {target}")


def main() -> int:
    problems: list[str] = []

    if not SKILLS_DIR.is_dir():
        print("no skills/ directory found", file=sys.stderr)
        return 1

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        problems.append("skills/ contains no skill directories")

    seen: set[str] = set()
    for skill_dir in skill_dirs:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"{skill_dir}: missing SKILL.md")
            continue

        text = skill_md.read_text(encoding="utf-8")
        fields = parse_frontmatter(text)
        if fields is None:
            problems.append(f"{skill_md}: missing or malformed YAML frontmatter")
            continue

        name = fields.get("name", "")
        description = fields.get("description", "")

        if not name:
            problems.append(f"{skill_md}: frontmatter is missing `name`")
        else:
            if not NAME_RE.match(name):
                problems.append(f"{skill_md}: name `{name}` is not lowercase-with-hyphens")
            if name != skill_dir.name:
                problems.append(f"{skill_md}: name `{name}` != directory `{skill_dir.name}`")
            if name in seen:
                problems.append(f"{skill_md}: duplicate skill name `{name}`")
            seen.add(name)

        if not description:
            problems.append(f"{skill_md}: frontmatter is missing `description`")
        elif len(description) < MIN_DESCRIPTION:
            problems.append(f"{skill_md}: description is too short to route on")
        elif len(description) > MAX_DESCRIPTION:
            problems.append(f"{skill_md}: description exceeds {MAX_DESCRIPTION} characters")
        elif not re.search(r"\b(use|trigger|when|for)\b", description, re.IGNORECASE):
            problems.append(f"{skill_md}: description should say when to use the skill")

        body = text[text.find("\n---", 3) + 4 :].strip()
        if len(body) < 200:
            problems.append(f"{skill_md}: body is too thin to be useful")

        check_links(skill_md, text, problems)

    for problem in problems:
        print(f"FAIL {problem}")

    if problems:
        print(f"\n{len(problems)} problem(s) found", file=sys.stderr)
        return 1

    print(f"OK {len(seen)} skill(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
