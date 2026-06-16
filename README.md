# Share Image Design

Minimal public skill pack for generating Let's Share-style editorial product images.

Note: the source project used both Kie.ai and direct fal.ai experiments. The reusable public scripts here use Kie.ai because the latest generic generator in the source repo (`scripts/kie_generate.py`) wraps the preferred current models there. fal.ai model IDs are documented as direct fallback/experimental paths, not as the primary public runner.

This repository intentionally contains only image-generation skills and scripts:

- no R2 publishing/upload pipeline
- no private source photos
- no generated assets
- no API tokens
- no Shopify/theme files

## Included

- `skills/share-image-design/SKILL.md` — operating guide for agents
- `skills/share-image-design/scripts/kie_generate.py` — generic Kie.ai image generation CLI
- `skills/share-image-design/scripts/eclat_batch.py` — batch generator for Éclat-style product still-lifes
- `docs/model-matrix.md` — tested/known model choices and fallback order
- `examples/prompts.md` — reusable prompt patterns

## API key

Set the key in your shell before running scripts:

```bash
export KIE_AI_API_KEY="..."
```

The scripts read the key from the environment. Do not commit `.env`, `.secrets`, outputs, source references, or generated images.

## Quick start

```bash
cd skills/share-image-design
python3 scripts/kie_generate.py seedream \
  --input "https://example.com/reference-product.jpg" \
  --prompt "Editorial product still-life. Preserve exact product shape, material, proportions and color. Warm coral, cream-peach, sage palette. Magazine-quality studio lighting." \
  --aspect 4:3 \
  --resolution 2K \
  --out generated/product-editorial.png
```

## Preferred model order

For intimate product/reference image editing, use:

1. `bytedance/seedream-v4-edit` — best current default for permissive product image-to-image.
2. `nano-banana-pro` — strong still-life generation, 1K/2K/4K, good for text-to-image and some edits.
3. `grok-imagine/image-to-image` or `grok-imagine/text-to-image` — permissive, aesthetic fallback.
4. `gpt-image-2-*` — high quality but strict moderation, fallback for non-sensitive scenes.
5. FAL fallbacks if using fal.ai directly: `fal-ai/bytedance/seededit/v3/edit-image`, then `fal-ai/qwen-image-edit-plus`, then experimental endpoints in `docs/model-matrix.md`.

See `docs/model-matrix.md` for details.
