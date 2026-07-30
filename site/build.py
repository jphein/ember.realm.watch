#!/usr/bin/env python3
"""Build docs/ — the GitHub Pages root for ember.realm.watch.

    python3 build.py

Emits:
    docs/index.html      HTML + inline <style> + inline (data-URI) art
    docs/assets/*.wav    the chimes, as real files
    docs/.nojekyll       so Pages serves the tree untouched by Jekyll

WHY ART IS INLINE AND AUDIO IS NOT. The first version base64'd everything, and the
measurement said that was wrong:

    audio data URIs : 255 KB  (74% of the page)
    image data URIs :  59 KB
    everything else :  31 KB

A `data:` URI is part of the document, so `<audio preload="none">` over one is a
LIE — the bytes are downloaded before the tag is parsed. Every visitor paid 255 KB
for six chimes whether or not they clicked one. As real files under assets/,
`preload="none"` becomes true and each chime is fetched on click.

Art stays inline: it is small, it is needed for first paint, and an extra round trip
would cost more than base64's ~33% overhead. It shrinks again when lyra's SVG lands —
and SVG must be inline regardless, because CSS cannot reach inside an <img> to
animate it.

Nothing is fetched off-box: no CDN, no external fonts, no remote images.
"""

import base64
import json
import os
import re
from html import escape as html_escape
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent                # this file lives in site/; the repo root is above
SRC = HERE / "index.src.html"
DOCS = REPO / "docs"              # the Pages root is at the REPO root, not under site/
OUT = DOCS / "index.html"
ASSET_DIR = DOCS / "assets"

# Asset roots are DISCOVERED, not hardcoded, because this page was written before the
# repo it belongs to existed. Ember was extracted out of ~/Projects/ha into its own
# repo, so art/ and sounds/ moved. First candidate that exists wins.
#
# `REPO / "esphome"` is FIRST and must stay first. The extraction put art/ and sounds/
# under esphome/, not at the repo root — so without this entry every candidate here
# misses and discovery falls all the way through to ~/Projects/ha/esphome, silently
# rebuilding the site from the OLD repo. That is the exact stale-copy failure this
# extraction exists to end: it would keep working, and keep being wrong.
_STALE = Path.home() / "Projects/ha/esphome"     # pre-extraction. Wrong, now.
_CANDIDATE_ROOTS = [
    REPO / "esphome",                            # where the extraction put them
    HERE / "ember-art-web",                      # lyra's web art
    REPO,                                        # assets at the repo root
    _STALE,                                      # see the guard in _find()
]


def _find(name: str) -> Path:
    for root in _CANDIDATE_ROOTS:
        if (root / name).is_dir():
            # THE CLASS FIX. Putting REPO/"esphome" first fixes one accident; it does
            # nothing about the next edit to this list. The actual defect is that
            # falling through to a stale root SUCCEEDS — silently rebuilding the site
            # from the old repo, correctly and indefinitely, with nothing in the output
            # to show it. A build that succeeds wrongly is worse than one that stops,
            # for the same reason a mute that never clears is worse than a pop. So this
            # is a hard stop, with an explicit escape hatch for anyone who means it.
            if root == _STALE and os.environ.get("EMBER_ALLOW_STALE_ASSETS") != "1":
                sys.exit(
                    f"\nREFUSING TO BUILD: '{name}/' resolved to the PRE-EXTRACTION path\n"
                    f"    {root}\n\n"
                    f"Ember lives here now, with art/ and sounds/ under esphome/.\n"
                    f"Building from the old repo would produce a perfect-looking page\n"
                    f"from stale assets — the failure the extraction exists to end.\n\n"
                    f"Fix the path, or set EMBER_ALLOW_STALE_ASSETS=1 if you mean it.\n"
                )
            return root / name
    sys.exit(f"no '{name}/' found. Looked in:\n  "
             + "\n  ".join(str(r) for r in _CANDIDATE_ROOTS))


ART = _find("art")
SOUNDS = _find("sounds")
WEBART = HERE / "ember-art-web"          # lyra's web art: a FLAT dir, not an art/ subdir
if not WEBART.is_dir():
    sys.exit(f"missing {WEBART} — lyra's web art is required for the hero")

# ── THE INLINING RULE ─────────────────────────────────────────────────────────
# Inline ONLY what CSS must reach inside. Everything else is a file under assets/,
# because a data URI is part of the document and therefore cannot be lazy, cached
# separately, or skipped. That rule took this page from 345 KB to 138 KB (31 KB
# gzipped), and it applies to art exactly as it applied to the chimes.
INLINE_SVG = {
    # The hero's keyframes live inside it and CSS cannot cross an <img> boundary.
    # This is the only asset that earns inlining.
    "wyrm_startle": WEBART / "wyrm-startle.svg",
    # Enclosure line art — inlined so `currentColor` resolves against the page.
    "case_exploded":     Path(__file__).resolve().parent / "renders" / "case-exploded.svg",
    # The back view earns inlining TWICE over: currentColor for the theme, and a named
    # group id (`case-back-btn-vis`) that the stylesheet paints in the accent colour so
    # the two button pads stand out from ~130 hex apertures. Both need CSS to reach
    # inside the SVG, which is precisely what an <img> forbids.
    "case_back":         Path(__file__).resolve().parent / "renders" / "case-back.svg",
    # The docked-rear view. It exists because a question was asked that NO existing figure
    # could answer — every other one shows the parts separated, or the slab from the front,
    # or the shell alone, so not one put a button and a stand wall in the same frame. Inlined
    # for the same two reasons as case-back: currentColor, and named ids the stylesheet
    # reaches (`case-dock-btn-vis`, `case-dock-scallop-vis`).
    "case_docked_rear":  Path(__file__).resolve().parent / "renders" / "case-docked-rear.svg",
    # The bezel face, as a SECTION 0.20mm below the front plane rather than a shaded render.
    # It exists because the hero could not do this job and it was not the hero's fault: a
    # 0.45mm recess on a 92mm part is sub-pixel depth at page scale, and a shaded view has only
    # the recess side-walls to work with, so the motif reads as triangulation noise. Slicing
    # below the face cuts through every recess and nothing else, so the outlines ARE the motif.
    # Same failure class as the five figures that could not show a buried button: a figure that
    # technically contains the information but cannot deliver it.
    "case_front":        Path(__file__).resolve().parent / "renders" / "case-front.svg",
    "case_print_layout": Path(__file__).resolve().parent / "renders" / "case-print-layout.svg",
}

INLINE = {}          # nothing else earns it

# Enclosure figures. The technical views are SVG stroked with `currentColor`, which
# is the whole reason they are INLINE_SVG below rather than <img>: a raster render is
# locked to the theme it was made in — dark line art vanishes on a dark page and light
# line art vanishes on a light one, and there is no single PNG that satisfies both.
# currentColor inherits whatever the page is using. CSS cannot cross an <img>
# boundary, so an <img> would freeze them.
RENDERS = HERE / "renders"

COPY = {
    # lyra's web art, referenced by URL. wyrm-states.svg is a CSS *background*, and CSS
    # never reaches inside one — so inlining it would buy nothing and cost 33% base64
    # plus a worse gzip ratio. The favicon is a separate request regardless.
    "wyrm_states":          WEBART / "wyrm-states.svg",
    "favicon":              WEBART / "favicon.svg",
    # device art, as <img> figures — below the fold, so fetched rather than inlined
    "wyrm_startle_shipped": ART / "wyrm_startle_shipped.png",
    "dragon_sheet":         ART / "dragon_sheet.png",
    # The one beauty shot. A shaded raster is right here — it is a photograph-like
    # figure, not line art, and nothing about it needs to change with the theme.
    "case_hero":            Path(__file__).resolve().parent / "renders" / "case-hero.png",
    # Chimes. chime_timer omitted (largest, musically least distinct — a longer
    # `announce`). chime_listening INCLUDED though the device never plays it: hearing
    # the tone that was deliberately silenced is the point of that section.
    "chime_touch":     SOUNDS / "chime_touch.wav",
    "chime_thinking":  SOUNDS / "chime_thinking.wav",
    "chime_announce":  SOUNDS / "chime_announce.wav",
    "chime_done":      SOUNDS / "chime_done.wav",
    "chime_listening": SOUNDS / "chime_listening.wav",
    "chime_error":     SOUNDS / "chime_error.wav",
}


def inline_svg(path: Path) -> str:
    """SVG markup safe to drop mid-document.

    Strips the XML prolog and any DOCTYPE — both are illegal inside an HTML body and
    make the parser bail in ways that are hard to attribute afterwards.
    """
    t = path.read_text()
    t = re.sub(r"<\?xml[^>]*\?>\s*", "", t)
    t = re.sub(r"<!DOCTYPE[^>]*>\s*", "", t, flags=re.I)
    return t.strip()


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    if not SRC.exists():
        sys.exit(f"missing {SRC}")
    absent = [str(p) for p, _ in INLINE.values() if not p.exists()]
    absent += [str(p) for p in COPY.values() if not p.exists()]
    absent += [str(p) for p in INLINE_SVG.values() if not p.exists()]
    if absent:
        sys.exit("missing asset(s):\n  " + "\n  ".join(absent))

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    html = SRC.read_text()

    svg_bytes = 0
    for name, path in INLINE_SVG.items():
        token = "{{SVG:" + name + "}}"
        if token in html:
            markup = inline_svg(path)
            html = html.replace(token, markup)
            svg_bytes += len(markup)

    inlined = 0
    for name, (path, mime) in INLINE.items():
        token = "{{ASSET:" + name + "}}"
        if token in html:
            uri = data_uri(path, mime)
            html = html.replace(token, uri)
            inlined += len(uri)

    copied = 0
    for name, path in COPY.items():
        token = "{{ASSET:" + name + "}}"
        if token not in html:
            continue
        shutil.copy2(path, ASSET_DIR / path.name)
        html = html.replace(token, f"assets/{path.name}")
        copied += path.stat().st_size

    leftover = sorted(set(re.findall(r"\{\{(?:ASSET|SVG):([^}]+)\}\}", html)))
    if leftover:
        sys.exit(f"unresolved placeholder(s): {leftover}")

    # The realm-version stamp. build-sigil.sh used to inject this tag directly, which
    # made two scripts writers on one file in opposite directions — this build strips
    # the tag, that script re-adds it, and whichever ran last looked correct. morpheus
    # removed his writer; this reads his output instead. One writer, no ordering.
    #
    # A missing version.json is a SKIPPED TAG, not an error: a fresh clone has no sigil
    # output yet and must still build.
    stamp = DOCS / "version.json"
    if stamp.exists():
        try:
            v = json.loads(stamp.read_text())
            ver = str(v.get("version") or v.get("semver") or "").strip()
            if ver:
                tag = f'<meta name="realm-version" content="{html_escape(ver)}">\n'
                html = html.replace("</head>", tag + "</head>", 1)
                print(f"  version tag : {ver}")
        except (ValueError, OSError) as e:
            print(f"  !! version.json unreadable, tag skipped: {e}")
    else:
        print("  version tag : skipped (no docs/version.json yet)")

    OUT.write_text(html)
    (DOCS / ".nojekyll").write_text("")

    # The print sheet is generated here rather than maintained by hand, because
    # `.nojekyll` means Pages serves docs/*.md as text/markdown — fine for the
    # reference docs (their home is the repo), wrong for the one page that is read
    # while a printer is running. Generating it from enclosure/PRINT-SHEET.md keeps
    # the markdown canonical: same reason the STLs are output and ember_case.py is
    # the artifact. A failure here fails the build rather than silently shipping a
    # stale page.
    import build_print_sheet
    build_print_sheet.main()

    print(f"wrote {OUT}  ({len(html) / 1024:.0f} KB)")
    print(f"  art from    : {ART}")
    print(f"  sounds from : {SOUNDS}")
    print(f"  web art     : {WEBART}")
    print(f"  inline SVG  : {svg_bytes / 1024:.0f} KB (the hero — CSS reaches inside it)")
    if inlined:
        print(f"  data URIs   : {inlined / 1024:.0f} KB")
    print(f"  copied      : {copied / 1024:.0f} KB -> docs/assets/ "
          f"({len(COPY)} files, fetched on click)")

    # SELF-CONTAINMENT CHECK, and the distinction matters: the invariant is that no
    # external RESOURCE is fetched at load time. Outbound <a href> navigations are fine
    # and expected — the buy link and the share buttons are the whole point of those
    # sections. So check the things the browser fetches without being asked:
    # stylesheets, scripts, images, fonts, and CSS url()/@import.
    fetched = []
    fetched += re.findall(r'<(?:script|img|audio|video|source|iframe)\b[^>]*\bsrc\s*=\s*["\']([^"\']+)', html, re.I)
    fetched += re.findall(r'<link\b[^>]*\bhref\s*=\s*["\']([^"\']+)', html, re.I)
    fetched += re.findall(r'url\(\s*["\']?([^"\')]+)', html)
    fetched += re.findall(r'@import\s+["\']([^"\']+)', html)
    offbox = [u for u in fetched if re.match(r'(?:https?:)?//', u.strip())]
    if offbox:
        print("  !! NOT SELF-CONTAINED — these are fetched from off-box:")
        for u in sorted(set(offbox)):
            print(f"       {u[:90]}")
    else:
        print(f"  self-contained: {len(fetched)} fetched refs, all local or data:")

    # Outbound links are listed, not flagged — so a wrong share URL is visible on
    # every build rather than discovered by a reader clicking it.
    links = sorted({m for m in re.findall(r'<a\b[^>]*\bhref\s*=\s*["\'](https?://[^"\']+)', html, re.I)})
    if links:
        print(f"  outbound links ({len(links)}):")
        for u in links:
            print(f"       {u.split('?')[0]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
