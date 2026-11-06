---
name: gpt-image
description: Generate and edit images with OpenAI GPT Image 2.6 (gpt-image-2.6-flare / gpt-image-2.6-sunburst). Use when the user asks to create, draw, render, design or edit an image, photo, logo, icon, poster, ad, infographic, diagram, slide visual, comic, UI mockup, transparent cutout, SVG logo or looping GIF — or mentions "gpt image", "tạo ảnh", "vẽ ảnh", "sửa ảnh", "chỉnh ảnh". Works with OpenAI or any OpenAI-compatible proxy (CLIProxyAPI, LiteLLM...). Requires GPT_IMAGE_API_KEY or OPENAI_API_KEY.
---

# GPT Image 2.6

Script: `${CLAUDE_PLUGIN_ROOT}/skills/gpt-image/scripts/gpt_image.py` (Python 3, stdlib only).
If `CLAUDE_PLUGIN_ROOT` is empty (skill installed standalone), use the `scripts/` folder next to this file.

## Provider

The script reads `GPT_IMAGE_BASE_URL` (fallback `OPENAI_BASE_URL`, default `https://api.openai.com/v1`) and `GPT_IMAGE_API_KEY` (fallback `OPENAI_API_KEY`). The base URL must end in `/v1`. Before the first generation on a new provider, run `python3 "$S" models` to see which image model ids it exposes; if `gpt-image-2.6-*` isn't listed, use the closest listed id with `-m <id>` and tell the user. Parameters newer than the provider's backend (e.g. `complexity`, `markup`, svg/gif) may be rejected — on a 400 error, drop that field and retry once, and report it.

## Workflow

1. **Understand the image**: intended use, subject, composition/aspect, style, exact text, references. Ask only if something essential is missing; otherwise pick sensible defaults.
2. **Write the prompt** using the rules below (read `references/prompting.md` for templates of the matching task type).
3. **Pick parameters** (table below). Run the script. Save into the user's project (default `generated-images/`).
4. **Inspect the result**: open the saved file with Read to look at it. Check text spelling, labels, identity/geometry preservation, that the edit changed only what was asked, and real alpha for transparency.
5. **Iterate one change at a time**: pass the previous output as `-i` to `edit`, request one change, restate what must stay the same.

## Commands

```bash
S="${CLAUDE_PLUGIN_ROOT}/skills/gpt-image/scripts/gpt_image.py"

# Generate
python3 "$S" generate "PROMPT" -m flare -s 1024x1536 -q medium -o generated-images/poster.png
# Long prompt from a file
python3 "$S" generate @prompt.txt -m sunburst -q high
# Several variations
python3 "$S" generate "PROMPT" -n 4 -o generated-images/logo.png      # -> logo-1..4.png
# Transparent asset
python3 "$S" generate "PROMPT" -b transparent -f png
# Scalable SVG logo (generation only)
python3 "$S" generate "PROMPT" -f svg -b transparent -n 1 -o generated-images/logo.svg
# Looping GIF (generation only)
python3 "$S" generate "PROMPT" -m sunburst -f gif -s 512x512 -q high --frame-count 9 --frame-duration-ms 200

# Edit (image 1, image 2 ... in -i order)
python3 "$S" edit "Change only X. Keep Y, Z unchanged." -i input.png -o generated-images/edit.png
python3 "$S" edit "Place the dog from image 2 next to the woman in image 1..." -i scene.jpg -i dog.jpg
# Edit guided by markup (transparent PNG overlay, same pixel size as image 1)
python3 "$S" edit "Recolor the object inside the red circle ... Remove the red circle." -i photo.webp --markup circle.png

# Inspect the request without spending credits
python3 "$S" generate "PROMPT" --dry-run
```

The script prints JSON `{model, saved[], seconds, usage}`. Unknown/new API fields: `--extra key=value`.

## Parameters

| Flag | Values | Guidance |
|---|---|---|
| `-m` | `flare` (default), `sunburst`, or full id | Flare = speed. Sunburst = demanding detail, dense layouts, precise edits. |
| `-q` | `auto low medium high xhigh max` | Detail like texture and small lettering. Start `medium`; raise only if small text/detail fails. |
| `-c` | `low medium high` | Planning before rendering. API default `high`. Use `low` for targeted single-detail edits; `high` when the prompt leaves design open. Fully specified designs barely change. Tune quality OR complexity, never both at once. |
| `-s` | `auto`, `1024x1024`, `1536x1024`, `1024x1536`, custom | Custom: both edges multiples of 16, aspect between 1:3 and 3:1 (e.g. slide `1536x864`). |
| `-b` | `auto opaque transparent` | Transparent: png/webp/svg only. Also ask for it in the prompt. |
| `-f` | `png jpeg webp svg gif` | `--compression` only for jpeg/webp. svg/gif only for `generate`. |
| `--markup` | PNG | Edits only; applies to the first image; don't combine with `--mask`. |

Do not send `input_fidelity` or `reasoning.summary` (unsupported on 2.6). For SVG don't send stream/partial_images/output_compression/prompt_rewriter.

## Prompting rules (from OpenAI's guide)

1. **Define the result** — subject + intended use (product photo, ad, diagram...), composition, aspect, placement. For complex requests use labeled sections: Scene / Subject / Details / Constraints.
2. **Readable format** — prose, bullets or JSON-like all work; choose what is easiest to maintain.
3. **Visible details** — materials, lighting, colors, medium. Say "photorealistic" / "real photograph" explicitly. Camera/lens terms are appearance cues. For cinematic/neon/rain/low-light: specify scale, atmosphere, color — not just mood words.
4. **People & actions** — body framing ("full body visible, feet included"), gaze, scale, hand/object interaction.
5. **Exact text** — put copy in quotes, say how many times it appears, position + typography; spell rare names letter by letter; add "No extra text, no watermarks, no unrelated logos". Use medium/high quality for small text.
6. **Edits: change vs. preserve** — "Change only X." then list what to keep (identity, geometry, layout, lighting, labels, camera angle, surrounding objects). State exclusions.
7. **Reference roles** — "image 1 = scene, image 2 = subject/style/clothing"; say what moves where.
8. **Iterate deliberately** — one change per turn; restate critical constraints if it drifts.

If the user writes in Vietnamese (or another language), you may write the prompt in English for precision, but keep any on-image text exactly in the language the user wants.

## Safety & honesty

- Don't create images impersonating real people deceptively, or other content OpenAI's policy forbids; if the API refuses, report the message.
- Never print or log the API key. If `OPENAI_API_KEY` is missing, tell the user to set it.
- For pixel-identical regions, composite the approved edit back into the original.
