# Model matrix

Models observed in `limace11/lets-share-redesign` image-generation scripts and reduced to the useful public set.

## Recommended order for Let's Share product imagery

1. `bytedance/seedream-v4-edit` via Kie.ai
   - Best current default for intimate product image-to-image.
   - Preserves reference product shape well when prompted explicitly.
   - Use for batch editorial still-life generation from reference product photos.

2. `nano-banana-pro` via Kie.ai
   - Good text-to-image and image-assisted still-life model.
   - Supports `1K`, `2K`, `4K`; `png` or `jpg`.
   - Useful for premium visual directions and non-explicit lifestyle/editorial imagery.

3. `grok-imagine/image-to-image` and `grok-imagine/text-to-image` via Kie.ai
   - Permissive fallback for intimate product references.
   - Use `enable_pro=true` for higher quality text-to-image.
   - Grok image-to-image accepts one reference URL.

4. `gpt-image-2-image-to-image` and `gpt-image-2-text-to-image` via Kie.ai
   - High quality but strict moderation.
   - Keep as fallback for non-sensitive still-life, brand, packaging or abstract shots.

## FAL direct fallback models tested/considered

These are not wired into the public scripts because this repo keeps one simple Kie.ai path, but they are useful when running fal.ai directly:

- `fal-ai/bytedance/seededit/v3/edit-image`
  - Confirmed as a practical fallback for product edits.
- `fal-ai/qwen-image-edit-plus`
  - Useful high-res/detail fallback; may need prompt tuning.
- `fal-ai/flux-pro/kontext`
  - Strong general edit model, but was observed as blocked/problematic for intimate product references in this project.
- `fal-ai/flux-pro/v1.1-ultra`
  - Text-to-image fallback for non-sensitive hero/still-life visuals.
- `fal-ai/hidream-e1-1` / `fal-ai/hidream-i1-full/edit`
  - Experimental fallback; quality/prompt adherence varied.
- `fal-ai/luma-photon/modify` and `fal-ai/luma-photon/flash/edit`
  - Experimental visual-style fallback.
- `fal-ai/wan-25-preview/image-to-image` / `fal-ai/wan/v2.5-preview/image-to-image`
  - Experimental; not preferred for final product stills.

## Video models from upstream skill, not included here

The upstream Kie skill also referenced video models:

- `veo3_fast`
- `veo3_quality`
- `veo3_lite`
- `grok-imagine/image-to-video`
- `grok-imagine/upscale`

This public repo intentionally excludes video workflows; it is image-generation only.

## Typography context for generated visuals

If images need room for on-site overlays, preserve the Shopify typography system:

- Display/title: `Gambarino`, fallback `Times New Roman`, then `serif`.
- Body/UI/buttons: `Satoshi`, fallback `Inter`, then `system-ui`, `sans-serif`.

Do not bake large final text into generated images unless the output is explicitly an ad creative; leave copy to the Shopify theme when possible.
