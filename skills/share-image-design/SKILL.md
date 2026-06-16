---
name: share-image-design
description: Generate Let's Share-style editorial product images using Kie.ai image models, with a tested fallback order and no publishing/storage side effects.
version: 1.0.0
author: Jeff / Jérémy
license: MIT
metadata:
  hermes:
    tags: [image-generation, product-photography, kie-ai, lets-share]
---

# Share Image Design

Use this skill when the task is to generate or regenerate product/editorial images for a Let's Share-style visual direction.

## Scope

Source note: `lets-share-redesign` used both Kie.ai and direct fal.ai tests. This skill exports the Kie.ai path as the primary runner because it is the latest generic wrapper; fal.ai IDs remain documented as fallbacks.

This skill is intentionally minimal:

- generate images only
- no R2 upload/publishing
- no Shopify/theme deployment
- no private reference assets in the repo
- no hardcoded API tokens

## Environment

Required:

```bash
export KIE_AI_API_KEY="..."
```

Optional convention:

```bash
mkdir -p generated
```

## Model choice

Preferred order for intimate product reference editing:

1. `bytedance/seedream-v4-edit` through Kie.ai — default for image-to-image product edits.
2. `nano-banana-pro` through Kie.ai — strong still-life generation; supports `1K`, `2K`, `4K`.
3. `grok-imagine/image-to-image` or `grok-imagine/text-to-image` through Kie.ai — permissive/aesthetic fallback.
4. `gpt-image-2-image-to-image` / `gpt-image-2-text-to-image` through Kie.ai — quality fallback for non-sensitive scenes; stricter moderation.
5. Direct fal.ai fallbacks, if available: `fal-ai/bytedance/seededit/v3/edit-image`, `fal-ai/qwen-image-edit-plus`, then experimental models listed in `docs/model-matrix.md`.

## Single generation CLI

From this skill directory:

```bash
python3 scripts/kie_generate.py seedream \
  --input "https://example.com/reference-product.jpg" \
  --prompt "Editorial product still-life. Preserve exact product shape, color, texture and proportions. Warm coral, cream-peach, sage palette. Premium magazine lighting." \
  --aspect 4:3 \
  --resolution 2K \
  --out generated/product-editorial.png
```

Other engines:

```bash
python3 scripts/kie_generate.py nb --prompt "..." --aspect 4:3 --resolution 2K --format png
python3 scripts/kie_generate.py grok --prompt "..." --aspect 4:3
python3 scripts/kie_generate.py gpt --prompt "..." --aspect 4:3
```

## Éclat batch

Use `eclat_batch.py` for a fixed set of Éclat editorial still-life prompts around one reference product:

```bash
python3 scripts/eclat_batch.py \
  --product 04 \
  --ref-url "https://example.com/reference-product.jpg" \
  --out-dir generated/eclat
```

## Prompt rules

- Preserve exact product geometry, material, color, texture, proportions and orientation.
- Specify lighting, surface, props, palette and camera/lens.
- Avoid sterile white backgrounds unless deliberately minimalist.
- For Let's Share Éclat: warm coral, magenta, cream-peach, sage, aubergine; never cyan/clinical blue.
- Generate a small preview before launching batches.

## Verification

Before sharing outputs:

1. Confirm files exist and are non-empty.
2. Keep prompt text or command history next to generated outputs for traceability.
3. Do not commit generated images, source references, `.env`, `.secrets`, or tokens.
