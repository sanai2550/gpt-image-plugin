# Prompt templates by task (GPT Image 2.6)

Condensed from https://developers.openai.com/api/docs/guides/image-prompting. Adapt, don't copy blindly.

## Photorealistic / style & lighting  (`-s 1024x1536 -q medium`)
```
Create a photorealistic candid photograph of an elderly sailor standing on a small fishing boat.
He has weathered skin with visible wrinkles, pores, and sun texture, and a few faded traditional sailor tattoos on his arms.
He is calmly adjusting a net while his dog sits nearby on the deck. Shot like a 35mm film photograph, medium close-up at eye level, using a 50mm lens.
Soft coastal daylight, shallow depth of field, subtle film grain, natural color balance.
The image should feel honest and unposed, with real skin texture, worn materials, and everyday detail. No glamorization, no heavy retouching.
```

## Explain a process (infographic)
Name process, audience, information. Verify labels and factual relationships afterwards.
```
Create a detailed Infographic of the functioning and flow of an automatic coffee machine like a Jura.
From bean basket, to grinding, to scale, water tank, boiler, etc.
I'd like to understand technically and visually the flow.
```

## Exact text / ad
```
Give me a cool in culture ad / fashion shot for a brand called Thread.
It's a hip young street brand. The ad shows a group of friends hanging out together with the tagline "Yours to Create."
Make it feel like a polished campaign image for a youth streetwear audience: stylish, contemporary, energetic, and tasteful.
Use clean composition, strong color direction, natural poses, and premium fashion photography cues.
Render the tagline exactly once, clearly and legibly, integrated into the ad layout.
No extra text, no watermarks, no unrelated logos.
```
Billboard variant:
```
Billboard text (EXACT, verbatim, no extra characters):
"Fresh and clean"
Typography: bold sans-serif, high contrast, centered, clean kerning.
Ensure text appears once and is perfectly legible.
No watermarks, no logos.
```

## Logo (png transparent ×4, or `-f svg`)
```
Create an original, non-infringing logo for a company called Field & Flour, a local bakery.
The logo should feel warm, simple, and timeless. Use clean, vector-like shapes, a strong silhouette, and balanced negative space.
Favor simplicity over detail so it reads clearly at small and large sizes. Flat design, minimal strokes, no gradients unless essential.
Fully transparent background. Deliver a single centered logo with generous padding, clean alpha edges, and no solid backdrop, scenery, checkerboard, or watermark.
```

## Open-ended illustration — compare complexity
Prompt that leaves design choices open benefits from `-c high` (default):
`A premium handcrafted layered paper-cut illustration of a football team celebrating a championship victory inside a packed stadium.`
Keep `-q` fixed when comparing complexity levels.

## Looping GIF  (`-m sunburst -f gif -s 512x512 -q high --frame-count 9 --frame-duration-ms 200` → 1.8 s)
Give a starting pose to return to and say whether the camera moves:
```
A little monkey in an olive-green hooded coat stands in a snowy pine forest at dusk. A wooden cabin glows in the background.
The monkey holds a glowing amber paper lantern at chest height, slowly lifts it, looks up and blinks, then lowers it back to its starting pose.
Keep the lantern in its hands and the camera still. Make the motion loop smoothly.
```

## Comic strip, UI preview, scientific visuals, slides & charts
- Comic: number the panels, describe each panel's action + dialogue in quotes, keep the same character description in every panel.
- Interface preview: platform, screen, layout regions, exact UI copy in quotes, style system (colors, type), "no lorem ipsum".
- Scientific/educational: audience level, what must be labeled, label list in quotes, "accurate proportions", verify facts.
- Slides/diagrams/charts: use a landscape custom size like `1536x864`; give title, exact bullet/label text, data values, and layout. Check every number and label.

---

# Edits (`edit` subcommand)

## Markup-guided local edit
Draw on a transparent PNG overlay (same pixel size as image 1), pass with `--markup`:
```
Recolor the striped vase inside the red circle to solid cobalt blue ceramic. Keep its shape, the dried stems, and the rest of the kitchen unchanged. Remove the red circle from the finished photo.
```

## Translate text, keep layout
```
Translate all text in the image into Vietnamese. Keep the design, layout, colors, icons and typography style unchanged. Do not leave any words in the original language.
```

## Style transfer
`Use image 1 as the style reference (palette, brushwork, lighting). Redraw image 2 in that style. Keep image 2's composition and subject.`

## Preserve identity, change clothing
`Keep the person's face, identity, hairstyle, pose and background exactly the same. Change only the outfit to <...>.`

## Combine references
```
Place the dog from the second image into the setting of image 1, right next to the woman, use the same style of lighting, composition and background. Do not change anything else.
```

## Transparent product cutout  (`-b transparent -f png`)
```
Extract the product from the input image and isolate it on a fully transparent background.
Output: centered product, crisp silhouette, no halos/fringing.
Preserve product geometry and label legibility exactly.
Add only light polishing. Do not add a solid backdrop, checkerboard, scenery, or shadow.
Do not restyle the product; remove the background and preserve clean alpha transparency.
```
A drawn checkerboard is NOT transparency — verify the alpha channel. Restate "preserve transparent background" on follow-up edits.

## Drawing → realistic, remove object, insert a person
- Sketch to photo: "Turn this drawing into a realistic photograph. Keep the composition, proportions and object placement of the sketch."
- Remove: "Remove <object>. Fill the area naturally to match surroundings. Change nothing else."
- Insert person: specify position, scale relative to scene, pose, matching light direction and shadows.

## Multi-turn refinement
1. Create the starting image. 2. Feed output back with `-i`, change ONE condition (e.g. "Make it a rainy night. Keep the billboard, text and composition unchanged."). 3. For a consistent character, write a fixed character sheet (appearance, clothes, colors) and repeat it in each prompt, passing the previous image as reference.

---

# Check the result
- Every word readable and matching the requested text? Diagram labels and relationships correct?
- Identities, product shapes, labels, reference details intact?
- Did the edit change only what was requested?
- Transparency: does the decoded file have transparent pixels?
  `python3 -c "import sys;from PIL import Image;im=Image.open(sys.argv[1]);print(im.mode, im.getextrema()[-1] if im.mode=='RGBA' else 'no alpha')" file.png`
