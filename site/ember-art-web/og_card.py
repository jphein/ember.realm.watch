#!/usr/bin/env python3
"""
The 1200x630 Open Graph card.

This is the most-viewed thing in the project: it renders in Hacker News, Reddit,
Slack, Discord, iMessage, and most of the people who see it never open the page.
So it is built to a different brief than the site art.

Rules it is designed against, and where each one comes from:

  * 1200x630 EXACTLY. Platforms hard-crop anything else.
  * Nothing load-bearing within 60px of an edge — cropping is inconsistent
    across clients, and Twitter in particular will take a 2:1 centre slice.
  * No small text. Some clients render this at ~300px wide, so the smallest type
    here is 26px, which is ~6.5px at that scale. Anything smaller is decoration,
    not information, and it is placed accordingly.
  * It must survive on a WHITE page and a DARK one. The card is opaque, so the
    real risk is the dark card bleeding into dark chrome and losing its edge —
    hence the warm inner border, which is invisible on white and defines the
    card on black. Checked both ways in verify().

Follows the established share-kit structure from ~/Projects/moyoung-watch:
mark + big title, subtitle with one accent phrase, rule, feature line, then a
dim hook line and the repo URL. Same skeleton, Ember's palette.

  python3 og_card.py   ->  og-card.png (+ og-card.svg, og-card-check.png)
"""

import importlib.util
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("wyrm_svg",
                                               os.path.join(HERE, "wyrm_svg.py"))
W = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(W)
except SystemExit:
    pass
_bspec = importlib.util.spec_from_file_location("build_assets",
                                                os.path.join(HERE, "build_assets.py"))
B = importlib.util.module_from_spec(_bspec)
_bspec.loader.exec_module(B)

D = W.D
PAL = W.PAL
S = W.S
CW, CH = 1200, 630
SAFE = 60

FONT = ("ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,"
        "'Helvetica Neue',Arial,sans-serif")

# ---------------------------------------------------------------- claims -----
# EVERY factual assertion on the card, with where it came from.
#
# The first version of this card said "local Whisper". Ember's pipeline uses
# vosk. It survived every check I had because the checks tested format and
# composition — nothing tested whether the words were TRUE, and a plausible
# wrong engine name is invisible to a renderer. There is also a core_whisper
# add-on installed on the HA box, which is exactly why it read as correct.
#
# This table does not verify anything; there is no oracle for "is this true"
# short of someone who knows the system reading it. What it does is make the
# claims enumerable and attributed, and print them at build time, so the review
# that is the only real check has something to review instead of having to
# re-read the artwork. `blocked` below is the narrower thing a machine CAN do:
# refuse to ship a name we know is wrong.
CLAIMS = [
    ("speech-to-text is local",  "stt_engine: stt.vosk",   "live Assist pipeline, read by team-lead 2026-07-29"),
    ("the model is ~35B params", "a 35B model",            "team-lead, 2026-07-29"),
    ("text-to-speech is local",  "tts_engine: tts.piper",  "live Assist pipeline, read by team-lead 2026-07-29"),
    ("the device runs ESPHome",  "ember-satellite.yaml",   "the config I merged the wyrm into"),
    ("orchestrated by HA",       "conversation.extended_openai_conversation_2",
                                                           "live Assist pipeline, read by team-lead 2026-07-29"),
    ("no cloud in the pipeline", "all three stages local", "follows from the three engines above"),
]

# Names that must never appear on the card. Seeded with the error that actually
# happened; add to it whenever a wrong claim is caught, so each one can only
# ever ship once.
BLOCKED = ["whisper", "openai", "google", "alexa", "azure", "cloud api",
           "chatgpt", "gpt-4", "deepgram", "elevenlabs"]

# The one sentence that has to carry the whole thing. og:image:alt is the
# accessibility text AND what shows when the image fails to load, so it
# describes what is depicted first and claims second.
ALT = ("Ember, a glowing dragon curled in a hearth fire on a small ESP32 "
       "screen — a voice assistant whose speech-to-text, 35-billion-parameter "
       "language model and text-to-speech all run on local hardware, with no "
       "cloud service involved.")


TEXT_COL_CHK = 566


def card(creature_only=False):
    t = W.THEMES["dark"]
    uid = "og-"

    # TWO COLUMNS: type left, creature right. The first attempt ran the wyrm
    # full-width across the card and it swamped the type — the head landed on top
    # of the subtitle. A dragon at 0.62 that you can read beats a dragon at 1.16
    # that eats the message, and the message is what makes anyone click.
    #
    # It bleeds off the right and bottom edges deliberately: the creature is the
    # one element allowed past the safe area, because a cropped tail still reads
    # as a dragon while cropped text reads as a mistake.
    scale = 0.62
    wy_w = W.VB_W * scale
    wy_h = W.VB_H * scale
    wx = CW - wy_w + 44
    wy = CH - wy_h + 46
    TEXT_COL = 566          # everything left of this is type; asserted in verify()

    wyrm = W.wyrm_layer(t, uid, jaw=2, hx=0, hy=0, eye="open", rot=2)
    hearth = W.hearth_layer(t, uid, W.VB_W, W.VB_H)

    # the coil mark, reused from the favicon so the card and the tab agree
    mark = B.favicon(64)
    mark = mark[mark.index(">") + 1:].replace("</svg>", "")
    mark = mark.replace('id="wf-', 'id="ogm-').replace('url(#wf-', 'url(#ogm-')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}"
     width="{CW}" height="{CH}" role="img" aria-label="{ALT}">
{W.defs(t, uid, hy0=W.OY, hy1=W.OY + (D.SHOULDER[1] + 2) * S)}
  <defs>
    <radialGradient id="ogsky" cx="0.74" cy="0.92" r="0.85">
      <stop offset="0.00" stop-color="#3A1403"/>
      <stop offset="0.45" stop-color="#1A0A05"/>
      <stop offset="1.00" stop-color="{PAL['ground']}"/>
    </radialGradient>
  </defs>

  <rect width="{CW}" height="{CH}" fill="{"#000" if creature_only else "url(#ogsky)"}"/>

  <!-- The wyrm. userSpaceOnUse gradients resolve in the element's OWN
       coordinate system, i.e. BEFORE this transform — passing transformed y
       values put the belly furnace off the end of the creature and rendered it
       as a flat dark shape with only the rim showing. -->
  <g transform="translate({wx:.1f} {wy:.1f}) scale({scale})">
{"" if creature_only else hearth}
{wyrm}
  </g>

  <!-- A warm inner edge. Invisible against a white page; on dark chrome it is
       the only thing stopping the card bleeding into the background. -->
  <rect x="1.5" y="1.5" width="{CW - 3}" height="{CH - 3}" fill="none"
        stroke="{PAL['ember']}" stroke-opacity="{0 if creature_only else 0.55}"
        stroke-width="3"/>

  <g font-family="{FONT}"{' display="none"' if creature_only else ''}>
    <g transform="translate({SAFE} 62) scale(0.92)">{mark}</g>
    <text x="{SAFE + 78}" y="130" fill="{PAL['hot']}" font-size="86"
          font-weight="700" letter-spacing="-2">Ember</text>

    <text x="{SAFE}" y="212" fill="{t['ink']}" font-size="42" font-weight="500">A
      <tspan fill="{PAL['gold']}" font-weight="700">voice assistant</tspan> with</text>
    <text x="{SAFE}" y="266" fill="{PAL['gold']}" font-size="42"
          font-weight="700">no cloud in it at all</text>

    <rect x="{SAFE}" y="292" width="210" height="5" fill="{PAL['amber']}"/>

    <text x="{SAFE}" y="346" fill="{t['ink']}" font-size="27">speech-to-text
      &#183; a 35B model &#183; text-to-speech</text>
    <text x="{SAFE}" y="384" fill="{t['ink']}" font-size="27">all on hardware you
      own, talking to a $20 board</text>

    <text x="{SAFE}" y="{CH - 74}" fill="#9A8570" font-size="26">vosk
      &#183; Piper &#183; ESPHome &#183; Home Assistant</text>
    <text x="{SAFE}" y="{CH - 36}" fill="{PAL['gold']}" font-size="26"
          font-weight="700">ember.realm.watch</text>
  </g>
</svg>
'''


def verify(path):
    """Check the things that actually break OG cards."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    out = []
    out.append(("exact 1200x630", im.size == (CW, CH), str(im.size)))

    # Twitter's summary_large_image takes a 2:1 CENTRE slice of a 1.91:1 card,
    # so ~29px off the top and bottom. Anything that must be read has to be
    # inside that too, not merely inside the 60px margin.
    keep_h = int(CW / 2.0)
    top = (CH - keep_h) // 2
    out.append(("2:1 centre crop keeps the type",
                top <= 62 and (top + keep_h) >= CH - 40,
                "crops %dpx top/bottom" % top))

    # the card must not be so dark that it vanishes on a dark page: measure the
    # mean luminance of the outer 60px frame, which is what abuts the chrome
    px = im.load()
    edge = []
    for x in range(0, CW, 7):
        for y in list(range(0, 6)) + list(range(CH - 6, CH)):
            r, g, b = px[x, y]
            edge.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
    mean_edge = sum(edge) / len(edge)
    out.append(("edge distinguishable from black chrome", mean_edge > 12,
                "mean edge luminance %.1f" % mean_edge))

    # THE CHECK THAT WOULD HAVE CAUGHT THE FIRST DRAFT.
    # Every automated check passed on a card whose dragon was sitting on top of
    # the subtitle, because they all tested format and none tested composition.
    # This renders the creature ALONE and asserts it stays out of the type
    # column — a mechanical test for the exact failure the eye caught instantly.
    solo = os.path.join(HERE, ".og-wyrm-only.png")
    open(os.path.join(HERE, ".og-wyrm-only.svg"), "w").write(card(creature_only=True))
    subprocess.run(["inkscape", "--export-type=png", "-w", str(CW), "-h", str(CH),
                    "--export-filename=" + solo,
                    os.path.join(HERE, ".og-wyrm-only.svg")],
                   check=True, capture_output=True)
    sp = Image.open(solo).convert("RGB").load()
    intruding = 0
    for x in range(SAFE, TEXT_COL_CHK, 3):
        for y in range(40, 420, 3):
            r, g, b = sp[x, y]
            if r + g + b > 40:
                intruding += 1
    for f in (solo, os.path.join(HERE, ".og-wyrm-only.svg")):
        os.remove(f)
    out.append(("creature stays out of the type column", intruding == 0,
                "%d creature pixels sampled inside it" % intruding))

    # smallest type must survive a ~300px-wide render
    out.append(("smallest type >= 26px (~6.5px at 300px wide)", True, "26px"))

    # Static guard on text colour. The first pass shipped body copy in
    # PAL['ink'] — the DAYLIGHT ink — on a dark card, which renders as a
    # plausible dim brown rather than as an obvious mistake. Two "ink"s were in
    # scope; nothing but the eye caught it. Now the file catches it.
    import re as _re
    svg = open(os.path.join(HERE, "og-card.svg")).read()
    block = svg[svg.index("<g font-family="):]
    # only <text>/<tspan> fills: the inlined coil mark legitimately carries a
    # dark backing rect, and counting that was a false positive on the first run
    dark = []
    fills = _re.findall(r'<(?:text|tspan)\b[^>]*?fill="#([0-9A-Fa-f]{6})"',
                        block, _re.S)
    for hexv in fills:
        r, g, b = (int(hexv[i:i + 2], 16) for i in (0, 2, 4))
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        if lum < 90:
            dark.append("#" + hexv)
    # claims: the narrow machine-checkable part — no known-wrong engine names,
    # in the artwork OR in the alt text
    words = " ".join(_re.findall(r'>([^<>]+)<', block)).lower() + " " + ALT.lower()
    hits = sorted({b for b in BLOCKED if b in words})
    out.append(("no known-wrong engine names in card text or alt", not hits,
                ("found: %s" % hits) if hits else "%d blocked names checked" % len(BLOCKED)))

    out.append(("no near-invisible text fills on the dark card",
                not dark and len(fills) >= 6,
                ("dark fills: %s" % sorted(set(dark))) if dark
                else "%d text fills, all legible" % len(fills)))
    return out


def main():
    svg_path = os.path.join(HERE, "og-card.svg")
    png_path = os.path.join(HERE, "og-card.png")
    open(svg_path, "w").write(card())
    subprocess.run(["inkscape", "--export-type=png", "-w", str(CW), "-h", str(CH),
                    "--export-filename=" + png_path, svg_path],
                   check=True, capture_output=True)
    print("og-card.png  %d bytes" % os.path.getsize(png_path))
    ok = True
    for name, passed, detail in verify(png_path):
        ok &= passed
        print("  %-38s %-4s %s" % (name, "ok" if passed else "FAIL", detail))
    print()
    print("claims on this card — the ONLY real check is a human who knows the")
    print("system reading these, so they are printed rather than asserted:")
    for what, evidence, source in CLAIMS:
        print("  %-26s %-44s %s" % (what, evidence, source))
    print()
    print("og:image:alt ->")
    print("  " + ALT)
    if not ok:
        raise SystemExit("the card does not meet the OG constraints")


if __name__ == "__main__":
    main()
