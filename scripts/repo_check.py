"""Validate repository infrastructure without requiring Comfy or Krita to be running."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml

from production_guard import (
    load_and_validate_episode,
    load_workflow_policy,
    validate_project_settings,
)


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


IGNORED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache"}
REQUIRED_PATHS = {
    "AGENTS.md",
    "config/manga.json",
    "manga.ps1",
    "projects/_template/project.json",
    "schemas/episode.schema.json",
    "schemas/manga.schema.json",
    "schemas/project.schema.json",
    ".agents/skills/krita-manga/SKILL.md",
}
OBSOLETE_POINTERS = {
    "AGENT.md",
    ".agents/AGENTS.md",
    ".codex/AGENTS.md",
    ".claude/agents",
    ".claude/skills",
}


def _files(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    result: list[Path] = []
    for pattern in patterns:
        result.extend(
            path
            for path in root.rglob(pattern)
            if not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
        )
    return sorted(set(result))


def _load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        raw = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("SKILL.md frontmatter must be an object")
    return data


def check_repo(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_PATHS):
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    for relative in sorted(OBSOLETE_POINTERS):
        if (root / relative).exists():
            errors.append(f"obsolete or misleading duplicate exists: {relative}")

    for path in _files(root, ("*.json",)):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {path.relative_to(root)}: {exc}")
    for path in _files(root, ("*.yaml", "*.yml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"invalid YAML {path.relative_to(root)}: {exc}")
    for path in (root / "pyproject.toml", root / ".codex" / "config.toml"):
        try:
            tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"invalid TOML {path.relative_to(root)}: {exc}")

    codex_config = root / ".codex" / "config.toml"
    try:
        codex_settings = tomllib.loads(codex_config.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        pass
    else:
        if codex_settings.get("approval_policy") == "never":
            errors.append(".codex/config.toml must not disable all approvals")
        if codex_settings.get("sandbox_mode") == "danger-full-access":
            errors.append(".codex/config.toml must not default to danger-full-access")

    claude_pointer = root / "CLAUDE.md"
    try:
        pointer_text = claude_pointer.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read CLAUDE.md: {exc}")
    else:
        if pointer_text != "@AGENTS.md":
            errors.append("CLAUDE.md must include the canonical root AGENTS.md")

    for project_file in sorted((root / "projects").glob("*/project.json")):
        try:
            settings = json.loads(project_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        errors.extend(finding.render() for finding in validate_project_settings(settings, project_file))
        bible = settings.get("series_bible") if isinstance(settings, dict) else None
        if bible and not (project_file.parent / str(bible)).is_file():
            errors.append(f"missing series bible: {project_file.parent / str(bible)}")

    for episode in sorted((root / "projects").glob("*/episodes/*.yaml")):
        _, findings = load_and_validate_episode(episode)
        errors.extend(finding.render() for finding in findings)

    try:
        policy = load_workflow_policy(root / "config" / "manga.json")
    except ValueError as exc:
        errors.append(str(exc))
    else:
        mandatory = {
            "generator": "comfy",
            "finisher": "krita",
            "allow_external_selected_images": False,
            "require_comfy_png_metadata": True,
            "require_textless_generation_prompt": True,
            "require_krita_source": True,
            "krita_manuscript_format": "kra",
            "require_krita_export": True,
            "require_visual_review_receipt": True,
        }
        for key, expected in mandatory.items():
            if policy.get(key) != expected:
                errors.append(f"workflow_policy.{key} must be {expected!r}")

    for skill in sorted((root / ".agents" / "skills").glob("*/SKILL.md")):
        try:
            metadata = _load_frontmatter(skill)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"invalid skill {skill.relative_to(root)}: {exc}")
            continue
        if metadata.get("name") != skill.parent.name:
            errors.append(f"skill name must match folder: {skill.relative_to(root)}")
        if not str(metadata.get("description", "")).strip():
            errors.append(f"skill description is empty: {skill.relative_to(root)}")

    template_script = root / "projects" / "_template" / "script.yaml"
    try:
        data = yaml.safe_load(template_script.read_text(encoding="utf-8"))
        panels = data["pages"][0]["panels"]
        if len(panels) != 1:
            errors.append("template script must model one selected image per page")
    except (OSError, UnicodeError, KeyError, TypeError, yaml.YAMLError) as exc:
        errors.append(f"invalid template script structure: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check_repo(args.root.resolve())
    if errors:
        print(f"REPOSITORY CHECK: FAIL ({len(errors)} finding(s))")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"REPOSITORY CHECK: PASS ({args.root.resolve()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
