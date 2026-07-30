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
import re
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
_CANDIDATE_ROOTS = [
    REPO / "esphome",                            # where the extraction put them
    HERE / "ember-art-web",                      # lyra's web art, when it lands
    REPO,                                        # assets at the repo root
    Path.home() / "Projects/ha/esphome",         # pre-extraction fallback; see above
]


def _find(name: str) -> Path:
    for root in _CANDIDATE_ROOTS:
        if (root / name).is_dir():
            return root / name
    sys.exit(f"no '{name}/' found. Looked in:\n  "
             + "\n  ".join(str(r) for r in _CANDIDATE_ROOTS))


ART = _find("art")
SOUNDS = _find("sounds")

# Inlined as data URIs — needed for first paint.
INLINE = {
    "wyrm_states_shipped":  (ART / "wyrm_states_shipped.png",  "image/png"),
    "wyrm_startle_shipped": (ART / "wyrm_startle_shipped.png", "image/png"),
    "dragon_sheet":         (ART / "dragon_sheet.png",         "image/png"),
}

# Copied to assets/ and referenced relatively, so preload="none" means what it says.
# Curated, not "everything in the directory": chime_timer is omitted (largest file,
# musically the least distinct — a longer `announce`). chime_listening IS included
# even though the device never plays it; hearing the tone that was deliberately
# silenced is the point of that section.
COPY = {
    "chime_touch":     SOUNDS / "chime_touch.wav",
    "chime_thinking":  SOUNDS / "chime_thinking.wav",
    "chime_announce":  SOUNDS / "chime_announce.wav",
    "chime_done":      SOUNDS / "chime_done.wav",
    "chime_listening": SOUNDS / "chime_listening.wav",
    "chime_error":     SOUNDS / "chime_error.wav",
}


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    if not SRC.exists():
        sys.exit(f"missing {SRC}")
    absent = [str(p) for p, _ in INLINE.values() if not p.exists()]
    absent += [str(p) for p in COPY.values() if not p.exists()]
    if absent:
        sys.exit("missing asset(s):\n  " + "\n  ".join(absent))

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    html = SRC.read_text()

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

    leftover = sorted(set(re.findall(r"\{\{ASSET:([^}]+)\}\}", html)))
    if leftover:
        sys.exit(f"unresolved placeholder(s): {leftover}")

    OUT.write_text(html)
    (DOCS / ".nojekyll").write_text("")

    print(f"wrote {OUT}  ({len(html) / 1024:.0f} KB)")
    print(f"  art from    : {ART}")
    print(f"  sounds from : {SOUNDS}")
    print(f"  inlined     : {inlined / 1024:.0f} KB of art (data URIs)")
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
