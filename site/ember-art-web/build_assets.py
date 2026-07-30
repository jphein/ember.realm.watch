#!/usr/bin/env python3
"""
Everything except the hero: favicon, the five-state strip, the startle
animation, and the winged comparison.

  python3 build_assets.py     (run wyrm_svg.py first, or just run this — it
                               imports the generator and drives it)

Every output is self-contained: no CDN, no remote images, no fonts fetched, no
JavaScript anywhere. The animation is CSS keyframes on inline SVG, which is the
only way a page can animate it — an <img src="...svg"> is a closed box that
outside CSS cannot reach into.
"""

import importlib.util
import math
import re
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
D = W.D
PAL = W.PAL
S = W.S


def _min(svg):
    """Strip inter-tag whitespace. Safe here: no <text>, so no significant
    whitespace to lose."""
    svg = re.sub(r"\n\s*", " ", svg)
    svg = re.sub(r">\s+<", "><", svg)
    return re.sub(r"\s{2,}", " ", svg).strip() + "\n"


# ------------------------------------------------------------------ favicon ---
def favicon(size=64):
    """The wyrm coiled into an ember.

    A favicon is 16px. The couchant hero is hopeless there — the dorsal ridge
    that carries "dragon" at 50px is sub-pixel at 16, and the long body becomes a
    smear. So the glyph is the pose I REJECTED for the device: coiled.

    That rejection was never about the coil being wrong, it was about the coil
    fighting a 240x76 band. In a 1:1 box the coil is exactly right, and it
    degrades the way a favicon should: at 16px you read a glowing ember, at 32px
    a curled creature, at 64px a dragon with its head on its tail. It fails into
    something meaningful rather than into mud.
    """
    cx = cy = 32.0
    # Archimedean spiral, wound inward, tube tapering to the tail
    ctrl = []
    # Tuned against BOTH ends of the range, not just one. A thin elegant spiral
    # vanishes at 16px; a fat one reads at 16px but is a solid annulus at 256.
    # 1.35 turns with the tube tapering 6.6 -> 2.0 keeps enough mass for the
    # small size while leaving a visible gap where the coil passes itself.
    turns, n = 1.35, 26
    for i in range(n):
        u = i / (n - 1.0)
        ang = -2.30 + turns * 2 * math.pi * u
        rad = 24.0 - 13.5 * u
        rr = 6.6 - 4.6 * u
        ctrl.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad, rr))
    coil = W._emit(W._tube_outline(ctrl, 20), 1.0, 1.0, 0.0, 0.0, prec=0)

    # the head, at the outer end of the spiral, facing into the coil
    hx = cx + math.cos(-2.35) * 23.5
    hy = cy + math.sin(-2.35) * 23.5
    ang = -2.35 - math.pi / 2.0

    def place(px, py):
        c, s_ = math.cos(ang), math.sin(ang)
        return (hx + px * c - py * s_, hy + px * s_ + py * c)

    skull = [place(x, y) for x, y in
             [(-10.0, -1.2), (-3.0, -6.4), (5.4, -6.0), (8.6, 0.6),
              (3.4, 6.0), (-5.0, 5.2)]]
    horn1 = [place(x, y) for x, y in [(1.6, -5.6), (2.8, -16.0), (7.2, -5.0)]]
    horn2 = [place(x, y) for x, y in [(6.0, -4.2), (15.0, -10.5), (9.0, 0.6)]]
    head = " ".join(W._emit(p, 1.0, 1.0, 0.0, 0.0, smooth=(i == 0), prec=1)
                    for i, p in enumerate([skull, horn1, horn2]))
    ex, ey = place(-3.4, -0.8)

    # Minified on the way out. luna inlines this as a data: URI in <link
    # rel="icon">, so its bytes land in every page's <head> — she asked for under
    # 2 KB and indentation is a third of it.
    return _min(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"
     width="{size}" height="{size}" role="img"
     aria-label="Ember — a hearth-wyrm coiled into an ember">
  <defs>
    <radialGradient id="wf-core" cx="0.5" cy="0.52" r="0.52">
      <stop offset="0.00" stop-color="{PAL['hot']}"/>
      <stop offset="0.28" stop-color="{PAL['gold']}"/>
      <stop offset="0.62" stop-color="{PAL['amber']}"/>
      <stop offset="1.00" stop-color="{PAL['ember']}"/>
    </radialGradient>
    <radialGradient id="wf-halo" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0.45" stop-color="{PAL['amber']}" stop-opacity="0.55"/>
      <stop offset="1.00" stop-color="{PAL['amber']}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="64" height="64" rx="13" fill="{PAL['ground']}"/>
  <circle cx="32" cy="32" r="27" fill="url(#wf-halo)"/>
  <g fill="url(#wf-core)">
    <path d="{coil}"/>
    <path d="{head}"/>
  </g>
  <circle cx="{ex:.1f}" cy="{ey:.1f}" r="2.1" fill="{PAL['hot']}"/>
</svg>
''')


FONTSTACK = ("ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif")


# ------------------------------------------------------------ states strip ---
def states_strip(labels=True):
    """Five panels, labelled at a size a human reads rather than an engineer
    squints at. Labels are <text>, so they stay crisp at any zoom and cost no
    font download — the generic family is resolved by the viewer."""
    pw, ph = W.VB_W, W.VB_H
    lab_h = 76.0 if labels else 0.0
    rows = []
    for i, (name, sub, theme, rot, jaw, eye, glow) in enumerate(W.STATES):
        t = W.THEMES[theme]
        uid = ("ws%d-" if labels else "wsb%d-") % i
        y = i * (ph + lab_h)
        body = W.wyrm_layer(t, uid, jaw, 0, 0, eye=eye, rot=rot)
        lab = f'''
    <text x="26" y="{ph + 34:.0f}" fill="{PAL['gold']}"
          font-family="{FONTSTACK}"
          font-size="30" font-weight="600">{i} &#183; {name}</text>
    <text x="26" y="{ph + 62:.0f}" fill="{PAL['dim']}"
          font-family="{FONTSTACK}"
          font-size="24">{sub}</text>''' if labels else ""
        rows.append(f'''  <g transform="translate(0 {y:.0f})">
{W.defs(t, uid, hy0=W.OY, hy1=W.OY + (D.SHOULDER[1] + 2) * S)}
    <rect width="{pw:.0f}" height="{ph:.0f}" fill="{t['bg']}"/>
{W.hearth_layer(t, uid, pw, ph)}
{body}{lab}
  </g>''')
    h = len(W.STATES) * (ph + lab_h)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {pw:.0f} {h:.0f}" '
            f'role="img" aria-label="Ember\'s five states">\n'
            f'  <rect width="{pw:.0f}" height="{h:.0f}" fill="{PAL["ground"]}"/>\n'
            + "\n".join(rows) + "\n</svg>\n")


# --------------------------------------------------------------- the startle --
def startle():
    """The hero, but it wakes when you touch it. Same gesture as the hardware.

    Driven from the CONTAINER: put class="ember-wake" on the hero wrapper and it
    fires on that element's :hover / :focus-visible / :focus-within / :active.
    Bigger hit area than the svg alone, and on touch the whole card is the
    target. `.is-awake` on any ancestor does the same thing programmatically.
    The svg carries no tabindex — the container owns focus, so there is one tab
    stop for one thing. No JS anywhere; if nothing fires the page shows a drowsy
    dragon, which is a resting state rather than a broken one.

    No prefers-reduced-motion block here on purpose: the page owns that.

    EVERY RULE IS SCOPED UNDER .ember-art. An inline <svg>'s <style> is not
    scoped to the svg — it is a stylesheet in the host document, so a bare
    `.hearth { opacity: .8 }` would restyle anything on the page that happens to
    use that class name. The class HOOKS stay as documented; only my rules are
    fenced in.
    """
    t = W.THEMES["dark"]
    uid = "wk-"
    px = W.OX + D.SHOULDER[0] * S
    py = W.OY + D.SHOULDER[1] * S
    shut = W.wyrm_layer(t, uid, 0, 0, 0, eye="open", rot=None)
    # the open-mouthed head, stacked on top and revealed on wake
    g_open = W.wyrm_group(2, 0, 0)
    lift = S * 0.34
    open_head = f'''    <g class="headneck jaw-open">
      <path class="head-rim" d="{g_open['head']}" fill="{t['rim']}"
            transform="translate(0 {-lift:.1f})"/>
      <path class="head" d="{g_open['head']}" fill="url(#wk-skull)"/>
      <path class="maw" d="{g_open['maw']}" fill="{PAL['hot']}"/>
    </g>'''
    style = f'''  <style>
    .ember-art .wyrm .headneck {{
      transform-origin: {px:.1f}px {py:.1f}px;
      transform: rotate(-24deg);
      transition: transform 420ms cubic-bezier(.16,1.2,.3,1);
    }}
    /* Both heads live in the DOM and CROSS-FADE. The open-mouthed head is a
       different silhouette, not a transform of the shut one, so morphing is not
       available without animating `d` (patchy support) or SMIL (deprecated).
       Swapping opacity is the classic limited-animation answer and it reads as a
       snap at these durations. The shut head MUST be faded out as the open one
       comes in — leaving it visible showed both jaws at once, a doubled head. */
    .ember-art .wyrm .jaw-open {{ opacity: 0; transition: opacity 120ms linear; }}
    .ember-art .wyrm .jaw-shut {{ opacity: 1; transition: opacity 120ms linear; }}
    .ember-art .wyrm .eye {{ opacity: .45; transition: opacity 200ms linear; }}
    .ember-art .wyrm .eye-glow {{ opacity: 0; transition: opacity 260ms linear; }}
    .ember-art .hearth {{ opacity: .8; transition: opacity 500ms ease-out; }}
    /* the idle breath: the creature is alive before you touch it */
    @keyframes ember-wyrm-breath {{
      0%,100% {{ opacity: .72; }}
      50%     {{ opacity: 1; }}
    }}
    .ember-art .wyrm .body {{ animation: ember-wyrm-breath 6s ease-in-out infinite; }}

    /* WAKE — driven from the CONTAINER, not the svg.
       Put class="ember-wake" on the hero container and it triggers on the whole
       card: bigger hit area, and on touch the entire card is the target. The svg
       carries no tabindex, so the container owning focus does not create a
       second tab stop for one thing.
       `.is-awake` on any ancestor does the same thing programmatically. */
    .ember-wake:hover .ember-art .wyrm .headneck,
    .ember-wake:focus-visible .ember-art .wyrm .headneck,
    .ember-wake:focus-within .ember-art .wyrm .headneck,
    .ember-wake:active .ember-art .wyrm .headneck,
    .is-awake .ember-art .wyrm .headneck {{ transform: rotate(2deg); }}

    .ember-wake:hover .ember-art .wyrm .jaw-shut,
    .ember-wake:focus-visible .ember-art .wyrm .jaw-shut,
    .ember-wake:focus-within .ember-art .wyrm .jaw-shut,
    .ember-wake:active .ember-art .wyrm .jaw-shut,
    .is-awake .ember-art .wyrm .jaw-shut {{ opacity: 0; }}

    .ember-wake:hover .ember-art .wyrm .jaw-open,
    .ember-wake:focus-visible .ember-art .wyrm .jaw-open,
    .ember-wake:focus-within .ember-art .wyrm .jaw-open,
    .ember-wake:active .ember-art .wyrm .jaw-open,
    .ember-wake:hover .ember-art .wyrm .eye,
    .ember-wake:focus-visible .ember-art .wyrm .eye,
    .ember-wake:focus-within .ember-art .wyrm .eye,
    .ember-wake:active .ember-art .wyrm .eye,
    .ember-wake:hover .ember-art .wyrm .eye-glow,
    .ember-wake:focus-visible .ember-art .wyrm .eye-glow,
    .ember-wake:focus-within .ember-art .wyrm .eye-glow,
    .ember-wake:active .ember-art .wyrm .eye-glow,
    .ember-wake:hover .ember-art .hearth,
    .ember-wake:focus-visible .ember-art .hearth,
    .ember-wake:focus-within .ember-art .hearth,
    .ember-wake:active .ember-art .hearth,
    .is-awake .ember-art .wyrm .jaw-open,
    .is-awake .ember-art .wyrm .eye,
    .is-awake .ember-art .wyrm .eye-glow,
    .is-awake .ember-art .hearth {{ opacity: 1; }}

    /* NO prefers-reduced-motion block here on purpose. The page carries a global
       `* {{ animation-duration: .001ms !important }}` rule; a second one here
       would be a second authority on the same question, and if it ever grew an
       !important the two would fight. The page wins. */
  </style>
'''
    parts = [W.defs(t, uid, hy0=W.OY, hy1=W.OY + (D.SHOULDER[1] + 2) * S),
             f'  <rect class="ground" width="{W.VB_W:.0f}" height="{W.VB_H:.0f}" '
             f'fill="{t["bg"]}"/>',
             W.hearth_layer(t, uid, W.VB_W, W.VB_H),
             shut.replace("  </g>", open_head + "\n  </g>")]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W.VB_W:.0f} {W.VB_H:.0f}" role="img" '
            f'aria-label="Ember, a hearth-wyrm. Point at it and it wakes.">\n'
            + style + '  <g class="ember-art">\n'
            + "\n".join(parts) + "\n  </g>\n</svg>\n")


# ------------------------------------------------------------ winged variant --
def winged():
    t = W.THEMES["dark"]
    uid = "ww-"
    g = W.wyrm_group(0, 0, 0)
    wing = W.trace(lambda: D.body_mask(True), S, W.OX, W.OY, name="body+wing")
    lift = S * 0.34
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W.VB_W:.0f} {W.VB_H:.0f}" role="img" '
            f'aria-label="The winged variant, not shipped">\n'
            + W.defs(t, uid, hy0=W.OY, hy1=W.OY + (D.SHOULDER[1] + 2) * S)
            + f'\n  <rect width="{W.VB_W:.0f}" height="{W.VB_H:.0f}" fill="{t["bg"]}"/>\n'
            + W.hearth_layer(t, uid, W.VB_W, W.VB_H)
            + f'''
  <g class="wyrm">
    <g class="headneck">
      <path d="{g['neck']}" fill="{t['rim']}" transform="translate(0 {-lift:.1f})"/>
      <path d="{g['neck']}" fill="url(#skull{uid})"/>
    </g>
    <path d="{wing}" fill="{t['rim2']}" transform="translate(0 {-lift:.1f})"/>
    <path d="{wing}" fill="url(#belly{uid})"/>
    <g class="headneck">
      <path d="{g['head']}" fill="{t['rim']}" transform="translate(0 {-lift:.1f})"/>
      <path d="{g['head']}" fill="url(#skull{uid})"/>
    </g>
  </g>
</svg>
''')


def main():
    out = {
        "favicon.svg": favicon(),
        "wyrm-states.svg": states_strip(True),
        "wyrm-states-bare.svg": states_strip(False),
        "wyrm-startle.svg": startle(),
        "wyrm-winged.svg": winged(),
    }
    for name, body in out.items():
        open(os.path.join(HERE, name), "w").write(body)
        print("%-20s %7d bytes" % (name, len(body)))

    open(os.path.join(HERE, "contact-sheet.html"), "w").write(contact_sheet())
    print("%-20s %7d bytes" % ("contact-sheet.html",
                               os.path.getsize(os.path.join(HERE, "contact-sheet.html"))))

    # raster fallbacks + previews
    for src, dst, w in [("wyrm-states.svg", "wyrm-states.png", 900),
                        ("favicon.svg", "favicon-64.png", 64),
                        ("favicon.svg", "favicon-32.png", 32),
                        ("favicon.svg", "favicon-16.png", 16)]:
        subprocess.run(["inkscape", "--export-type=png", "-w", str(w),
                        "--export-filename=" + os.path.join(HERE, dst),
                        os.path.join(HERE, src)], check=True, capture_output=True)
        print("%-20s <- %s @%dpx" % (dst, src, w))




# ---------------------------------------------------------- contact sheet ----
def contact_sheet():
    """One self-contained page with everything on it. No CDN, no remote images,
    no fonts fetched, no JS — the same rules the site itself has to keep, so if
    this page works the assets will."""
    def rd(n):
        return open(os.path.join(HERE, n)).read()
    fav = rd("favicon.svg")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ember — hearth-wyrm contact sheet</title>
<link rel="icon" href="data:image/svg+xml;utf8,""" + \
        fav.replace('"', "'").replace("#", "%23").replace("\n", "") + """">
<style>
:root{--bg:#0A0604;--ink:#F2DCB8;--gold:#FFA81E;--dim:#6A5240;--card:#140C08}
@media (prefers-color-scheme: light){
  :root{--bg:#F2E8DA;--ink:#2A1C12;--gold:#B8600C;--dim:#8A7662;--card:#EADDCB}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:clamp(28px,5vw,44px);margin:0 0 4px;letter-spacing:-.02em}
h1 small{display:block;font-size:15px;font-weight:400;color:var(--dim);
         letter-spacing:0;margin-top:6px}
h2{font-size:14px;text-transform:uppercase;letter-spacing:.09em;color:var(--gold);
   margin:44px 0 10px;font-weight:650}
p{max-width:66ch;color:var(--ink);opacity:.85}
.card{background:var(--card);border-radius:14px;padding:14px;overflow:hidden}
.card svg{width:100%;height:auto;display:block;border-radius:8px}
.favs{display:flex;align-items:flex-end;gap:22px;flex-wrap:wrap}
.favs figure{margin:0;text-align:center}
.favs figcaption{font-size:12px;color:var(--dim);margin-top:6px}
.favs svg{display:block}
.hint{font-size:13px;color:var(--dim);margin-top:8px}
code{background:rgba(255,168,30,.12);padding:1px 5px;border-radius:4px;
     font:13px ui-monospace,SFMono-Regular,Menlo,monospace}
</style></head><body><main>
<h1>Ember — the hearth-wyrm
  <small>Web art for ember.realm.watch. Traced from the same parametric curves
  that generate the device sprite, so the site and the hardware are the same
  animal. Self-contained: no CDN, no remote images, no JavaScript.</small></h1>

<h2>Hero — try pointing at it</h2>
<div class="card">""" + rd("wyrm-startle.svg") + """</div>
<p class="hint">Wakes on <code>:hover</code>, <code>:focus-visible</code> and
<code>:active</code>, so mouse, keyboard and touch all reach it. Inline the SVG —
CSS cannot reach into an <code>&lt;img&gt;</code>. A page can also drive it by
toggling <code>.is-awake</code> on any ancestor. Honours
<code>prefers-reduced-motion</code>.</p>

<h2>Hero — static</h2>
<div class="card">""" + rd("wyrm.svg") + """</div>

<h2>Favicon — the coil</h2>
<div class="favs">
  <figure>""" + fav.replace('width="64" height="64"', 'width="16" height="16"') + \
        """<figcaption>16</figcaption></figure>
  <figure>""" + fav.replace('width="64" height="64"', 'width="32" height="32"') + \
        """<figcaption>32</figcaption></figure>
  <figure>""" + fav.replace('width="64" height="64"', 'width="64" height="64"') + \
        """<figcaption>64</figcaption></figure>
  <figure>""" + fav.replace('width="64" height="64"', 'width="180" height="180"') + \
        """<figcaption>180 (apple-touch)</figcaption></figure>
</div>
<p class="hint">The couchant hero is hopeless at 16px, so the glyph is the coiled
pose — the one rejected for the device because it fought a 240&times;76 band. In a
1:1 box it is exactly right, and it degrades into a glowing ember rather than into
mud.</p>

<h2>Open Graph card &mdash; 1200&times;630</h2>
<div class="card">""" + (rd("og-card.svg") if os.path.exists(os.path.join(HERE,"og-card.svg")) else "") + """</div>
<p class="hint">The most-viewed asset here: it renders in HN, Reddit, Slack,
Discord and iMessage for people who never open the page. Built by
<code>og_card.py</code>, which also prints the <code>og:image:alt</code> text and
checks the constraints that actually break these &mdash; exact size, the 2:1
centre crop, edge contrast against dark chrome, and that the creature stays out
of the type column.</p>

<h2>The five states</h2>
<div class="card">""" + rd("wyrm-states.svg") + """</div>

<h2>Rejected: wings</h2>
<div class="card">""" + rd("wyrm-winged.svg") + """</div>
<p class="hint">Shipped so the call is checkable rather than asserted. The
membrane becomes a central mass that swallows the dorsal ridge and flattens the
long low line the silhouette depends on.</p>
</main></body></html>
"""


if __name__ == "__main__":
    main()
