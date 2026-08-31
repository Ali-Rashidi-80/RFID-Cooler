# Logo generation prompt — RFID Cooler Controller

**Canonical assets:** [`assets/logo.svg`](../assets/logo.svg) (vector) · [`assets/logo-3d.png`](../assets/logo-3d.png) (3D render)

Use this prompt with DALL·E, Midjourney, Stable Diffusion, or Cursor **GenerateImage** when refreshing brand assets.

---

## Master prompt (3D product icon)

```
Professional 3D product logo icon for "RFID Cooler Controller" industrial IoT firmware.

Subject: a stylized evaporative cooler unit merged with an RFID contactless card wave symbol.

Style: premium industrial tech, isometric 3D render, matte brushed aluminum housing with teal-cyan accent glow (#147A8A → #3ECFB2), subtle frost/ice vapor particles suggesting evaporative cooling.

Composition: centered on dark charcoal background (#070D11). Abstract dual-relay motif (two small glowing contact nodes) — no text, no letters.

Constraints: clean geometric lines, no clutter, crisp edges, suitable as GitHub repo avatar 512×512, soft studio lighting, slight depth of field, photorealistic PBR materials, high contrast.
```

## Negative prompt

```
text, watermark, logo typography, cartoon, clipart, low poly, blurry, oversaturated, human figures, mains wiring, realistic electrical hazard, brand names, Tuya, Sonoff
```

## Color palette (match firmware docs)

| Token | Hex | Use |
|-------|-----|-----|
| Deep base | `#070D11` | Background |
| Industrial teal | `#0B3D4A` | Body shadow |
| Primary | `#147A8A` | SSR / structure |
| Accent | `#3ECFB2` | RFID waves, Fast state |

## Export checklist

- [x] `assets/logo.svg` — flat vector for badges and favicons
- [x] `assets/logo-3d.png` — 512×512 social / README hero
- [ ] Optional: `assets/logo-wordmark.svg` — horizontal lockup with project name
- [ ] Update `README.md` / `README.fa.md` `<img>` tags if filenames change

## Usage in repo

Reference from markdown:

```html
<img src="assets/logo-3d.png" alt="RFID Cooler logo" width="128" height="128" />
```

SVG for crisp scaling:

```html
<img src="assets/logo.svg" alt="RFID Cooler logo" width="128" height="128" />
```
