# Ember — web art (the hearth-wyrm)

Lyra · 2026-07-29 · for `ember.realm.watch`

Open **`contact-sheet.html`** first — everything is on it, and the hero wakes when
you point at it.

## What these are

The same creature that is on the device right now. `wyrm_svg.py` **imports** the
device generator — `esphome/art/dragon.py`, now in `ember.realm.watch` — and traces the supersampled grid its mask
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
| `favicon.svg` | the coil glyph, **1.7 KB of markup** for `<link rel="icon">` inlining; `favicon-{16,32,64}.png` are fallbacks | 1 KB |
| `wyrm-states.svg` / `.png` | the five states, **labelled**, for a spec section | 18 KB |
| `wyrm-states-bare.svg` | same five states, **no labels** — for CSS-sliced cards where HTML carries the text | 18 KB |
| `wyrm-winged.svg` | the rejected variant, kept so the call is checkable | 7 KB |
| `og-card.png` | **1200×630 Open Graph card** → `docs/assets/og-card.png` | 131 KB |
| `og-card.svg` | its source | — |
| `contact-sheet.html` | everything on one self-contained page | 47 KB |
| `case-motif.svg` | the dorsal ridge as a 1:1 mm grille repeat, for nebula's shell | — |

Self-contained: the only URL anywhere is the SVG namespace declaration, which is
never fetched. Zero `<script>` tags. No fonts downloaded — labels use the
system UI stack.

**Every `id` is namespaced per file** (`wh-`, `wk-`, `ws0-`…`ws4-`, `ww-`, `wf-`,
`og-`). Inlined SVGs share one document ID space, and an unprefixed
`<linearGradient id="belly">` in two files cross-wires — rendering something
plausible rather than something obviously broken. There is a collision audit in
the build.

**The state sheet is five equal panels stacked vertically in one file** — exactly
528 units each, origins at 0/528/1056/1584/2112 — so
`background-size: 100% 500%` with positions at 0/25/50/75/100% slices it exactly.
Use `wyrm-states-bare.svg` for the cards: text baked into artwork shrinks with
the card, HTML text does not, and a screen reader cannot see text inside a CSS
background image.

**The startle's stylesheet is scoped under `.ember-art`.** An inline `<svg>`'s
`<style>` is *not* scoped to that svg — it is a stylesheet in the host document,
so a bare `.hearth { opacity: .8 }` would restyle anything on the page using that
class name. The class *hooks* are unchanged; only the rules are fenced. The
keyframe is `ember-wyrm-breath` for the same reason.

## Using the hero

```html
<!-- inline the file's contents here, not <img src> -->
<svg …>…</svg>
```

Put **`class="ember-wake"` on the hero container** and it wakes on that
container's `:hover` / `:focus-visible` / `:focus-within` / `:active` — bigger hit
area than the svg alone, and on touch the whole card is the target. `.is-awake`
on any ancestor does the same thing programmatically.

The svg deliberately carries **no `tabindex`**: the container owns focus, so
there is one tab stop for one thing rather than two.

It also carries **no `prefers-reduced-motion` block**. The page has a global
`* { animation-duration: .001ms !important }` rule, and a second authority on the
same question would eventually fight it. The page wins.

Hooks, if you want to restyle rather than replace: `.wyrm`, `.headneck`, `.body`,
`.neck`, `.head`, `.jaw-shut`, `.jaw-open`, `.maw`, `.eye`, `.eye-glow`,
`.hearth` (drop this one class to lose the fire and keep the creature).

## Where these go

Per morpheus: generator + spans live in **`esphome/art/`** (that directory name is
load-bearing — the generated block in the yaml references `esphome/art/dragon.py`,
so it must not be renamed). Site and README imagery goes to **`docs/assets/`**.

`wyrm_svg.py` finds the device generator by searching `DEVICE_ART_CANDIDATES` in
priority order and prints which one it used. It moved once already (from
`~/Projects/ha/` to `ember.realm.watch`) and a hardcoded path died six frames
deep in an import; the next move is a one-line addition and a clear message.

## The OG card

`python3 og_card.py` builds it and prints the alt text plus its checks:

```
  exact 1200x630                                ok
  2:1 centre crop keeps the type                ok   crops 15px top/bottom
  edge distinguishable from black chrome        ok   mean edge luminance 32.6
  creature stays out of the type column         ok   0 creature pixels inside it
  smallest type >= 26px (~6.5px at 300px wide)  ok
  no near-invisible text fills on the dark card ok   8 text fills, all legible
```

The last two checks exist because the first draft failed both and every check I
had at the time passed anyway: the dragon was sitting on the subtitle, and the
body copy was in `PAL['ink']` — the *daylight* ink — on a dark card. Format
checks do not catch composition, so now two of them do.

`og:image:alt`:

> Ember, a glowing dragon curled in a hearth fire on a small ESP32 screen — a
> voice assistant whose speech-to-text, 35-billion-parameter language model and
> text-to-speech all run on local hardware, with no cloud service involved.

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
