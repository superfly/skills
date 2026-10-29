#!/usr/bin/env python3
"""Validate this repository's skills and plugin manifests.

Checks, per skill directory under plugins/*/skills/:
  - a SKILL.md exists and opens with a YAML frontmatter block
  - required fields `name` and `description` are present and non-empty
  - `name` matches its directory and is lowercase-with-hyphens
  - `description` is 1-1024 characters and says when to use the skill
  - the body is under 500 lines and not trivially short
  - relative markdown links resolve on disk, in SKILL.md and every reference

Checks, per plugin directory under plugins/:
  - every *.json parses
  - every .*-plugin/plugin.json declares the same `version`
  - every MCP config points at https://mcp.fly.io
  - hooks/hooks.json commands reference scripts that exist
  - every *.py compiles

Also checks that each repo-level marketplace.json points at an existing
plugin directory, and that skills.sh.json paths exist.

Exits non-zero with a list of problems. No third-party dependencies.
"""

from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT / "plugins"
MCP_URL = "https://mcp.fly.io"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MIN_DESCRIPTION = 40
MAX_DESCRIPTION = 1024
MAX_SKILL_LINES = 500


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return top-level scalar keys from a leading `---` block, or None.

    Handles the folded form `description: >` by joining the indented lines.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    current: str | None = None
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            if current is not None and fields.get(current, "") is not None:
                fields[current] = (fields[current] + " " + line.strip()).strip()
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        value = value.strip().strip("\"'")
        if value in (">", "|", ">-", "|-"):
            value = ""
        fields[key] = value
        current = key
    return fields


def check_links(md: Path, text: str, problems: list[str]) -> None:
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = (md.parent / target.split("#", 1)[0]).resolve()
        if not path.exists():
            problems.append(f"{md.relative_to(ROOT)}: broken relative link -> {target}")


def check_skill(skill_dir: Path, seen: set[str], problems: list[str]) -> None:
    skill_md = skill_dir / "SKILL.md"
    rel = skill_md.relative_to(ROOT)
    if not skill_md.is_file():
        problems.append(f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")
        return

    text = skill_md.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if fields is None:
        problems.append(f"{rel}: missing or malformed YAML frontmatter")
        return

    name = fields.get("name", "")
    description = fields.get("description", "")

    if not name:
        problems.append(f"{rel}: frontmatter is missing `name`")
    else:
        if not NAME_RE.match(name):
            problems.append(f"{rel}: name `{name}` is not lowercase-with-hyphens")
        if name != skill_dir.name:
            problems.append(f"{rel}: name `{name}` != directory `{skill_dir.name}`")
        if name in seen:
            problems.append(f"{rel}: duplicate skill name `{name}`")
        seen.add(name)

    if not description:
        problems.append(f"{rel}: frontmatter is missing `description`")
    elif len(description) < MIN_DESCRIPTION:
        problems.append(f"{rel}: description is too short to route on")
    elif len(description) > MAX_DESCRIPTION:
        problems.append(f"{rel}: description is {len(description)} chars; max {MAX_DESCRIPTION}")
    elif not re.search(r"\b(use|trigger|when|for)\b", description, re.IGNORECASE):
        problems.append(f"{rel}: description should say when to use the skill")

    body = text[text.find("\n---", 3) + 4 :].strip()
    if len(body) < 200:
        problems.append(f"{rel}: body is too thin to be useful")
    if text.count("\n") > MAX_SKILL_LINES:
        problems.append(f"{rel}: SKILL.md has {text.count(chr(10))} lines; keep it under {MAX_SKILL_LINES}")

    check_links(skill_md, text, problems)
    for ref in sorted((skill_dir / "references").glob("*.md")) if (skill_dir / "references").is_dir() else []:
        check_links(ref, ref.read_text(encoding="utf-8"), problems)


def load_json(path: Path, problems: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
        return None


def mcp_urls(value) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            if key in ("url", "serverUrl") and isinstance(inner, str):
                urls.append(inner)
            else:
                urls.extend(mcp_urls(inner))
    elif isinstance(value, list):
        for inner in value:
            urls.extend(mcp_urls(inner))
    return urls


def check_plugin(plugin_dir: Path, problems: list[str]) -> None:
    prel = plugin_dir.relative_to(ROOT)
    manifests = sorted(plugin_dir.glob(".*-plugin/plugin.json"))
    if not manifests:
        problems.append(f"{prel}: no .*-plugin/plugin.json manifests")
    versions: dict[str, str] = {}
    for manifest in manifests:
        data = load_json(manifest, problems)
        if isinstance(data, dict):
            versions[str(manifest.relative_to(ROOT))] = str(data.get("version", ""))
            if data.get("name") != plugin_dir.name:
                problems.append(f"{manifest.relative_to(ROOT)}: name `{data.get('name')}` != directory `{plugin_dir.name}`")
    if len(set(versions.values())) > 1:
        problems.append(f"{prel}: manifests disagree on version: " + ", ".join(f"{k}={v}" for k, v in versions.items()))

    for cfg in [plugin_dir / ".mcp.json", plugin_dir / "mcp_config.json", *plugin_dir.glob(".*-plugin/mcp.json")]:
        if not cfg.exists():
            continue
        data = load_json(cfg, problems)
        if data is None:
            continue
        urls = mcp_urls(data)
        if not urls:
            problems.append(f"{cfg.relative_to(ROOT)}: no MCP server URL")
        for url in urls:
            if url != MCP_URL:
                problems.append(f"{cfg.relative_to(ROOT)}: MCP URL is {url}, expected {MCP_URL}")

    hooks = plugin_dir / "hooks" / "hooks.json"
    if hooks.exists():
        data = load_json(hooks, problems)
        text = hooks.read_text(encoding="utf-8")
        for script in re.findall(r"/(scripts/[A-Za-z0-9_./-]+\.(?:py|sh))", text):
            if not (plugin_dir / script).is_file():
                problems.append(f"{hooks.relative_to(ROOT)}: references missing {script}")

    for other in plugin_dir.rglob("*.json"):
        if other.name not in ("plugin.json", "mcp.json", ".mcp.json", "mcp_config.json"):
            load_json(other, problems)

    for script in plugin_dir.rglob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            problems.append(f"{script.relative_to(ROOT)}: does not compile ({exc.msg})")


def check_marketplaces(problems: list[str]) -> None:
    for market in [ROOT / ".claude-plugin" / "marketplace.json", ROOT / ".cursor-plugin" / "marketplace.json", ROOT / ".agents" / "plugins" / "marketplace.json"]:
        if not market.exists():
            problems.append(f"{market.relative_to(ROOT)}: missing")
            continue
        data = load_json(market, problems)
        if not isinstance(data, dict):
            continue
        for plugin in data.get("plugins", []):
            source = plugin.get("source")
            path = source.get("path") if isinstance(source, dict) else source
            if not isinstance(path, str) or not (ROOT / path).is_dir():
                problems.append(f"{market.relative_to(ROOT)}: plugin `{plugin.get('name')}` source `{path}` is not a directory")

    skills_sh = ROOT / "skills.sh.json"
    if skills_sh.exists():
        data = load_json(skills_sh, problems)
        if isinstance(data, dict):
            for path in data.get("paths", []):
                if not isinstance(path, str) or not path.startswith("./") or not (ROOT / path).is_dir():
                    problems.append(f"skills.sh.json: path `{path}` must start with ./ and exist")


def main() -> int:
    problems: list[str] = []

    if not PLUGINS_DIR.is_dir():
        print("no plugins/ directory found", file=sys.stderr)
        return 1

    seen: set[str] = set()
    plugin_dirs = sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir())
    if not plugin_dirs:
        problems.append("plugins/ contains no plugin directories")

    for plugin_dir in plugin_dirs:
        check_plugin(plugin_dir, problems)
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            problems.append(f"{plugin_dir.relative_to(ROOT)}: missing skills/")
            continue
        skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
        if not skill_dirs:
            problems.append(f"{skills_dir.relative_to(ROOT)}: contains no skill directories")
        for skill_dir in skill_dirs:
            check_skill(skill_dir, seen, problems)

    check_marketplaces(problems)

    for problem in problems:
        print(f"FAIL {problem}")

    if problems:
        print(f"\n{len(problems)} problem(s) found", file=sys.stderr)
        return 1

    print(f"OK {len(seen)} skill(s) in {len(plugin_dirs)} plugin(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
