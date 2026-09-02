"""Fail closed when a manga project bypasses the Comfy -> Krita workflow."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import sys
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from PIL import Image, UnidentifiedImageError


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "manga.json"
CONFIG_SCHEMA_PATH = REPO_ROOT / "schemas" / "manga.schema.json"
EPISODE_SCHEMA_PATH = REPO_ROOT / "schemas" / "episode.schema.json"
PROJECT_SCHEMA_PATH = REPO_ROOT / "schemas" / "project.schema.json"
REQUIRED_KRITA_LAYERS = {"AI素材", "文字", "フキダシ"}
TEXTLESS_KRITA_LAYERS = {"文字", "フキダシ"}
FORBIDDEN_TEXT_MARKERS = (
    "text (verbatim)",
    "typography:",
    "render the following text",
    "render only the exact japanese text",
    "draw the exact word",
    "draw the word",
    "write the word",
    "display the text",
    "include the text",
)
FORBIDDEN_TEXT_PATTERNS = (
    re.compile(
        r"\b(?:draw|render|write|display|show|include|add|place|print)\s+"
        r"(?:the\s+)?(?:exact\s+)?(?:text|word|words|letters|numbers|title|caption|label|logo|signature)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?:文字|台詞|セリフ|字幕|題名|タイトル|ロゴ|署名).{0,8}(?:描く|入れる|表示する|書く)"),
)
VISUAL_REVIEW_CHECKS = {
    "selected_has_no_visible_text",
    "krita_merged_has_no_visible_text",
    "export_has_no_visible_text",
}


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manga_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(CONFIG_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(config),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            detail = "; ".join(
                f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
                for error in errors
            )
            raise ValueError(f"config does not match schema: {detail}")
    except (
        OSError,
        UnicodeError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        SchemaError,
        ValueError,
    ) as exc:
        raise ValueError(f"cannot load manga config from {path}: {exc}") from exc
    return config


def load_workflow_policy(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    try:
        return load_manga_config(path)["workflow_policy"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"cannot load workflow policy from {path}: {exc}") from exc


def validate_project_settings(settings: Any, path: Path) -> list[Finding]:
    try:
        schema = json.loads(PROJECT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError, ValueError) as exc:
        return [Finding("PROJECT_SCHEMA_INVALID", PROJECT_SCHEMA_PATH, str(exc))]
    errors = sorted(
        Draft202012Validator(schema).iter_errors(settings),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    return [
        Finding(
            "PROJECT_CONFIG_INVALID",
            path,
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}",
        )
        for error in errors
    ]


def load_and_validate_episode(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        schema = json.loads(EPISODE_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError, ValueError) as exc:
        return None, [Finding("EPISODE_SCHEMA_INVALID", EPISODE_SCHEMA_PATH, str(exc))]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return None, [Finding("EPISODE_INVALID", path, str(exc))]
    errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    findings = [
        Finding(
            "EPISODE_INVALID",
            path,
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}",
        )
        for error in errors
    ]
    if not isinstance(data, dict):
        return None, findings
    if path.stem.isdigit() and data.get("episode") != int(path.stem):
        findings.append(
            Finding(
                "EPISODE_NUMBER_MISMATCH",
                path,
                f"episode is {data.get('episode')!r}, but filename is {path.stem}.yaml",
            )
        )
    panels = data.get("panels")
    if data.get("format") == "one-post-one-panel" and isinstance(panels, list) and len(panels) != 1:
        findings.append(
            Finding(
                "EPISODE_PANEL_COUNT_INVALID",
                path,
                "one-post-one-panel episodes must contain exactly one panel",
            )
        )
    return data, findings


def _image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def _image_size_bytes(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as image:
        image.verify()
    with Image.open(io.BytesIO(data)) as image:
        return image.size


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


def validate_visual_prompt(path: Path) -> list[Finding]:
    if not path.is_file():
        return [Finding("PROMPT_MISSING", path, "Comfy prompt file is required")]
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        return [Finding("PROMPT_INVALID", path, str(exc))]
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
                    f"found '{marker}'; Comfy prompts must describe visuals only",
                )
            )
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append(
                Finding(
                    "PROMPT_BAKES_TEXT",
                    path,
                    f"found text-rendering request {match.group(0)!r}; Comfy prompts must describe visuals only",
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


def validate_comfy_png(
    path: Path,
    prompt_path: Path,
    *,
    required_node_types: Iterable[str] = (),
    expected_checkpoint: str | None = None,
) -> list[Finding]:
    try:
        _image_size(path)
        metadata = png_text_metadata(path)
    except (OSError, ValueError, UnidentifiedImageError, zlib.error) as exc:
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

    nodes = [node for node in embedded.values() if isinstance(node, dict)]
    class_types = {str(node.get("class_type", "")) for node in nodes}
    findings: list[Finding] = []
    missing_node_types = sorted(set(required_node_types) - class_types)
    if missing_node_types:
        findings.append(
            Finding(
                "COMFY_WORKFLOW_INCOMPLETE",
                path,
                f"required Comfy nodes are missing: {', '.join(missing_node_types)}",
            )
        )

    try:
        expected_prompt = prompt_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        findings.append(Finding("PROMPT_INVALID", prompt_path, str(exc)))
        return findings
    prompt_nodes = [
        node
        for node in nodes
        if node.get("class_type") == "CLIPTextEncode"
        and isinstance(node.get("inputs"), dict)
    ]
    if not any(node["inputs"].get("text") == expected_prompt for node in prompt_nodes):
        findings.append(
            Finding(
                "COMFY_PROMPT_MISMATCH",
                path,
                f"embedded positive CLIP prompt does not match {prompt_path}",
            )
        )

    checkpoint_nodes = [
        node
        for node in nodes
        if node.get("class_type") == "CheckpointLoaderSimple"
        and isinstance(node.get("inputs"), dict)
    ]
    checkpoint_names = {
        str(node["inputs"].get("ckpt_name"))
        for node in checkpoint_nodes
        if node["inputs"].get("ckpt_name")
    }
    if checkpoint_nodes and not checkpoint_names:
        findings.append(Finding("COMFY_CHECKPOINT_MISSING", path, "Comfy metadata has no checkpoint name"))
    elif expected_checkpoint and expected_checkpoint not in checkpoint_names:
        findings.append(
            Finding(
                "COMFY_CHECKPOINT_MISMATCH",
                path,
                f"embedded checkpoint does not match configured model {expected_checkpoint!r}",
            )
        )
    sampler_nodes = [
        node
        for node in nodes
        if node.get("class_type") == "KSampler" and isinstance(node.get("inputs"), dict)
    ]
    if sampler_nodes and not any(isinstance(node["inputs"].get("seed"), int) for node in sampler_nodes):
        findings.append(Finding("COMFY_SEED_MISSING", path, "Comfy metadata has no integer sampler seed"))
    return findings


def _lzf_decompress(data: bytes, expected_size: int) -> bytes:
    output = bytearray()
    cursor = 0
    while cursor < len(data):
        control = data[cursor]
        cursor += 1
        if control < 32:
            length = control + 1
            end = cursor + length
            if end > len(data):
                raise ValueError("truncated LZF literal")
            output.extend(data[cursor:end])
            cursor = end
            continue

        length = control >> 5
        reference = len(output) - ((control & 0x1F) << 8) - 1
        if length == 7:
            if cursor >= len(data):
                raise ValueError("truncated LZF length")
            length += data[cursor]
            cursor += 1
        if cursor >= len(data):
            raise ValueError("truncated LZF reference")
        reference -= data[cursor]
        cursor += 1
        length += 2
        if reference < 0:
            raise ValueError("invalid LZF reference")
        for _ in range(length):
            if reference >= len(output):
                raise ValueError("invalid LZF copy")
            output.append(output[reference])
            reference += 1
        if len(output) > expected_size:
            raise ValueError("LZF tile exceeds its declared size")
    if len(output) != expected_size:
        raise ValueError(
            f"LZF tile decoded to {len(output)} bytes; expected {expected_size}"
        )
    return bytes(output)


def _read_ascii_header(stream: io.BytesIO, label: str) -> str:
    line = stream.readline()
    if not line.endswith(b"\n"):
        raise ValueError(f"truncated Krita {label} header")
    try:
        return line[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"invalid Krita {label} header") from exc


def _paint_layer_is_empty(archive: zipfile.ZipFile, filename: str) -> bool:
    suffix = f"/layers/{filename}"
    matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"could not locate pixel data for layer file '{filename}'")
    pixel_member = matches[0]
    default_member = pixel_member + ".defaultpixel"
    if default_member not in archive.namelist():
        raise ValueError(f"default pixel is missing for layer file '{filename}'")
    default_pixel = archive.read(default_member)

    stream = io.BytesIO(archive.read(pixel_member))
    if _read_ascii_header(stream, "version") != "VERSION 2":
        raise ValueError("unsupported Krita paint-layer version")
    width_header = _read_ascii_header(stream, "tile width")
    height_header = _read_ascii_header(stream, "tile height")
    pixel_header = _read_ascii_header(stream, "pixel size")
    data_header = _read_ascii_header(stream, "tile count")
    try:
        tile_width = int(width_header.removeprefix("TILEWIDTH "))
        tile_height = int(height_header.removeprefix("TILEHEIGHT "))
        pixel_size = int(pixel_header.removeprefix("PIXELSIZE "))
        tile_count = int(data_header.removeprefix("DATA "))
    except ValueError as exc:
        raise ValueError("invalid Krita paint-layer dimensions") from exc
    if not width_header.startswith("TILEWIDTH ") or not height_header.startswith("TILEHEIGHT "):
        raise ValueError("invalid Krita tile-size headers")
    if not pixel_header.startswith("PIXELSIZE ") or not data_header.startswith("DATA "):
        raise ValueError("invalid Krita pixel-data headers")
    if pixel_size != len(default_pixel):
        raise ValueError("Krita default pixel size does not match layer pixel size")

    expected_size = tile_width * tile_height * pixel_size
    empty_tile = default_pixel * (tile_width * tile_height)
    for _ in range(tile_count):
        tile_header = _read_ascii_header(stream, "tile")
        match = re.fullmatch(r"-?\d+,-?\d+,([A-Z0-9]+),(\d+)", tile_header)
        if not match:
            raise ValueError(f"invalid Krita tile header: {tile_header!r}")
        compression, encoded_size_text = match.groups()
        encoded_size = int(encoded_size_text)
        encoded = stream.read(encoded_size)
        if len(encoded) != encoded_size:
            raise ValueError("truncated Krita tile payload")
        if compression == "RAW":
            decoded = encoded
            if len(decoded) != expected_size:
                raise ValueError("RAW tile size does not match its declared dimensions")
        elif compression == "LZF":
            if not encoded:
                raise ValueError("empty Krita LZF tile payload")
            # Krita prefixes stored LZF tiles with one compressor-format byte.
            decoded = _lzf_decompress(encoded[1:], expected_size)
        else:
            raise ValueError(f"unsupported Krita tile compression: {compression}")
        if decoded != empty_tile:
            return False
    return True


def _krita_layers(
    path: Path,
) -> tuple[set[str], dict[str, dict[str, str]], set[str], zipfile.ZipFile]:
    archive = zipfile.ZipFile(path)
    try:
        names = set(archive.namelist())
        if archive.read("mimetype") != b"application/x-krita":
            raise ValueError("mimetype is not application/x-krita")
        if "maindoc.xml" not in names:
            raise ValueError("maindoc.xml does not exist")
        document = ET.fromstring(archive.read("maindoc.xml"))
        layers: dict[str, dict[str, str]] = {}
        duplicates: set[str] = set()
        for element in document.iter():
            tag = element.tag.rsplit("}", 1)[-1].lower()
            name = element.attrib.get("name")
            if tag != "layer" or not name:
                continue
            if name in layers:
                duplicates.add(name)
            layers[name] = dict(element.attrib)
        return set(layers), layers, duplicates, archive
    except Exception:
        archive.close()
        raise


def validate_krita_source(
    path: Path, *, empty_layers: set[str] | None = None
) -> list[Finding]:
    if path.suffix.lower() != ".kra":
        return [Finding("KRITA_FORMAT_REQUIRED", path, "editable manuscript must use Krita .kra format")]
    try:
        names, layers, duplicates, archive = _krita_layers(path)
    except (KeyError, OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        return [Finding("KRITA_SOURCE_INVALID", path, str(exc))]
    try:
        findings: list[Finding] = []
        required_duplicates = sorted(REQUIRED_KRITA_LAYERS & duplicates)
        if required_duplicates:
            findings.append(
                Finding(
                    "KRITA_LAYER_DUPLICATE",
                    path,
                    f"required layer names must be unique: {', '.join(required_duplicates)}",
                )
            )
        missing = sorted(REQUIRED_KRITA_LAYERS - names)
        if missing:
            findings.append(
                Finding(
                    "KRITA_LAYERS_MISSING",
                    path,
                    f"required editable layers are missing: {', '.join(missing)}",
                )
            )
            return findings

        if "mergedimage.png" not in archive.namelist():
            findings.append(
                Finding("KRITA_PREVIEW_MISSING", path, "KRA has no mergedimage.png preview")
            )
        else:
            try:
                width, height = _image_size_bytes(archive.read("mergedimage.png"))
                if width <= 0 or height <= 0:
                    raise ValueError("preview dimensions must be positive")
            except (KeyError, OSError, ValueError, UnidentifiedImageError) as exc:
                findings.append(Finding("KRITA_PREVIEW_INVALID", path, str(exc)))

        ai_layer = layers.get("AI素材")
        if ai_layer is None or ai_layer.get("nodetype") != "paintlayer" or not ai_layer.get("filename"):
            findings.append(
                Finding("KRITA_AI_LAYER_UNVERIFIABLE", path, "AI素材 must be a named paint layer")
            )
        else:
            try:
                if _paint_layer_is_empty(archive, ai_layer["filename"]):
                    findings.append(
                        Finding("KRITA_AI_LAYER_EMPTY", path, "AI素材 does not contain selected artwork")
                    )
            except ValueError as exc:
                findings.append(Finding("KRITA_AI_LAYER_UNVERIFIABLE", path, str(exc)))
        for layer_name in sorted(empty_layers or set()):
            layer = layers.get(layer_name)
            if layer is None:
                continue
            if layer.get("nodetype") != "paintlayer" or not layer.get("filename"):
                findings.append(
                    Finding(
                        "KRITA_EMPTY_LAYER_UNVERIFIABLE",
                        path,
                        f"cannot prove that required-empty layer '{layer_name}' is empty",
                    )
                )
                continue
            try:
                is_empty = _paint_layer_is_empty(archive, layer["filename"])
            except ValueError as exc:
                findings.append(
                    Finding(
                        "KRITA_EMPTY_LAYER_UNVERIFIABLE",
                        path,
                        f"cannot inspect required-empty layer '{layer_name}': {exc}",
                    )
                )
                continue
            if not is_empty:
                findings.append(
                    Finding(
                        "KRITA_TEXT_LAYER_NOT_EMPTY",
                        path,
                        f"textless image policy requires layer '{layer_name}' to be empty",
                    )
                )
        return findings
    finally:
        archive.close()


def _requires_textless_image(settings: dict[str, Any]) -> bool:
    return settings.get("image_text_policy") == "textless"


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


def _export_for_stem(project: Path, stem: str) -> Path | None:
    export_dir = project / "export"
    for suffix in (".png", ".jpg", ".jpeg"):
        candidate = export_dir / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def validate_export_image(exported: Path, source: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        export_size = _image_size(exported)
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        return [Finding("KRITA_EXPORT_INVALID", exported, str(exc))]
    try:
        with zipfile.ZipFile(source) as archive:
            preview_size = _image_size_bytes(archive.read("mergedimage.png"))
    except (KeyError, OSError, ValueError, zipfile.BadZipFile, UnidentifiedImageError) as exc:
        return [Finding("KRITA_EXPORT_SOURCE_INVALID", source, str(exc))]
    if export_size != preview_size:
        findings.append(
            Finding(
                "KRITA_EXPORT_SIZE_MISMATCH",
                exported,
                f"export size {export_size} does not match KRA preview {preview_size}",
            )
        )
    if exported.stat().st_mtime_ns < source.stat().st_mtime_ns:
        findings.append(
            Finding(
                "KRITA_EXPORT_STALE",
                exported,
                "export is older than its editable KRA source; export again from Krita",
            )
        )
    return findings


def _review_artifacts(project: Path, stem: str) -> dict[str, Path]:
    exported = _export_for_stem(project, stem)
    artifacts = {
        "selected": project / "panels" / "selected" / f"{stem}.png",
        "kra": project / "pages" / f"{stem}.kra",
    }
    if exported is not None:
        artifacts["export"] = exported
    return artifacts


def create_visual_review_receipt(project: Path, stem: str, reviewer: str) -> Path:
    if not re.fullmatch(r"\d{3}", stem):
        raise ValueError("panel must be three digits")
    if not reviewer.strip():
        raise ValueError("reviewer must not be empty")
    project_file = project / "project.json"
    try:
        settings = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read project settings: {exc}") from exc
    settings_findings = validate_project_settings(settings, project_file)
    if settings_findings:
        raise ValueError(
            "project settings are invalid: "
            + "; ".join(finding.render() for finding in settings_findings)
        )
    if not _requires_textless_image(settings):
        raise ValueError("visual no-text review receipts apply only to textless projects")

    artifacts = _review_artifacts(project, stem)
    missing = [str(path) for path in artifacts.values() if not path.is_file()]
    if "export" not in artifacts:
        missing.append(str(project / "export" / f"{stem}.png"))
    if missing:
        raise FileNotFoundError(f"review artifacts are missing: {', '.join(missing)}")
    config = load_manga_config()
    policy = config["workflow_policy"]
    prompt = project / "prompts" / f"{stem}.txt"
    selected = artifacts["selected"]
    source = artifacts["kra"]
    exported = artifacts["export"]
    preflight = validate_visual_prompt(prompt)
    if prompt.is_file():
        preflight.extend(
            validate_comfy_png(
                selected,
                prompt,
                required_node_types=policy["required_comfy_node_types"],
                expected_checkpoint=config["comfy"]["checkpoint"],
            )
        )
    preflight.extend(validate_krita_source(source, empty_layers=TEXTLESS_KRITA_LAYERS))
    preflight.extend(validate_export_image(exported, source))
    lettering = project / "lettering" / f"{stem}.txt"
    if lettering.is_file():
        preflight.append(
            Finding(
                "TEXT_INPUT_FORBIDDEN",
                lettering,
                "textless image policy forbids lettering inputs",
            )
        )
    if preflight:
        raise ValueError(
            "review preflight failed: "
            + "; ".join(finding.render() for finding in preflight)
        )
    receipt = {
        "version": 1,
        "panel": stem,
        "reviewer": reviewer.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "checks": {name: True for name in sorted(VISUAL_REVIEW_CHECKS)},
        "artifacts": {
            name: {
                "path": path.relative_to(project).as_posix(),
                "sha256": sha256_file(path),
            }
            for name, path in artifacts.items()
        },
    }
    destination = project / "reviews" / f"{stem}.visual.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def validate_visual_review_receipt(project: Path, stem: str) -> list[Finding]:
    path = project / "reviews" / f"{stem}.visual.json"
    if not path.is_file():
        return [
            Finding(
                "VISUAL_REVIEW_MISSING",
                path,
                "textless output requires a hash-bound visual review receipt",
            )
        ]
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [Finding("VISUAL_REVIEW_INVALID", path, str(exc))]
    findings: list[Finding] = []
    if receipt.get("version") != 1 or receipt.get("panel") != stem or not receipt.get("reviewer"):
        findings.append(
            Finding("VISUAL_REVIEW_INVALID", path, "receipt identity or reviewer is invalid")
        )
    checks = receipt.get("checks", {})
    if not isinstance(checks, dict) or any(checks.get(name) is not True for name in VISUAL_REVIEW_CHECKS):
        findings.append(
            Finding("VISUAL_REVIEW_INVALID", path, "all required no-visible-text checks must be true")
        )
    artifacts = _review_artifacts(project, stem)
    recorded = receipt.get("artifacts", {})
    for name in ("selected", "kra", "export"):
        actual = artifacts.get(name)
        item = recorded.get(name) if isinstance(recorded, dict) else None
        if actual is None or not actual.is_file() or not isinstance(item, dict):
            findings.append(
                Finding("VISUAL_REVIEW_STALE", path, f"receipt artifact is missing: {name}")
            )
            continue
        expected_path = actual.relative_to(project).as_posix()
        if item.get("path") != expected_path or item.get("sha256") != sha256_file(actual):
            findings.append(
                Finding("VISUAL_REVIEW_STALE", path, f"receipt no longer matches {expected_path}")
            )
    return findings


def _ready_episode_stems(
    project: Path, ready_statuses: set[str]
) -> tuple[set[str], list[Finding]]:
    stems: set[str] = set()
    findings: list[Finding] = []
    for episode in sorted((project / "episodes").glob("*.yaml")):
        if not re.fullmatch(r"\d{3}", episode.stem):
            findings.append(
                Finding("EPISODE_NAME_INVALID", episode, "episode filename must be NNN.yaml")
            )
            continue
        data, validation_findings = load_and_validate_episode(episode)
        findings.extend(validation_findings)
        if data is None or validation_findings:
            continue
        if str(data.get("status", "")) in ready_statuses:
            stems.add(episode.stem)
    return stems, findings


def validate_project(project: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        config = load_manga_config()
        policy = config["workflow_policy"]
    except ValueError as exc:
        return [Finding("POLICY_CONFIG_INVALID", DEFAULT_CONFIG_PATH, str(exc))]
    project_file = project / "project.json"
    try:
        settings = json.loads(project_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [Finding("PROJECT_CONFIG_INVALID", project_file, str(exc))]

    settings_findings = validate_project_settings(settings, project_file)
    if settings_findings:
        return settings_findings

    workflow = settings["workflow"]
    if workflow.get("generator") != policy["generator"] or workflow.get("finisher") != policy["finisher"]:
        findings.append(
            Finding(
                "WORKFLOW_DECLARATION_INVALID",
                project_file,
                f"workflow must declare generator={policy['generator']!r} and finisher={policy['finisher']!r}",
            )
        )
    one_panel_per_page = settings.get("format") == "one-post-one-panel"
    requires_textless_image = _requires_textless_image(settings)

    series_bible = settings.get("series_bible")
    if series_bible and not (project / str(series_bible)).is_file():
        findings.append(
            Finding("SERIES_BIBLE_MISSING", project / str(series_bible), "configured series bible does not exist")
        )

    if requires_textless_image:
        lettering_dir = project / "lettering"
        for lettering in sorted(lettering_dir.glob("*.txt")):
            findings.append(
                Finding(
                    "TEXT_INPUT_FORBIDDEN",
                    lettering,
                    "textless image policy forbids lettering inputs; publish prose outside the image",
                )
            )

    prompts_dir = project / "prompts"
    if policy["require_textless_generation_prompt"]:
        for prompt in sorted(prompts_dir.glob("*.txt")):
            findings.extend(validate_visual_prompt(prompt))

    selected_dir = project / "panels" / "selected"
    selected = {path.stem: path for path in sorted(selected_dir.glob("*.png"))}
    ready_stems, episode_findings = _ready_episode_stems(
        project, set(str(value) for value in policy["ready_episode_statuses"])
    )
    findings.extend(episode_findings)
    if not selected and not ready_stems:
        findings.append(Finding("SELECTED_PANEL_MISSING", selected_dir, "no selected Comfy panel exists"))
    expected_stems = sorted(set(selected) | ready_stems)
    for stem in expected_stems:
        panel = selected.get(stem)
        prompt = prompts_dir / f"{stem}.txt"
        if policy["require_textless_generation_prompt"]:
            findings.extend(validate_visual_prompt(prompt))
        if panel is None:
            findings.append(
                Finding("SELECTED_PANEL_MISSING", selected_dir / f"{stem}.png", "ready episode has no selected Comfy panel")
            )
        elif prompt.is_file() and (
            policy["require_comfy_png_metadata"]
            or not policy["allow_external_selected_images"]
        ):
            findings.extend(
                validate_comfy_png(
                    panel,
                    prompt,
                    required_node_types=policy["required_comfy_node_types"],
                    expected_checkpoint=config["comfy"]["checkpoint"],
                )
            )
        source = _page_source(project, stem, one_panel_per_page)
        if source is None:
            if policy["require_krita_source"]:
                findings.append(
                    Finding(
                        "KRITA_SOURCE_MISSING",
                        project / "pages" / f"{stem}.{policy['krita_manuscript_format']}",
                        "production episode has no matching editable Krita source",
                    )
                )
        else:
            findings.extend(
                validate_krita_source(
                    source,
                    empty_layers=TEXTLESS_KRITA_LAYERS if requires_textless_image else None,
                )
            )

        exported = _export_for_stem(project, stem)
        if exported is None:
            if policy["require_krita_export"]:
                findings.append(
                    Finding(
                        "KRITA_EXPORT_MISSING",
                        project / "export" / f"{stem}.png",
                        "production episode has no matching final Krita export",
                    )
                )
        elif source is not None:
            findings.extend(validate_export_image(exported, source))

        if requires_textless_image and policy["require_visual_review_receipt"]:
            findings.extend(validate_visual_review_receipt(project, stem))

    export_dir = project / "export"
    exports = sorted(path for path in export_dir.glob("*.*") if path.suffix.lower() in {".png", ".jpg", ".jpeg"})
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
        elif exported.stem not in expected_stems:
            findings.extend(validate_export_image(exported, source))

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
    source.add_argument("--empty-layer", action="append", default=[])
    review = commands.add_parser(
        "record-review",
        help="record a hash-bound visual review after a human or agent inspected all textless renders",
    )
    review.add_argument("--project", type=Path, required=True)
    review.add_argument("--panel", required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--confirm-no-visible-text", action="store_true", required=True)
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
        return _print_result(
            validate_krita_source(subject, empty_layers=set(args.empty_layer)), subject
        )
    if args.command == "record-review":
        subject = args.project.resolve()
        try:
            receipt = create_visual_review_receipt(subject, args.panel, args.reviewer)
        except (OSError, ValueError) as exc:
            return _print_result(
                [Finding("VISUAL_REVIEW_NOT_RECORDED", subject, str(exc))], subject
            )
        print(f"VISUAL REVIEW RECORDED: {receipt}")
        return 0
    subject = args.image.resolve()
    findings = validate_visual_prompt(args.prompt.resolve())
    if not findings:
        try:
            config = load_manga_config()
            policy = config["workflow_policy"]
        except ValueError as exc:
            findings.append(Finding("POLICY_CONFIG_INVALID", DEFAULT_CONFIG_PATH, str(exc)))
        else:
            findings.extend(
                validate_comfy_png(
                    subject,
                    args.prompt.resolve(),
                    required_node_types=policy["required_comfy_node_types"],
                    expected_checkpoint=config["comfy"]["checkpoint"],
                )
            )
    return _print_result(findings, subject)


if __name__ == "__main__":
    raise SystemExit(main())
