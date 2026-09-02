"""Fail closed when a manga project bypasses the Comfy -> Krita workflow."""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED_KRITA_LAYERS = {"AI素材", "文字"}
FORBIDDEN_TEXT_MARKERS = (
    "text (verbatim)",
    "typography:",
    "render the following text",
    "render only the exact japanese text",
)


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class Finding:
    code: str
    path: Path
    message: str

    def render(self) -> str:
        return f"[{self.code}] {self.path}: {self.message}"


def _png_chunks(path: Path) -> Iterable[tuple[bytes, bytes]]:
    with path.open("rb") as stream:
        if stream.read(8) != PNG_SIGNATURE:
            raise ValueError("PNG signature is missing")
        found_end = False
        while True:
            length_bytes = stream.read(4)
            if not length_bytes:
                break
            if len(length_bytes) != 4:
                raise ValueError("truncated PNG chunk length")
            length = struct.unpack(">I", length_bytes)[0]
            kind = stream.read(4)
            data = stream.read(length)
            crc_bytes = stream.read(4)
            if len(kind) != 4 or len(data) != length or len(crc_bytes) != 4:
                raise ValueError("truncated PNG chunk")
            expected_crc = struct.unpack(">I", crc_bytes)[0]
            actual_crc = zlib.crc32(kind + data) & 0xFFFFFFFF
            if expected_crc != actual_crc:
                raise ValueError(f"invalid CRC in {kind.decode('ascii', errors='replace')} chunk")
            yield kind, data
            if kind == b"IEND":
                found_end = True
                break
        if not found_end:
            raise ValueError("PNG IEND chunk is missing")


def png_text_metadata(path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for kind, data in _png_chunks(path):
        if kind == b"tEXt":
            keyword, value = data.split(b"\x00", 1)
            metadata[keyword.decode("latin-1")] = value.decode("utf-8", errors="replace")
        elif kind == b"zTXt":
            keyword, compressed = data.split(b"\x00", 1)
            if not compressed or compressed[0] != 0:
                raise ValueError("unsupported zTXt compression method")
            metadata[keyword.decode("latin-1")] = zlib.decompress(compressed[1:]).decode(
                "utf-8", errors="replace"
            )
        elif kind == b"iTXt":
            keyword, rest = data.split(b"\x00", 1)
            if len(rest) < 2:
                raise ValueError("invalid iTXt chunk")
            compressed, method, rest = rest[0], rest[1], rest[2:]
            _language, rest = rest.split(b"\x00", 1)
            _translated, value = rest.split(b"\x00", 1)
            if compressed:
                if method != 0:
                    raise ValueError("unsupported iTXt compression method")
                value = zlib.decompress(value)
            metadata[keyword.decode("latin-1")] = value.decode("utf-8", errors="replace")
    return metadata


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def validate_visual_prompt(path: Path) -> list[Finding]:
    if not path.is_file():
        return [Finding("PROMPT_MISSING", path, "Comfy prompt file is required")]
    text = path.read_text(encoding="utf-8").strip()
    findings: list[Finding] = []
    if not text:
        findings.append(Finding("PROMPT_EMPTY", path, "Comfy prompt must not be empty"))
        return findings
    lowered = text.lower()
    for marker in FORBIDDEN_TEXT_MARKERS:
        if marker in lowered:
            findings.append(
                Finding(
                    "PROMPT_BAKES_TEXT",
                    path,
                    f"found '{marker}'; narration and lettering must be added in Krita",
                )
            )
    if "no text" not in lowered and "文字なし" not in text:
        findings.append(
            Finding(
                "PROMPT_NO_TEXT_RULE_MISSING",
                path,
                "Comfy prompt must explicitly require 'no text' or '文字なし'",
            )
        )
    return findings


def validate_comfy_png(path: Path, prompt_path: Path) -> list[Finding]:
    try:
        metadata = png_text_metadata(path)
    except (OSError, ValueError, zlib.error) as exc:
        return [Finding("SELECTED_PNG_INVALID", path, str(exc))]

    raw_prompt = metadata.get("prompt")
    if raw_prompt is None:
        return [
            Finding(
                "COMFY_METADATA_MISSING",
                path,
                "selected PNG has no Comfy 'prompt' metadata; external/built-in images are not selectable",
            )
        ]
    try:
        embedded = json.loads(raw_prompt)
    except json.JSONDecodeError as exc:
        return [Finding("COMFY_METADATA_INVALID", path, f"prompt metadata is not JSON: {exc}")]
    if not isinstance(embedded, dict):
        return [Finding("COMFY_METADATA_INVALID", path, "prompt metadata must be a JSON object")]

    expected_prompt = prompt_path.read_text(encoding="utf-8").strip()
    embedded_strings = set(_strings(embedded))
    if expected_prompt not in embedded_strings:
        return [
            Finding(
                "COMFY_PROMPT_MISMATCH",
                path,
                f"embedded Comfy prompt does not match {prompt_path}",
            )
        ]
    return []


def _krita_layer_names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        if archive.read("mimetype") != b"application/x-krita":
            raise ValueError("mimetype is not application/x-krita")
        if "maindoc.xml" not in names:
            raise ValueError("maindoc.xml does not exist")
        document = ET.fromstring(archive.read("maindoc.xml"))
        return {element.attrib["name"] for element in document.iter() if "name" in element.attrib}


def validate_krita_source(path: Path) -> list[Finding]:
    if path.suffix.lower() != ".kra":
        return [Finding("KRITA_FORMAT_REQUIRED", path, "editable manuscript must use Krita .kra format")]
    try:
        names = _krita_layer_names(path)
    except (KeyError, OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        return [Finding("KRITA_SOURCE_INVALID", path, str(exc))]
    missing = sorted(REQUIRED_KRITA_LAYERS - names)
    if missing:
        return [
            Finding(
                "KRITA_LAYERS_MISSING",
                path,
                f"required editable layers are missing: {', '.join(missing)}",
            )
        ]
    return []


def _page_source(project: Path, stem: str, one_panel_per_page: bool) -> Path | None:
    pages = project / "pages"
    candidates = [pages / f"{stem}.kra"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    if not one_panel_per_page:
        for suffix in ("*.kra",):
            match = next(iter(sorted(pages.glob(suffix))), None)
            if match:
                return match
    return None


def validate_project(project: Path) -> list[Finding]:
    findings: list[Finding] = []
    project_file = project / "project.json"
    try:
        settings = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("PROJECT_CONFIG_INVALID", project_file, str(exc))]

    workflow = settings.get("workflow", {})
    if workflow.get("generator") != "comfy" or workflow.get("finisher") != "krita":
        findings.append(
            Finding(
                "WORKFLOW_DECLARATION_INVALID",
                project_file,
                "workflow must declare generator='comfy' and finisher='krita'",
            )
        )
    one_panel_per_page = settings.get("format") == "one-post-one-panel"

    prompts_dir = project / "prompts"
    for prompt in sorted(prompts_dir.glob("*.txt")):
        findings.extend(validate_visual_prompt(prompt))

    selected_dir = project / "panels" / "selected"
    selected = sorted(selected_dir.glob("*.png"))
    if not selected:
        findings.append(Finding("SELECTED_PANEL_MISSING", selected_dir, "no selected Comfy panel exists"))
    for panel in selected:
        prompt = prompts_dir / f"{panel.stem}.txt"
        findings.extend(validate_visual_prompt(prompt))
        if prompt.is_file():
            findings.extend(validate_comfy_png(panel, prompt))
        source = _page_source(project, panel.stem, one_panel_per_page)
        if source is None:
            findings.append(
                Finding(
                    "KRITA_SOURCE_MISSING",
                    project / "pages" / f"{panel.stem}.kra",
                    "selected panel has no matching editable Krita .kra source",
                )
            )
        else:
            findings.extend(validate_krita_source(source))

    export_dir = project / "export"
    exports = sorted(path for path in export_dir.glob("*.*") if path.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not exports:
        findings.append(
            Finding(
                "KRITA_EXPORT_MISSING",
                export_dir,
                "no final PNG/JPEG exported from Krita exists",
            )
        )
    for exported in exports:
        source = _page_source(project, exported.stem, one_panel_per_page)
        if source is None:
            findings.append(
                Finding(
                    "KRITA_EXPORT_SOURCE_MISSING",
                    exported,
                    "final export has no matching editable Krita source",
                )
            )

    return sorted(set(findings), key=lambda item: (str(item.path), item.code, item.message))


def _print_result(findings: list[Finding], subject: Path) -> int:
    if findings:
        print(f"PRODUCTION GUARD: FAIL ({len(findings)} finding(s))")
        for finding in findings:
            print(f"- {finding.render()}")
        return 1
    print(f"PRODUCTION GUARD: PASS ({subject})")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a complete manga project")
    validate.add_argument("--project", type=Path, required=True)
    prompt = commands.add_parser("check-prompt", help="reject prompts that bake text into Comfy output")
    prompt.add_argument("--prompt", type=Path, required=True)
    image = commands.add_parser("check-image", help="verify Comfy metadata and prompt identity")
    image.add_argument("--image", type=Path, required=True)
    image.add_argument("--prompt", type=Path, required=True)
    source = commands.add_parser("check-krita", help="verify a layered Krita .kra manuscript")
    source.add_argument("--source", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "validate":
        subject = args.project.resolve()
        return _print_result(validate_project(subject), subject)
    if args.command == "check-prompt":
        subject = args.prompt.resolve()
        return _print_result(validate_visual_prompt(subject), subject)
    if args.command == "check-krita":
        subject = args.source.resolve()
        return _print_result(validate_krita_source(subject), subject)
    subject = args.image.resolve()
    findings = validate_visual_prompt(args.prompt.resolve())
    if not findings:
        findings.extend(validate_comfy_png(subject, args.prompt.resolve()))
    return _print_result(findings, subject)


if __name__ == "__main__":
    raise SystemExit(main())
