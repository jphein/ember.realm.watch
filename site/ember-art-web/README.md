# Ember — web art (the hearth-wyrm)

Lyra · 2026-07-29 · for `ember.realm.watch`

Open **`contact-sheet.html`** first — everything is on it, and the hero wakes when
you point at it.

## What these are

The same creature that is on the device right now. `wyrm_svg.py` **imports**
`~/Projects/ha/esphome/art/dragon.py` and traces the supersampled grid its mask
builders produce, so the site and the hardware are not "matching art" — they are
one set of curves rendered two ways. Re-pose the wyrm on the device and these
regenerate to match.

The device version is 1-bit run-length spans shaded per-pixel from a fire ramp,
because the framebuffer is in PSRAM and every pixel costs. None of that applies
here, so the web version gets real gradients, a rim light and sub-pixel curves.

## Files

| file | use | gzip |
|---|---|---|
| `wyrm-startle.svg` | **the hero.** Inline it — CSS cannot reach into an `<img>` | 13 KB |
| `wyrm.svg` / `wyrm-light.svg` | static hero, dark / parchment | 8 KB |
| `favicon.svg` | the coil glyph; `favicon-{16,32,64}.png` are fallbacks | 3 KB |
| `wyrm-states.svg` / `.png` | the five states, labelled, for a project page | 18 KB |
| `wyrm-winged.svg` | the rejected variant, kept so the call is checkable | 7 KB |
| `contact-sheet.html` | everything on one self-contained page | 47 KB |

Self-contained: the only URL anywhere is the SVG namespace declaration, which is
never fetched. Zero `<script>` tags. No fonts downloaded — labels use the
system UI stack.

## Using the hero

```html
<!-- inline the file's contents here, not <img src> -->
<svg …>…</svg>
```

It wakes on `:hover`, `:focus-visible` and `:active` — mouse, keyboard and touch.
`tabindex="0"` is already on the `<svg>`, so it is keyboard-reachable and shows a
focus ring. A page can also drive it by toggling `.is-awake` on any ancestor.
`prefers-reduced-motion` drops the transition and the idle breath but keeps the
pose change, so the affordance survives.

Hooks, if you want to restyle rather than replace: `.wyrm`, `.headneck`, `.body`,
`.neck`, `.head`, `.jaw-shut`, `.jaw-open`, `.maw`, `.eye`, `.eye-glow`,
`.hearth` (drop this one class to lose the fire and keep the creature).

## Palette

```
ground #0A0604 · ash #3A322C · bed #4A1002 · ember #8E2206
amber  #E05A08 · gold #FFA81E · white-hot #FFE8B4 · alarm #FF3C18
parchment #F2E8DA · ink #2A1C12                     (daylight)
```

## Regenerating

```bash
python3 wyrm_svg.py      # hero + the fidelity check
python3 build_assets.py  # favicon, states, startle, winged, contact sheet
```

`wyrm_svg.py` ends with a measurement, and it is the guard that matters:

```
silhouette fidelity — vector vs the device's own geometry, at 8x:
  body       IoU 0.9714   device  1168.5 px^2  vector  1194.0 px^2   ok
  head-shut  IoU 0.9471   device   209.3 px^2  vector   208.5 px^2   ok
  head-open  IoU 0.9463   device   228.6 px^2  vector   228.7 px^2   ok
```

Ground truth is the **supersampled grid**, not the 120×50 sprite. That took a
measurement to settle: the body scores 0.86 against the sprite and 0.98 against
the geometry the sprite is a quantisation of — the difference is the sprite's own
pixelation, not the vector's error. Comparing against the sprite would have had
me "fixing" the vector to reproduce aliasing.

The head matters most here because it is **not** traced. It is rebuilt from the
same primitives (a tapered skull tube, brow, two horns, cheek frill, jaw tube),
whose numbers are copied from `dragon.py`. That is a drift risk, so the check
above is what catches it: re-sculpt the device head without updating these and
the build fails.

## Two decisions worth knowing

**The favicon is the coiled pose — the one rejected for the device.** That
rejection was never about the coil being wrong, only about it fighting a 240×76
band. In a 1:1 box the coil is exactly right, and it degrades the way a favicon
must: an ember at 16px, a curled creature at 32, a dragon with its head over its
tail at 64. It fails into something meaningful instead of into mud.

**No wings.** See `wyrm-winged.svg`. Reasons in `../lyra-artist.md`.
