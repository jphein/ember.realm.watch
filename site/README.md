# Ember — GitHub Pages site

Mirrors the repo layout morpheus confirmed: **`docs/` is the Pages root.**

```
index.src.html      ← EDIT THIS
build.py            ← then run this
make_og_card.py     ← regenerates the social preview image
docs/               ← the deliverable; stage this whole directory
  index.html          138 KB · HTML + inline <style> + the inlined hero SVG
                              (31 KB gzipped, which is what Pages serves)
  assets/*.wav        191 KB · the six chimes, fetched on click
  assets/og-card.png   33 KB · 1200x630 social preview (PLACEHOLDER)
  .nojekyll           serve the tree untouched by Jekyll
```

## ⚠️ Two things that need confirming before this goes live

1. **The canonical URL is assumed.** Every `og:`/`twitter:` tag and all six share links
   hardcode `https://jphein.github.io/ember.realm.watch/`. **Confirm with morpheus-extract**,
   who owns the repo. If it differs, it appears in `index.src.html` (meta block + share hrefs)
   and in `build.py`'s printed outbound-link list — one `sed` fixes all of them, and `build.py`
   prints every outbound link on each run so a wrong one is visible rather than discovered by a
   reader clicking it.
2. **`assets/og-card.png` is a placeholder.** `make_og_card.py` composes it from the shipped
   device art so the Open Graph tags are never pointing at a 404 — a broken `og:image` degrades
   to *no preview at all*, not to a plain link. lyra-artist is composing the real one. When it
   lands, drop it in and update `og:image:alt`, which currently describes the placeholder.

**Never edit `docs/index.html`** — it is generated and will be overwritten.

```bash
$EDITOR index.src.html
python3 build.py
```

`build.py` replaces `{{ASSET:name}}` placeholders and refuses to write a file with any
placeholder left unresolved. It also warns if an off-box URL appears.

## Why one page

The story is one arc — what Ember is, what it looks like, what it sounds like, what went
wrong building it. The engineering half is the most interesting part, and splitting it across
routes would break the narrative exactly where a reader decides whether the project is
serious. One page is also one artifact to review and nothing to keep in sync.

If it grows past ~2× this length the natural seam is lifting "Engineering" out. Not before.

**The engineering notes deliberately do not duplicate `docs/hardware.md`** (nebula-docs owns
that). The split is by *job*: the site's job is to make you care, the reference doc's job is to
help you build. So the site carries a curated six-row table with narrative framing and links
out for the exhaustive version. If you find yourself copying a table between the two, one of
them is in the wrong place.

## Why art is inline and audio is not

The first version base64'd everything into one 345 KB file. The measurement said that was
wrong:

```
audio data URIs : 255 KB  (74% of the page)
image data URIs :  59 KB
everything else :  31 KB
```

A `data:` URI is **part of the document**, so `<audio preload="none">` over one is a lie — the
bytes are downloaded before the tag is parsed. Every visitor paid 255 KB for six chimes whether
or not they clicked one. As real files under `assets/`, `preload="none"` becomes true and each
chime is fetched on click. **345 KB → 95 KB initial page.**

Art stays inline: it is small, it is needed for first paint, and an extra round trip would cost
more than base64's ~33% overhead. It shrinks again when lyra's SVG lands — and SVG must be
inline regardless, because CSS cannot reach inside an `<img>` to animate it.

Still nothing off-box: no CDN, no external fonts, no remote images. Verify after any edit:

```bash
grep -o 'https\?://[^"'"'"')]*' docs/index.html | grep -v w3.org    # must print nothing
```

## Assets

`build.py` **discovers** `art/` and `sounds/` rather than hardcoding a path, because this page
was written before its repo existed. It tries, in order: `../ember-art-web/` (lyra's web art),
beside this directory, `~/Projects/ember.realm.watch`, then `~/Projects/ha/esphome`. So it keeps
building across the extraction with no edit at the moment of the move. If it ever reports the
wrong pair, that list is the thing to fix — it prints which roots it used on every run.

Curation is deliberate; every byte ships to every visitor.

- `chime_timer` is **omitted** — largest file, musically the least distinct (a longer
  `announce`), so it costs the most weight for the least added information.
- `chime_listening` is **included** even though the device never plays it. Hearing the tone
  that was deliberately silenced is the point of that section.
- The hero and the five state cards are **one** sprite (`wyrm_states_shipped.png`) sliced with
  CSS `background-position`, so the largest image is inlined once and used six times.

## Themes

Dark and light, both via `prefers-color-scheme` and CSS custom properties, plus
`:root[data-theme="dark"|"light"]` overrides so a host page or a future toggle can force
either. **Dark is the default** — it is the base `:root`, and the device itself is a dark
screen. The palette is the firmware's own fire ramp (ember → amber → gold → white-hot, ash
off-ramp) so the site and the hardware are the same object.

Embedded device art keeps its dark background in both themes on purpose: it is a screenshot of
a screen, and recolouring it would misrepresent the hardware.

Check light without changing your OS:

```bash
sed 's|<html lang="en-GB">|<html lang="en-GB" data-theme="light">|' docs/index.html > /tmp/l.html
xdg-open /tmp/l.html
```

## Accessibility

- Sprite-backed panels are `role="img"` with descriptive `aria-label`s, because a CSS
  background is invisible to a screen reader.
- Chimes are real `<button>`s with `aria-label` and `aria-pressed`.
- `prefers-reduced-motion` disables the hero glow and all transitions. **Note for lyra:** the
  global rule is `*{animation-duration:.001ms !important}`, which will neutralise your
  keyframes — that is intended, but it means you don't need your own media query.
- `:focus-visible` styled; mono type ≥ .68rem; contrast holds in both themes.

## Lyra's art — integrated

From `../ember-art-web/`, located by `_WEBART` in `build.py` (it is a *flat* directory, not an
`art/` subdir, so it is discovered separately from the device art).

| asset | how it is used | why |
|---|---|---|
| `wyrm-startle.svg` | **inlined** as markup | Its keyframes live inside it and CSS cannot cross an `<img>` boundary. This is the only asset that earns inlining. |
| `wyrm-states.svg` | file, CSS `background` | CSS never reaches *inside* a background image, so inlining would buy nothing and cost 33% base64 plus a worse gzip ratio. |
| `favicon.svg` | file, `<link rel="icon">` | 2.8 KB inline in every page load is worse than one cached fetch, and a favicon is a separate request regardless. |

**The inlining rule, stated once:** inline only what CSS must reach inside. That rule took the
page from 345 KB to 138 KB (31 KB gzipped) and it applies to art exactly as it applied to audio.

### Geometry that the CSS depends on

- Hero viewBox is **1136×528** (2.15:1). It fills the content column; nothing depends on the
  exact ratio, so a re-pose is safe.
- States viewBox is **1136×3020 — five exact panels of 1136×604.** The card CSS slices it with
  `background-size:100% 500%` at positions 0/25/50/75/100%. **If the panel count or the equal
  spacing changes, those stops need recomputing.** Card `aspect-ratio` is `1136/604`.

### Two things worth knowing before editing the hero

- **Do not add an overlay on top of the inline SVG.** It carries its own idle breath, so a second
  animation fights it — and an overlay sits between the pointer and the thing it is meant to wake.
  An earlier version of this page had exactly that and it was removed.
- **Her `<style>` block leaks to the whole document**, as every inline SVG's does. Its selectors
  are `.wyrm`, `.hearth`, `.is-awake` — verified against every class token on this page, no
  collisions. Her IDs (`belly`, `eyeglow`, `hearthglow`, `rim`, `skull`, `tongue`) are unprefixed
  but do not overlap `wyrm-states.svg`, so nothing cross-wires *while only the hero is inlined*.
  **If anyone ever inlines the states sheet as well, prefix both first.**

### Labels

Her art carries the state *name* ("1 · listening"); the HTML `.rung` line carries its position
on the fire *ramp*. Different information on purpose — and the HTML one matters because her
label is set in the artwork, so it shrinks with the two-column cards while the HTML does not.

## The share kit

Lifted from `~/Projects/moyoung-watch/docs/index.html` — JP's established pattern for a project
page — so the two sites behave the same way. Full Open Graph + Twitter card set, then six
buttons: Facebook, Hacker News and Reddit as real submit intents with pre-written titles;
Hackaday as copy-then-open (they take tips by paste, not by intent); Instagram as copy-only
(no web share exists); and `Share…`, hidden by CSS and revealed by JS only where
`navigator.share` actually exists.

Pre-written titles are in `index.src.html`. The hook is deliberately *no cloud at all* rather
than *dragon*, because the dragon is the reason people stay and the privacy claim is the reason
they click:

- **HN**: `Show HN: A $20 voice assistant with no cloud — local STT, a 35B LLM, and a dragon`
- **Reddit**: the same claim, spelled out, since Reddit tolerates length

`build.py` distinguishes **fetched resources** from **outbound links**. Self-containment means
nothing is *fetched* off-box; an `<a href>` to Amazon or Hacker News is a navigation and is the
whole point of those sections. The old check flagged both and would have cried wolf on every
build.

## Notes for whoever edits next

- Nothing here reads or writes `~/Projects/ha/scratch/ember-satellite.yaml`.
- Claims are deliberately hedged where the engineering is unresolved — the pop section says the
  two candidate mechanisms have not been distinguished, because they haven't. **Please don't
  tighten that into a victory claim.** Being accurate about what is still open is part of why
  the page is worth reading.
