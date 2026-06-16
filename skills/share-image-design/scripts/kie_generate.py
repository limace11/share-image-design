#!/usr/bin/env python3
"""
kie_generate.py — Image generation via KIE.AI API.

Supports three engines:
  gpt   → GPT Image 2        (OpenAI,  strict content moderation)
  nb    → Nano Banana Pro    (Google Gemini, vision moderation flags intimate refs)
  grok  → Grok Imagine (xAI) → nsfw_checker default off, accepts intimate product refs

Env:
  KIE_AI_API_KEY   required

Usage:
  # Text-to-image (no --input given)
  python kie_generate.py gpt  --prompt "..." [--aspect 1:1] [--out PATH]
  python kie_generate.py nb   --prompt "..." [--aspect 1:1] [--resolution 2K] [--format png] [--out PATH]
  python kie_generate.py grok --prompt "..." [--aspect 1:1] [--out PATH]

  # Image-to-image (pass one or more --input URL)
  python kie_generate.py gpt  --prompt "..." --input https://... [--input ...] [--out PATH]
  python kie_generate.py nb   --prompt "..." --input https://... [--input ...] [--resolution 2K] [--out PATH]
  python kie_generate.py grok --prompt "..." --input https://...                                 [--out PATH]

Docs:
  - Endpoint:  POST https://api.kie.ai/api/v1/jobs/createTask
  - Poll:      GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...
  - GPT t2i:   model="gpt-image-2-text-to-image",  input: {prompt, aspect_ratio, nsfw_checker}
  - GPT i2i:   model="gpt-image-2-image-to-image", input: {prompt, input_urls, aspect_ratio, nsfw_checker}
  - NB  both:  model="nano-banana-pro",            input: {prompt, image_input?, aspect_ratio, resolution, output_format}
  - Grok t2i:  model="grok-imagine/text-to-image",  input: {prompt, aspect_ratio, nsfw_checker, enable_pro}
  - Grok i2i:  model="grok-imagine/image-to-image", input: {prompt, image_urls, nsfw_checker}
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

API_BASE = "https://api.kie.ai/api/v1/jobs"

ASPECT_RATIOS = {"auto", "1:1", "5:4", "9:16", "21:9", "16:9", "4:3", "3:2", "4:5", "3:4", "2:3"}
GROK_ASPECTS = {"1:1", "2:3", "3:2", "16:9", "9:16"}
RESOLUTIONS = {"1K", "2K", "4K"}
FORMATS = {"png", "jpg"}

DOWNLOAD_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level:5s} {msg}", flush=True)


def get_api_key() -> str:
    key = os.environ.get("KIE_AI_API_KEY")
    if not key:
        log("KIE_AI_API_KEY not set. source .secrets/kie.env first.", "FATAL")
        sys.exit(2)
    return key


def post_json(url: str, payload: dict, api_key: str, timeout: int = 30) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str, api_key: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def create_task(api_key: str, model: str, inputs: dict) -> str:
    payload = {"model": model, "input": inputs}
    log(f"POST createTask  model={model}")
    log(f"  inputs keys: {list(inputs.keys())}")
    res = post_json(f"{API_BASE}/createTask", payload, api_key)
    if res.get("code") != 200:
        log(f"createTask error: {res}", "FATAL")
        sys.exit(3)
    task_id = res["data"]["taskId"]
    log(f"Task created: {task_id}")
    return task_id


def poll_task(api_key: str, task_id: str, max_wait_s: int = 300) -> dict:
    start = time.monotonic()
    delay = 2.0
    while True:
        elapsed = time.monotonic() - start
        if elapsed > max_wait_s:
            log(f"Polling timed out after {max_wait_s}s", "FATAL")
            sys.exit(4)

        res = get_json(f"{API_BASE}/recordInfo?taskId={task_id}", api_key)
        if res.get("code") != 200:
            log(f"recordInfo error: {res}", "FATAL")
            sys.exit(5)

        data = res["data"]
        state = data.get("state", "unknown")
        log(f"  state={state}  ({int(elapsed)}s elapsed)")

        if state == "success":
            return data
        if state == "fail":
            log(
                f"Task failed: code={data.get('failCode')} msg={data.get('failMsg')}",
                "FATAL",
            )
            sys.exit(6)

        time.sleep(delay)
        delay = min(delay * 1.3, 10.0)


def download(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log(f"Download -> {out_path}")
    req = urllib.request.Request(
        url, headers={"User-Agent": DOWNLOAD_UA, "Accept": "image/*,*/*"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp, open(out_path, "wb") as f:
        f.write(resp.read())
    size_kb = out_path.stat().st_size / 1024
    log(f"Saved {size_kb:.1f} KB")


def handle_result(data: dict, out_path: Path) -> None:
    result_json = data.get("resultJson")
    if not result_json:
        log("No resultJson in response", "FATAL")
        sys.exit(7)
    result = json.loads(result_json)
    urls = result.get("resultUrls") or []
    if not urls:
        log(f"No resultUrls in: {result}", "FATAL")
        sys.exit(8)

    if len(urls) == 1:
        download(urls[0], out_path)
        print(str(out_path))
    else:
        base = out_path.with_suffix("")
        ext = out_path.suffix or ".png"
        for i, url in enumerate(urls, 1):
            p = base.parent / f"{base.name}_{i}{ext}"
            download(url, p)
            print(str(p))


def default_out_path(prefix: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("generated") / f"{prefix}-{ts}.png"


def validate_choice(value: str, allowed: set, name: str) -> str:
    if value not in allowed:
        log(f"Invalid {name} '{value}'. Allowed: {sorted(allowed)}", "FATAL")
        sys.exit(1)
    return value


def cmd_gpt(args) -> None:
    api_key = get_api_key()
    has_input = bool(args.input)
    if has_input:
        model = "gpt-image-2-image-to-image"
        inputs = {
            "prompt": args.prompt,
            "input_urls": args.input,
            "aspect_ratio": validate_choice(args.aspect, ASPECT_RATIOS, "aspect_ratio"),
            "nsfw_checker": args.nsfw_check,
        }
    else:
        model = "gpt-image-2-text-to-image"
        inputs = {
            "prompt": args.prompt,
            "aspect_ratio": validate_choice(args.aspect, ASPECT_RATIOS, "aspect_ratio"),
            "nsfw_checker": args.nsfw_check,
        }
    task_id = create_task(api_key, model, inputs)
    data = poll_task(api_key, task_id, max_wait_s=args.wait)
    out = Path(args.out) if args.out else default_out_path("gpt-i2i" if has_input else "gpt-t2i")
    handle_result(data, out)


def cmd_seedream(args) -> None:
    """ByteDance Seedream v4 Edit — confirmed permissive for intimate product i2i."""
    api_key = get_api_key()
    if not args.input:
        log("Seedream v4 Edit requires at least one --input URL", "FATAL")
        sys.exit(1)
    # Map our aspect flag to Seedream's image_size enum
    size_map = {
        "1:1": "square_hd", "auto": "square_hd",
        "4:3": "landscape_4_3", "16:9": "landscape_16_9",
        "3:4": "portrait_4_3", "9:16": "portrait_16_9",
    }
    image_size = size_map.get(args.aspect, "square_hd")
    inputs = {
        "prompt": args.prompt,
        "image_urls": args.input[:10],  # up to 10
        "image_size": image_size,
        "image_resolution": args.resolution,
        "max_images": args.n,
    }
    task_id = create_task(api_key, "bytedance/seedream-v4-edit", inputs)
    data = poll_task(api_key, task_id, max_wait_s=args.wait)
    out = Path(args.out) if args.out else default_out_path("seedream-edit")
    handle_result(data, out)


def cmd_grok(args) -> None:
    api_key = get_api_key()
    has_input = bool(args.input)
    if has_input:
        # Grok i2i accepts only 1 URL in image_urls per docs
        if len(args.input) > 1:
            log(f"Grok i2i accepts only 1 image_url, got {len(args.input)} — using first", "WARN")
        model = "grok-imagine/image-to-image"
        inputs = {
            "prompt": args.prompt,
            "image_urls": [args.input[0]],
            "nsfw_checker": args.nsfw_check,
        }
    else:
        model = "grok-imagine/text-to-image"
        inputs = {
            "prompt": args.prompt,
            "aspect_ratio": validate_choice(args.aspect, GROK_ASPECTS, "aspect_ratio (grok)"),
            "nsfw_checker": args.nsfw_check,
            "enable_pro": args.enable_pro,
        }
    task_id = create_task(api_key, model, inputs)
    data = poll_task(api_key, task_id, max_wait_s=args.wait)
    out = Path(args.out) if args.out else default_out_path("grok-i2i" if has_input else "grok-t2i")
    handle_result(data, out)


def cmd_nb(args) -> None:
    api_key = get_api_key()
    inputs = {
        "prompt": args.prompt,
        "aspect_ratio": validate_choice(args.aspect, ASPECT_RATIOS, "aspect_ratio"),
        "resolution": validate_choice(args.resolution, RESOLUTIONS, "resolution"),
        "output_format": validate_choice(args.format, FORMATS, "output_format"),
    }
    if args.input:
        inputs["image_input"] = args.input  # Nano Banana param: `image_input`
    task_id = create_task(api_key, "nano-banana-pro", inputs)
    data = poll_task(api_key, task_id, max_wait_s=args.wait)
    default_name = "nb-i2i" if args.input else "nb-t2i"
    default = default_out_path(default_name).with_suffix(f".{args.format}")
    out = Path(args.out) if args.out else default
    handle_result(data, out)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="engine", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--prompt", required=True, help="Prompt text (max 20k chars)")
    shared.add_argument("--aspect", default="auto", help=f"Aspect ratio, one of {sorted(ASPECT_RATIOS)}")
    shared.add_argument(
        "--input",
        action="append",
        default=[],
        help="Reference image URL for image-to-image (repeatable). If omitted → text-to-image.",
    )
    shared.add_argument("--out", help="Output file path. Default: generated/<engine>-<mode>-<timestamp>.<ext>")
    shared.add_argument("--wait", type=int, default=300, help="Max seconds to wait for task completion")

    gpt = sub.add_parser(
        "gpt",
        parents=[shared],
        help="GPT Image 2 (OpenAI) — strict content moderation",
    )
    gpt.add_argument(
        "--nsfw-check",
        type=lambda v: v.lower() in ("true", "1", "yes"),
        default=True,
        help="OpenAI NSFW filter (default: true)",
    )
    gpt.set_defaults(func=cmd_gpt)

    nb = sub.add_parser(
        "nb",
        parents=[shared],
        help="Nano Banana Pro (Google Gemini) — more permissive, supports 1K/2K/4K",
    )
    nb.add_argument("--resolution", default="2K", help=f"Output resolution, one of {sorted(RESOLUTIONS)}")
    nb.add_argument("--format", default="png", help=f"Output format, one of {sorted(FORMATS)}")
    nb.set_defaults(func=cmd_nb)

    seed = sub.add_parser(
        "seedream",
        parents=[shared],
        help="ByteDance Seedream v4 Edit — permissive moderation, i2i editing",
    )
    seed.add_argument("--resolution", default="2K", help=f"Output resolution, one of {sorted(RESOLUTIONS)}")
    seed.add_argument("--n", type=int, default=1, help="Number of images per task (max_images, 1-4)")
    seed.set_defaults(func=cmd_seedream)

    grok = sub.add_parser(
        "grok",
        parents=[shared],
        help="Grok Imagine (xAI) — nsfw_checker default off, accepts intimate refs",
    )
    grok.add_argument(
        "--nsfw-check",
        type=lambda v: v.lower() in ("true", "1", "yes"),
        default=False,
        help="Grok NSFW filter (default: false — Grok is permissive)",
    )
    grok.add_argument(
        "--enable-pro",
        type=lambda v: v.lower() in ("true", "1", "yes"),
        default=True,
        help="Grok pro mode (slower + higher quality, default: true)",
    )
    grok.set_defaults(func=cmd_grok)

    return p


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        log(f"HTTP {e.code} {e.reason}: {body}", "FATAL")
        sys.exit(10)
    except urllib.error.URLError as e:
        log(f"Network error: {e}", "FATAL")
        sys.exit(11)


if __name__ == "__main__":
    main()
