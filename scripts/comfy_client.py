"""Small dependency-free client for a local ComfyUI server."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


class ComfyError(RuntimeError):
    pass


def request_json(server: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = server.rstrip("/") + path
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        request = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ComfyError(f"ComfyUI に接続できません: {url}\n{exc}") from exc


def available_checkpoints(server: str) -> list[str]:
    info = request_json(server, "/object_info/CheckpointLoaderSimple")
    try:
        values = info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ComfyError("ComfyUI からチェックポイント一覧を取得できませんでした") from exc
    return [str(value) for value in values]


def choose_checkpoint(server: str, requested: str | None) -> str:
    choices = available_checkpoints(server)
    if not choices:
        raise ComfyError(
            "チェックポイントがありません。Comfy Desktop の Model Library またはテンプレート画面から、"
            "6GB VRAM で動くモデルを1つ導入してください。"
        )
    if requested:
        if requested not in choices:
            raise ComfyError(f"モデル '{requested}' が見つかりません。候補: {', '.join(choices)}")
        return requested
    return choices[0]


def available_controlnets(server: str) -> list[str]:
    info = request_json(server, "/object_info/ControlNetLoader")
    try:
        values = info["ControlNetLoader"]["input"]["required"]["control_net_name"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ComfyError("ComfyUI から ControlNet 一覧を取得できませんでした") from exc
    return [str(value) for value in values]


def choose_controlnet(server: str, requested: str | None) -> str:
    choices = available_controlnets(server)
    if not choices:
        raise ComfyError("ControlNet モデルがありません。models/controlnet に導入してください。")
    if requested:
        if requested not in choices:
            raise ComfyError(f"ControlNet '{requested}' が見つかりません。候補: {', '.join(choices)}")
        return requested
    return choices[0]


def upload_image(server: str, path: Path) -> str:
    path = path.resolve()
    boundary = f"----manga-system-{uuid.uuid4().hex}"
    newline = b"\r\n"
    body = bytearray()

    def field(name: str, value: str) -> None:
        body.extend(f"--{boundary}".encode("ascii") + newline)
        body.extend(f'Content-Disposition: form-data; name="{name}"'.encode("ascii") + newline + newline)
        body.extend(value.encode("utf-8") + newline)

    body.extend(f"--{boundary}".encode("ascii") + newline)
    body.extend(
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"'.encode("utf-8")
        + newline
    )
    body.extend(b"Content-Type: image/png" + newline + newline)
    body.extend(path.read_bytes() + newline)
    field("type", "input")
    field("overwrite", "true")
    body.extend(f"--{boundary}--".encode("ascii") + newline)

    request = urllib.request.Request(
        server.rstrip("/") + "/upload/image",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ComfyError(f"ControlNet 構図ガイドをアップロードできません: {path}\n{exc}") from exc
    name = result.get("name")
    if not name:
        raise ComfyError(f"ComfyUI がアップロード名を返しませんでした: {result}")
    subfolder = str(result.get("subfolder", "")).strip("/\\")
    return f"{subfolder}/{name}" if subfolder else str(name)


def build_workflow(
    template: dict[str, Any], *, checkpoint: str, prompt: str, negative: str,
    seed: int, width: int, height: int, steps: int, cfg: float,
    sampler: str, scheduler: str, prefix: str, control_image: str = "",
    controlnet: str = "", control_strength: float = 1.0,
) -> dict[str, Any]:
    workflow = json.loads(json.dumps(template))
    workflow["1"]["inputs"]["ckpt_name"] = checkpoint
    workflow["2"]["inputs"]["text"] = prompt
    workflow["3"]["inputs"]["text"] = negative
    workflow["4"]["inputs"].update(width=width, height=height)
    workflow["5"]["inputs"].update(
        seed=seed, steps=steps, cfg=cfg, sampler_name=sampler, scheduler=scheduler
    )
    workflow["7"]["inputs"]["filename_prefix"] = prefix
    if control_image:
        try:
            workflow["8"]["inputs"]["image"] = control_image
            workflow["10"]["inputs"]["control_net_name"] = controlnet
            workflow["11"]["inputs"]["strength"] = control_strength
        except KeyError as exc:
            raise ComfyError("ControlNet 用ワークフローに必要なノードがありません") from exc
    return workflow


def wait_for_outputs(server: str, prompt_id: str, timeout: int) -> list[dict[str, str]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        item = request_json(server, f"/history/{prompt_id}").get(prompt_id)
        if item:
            status = item.get("status", {})
            if status.get("status_str") == "error":
                raise ComfyError(f"ComfyUI の生成が失敗しました: {status.get('messages', [])}")
            images: list[dict[str, str]] = []
            for node in item.get("outputs", {}).values():
                images.extend(node.get("images", []))
            if images:
                return images
        time.sleep(1)
    raise ComfyError(f"生成が {timeout} 秒以内に完了しませんでした")


def download_output(server: str, image: dict[str, str], destination: Path) -> None:
    query = urllib.parse.urlencode(
        {"filename": image["filename"], "subfolder": image.get("subfolder", ""), "type": image.get("type", "output")}
    )
    url = server.rstrip("/") + "/view?" + query
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            destination.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ComfyError(f"生成画像を取得できません: {url}\n{exc}") from exc


def generate(args: argparse.Namespace) -> list[Path]:
    template = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    checkpoint = choose_checkpoint(args.server, args.model or None)
    control_image = ""
    controlnet = ""
    if args.control_image:
        control_image = upload_image(args.server, Path(args.control_image))
        controlnet = choose_controlnet(args.server, args.controlnet or None)
    seed = args.seed if args.seed >= 0 else random.SystemRandom().randrange(0, 2**63 - 1)
    workflow = build_workflow(
        template, checkpoint=checkpoint,
        prompt=Path(args.prompt_file).read_text(encoding="utf-8").strip(),
        negative=args.negative, seed=seed, width=args.width, height=args.height,
        steps=args.steps, cfg=args.cfg, sampler=args.sampler,
        scheduler=args.scheduler, prefix=f"manga/{args.project}_{args.panel}",
        control_image=control_image, controlnet=controlnet,
        control_strength=args.control_strength,
    )
    queued = request_json(args.server, "/prompt", {"prompt": workflow, "client_id": str(uuid.uuid4())})
    prompt_id = queued.get("prompt_id")
    if not prompt_id:
        raise ComfyError(f"ComfyUI が prompt_id を返しませんでした: {queued}")
    control_note = f", controlnet={controlnet}" if controlnet else ""
    print(f"生成開始: model={checkpoint}{control_note}, seed={seed}, prompt_id={prompt_id}")
    images = wait_for_outputs(args.server, prompt_id, args.timeout)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for index, image in enumerate(images, start=1):
        suffix = Path(image["filename"]).suffix or ".png"
        destination = output_dir / f"{args.panel}_{seed}_{index:02d}{suffix}"
        download_output(args.server, image, destination)
        saved.append(destination)
        print(f"保存: {destination}")
    return saved


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--server", required=True)
    result.add_argument("--workflow", required=True)
    result.add_argument("--prompt-file", required=True)
    result.add_argument("--output-dir", required=True)
    result.add_argument("--project", required=True)
    result.add_argument("--panel", required=True)
    result.add_argument("--model", default="")
    result.add_argument("--control-image", default="")
    result.add_argument("--controlnet", default="")
    result.add_argument("--control-strength", type=float, default=1.0)
    result.add_argument("--negative", default="")
    result.add_argument("--seed", type=int, default=-1)
    result.add_argument("--width", type=int, default=768)
    result.add_argument("--height", type=int, default=1024)
    result.add_argument("--steps", type=int, default=24)
    result.add_argument("--cfg", type=float, default=6.5)
    result.add_argument("--sampler", default="dpmpp_2m")
    result.add_argument("--scheduler", default="karras")
    result.add_argument("--timeout", type=int, default=900)
    return result


def main() -> int:
    try:
        generate(parser().parse_args())
        return 0
    except (ComfyError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
