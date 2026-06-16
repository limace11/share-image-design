#!/usr/bin/env python3
"""
eclat_batch.py — Generate 10 Éclat-aesthetic variations of ONE RealShare product via Seedream v4 Edit.

Usage:
  python scripts/eclat_batch.py --product NN --ref-url URL [--skip N] [--out-dir DIR]

Each call generates up to 10 images: 6 editorial product still-lifes, 2 macro/texture details,
2 multi-object compositions. Saves to <out-dir>/realshare-NN/<NN>-<slug>.png

Outputs progress + final summary line. Designed to be invoked in parallel for each product.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

API_KEY = os.environ.get("KIE_AI_API_KEY")
if not API_KEY:
    print("FATAL: KIE_AI_API_KEY not set", file=sys.stderr); sys.exit(2)

DOWNLOAD_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# 10 prompt templates. Each preserves the exact product shape/proportions/skin tone from the ref.
# All within Éclat palette: coral, magenta, cream-peach, sage, aubergine.
PROMPTS = [
    {
        "slug": "01-blood-orange-satin",
        "aspect": "4:3",
        "prompt": (
            "Editorial product still-life. Preserve the exact silicone object shape, proportions, suction-cup base "
            "and skin tone from the reference. Place it three-quarter angle on a cream-peach satin sheet. "
            "Setting: halved blood-orange glistening off-center, single dried olive branch trailing across the lower frame, "
            "water droplet on the silicone. Light: large softbox top-left, warm 3200K, gentle shadow falling lower-right. "
            "Color: coral + magenta + cream-peach + sage. No cyan, no clinical white void. "
            "Style: The Gentlewoman magazine × Jacquemus, Phase One 80mm macro, Portra 400 grain."
        ),
    },
    {
        "slug": "02-aubergine-velvet-dahlia",
        "aspect": "4:3",
        "prompt": (
            "Editorial product still-life. Preserve the exact silicone object shape, proportions, suction-cup base "
            "and skin tone from the reference. Place it lying on a deep aubergine velvet surface, one dried magenta dahlia bloom "
            "trailing nearby, a thin gold-painted ceramic dish in the lower-right corner. "
            "Light: hard studio flash from camera-right, deep saturated shadow falling left. "
            "Color: aubergine + magenta + warm gold accents + sage. "
            "Style: Roe Ethridge × Wallpaper magazine, Hasselblad 100mm macro, large format feel."
        ),
    },
    {
        "slug": "03-sage-plaster-wall",
        "aspect": "3:4",
        "prompt": (
            "Editorial product still-life, vertical 3:4. Preserve the exact silicone object shape, proportions, suction-cup "
            "base and skin tone from the reference. Place it standing on its base on a thin coral linen drape, against a "
            "textured sage-green plaster wall. One dried olive sprig leaning beside it, a small cream ceramic bowl with sea salt. "
            "Light: soft north window light from camera-left, gentle modeling on the silicone, deep shadow on the wall to the right. "
            "Color: sage + coral + cream + warm bronze accents. "
            "Style: Kinfolk magazine × Monocle product editorial, Pentax 67 medium format, Portra 400 grain."
        ),
    },
    {
        "slug": "04-magenta-silk-sage-sprig",
        "aspect": "4:3",
        "prompt": (
            "Editorial product still-life. Preserve the exact silicone object shape, proportions, suction-cup base "
            "and skin tone from the reference. Place it on a crumpled magenta silk pillowcase, next to a single dried sage sprig "
            "and a small ceramic bowl of salt crystals. Light: hard sun coming through venetian blinds, casting horizontal "
            "bands of shadow across the scene, warm and saturated. "
            "Color: magenta + cream + warm sage + soft amber light bands. "
            "Style: Pietro Birindelli × Jacquemus e-commerce, medium format, late-morning private-luxury mood."
        ),
    },
    {
        "slug": "05-coral-painted-wall-fig",
        "aspect": "4:3",
        "prompt": (
            "Editorial product still-life. Preserve the exact silicone object shape, proportions, suction-cup base "
            "and skin tone from the reference. Place it on a low cream-peach surface against a hand-painted coral-orange "
            "wall in the background. Setting: one halved fresh fig with red flesh exposed, a small cream silk ribbon "
            "curling in mid-air, a thin shadow of an unseen plant frond across the wall. "
            "Light: warm side flash from camera-right freezing the ribbon mid-motion. "
            "Color: coral + cream + fig-red accents + soft sage shadow. "
            "Style: Tim Walker × Petra Collins, large format film, saturated editorial."
        ),
    },
    {
        "slug": "06-warm-wood-linen-figs",
        "aspect": "3:2",
        "prompt": (
            "Editorial product still-life, 3:2 landscape. Preserve the exact silicone object shape, proportions, suction-cup "
            "base and skin tone from the reference. Place it on a warm-walnut wood plank surface, alongside a softly crumpled "
            "natural linen napkin, two ripe figs (one whole, one halved showing red pulp), and a sprig of dried sage. "
            "Light: late golden hour through a side window, warm rake from camera-right, long soft shadows. "
            "Color: warm wood + cream linen + fig-red + sage + soft coral light. "
            "Style: Bobbi Lin food editorial × The Gentlewoman, Phase One 80mm, Portra 400 grain, art-directed."
        ),
    },
    {
        "slug": "07-cream-concrete-minimal",
        "aspect": "1:1",
        "prompt": (
            "Minimalist editorial product still-life, 1:1 square. Preserve the exact silicone object shape, proportions, "
            "suction-cup base and skin tone from the reference. Place it on a polished cream-concrete surface, with only "
            "one single small dried coral flower placed off-center for color. Strong negative space, refined composition. "
            "Light: single large overhead softbox, soft falloff, clean shadow directly beneath the object. "
            "Color: cream + warm taupe shadow + one coral accent. No cyan, no sterile lab white. "
            "Style: Apple product photo × Wallpaper magazine, Hasselblad 100mm macro, contemporary luxury."
        ),
    },
    {
        "slug": "08-venetian-blind-shadows",
        "aspect": "3:4",
        "prompt": (
            "Editorial product still-life, vertical 3:4. Preserve the exact silicone object shape, proportions, suction-cup "
            "base and skin tone from the reference. Place it on a cream-peach satin sheet draped across a low surface, "
            "with hard horizontal sun-shadow bands from venetian blinds falling across the scene. "
            "Single dried olive branch echoing the shadow lines. Mood: Sunday-morning private luxury. "
            "Light: warm hard sun through blinds, sharp graphic shadows, saturated. "
            "Color: cream + coral light + amber shadow + sage olive. "
            "Style: Pietro Birindelli × Roe Ethridge, medium format, cinematic."
        ),
    },
    {
        "slug": "09-macro-texture-droplet",
        "aspect": "1:1",
        "prompt": (
            "Macro material study photograph, 1:1 square. Extreme close-up of the silicone surface from the reference object — "
            "preserve the matte skin tone and texture exactly. Frame so only the soft-touch surface and a small portion of the "
            "rounded base fill the frame, texture-first composition, almost abstract. One water droplet catching warm light. "
            "Background: a sliver of cream-peach satin and a dried olive leaf at the top edge. "
            "Light: raking hard light from upper-left, warm tones, showing every micro-detail. "
            "Color: skin tone + cream-peach + warm sage. "
            "Style: The Gentlewoman material library × Apple AirPods macro launch, Phase One 120mm macro, premium manufacturing feel."
        ),
    },
    {
        "slug": "10-flatlay-still-life",
        "aspect": "4:3",
        "prompt": (
            "Editorial flat-lay still-life, top-down 90° overhead, 4:3. Preserve the exact silicone object shape, proportions, "
            "suction-cup base and skin tone from the reference, lying horizontally on a crumpled cream-peach satin sheet. "
            "Arrange around it: a halved blood-orange with juice beads, three dried olive sprigs fanning across one corner, "
            "a small ceramic dish with sea salt crystals, a folded magenta silk ribbon trailing the bottom edge. "
            "Treat the object as ONE element among several art-directed still-life pieces, not the singular focus. "
            "Light: hard overhead sun upper-left, crisp diagonal shadows. "
            "Color: coral + magenta + cream + sage + warm blood-orange red. "
            "Style: Bobbi Lin food flat-lay × Jacquemus, Portra 400 grain."
        ),
    },
]

SIZE_MAP = {
    "1:1": "square_hd", "auto": "square_hd",
    "4:3": "landscape_4_3", "16:9": "landscape_16_9",
    "3:4": "portrait_4_3", "9:16": "portrait_16_9",
    "3:2": "landscape_4_3", "2:3": "portrait_4_3",  # fallback approximations
}


def log(msg, prefix=""):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {prefix}{msg}", flush=True)


def post(url, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode(errors='replace')}


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": DOWNLOAD_UA, "Accept": "image/*,*/*"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())
    return path.stat().st_size / 1024


def generate_one(prefix, ref_url, prompt_data, out_path):
    inputs = {
        "prompt": prompt_data["prompt"],
        "image_urls": [ref_url],
        "image_size": SIZE_MAP.get(prompt_data["aspect"], "square_hd"),
        "image_resolution": "2K",
        "max_images": 1,
    }
    payload = {"model": "bytedance/seedream-v4-edit", "input": inputs}
    res = post("https://api.kie.ai/api/v1/jobs/createTask", payload)
    if "http_error" in res or res.get("code") != 200:
        log(f"createTask FAIL: {res}", prefix=prefix)
        return False
    task_id = res["data"]["taskId"]
    start = time.monotonic(); delay = 2.0
    while True:
        elapsed = int(time.monotonic() - start)
        if elapsed > 240:
            log(f"  {prompt_data['slug']} TIMEOUT", prefix=prefix); return False
        info = get(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}")
        data = info.get("data") or {}
        state = data.get("state")
        if state == "success":
            rj = json.loads(data.get("resultJson") or "{}")
            urls = rj.get("resultUrls") or []
            if not urls:
                log(f"  {prompt_data['slug']} NO URLS", prefix=prefix); return False
            kb = download(urls[0], out_path)
            log(f"  {prompt_data['slug']} OK ({kb:.0f} KB, {elapsed}s)", prefix=prefix)
            return True
        if state == "fail":
            log(f"  {prompt_data['slug']} FAIL: {data.get('failMsg')}", prefix=prefix); return False
        time.sleep(delay); delay = min(delay * 1.3, 8.0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--product", required=True, help="Product number, e.g. 04")
    p.add_argument("--ref-url", required=True, help="Public HTTPS URL of the reference image")
    p.add_argument("--out-dir", default="generated/eclat", help="Base output dir")
    p.add_argument("--skip", type=int, default=0, help="Skip first N prompts (for resume)")
    p.add_argument("--limit", type=int, default=0, help="Stop after N prompts (0=all)")
    args = p.parse_args()

    prefix = f"[realshare-{args.product}] "
    log(f"Starting batch for realshare-{args.product}, ref={args.ref_url}", prefix=prefix)
    out_root = Path(args.out_dir) / f"realshare-{args.product}"
    out_root.mkdir(parents=True, exist_ok=True)

    prompts_to_run = PROMPTS[args.skip:]
    if args.limit:
        prompts_to_run = prompts_to_run[:args.limit]

    ok, fail = 0, 0
    for pd in prompts_to_run:
        out_path = out_root / f"{args.product}-{pd['slug']}.png"
        if out_path.exists():
            log(f"  {pd['slug']} SKIP (exists)", prefix=prefix)
            continue
        if generate_one(prefix, args.ref_url, pd, out_path):
            ok += 1
        else:
            fail += 1

    log(f"DONE realshare-{args.product}: {ok} ok, {fail} fail, out={out_root}", prefix=prefix)


if __name__ == "__main__":
    main()
