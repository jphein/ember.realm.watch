"""
Emit the FRONT FACE of the front bezel: a debossed hex field on the frame band, and the
Ember mark debossed into the top-left of the brow.

ONE MARK, RENDERED THREE WAYS. `site/ember-art-web/favicon.svg` is the source of the
hearth-wyrm-coiled-into-an-ember: the browser tab draws it in the fire ramp, the website
draws it at the top of the page, and this traces the same curves into geometry. Re-draw
the favicon and the plastic follows. Same contract as tools/make_wyrm_spans.py.

WHY DEBOSS, AND WHY IT IS FREE
    The bezel prints FRONT FACE DOWN at 0.16mm layers. A deboss is therefore a recess in
    the FIRST layers, against a smooth sheet: crisp edges, glossy floor, no supports, no
    overhangs, no print-time cost. Every depth here is an exact multiple of the layer
    height so the recess floor lands ON a layer boundary instead of being a sliced-thin
    remainder.

Run:  ../cadenv/bin/python tools/make_bezel_face.py   (writes bezel_face.py beside it)
      -> also writes bezel_face_preview.png, a real-scale shaded view. LOOK AT IT.
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FAVICON = os.path.join(REPO, "site", "ember-art-web", "favicon.svg")

# ============================================================================
# 1. THE BEZEL, DERIVED FROM THE SAME PRIMITIVES ember_case.py DERIVES IT FROM
#    Transcribed primitives only; verify_against_ember_case() asserts every
#    derived number below still matches the real part.
# ============================================================================
BW, BL      = 50.00, 86.00
FIT, WALL   = 0.35, 2.60
BEZEL_T     = 3.00
CORNER_R    = 3.50
VA          = (3.20, 46.80, 16.81, 74.86)
WIN_MARGIN  = 0.40
MIC         = (40.00, 81.50)
MIC_FLARE_D = 4.60                       # outside flare at the front face
HOLES       = [(4.0, 4.0), (46.0, 4.0), (4.0, 82.0), (46.0, 82.0)]
PILOT_D     = 2.50
BOSS_D      = 5.40
GLASS_Z     = 4.30
GLASS_GAP   = 0.40
# stand, for the occlusion finding below
ST_H, SLOT_FLOOR, TILT = 40.0, 24.0, 15.0

OX0, OX1 = -(FIT + WALL), BW + FIT + WALL        # -2.95 .. 52.95
OY0, OY1 = -(FIT + WALL), BL + FIT + WALL        # -2.95 .. 88.95
OUT_R    = CORNER_R + FIT + WALL                 # 6.45
WIN      = (VA[0] - WIN_MARGIN, VA[1] + WIN_MARGIN,
            VA[2] - WIN_MARGIN, VA[3] + WIN_MARGIN)   # 2.80 47.20 16.41 75.26
WIN_R    = 1.50
SEAM_Z   = GLASS_Z + GLASS_GAP
FRONT_Z  = SEAM_Z + BEZEL_T
PILOT_TOP = SEAM_Z + 1.50                        # blind pilot stops here: 1.50mm of roof

# >>> THE STAND EATS THE CHIN. This is the finding that set the layout. <<<
#
# The chin is the biggest strip ON THE PART (19.36mm) and very nearly the smallest area
# on the FACE YOU LOOK AT. The assembled slab drops into the stand's slot and
# ember_case.py's own VA_CLEAR assert computes the engagement: (ST_H - SLOT_FLOOR) /
# cos(TILT) = 16.56mm measured along the slab from its bottom edge. So the stand's front
# wall covers the bezel from y = -2.95 up to y = 13.61, and only 2.80mm of the 19.36mm
# chin is ever visible once Ember is standing where it is designed to stand.
#
# Ranking the front face by what a person actually SEES, in the stand:
#     brow   13.69 x 55.90 = 765 mm2   <- the largest visible area, and it is the TOP
#     rails   5.75 x 58.85 = 338 mm2 each, full length beside the screen
#     chin   55.90 x  2.80 = 157 mm2   <- a sliver
# Putting the show on the chin would have put it inside a box.
STAND_COVER = (ST_H - SLOT_FLOOR) / math.cos(math.radians(TILT))
STAND_TOP_Y = OY0 + STAND_COVER                  # 13.61

LAYER = 0.16                             # bezel prints front-face-down at this height
NOZZLE = 0.40

# ============================================================================
# 2. THE DEBOSSED HEX FIELD  --  fourth scale of the house motif
# ============================================================================
# SCALE. The hexagon already appears at 6.50mm (speaker grille, across flats) and 3.20mm
# (back shell). 6.50 / 3.20 = 2.03, so the object is running a factor-of-two series and
# the next term is 1.60. 1.55 is that term, trimmed to fit the rail (below).
#
# GOING FINER THAN THE BACK IS THE POINT, NOT A COMPROMISE. On the back, hexes ARE holes.
# On the front, nothing passes through and nothing may LOOK like it does. A front field at
# the back's 3.20mm/0.80mm spec would read as a vent array, and a person would reasonably
# conclude the front had speaker holes or a light pipe. At 1.55mm it is unmistakably a
# surface finish: too fine to be an aperture, coarse enough to still be the family's hexagon
# in the hand.
HEX_AFLAT = 1.55        # across the flats
HEX_WEB   = 0.45        # material between hexes
# THE WEB DOES NOT HALVE WITH THE SERIES, because it is the one dimension with a hard
# floor: 0.45mm is a shade over one 0.40mm extrusion width, so layer 1 lays the web as a
# single squished bead on the bed. The web is set by the nozzle, not by the motif.
HEX_DEPTH = 2 * LAYER   # 0.32 -- see DEPTH note below

# >>> THE HEXAGON MUST BE ROTATED 30deg AND THE EXISTING CODE DOES NOT DO IT. <<<
#
# build123d's RegularPolygon(R, 6) puts a vertex at 0deg, which is a FLAT-TOP hexagon:
# 2R wide, sqrt(3)R across the flats vertically. But the lattice maths in this file and in
# ember_case (dx = aflat + web, dy = 1.5R + web*sqrt(3)/2) is POINTY-TOP spacing. Draw a
# flat-top cell on a pointy-top lattice and the cell's long axis lands on the short pitch,
# so the web silently collapses. Measured, exactly, by polygon separation:
#
#     field                         stated web   AS BUILT (rot 0)   with rot=30
#     stand speaker grille            0.90 mm    *** OVERLAP ***      0.900 mm
#     back shell hex field            0.80 mm        0.305 mm         0.800 mm
#     this front field                0.45 mm        0.210 mm         0.450 mm
#
# For the grille that is not a tolerance question, it is a broken part: the 33 cells fuse
# into one solid (build123d returns 1 solid, not 33) and the material BETWEEN them becomes
# 43 ISOLATED PRISMS of 2.5-5.4mm2 each, attached to nothing, spanning the full wall. The
# grille prints as one 37x24mm opening with 43 loose triangles in it. With rotation=30 the
# same field is one connected web.
#
# ember_case.py is not mine to edit -- reported to the team lead with the reproduction.
# THIS file passes the rotation explicitly and verify_field_geometry() below asserts, from
# the real built solids, that the web is what the header claims.
HEX_ROT = 30.0

BAND_OUT  = 0.80        # smooth margin, outer silhouette -> field
BAND_WIN  = 0.80        # smooth margin, screen window -> field
# FIELD_TOP: the field stops dead at the window's top edge and the brow above it stays
# smooth. Reasons, in order of force:
#   1. THE MIC FORBIDS A BAND ACROSS THE BROW. The port's outside flare is a d4.60 circle
#      centred (40.0, 81.5) -- 5.65mm from the brow's outer edge and 6.24mm from the
#      window, i.e. as close to DEAD CENTRE in the brow's 13.69mm as makes no difference.
#      Any band hugging the outer edge lands 0.20mm off it; any band hugging the window
#      lands ON it. Give the port the d8.0 smooth island it needs and the residue above
#      and below is 2.65mm and 1.44mm -- 1.5 and 0.8 rows. Crumbs, not a lattice.
#   2. A d4.60 bore in a field of debossed hexagons stops reading as a microphone and
#      starts reading as one hexagon that went wrong. The cheapest guarantee that the
#      one functional hole on this face is legible is to put no decoration near it.
#   3. The logo needs a ground. 9.20mm of mark in 13.69mm of brow, with nothing else in
#      it, is a logo. The same mark in a field is a denser patch of texture.
FIELD_TOP = WIN[3]      # 75.26
# PILOT KEEPOUTS. The four blind M3 pilots stop 1.50mm below the front face. Debossing over
# one takes that roof to 1.18mm, and a self-tapper driven a half-turn too far then shows as
# a dimple on the face you look at. d4.00 leaves 0.75mm of full-thickness material all round
# each d2.50 pilot -- enough, and small enough not to punch a bald patch in the chin.
KEEPOUT_D = 4.00

# >>> THE RAIL IS TOO NARROW FOR A HONEYCOMB. MEASURED, NOT ASSERTED. <<<
#
# A two-column lattice needs the band to be at least aflat + 1.5*dx wide, because the two
# row parities are offset by dx/2 and BOTH have to fit. The rail band is 5.75 - 0.80 - 0.80
# = 4.15mm. The requirement at the family's scale is 4.55mm. It does not fit, and the first
# render showed exactly what "does not fit" looks like: rows alternating two cells, one
# cell, two cells -- which reads as dropouts, as a misprint, not as a lattice.
#
# Sweeping the whole parameter space (see the table in the commit message) there is no
# comfortable answer near the motif's scale:
#     aflat 1.60, any web            -> never fits, even at a 0.40mm window margin
#     aflat 1.55, web 0.40, win 0.40 -> fits by 0.075mm. Tangent. Fragile.
#     aflat 1.39 or finer            -> fits, but abandons the 6.50/3.20/1.60 octave AND
#                                       the web becomes ~1/3 of the cell, so the field
#                                       reads as grey haze rather than as hexagons.
# Shaving the window margin to 0.40mm to buy 0.4mm of band is also the wrong trade: that
# margin is the flat lip around the screen, the highest-attention edge on the object.
#
# So the rails do NOT get a field. They get a single centred CHAIN of the same hexagon,
# point-to-point. In a 4.15mm band one 1.55mm cell leaves 1.30mm of smooth margin on both
# sides -- comfortable rather than tangent -- and one column has no parity to alternate,
# so there is nothing left to read as a dropout. It is the same hexagon at the same scale;
# only the packing changes, because the space changed.
RAIL_PITCH_WEB = HEX_WEB   # point-to-point gap between chain cells
# RAIL_TO_TOP: run the chains the full height of the face, or stop them level with the top
# of the screen? Both were rendered before choosing (tools/bezel_face_rails.png). Stopping
# at the screen wins: the chain's last cell puts its top vertex exactly on FIELD_TOP, which
# is the window's own top edge, so the two chains and the top of the screen read as one line
# across the face. Run to the top instead and both chains die partway into the r6.45 corner
# fillets at whatever height the arc happens to cut them -- more hexagons, in exchange for
# the only strong line on the face. The brow is then a clean band holding the logo and the
# port, which is the job the brow already had.
RAIL_TO_TOP = False

# ============================================================================
# 3. THE MARK
# ============================================================================
# WHY THE FAVICON AND NOT THE OTHER TWO CANDIDATES. A deboss gives you ONE flat depth, so
# the mark has to survive as a silhouette:
#   * the wordmark "Ember" -- at 9mm tall the strokes are ~0.3mm. Gone.
#   * the hearth-wyrm from esphome/art/dragon.py -- 120x50px, 2.4:1. It is drawn long and
#     low ON PURPOSE, to agree with a 240x76 flame band. A 2.4:1 creature in a square
#     corner is 9.2 x 3.8mm and its features land at 0.33mm. Gone.
#   * the favicon's coiled wyrm -- its silhouette is a RING. A ring is the most robust
#     shape there is at this size: all of its legibility is in its outline, it has no thin
#     terminations, and at 9.20mm its wall is ~1.9mm. It wins on merit, not on convenience.
MARK_H     = 9.20                  # traced silhouette height, mm
MARK_LEFT  = 7.60                  # see MARK PLACEMENT below
MARK_CY    = (WIN[3] + OY1) / 2    # 82.105, the brow's own centreline
MARK_DEPTH = 3 * LAYER             # 0.48
# MARK PLACEMENT -- WHY THE LOGO CANNOT TUCK INTO THE CORNER.
# The top-left screw boss sits at (4.0, 82.0). The brow's centreline is y = 82.105. The
# boss is therefore within 0.11mm of DEAD CENTRE in the brow, and its d2.50 pilot thins
# the roof to 1.50mm. There is no room above or below it in a 13.69mm strip, so the mark
# cannot sit over it and cannot sit outboard of it -- outboard is the r6.45 corner fillet.
# It goes just INBOARD, at x >= 7.60, which clears the whole d5.40 boss by 0.90mm. The
# result is a logo with a generous left margin instead of one jammed into a radius, which
# is the better of the two looks anyway.
#
# DEPTH. 0.48mm (3 layers) for the mark against 0.32mm (2) for the field, so the hierarchy
# is in the geometry and not just in the placement. Deeper is NOT better: a recess reads by
# shadow, and past roughly 1:4 depth-to-width the shadow fills the whole recess and the
# shape goes from drawn to blank. 0.48 in a 1.9mm ring wall is 1:4. 0.32 in a 1.55mm hex
# is 1:4.8.
#
# GLOW. JP prints in WHITE and white PLA is translucent, so a thinner region glows more.
# Worth checking we have not built a lantern: the field removes 0.32 of 3.00mm (11%) and
# the mark 0.48 (16%). Neither is a light pipe -- and the deepest cut is the mark, which is
# the one place a faint halo would be welcome rather than a defect. Nothing here is printed
# yet, so that is a prediction, not a result.
#
# THE MARK IS A TONAL NEGATIVE OF THE FAVICON, unavoidably. On screen the coil is bright
# and its heart is dark. Debossed, the coil is the shadow and its heart is bare plastic at
# full height. White plastic has one colour; the only ink is shadow. The SHAPE is identical
# and that is what carries recognition.
EYE_MODE = "island"       # "island" | "none"
EYE_D    = 0.90           # mm. FLOOR, deliberately larger than the favicon scales to.
# THE EYE IS SPECIFIED, NOT TRACED. Scaled honestly from the SVG it lands at d0.73mm, and
# it is punched AFTER the silhouette is grown, so growing the mark would otherwise eat it.
# Drawing it analytically at a floor of 0.90mm (2.25 extrusion widths) keeps it printable
# as a bare-material island and keeps it a design decision instead of a rounding artefact.
# It is the one detail that makes the mark a creature rather than a doughnut: the eye is
# the only part of the logo left at FULL bezel height, so it catches light while everything
# around it is shadow.

MIN_FEATURE = 0.40        # mm. One extrusion width. Measured by OPENING, never by erosion.
RES = 10.0                # px per mm for the trace. 0.10mm rows -> far below print res.


# ============================================================================
# 4. rasterise the mark
# ============================================================================
def trace_mark() -> tuple[np.ndarray, tuple[float, float]]:
    """Render the favicon's flame paths flat and return (mask, eye_centre_in_mask_mm).

    Drops the background plate, the halo and the gradients -- none of them survive as
    depth. Keeps path 1 (the coil, an annulus: its inner disc is a hole in the fill and
    stays bare plastic) and path 2 (head + the two breath slivers).
    """
    src = open(FAVICON).read()
    paths = re.findall(r'<path d="(.*?)"/>', src)
    m_eye = re.search(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', src)
    assert len(paths) == 2, f"favicon has {len(paths)} paths, expected 2 -- re-read it"
    assert m_eye, "favicon has no eye circle -- re-read it"
    ex, ey = float(m_eye.group(1)), float(m_eye.group(2))

    # Render big, then scale: inkscape's own -w is the only sizing we need, and the
    # viewBox is 64x64 so px/unit is exact.
    px = 1600
    body = "".join(f'<path d="{d}" fill="#000"/>' for d in paths)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
           f'width="{px}" height="{px}"><rect width="64" height="64" fill="#fff"/>'
           f"{body}</svg>")
    with tempfile.TemporaryDirectory() as td:
        s, p = os.path.join(td, "m.svg"), os.path.join(td, "m.png")
        open(s, "w").write(svg)
        # argv array, never a shell string
        subprocess.run(["inkscape", "--export-type=png", f"--export-filename={p}",
                        "-w", str(px), "-h", str(px), s],
                       check=True, capture_output=True)
        img = Image.open(p).convert("L")
        big = np.array(img) < 128                     # True = mark

    # crop to the silhouette, then resample to RES px/mm at MARK_H tall
    ys, xs = np.nonzero(big)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = big[y0:y1, x0:x1]
    ch, cw = crop.shape
    tgt_h = int(round(MARK_H * RES))
    tgt_w = int(round(cw / ch * tgt_h))
    small = np.array(Image.fromarray((crop * 255).astype(np.uint8))
                     .resize((tgt_w, tgt_h), Image.LANCZOS)) > 127

    # the eye, in the cropped mask's own mm frame (origin bottom-left, +y up)
    upp = MARK_H / ch                                  # mm per big-render pixel
    eye_x = (ex * px / 64.0 - x0) * upp
    eye_y = MARK_H - (ey * px / 64.0 - y0) * upp
    return small, (eye_x, eye_y)


def _grow(m: np.ndarray, k: int) -> np.ndarray:
    out = m.copy()
    for _ in range(k):
        g = out.copy()
        g[1:, :] |= out[:-1, :]; g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]; g[:, :-1] |= out[:, 1:]
        out = g
    return out


def _shrink(m: np.ndarray, k: int) -> np.ndarray:
    out = m.copy()
    for _ in range(k):
        t = out.copy()
        t[1:, :] &= out[:-1, :]; t[:-1, :] &= out[1:, :]
        t[:, 1:] &= out[:, :-1]; t[:, :-1] &= out[:, 1:]
        out = t
    return out


def opening_loss(mask: np.ndarray, k: int) -> float:
    """Fraction of area in features THINNER than 2k px, by morphological opening.

    >>> THE ONLY HONEST MINIMUM-FEATURE TEST. <<<
    make_wyrm_spans.py records two wrong ones that both shipped before this: "grow until
    the thinnest row-run clears the floor" never terminates, because dilation always makes
    new 1px boundary rows; and "the k at which erosion empties the mask" measures the
    THICKEST feature, because the last region standing is the fattest. A feature thinner
    than 2k does not survive erode-then-dilate by k. That is the test.
    """
    o = _grow(_shrink(mask, k), k)
    return (mask.sum() - o.sum()) / max(mask.sum(), 1)


def runs(row: np.ndarray):
    out, x, n = [], 0, len(row)
    while x < n:
        if row[x]:
            s = x
            while x < n and row[x]:
                x += 1
            out.append((s, x))
        else:
            x += 1
    return out


# ============================================================================
# 5. the frame band
# ============================================================================
def _in_rrect(x, y, x0, x1, y0, y1, r) -> bool:
    """Point inside an axis-aligned rounded rectangle."""
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 1e-9


def hex_field():
    """The debossed hexagons: a lattice in the chin, a chain up each rail.

    SAME LATTICE MATHS AND SAME HOUSE RULE AS ember_case._hex_panel: R = aflat/sqrt(3),
    dx = aflat + web, dy = 1.5R + web*sqrt(3)/2, and every hex is kept WHOLLY inside its
    region, tested against the CIRCUMRADIUS in both axes.

    A HEX LATTICE HAS NO STRAIGHT EDGE -- any boundary is either serrated (whole cells) or
    clipped (partial cells). The back shell already chose serrated, so the front chooses
    serrated too: one rule for both faces, no new dependency, and the front field is
    exactly as printable as the back's.

    TWO PACKINGS, ONE HEXAGON. The chin is 17.76mm of band and takes the full lattice. The
    rails are 4.15mm and take a single centred chain -- see the RAIL note above for the
    measurement that forced it. Both rails' chains are anchored from the TOP, at
    FIELD_TOP - R, because the top end is the end at eye level beside the screen and it has
    to land in the same place on both sides.
    """
    R = HEX_AFLAT / math.sqrt(3)
    dx = HEX_AFLAT + HEX_WEB
    dy = 1.5 * R + HEX_WEB * math.sqrt(3) / 2

    bx0, bx1 = OX0 + BAND_OUT, OX1 - BAND_OUT
    by0, by1 = OY0 + BAND_OUT, OY1 - BAND_OUT
    br = OUT_R - BAND_OUT
    wx0, wx1 = WIN[0] - BAND_WIN, WIN[1] + BAND_WIN
    wy0, wy1 = WIN[2] - BAND_WIN, WIN[3] + BAND_WIN
    wr = WIN_R + BAND_WIN
    CHIN_TOP = wy0                                  # 15.61, the chin band's top

    def in_band(hx, hy) -> bool:
        for (tx, ty) in ((hx - R, hy), (hx + R, hy), (hx, hy - R), (hx, hy + R)):
            if not _in_rrect(tx, ty, bx0, bx1, by0, by1, br):
                return False
        if not (hx + R < wx0 or hx - R > wx1 or hy + R < wy0 or hy - R > wy1):
            for (tx, ty) in ((hx - R, hy), (hx + R, hy), (hx, hy - R), (hx, hy + R),
                             (hx, hy)):
                if _in_rrect(tx, ty, wx0, wx1, wy0, wy1, wr):
                    return False
        for (px_, py_) in HOLES:
            if math.hypot(hx - px_, hy - py_) < KEEPOUT_D / 2 + R:
                return False
        return True

    # ---- chin: full lattice, everything below the window band -----------
    cx0, cy0 = (OX0 + OX1) / 2, (OY0 + OY1) / 2
    ny = int((OY1 - OY0) / dy) + 2
    nx = int((OX1 - OX0) / dx) + 2
    chin = []
    for j in range(-ny, ny + 1):
        for i in range(-nx, nx + 1):
            hx = cx0 + i * dx + (dx / 2 if j % 2 else 0)
            hy = cy0 + j * dy
            if hy + R > CHIN_TOP:
                continue
            if in_band(hx, hy):
                chin.append((round(hx, 4), round(hy, 4)))

    # ---- rails: one centred chain each, anchored from the top -----------
    # Snap each chain onto a column of the chin lattice so the two packings agree where
    # they meet, instead of jogging by a fraction of a cell at the bottom corners.
    rails, pitch = [], 2 * R + RAIL_PITCH_WEB
    for (r0, r1) in ((bx0, wx0), (wx1, bx1)):
        mid = (r0 + r1) / 2
        k = round((mid - cx0) / (dx / 2))
        rx = cx0 + k * (dx / 2)
        assert r0 + R <= rx <= r1 - R, f"rail chain at x={rx:.3f} escapes band {r0}..{r1}"
        hy = (by1 if RAIL_TO_TOP else FIELD_TOP) - R
        while hy - R > CHIN_TOP:
            if in_band(rx, hy):
                rails.append((round(rx, 4), round(hy, 4)))
            hy -= pitch

    cent = sorted(chin + rails, key=lambda c: (c[1], c[0]))
    buried = sum(1 for (_, hy) in cent if hy < STAND_TOP_Y)
    area = len(cent) * (math.sqrt(3) / 2 * HEX_AFLAT ** 2)
    return cent, R, dict(dx=dx, dy=dy, buried=buried, area=area,
                         chin=len(chin), rails=len(rails), pitch=pitch,
                         chin_top=CHIN_TOP)


# ============================================================================
# 6. preview -- a real-scale shaded view of the face. LOOK AT IT.
# ============================================================================
def preview(mark_rects, mark_org, centres, R, path, ppm=26.0):
    W = int((OX1 - OX0) * ppm)
    H = int((OY1 - OY0) * ppm)
    hmap = np.zeros((H, W), np.float32)      # depth below the front face, mm
    solid = np.zeros((H, W), bool)

    def to_px(x, y):
        return (x - OX0) * ppm, (OY1 - y) * ppm

    yy, xx = np.mgrid[0:H, 0:W]
    mx = xx / ppm + OX0
    my = OY1 - yy / ppm

    def rr_mask(x0, x1, y0, y1, r):
        cxx = np.clip(mx, x0 + r, x1 - r)
        cyy = np.clip(my, y0 + r, y1 - r)
        return ((mx >= x0) & (mx <= x1) & (my >= y0) & (my <= y1)
                & ((mx - cxx) ** 2 + (my - cyy) ** 2 <= r * r))

    inside = rr_mask(OX0, OX1, OY0, OY1, OUT_R)
    window = rr_mask(WIN[0], WIN[1], WIN[2], WIN[3], WIN_R)
    solid = inside & ~window

    # hexes
    from PIL import ImageDraw
    layer = Image.new("F", (W, H), 0.0)
    d = ImageDraw.Draw(layer)
    for (hx, hy) in centres:
        pts = []
        for k in range(6):
            a = math.radians(60 * k + 90)          # pointy-top
            pts.append(to_px(hx + R * math.cos(a), hy + R * math.sin(a)))
        d.polygon(pts, fill=HEX_DEPTH)
    hmap = np.array(layer)

    # mark
    layer2 = Image.new("F", (W, H), 0.0)
    d2 = ImageDraw.Draw(layer2)
    ox, oy = mark_org
    for (rx, ry, rw, rh) in mark_rects:
        x0p, y0p = to_px(ox + rx, oy + ry + rh)
        x1p, y1p = to_px(ox + rx + rw, oy + ry)
        d2.rectangle([x0p, y0p, x1p, y1p], fill=MARK_DEPTH)
    hmap = np.maximum(hmap, np.array(layer2))

    # eye punched back to zero, and the mic bore
    layer3 = Image.new("F", (W, H), 0.0)
    d3 = ImageDraw.Draw(layer3)
    mxp, myp = to_px(MIC[0], MIC[1])
    rr = MIC_FLARE_D / 2 * ppm
    d3.ellipse([mxp - rr, myp - rr, mxp + rr, myp + rr], fill=1.2)
    hmap = np.maximum(hmap, np.array(layer3))
    hmap[~solid] = 0.0

    # shade: grazing light from upper-left off the height map
    gy, gx = np.gradient(hmap.astype(np.float32))
    lx, ly = -0.80, 0.60
    relief = np.clip(0.5 + 9.0 * (gx * lx + gy * ly), 0, 1)
    base = 0.90 - 0.42 * np.clip(hmap / 0.6, 0, 1)      # deeper = more occluded
    img = np.clip(base * (0.55 + 0.75 * relief), 0, 1)
    rgb = np.dstack([img * 252, img * 250, img * 244]).astype(np.uint8)
    rgb[~solid] = (16, 14, 13)
    rgb[window] = (24, 22, 21)
    Image.fromarray(rgb).save(path)


# ============================================================================
# 7. cross-check against the real part
# ============================================================================
def verify_field_geometry(cent, R):
    """Build the real hexes and assert the web is what the header claims.

    Not a parameter check -- an OBSERVATION of the built solids. Two things it catches:
    a fused field (any overlap collapses distinct cells into one solid, which is how the
    stand grille's defect shows), and a web that differs from the stated one.
    """
    try:
        from build123d import Pos, RegularPolygon, extrude
    except Exception as e:                                  # noqa: BLE001
        print(f"  ! field geometry check SKIPPED ({type(e).__name__}: {e})")
        return False
    sub = cent[:60]                                          # enough to hit all neighbours
    out = None
    for (hx, hy) in sub:
        h = Pos(hx, hy, 0) * extrude(RegularPolygon(R, 6, rotation=HEX_ROT), HEX_DEPTH)
        out = h if out is None else out + h
    n = len(out.solids())
    assert n == len(sub), (f"{len(sub)} hexes built as {n} solids -- they OVERLAP and the "
                           f"web is gone. Check HEX_ROT ({HEX_ROT}).")
    # exact 2D separation for the two neighbour offsets
    def pts(cx, cy):
        return [(cx + R * math.cos(math.radians(60 * k + HEX_ROT)),
                 cy + R * math.sin(math.radians(60 * k + HEX_ROT))) for k in range(6)]

    def seg_d(p, q, r, s):
        def pd(pt, a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0.0, min(1.0, ((pt[0]-a[0])*dx + (pt[1]-a[1])*dy) / (dx*dx + dy*dy)))
            return math.hypot(pt[0]-a[0]-t*dx, pt[1]-a[1]-t*dy)
        return min(pd(p, r, s), pd(q, r, s), pd(r, p, q), pd(s, p, q))

    dx = HEX_AFLAT + HEX_WEB
    dy = 1.5 * R + HEX_WEB * math.sqrt(3) / 2
    A = pts(0, 0)
    worst = 1e9
    for (ox, oy) in ((dx, 0), (dx / 2, dy)):
        B = pts(ox, oy)
        worst = min(worst, min(seg_d(A[i], A[(i+1) % 6], B[j], B[(j+1) % 6])
                               for i in range(6) for j in range(6)))
    assert abs(worst - HEX_WEB) < 0.02, (
        f"measured web {worst:.3f}mm != stated {HEX_WEB}mm -- flat/pointy mismatch")
    assert worst >= NOZZLE - 1e-9, f"web {worst:.3f}mm is under one extrusion width"
    print(f"  field geometry OK ({n} discrete solids, measured web {worst:.3f} mm "
          f"at rotation={HEX_ROT:g})")
    return True


def verify_against_ember_case():
    """Assert every transcribed number still matches ember_case.py.

    Soft: on a fresh tree ember_case.py may not import yet (it will import the file THIS
    script writes). Skipping is reported, never silent.
    """
    try:
        sys.path.insert(0, os.path.join(REPO, "enclosure"))
        import ember_case as E
    except Exception as e:                                  # noqa: BLE001
        print(f"  ! ember_case cross-check SKIPPED ({type(e).__name__}: {e})")
        return False
    pairs = [("OX0", OX0, E.OX0), ("OX1", OX1, E.OX1), ("OY0", OY0, E.OY0),
             ("OY1", OY1, E.OY1), ("OUT_R", OUT_R, E.OUT_R),
             ("BEZEL_T", BEZEL_T, E.BEZEL_T), ("FRONT_Z", FRONT_Z, E.FRONT_Z),
             ("MIC", MIC, E.MIC), ("HOLES", HOLES, E.HOLES),
             ("VA", VA, E.VA), ("WIN_MARGIN", WIN_MARGIN, E.WIN_MARGIN)]
    for name, mine, theirs in pairs:
        assert mine == theirs, f"{name}: {mine} != ember_case's {theirs}"
    eng = (E.ST_H - E.SLOT_FLOOR) / math.cos(math.radians(E.TILT))
    assert abs(eng - STAND_COVER) < 1e-6, "stand engagement drifted"
    print(f"  ember_case cross-check OK ({len(pairs)} constants + stand engagement)")
    return True


def main() -> int:
    # ---- the mark -------------------------------------------------------
    raw, (eye_x, eye_y) = trace_mark()
    # GROW A LITTLE, THEN MEASURE THE RIGHT THING. The breath slivers taper to a point and
    # the head's web beside the eye is thin; one pixel of growth (0.10mm) squares them up.
    # A silhouette is not an aperture, so fattening it is nearly free -- it only makes the
    # shadow bolder -- but it is still a TRADE and the opening number decides it, not taste.
    grow = 1
    m = _grow(raw, grow)
    h, w = m.shape
    scale = 1.0 / RES

    # punch the eye -- analytic, after the growth, at its own printable floor
    if EYE_MODE == "island":
        r_px = EYE_D / 2 * RES
        gy, gx = np.mgrid[0:h, 0:w]
        exp, eyp = eye_x * RES, (MARK_H - eye_y) * RES
        m = m & ~(((gx + 0.5 - exp) ** 2 + (gy + 0.5 - eyp) ** 2) <= r_px ** 2)

    k = max(1, int(round(MIN_FEATURE * RES / 2)))     # 2k px == MIN_FEATURE
    loss = opening_loss(m, k)

    rects = []
    for y in range(h):
        for (x0, x1) in runs(m[y]):
            rects.append((round(x0 * scale, 4), round((h - 1 - y) * scale, 4),
                          round((x1 - x0) * scale, 4), round(scale, 4)))
    mark_w, mark_h = w * scale, h * scale
    mark_area = sum(r[2] * r[3] for r in rects)
    mark_org = (MARK_LEFT, MARK_CY - mark_h / 2)

    # ---- clearances, on the real placed geometry ------------------------
    ox, oy = mark_org
    def mark_pts():
        for (rx, ry, rw, rh) in rects:
            yield (ox + rx, oy + ry); yield (ox + rx + rw, oy + ry)
            yield (ox + rx, oy + ry + rh); yield (ox + rx + rw, oy + ry + rh)
    d_pilot = min(math.hypot(px_ - x, py_ - y) - PILOT_D / 2
                  for (px_, py_) in HOLES for (x, y) in mark_pts())
    d_boss = min(math.hypot(px_ - x, py_ - y) - BOSS_D / 2
                 for (px_, py_) in HOLES for (x, y) in mark_pts())
    d_mic = min(math.hypot(MIC[0] - x, MIC[1] - y) for (x, y) in mark_pts()) - MIC_FLARE_D / 2
    d_win = oy - WIN[3]
    # honest outer-edge clearance: distance to the REAL silhouette, fillet included, not to
    # a bounding rectangle. The mark's bbox corner sits inside the r6.45 top-left fillet's
    # radius; only the traced geometry can say whether the MARK does.
    def d_to_outline(x, y):
        cx = min(max(x, OX0 + OUT_R), OX1 - OUT_R)
        cy = min(max(y, OY0 + OUT_R), OY1 - OUT_R)
        if x < OX0 + OUT_R and y > OY1 - OUT_R:      # top-left fillet quadrant
            return OUT_R - math.hypot(x - cx, y - cy)
        return min(x - OX0, OX1 - x, y - OY0, OY1 - y)
    d_out = min(d_to_outline(x, y) for (x, y) in mark_pts())

    # ---- the field ------------------------------------------------------
    cent, R, st = hex_field()
    d_mic_hex = min((math.hypot(hx - MIC[0], hy - MIC[1]) - R - MIC_FLARE_D / 2)
                    for (hx, hy) in cent)

    # ---- write ----------------------------------------------------------
    out = os.path.join(HERE, "bezel_face.py")
    with open(out, "w") as f:
        W = f.write
        W('"""GENERATED by tools/make_bezel_face.py -- do not edit.\n\n')
        W("The front face of the front bezel: a debossed hex field on the frame band, and\n")
        W("the Ember mark debossed into the brow's top left. The mark is traced from\n")
        W("site/ember-art-web/favicon.svg -- the same curves the browser tab and the\n")
        W("website draw. Depths are exact multiples of the 0.16mm layer height, because the\n")
        W("bezel prints FRONT FACE DOWN and every one of these is a recess in layer 1.\n")
        W('"""\n\n')
        W("# ---------------------------------------------------------------- hex field\n")
        n_bur, n_chin, n_rail = st["buried"], st["chin"], st["rails"]
        pct = 100.0 * n_bur / len(cent)
        W(f"# {len(cent)} hexes, {st['area']:.1f} mm2 of face, {HEX_AFLAT}mm across flats\n")
        W(f"# on a {HEX_WEB}mm web. Fourth scale of the motif: 6.50 (grille) / 3.20 (back)\n")
        W(f"# / {HEX_AFLAT} (here). Finer than the back ON PURPOSE -- on the back a hex is a\n")
        W("# hole, here it must not look like one.\n")
        W(f"# PACKING: {n_chin} in the chin as a full lattice, {n_rail} as a single centred\n")
        W("# chain up each rail. The rail is 4.15mm and a two-column lattice needs 4.55mm --\n")
        W("# see make_bezel_face.py for the sweep. One column has no parity to alternate.\n")
        W(f"# >>> {n_bur} of them ({pct:.0f}%) sit below y={STAND_TOP_Y:.2f} and are INSIDE\n")
        W("# THE STAND SLOT in normal use. The chin is the biggest strip on the PART and a\n")
        W("# sliver of the FACE: the stand's front wall covers 16.56mm of the slab. What a\n")
        W("# person actually sees of these hexagons is the two rails. The chin lattice is a\n")
        W("# reward for picking Ember up -- the same bargain the back shell's field already\n")
        W("# takes, since the slot buries that too. <<<\n")
        W(f"FRONT_HEX_AFLAT = {HEX_AFLAT}\n")
        W(f"FRONT_HEX_R     = {R:.6f}        # circumradius, = aflat/sqrt(3)\n")
        W(f"FRONT_HEX_WEB   = {HEX_WEB}          # MEASURED on the built solids, not assumed\n")
        W(f"# >>> RegularPolygon(R, 6) IS FLAT-TOP. This lattice is POINTY-TOP. Build every\n")
        W("# cell as RegularPolygon(FRONT_HEX_R, 6, rotation=FRONT_HEX_ROT) or the web\n")
        W(f"# collapses from {HEX_WEB} to 0.210mm. <<<\n")
        W(f"FRONT_HEX_ROT   = {HEX_ROT}         # degrees. NOT optional.\n")
        W(f"FRONT_HEX_DEPTH = {HEX_DEPTH}         # {HEX_DEPTH/LAYER:.0f} layers at {LAYER}\n")
        W(f"FRONT_HEX_DX, FRONT_HEX_DY = {st['dx']:.6f}, {st['dy']:.6f}\n")
        W(f"FRONT_BAND_OUT, FRONT_BAND_WIN = {BAND_OUT}, {BAND_WIN}\n")
        W(f"FRONT_FIELD_TOP = {FIELD_TOP}      # field stops here; the brow above is smooth\n")
        W(f"FRONT_PILOT_KEEPOUT_D = {KEEPOUT_D}\n")
        W(f"STAND_TOP_Y = {STAND_TOP_Y:.4f}     # stand's front wall crosses the bezel here\n")
        W("# pointy-top hex centres, bezel coordinates. Every one is WHOLLY inside the\n")
        W("# band -- same rule as ember_case._hex_panel, so no clipping is needed.\n")
        W("FRONT_HEX = [\n")
        for c in cent:
            W(f"    {c},\n")
        W("]\n\n")
        W("# ---------------------------------------------------------------- Ember mark\n")
        W(f"# {len(rects)} rects, {mark_area:.2f} mm2, {mark_w:.2f} x {mark_h:.2f} mm, "
          f"grown {grow}px ({grow/RES:.2f}mm).\n")
        W(f"# Opening at k={k} loses {100*loss:.2f}% -> every feature >= "
          f"{2*k/RES:.2f} mm, printable.\n")
        W(f"# clearances: pilot {d_pilot:.2f} | boss {d_boss:.2f} | mic flare {d_mic:.2f} "
          f"| window {d_win:.2f} | outline {d_out:.2f} mm\n")
        W(f"MARK_DEPTH  = {MARK_DEPTH}          # {MARK_DEPTH/LAYER:.0f} layers at {LAYER}\n")
        W(f"MARK_W, MARK_H = {mark_w:.4f}, {mark_h:.4f}\n")
        W(f"MARK_AREA   = {mark_area:.4f}\n")
        W(f"MARK_ORIGIN = ({mark_org[0]:.4f}, {mark_org[1]:.4f})   "
          f"# bezel coords of the mark's bottom-left\n")
        W(f"EYE_D       = {EYE_D}          # bare-material island, full bezel height\n")
        W("# (x, y, w, h) rectangles in mm, origin at MARK_ORIGIN, +y up.\n")
        W("MARK = [\n")
        for r in rects:
            W(f"    {r},\n")
        W("]\n")

    png = os.path.join(HERE, "bezel_face_preview.png")
    preview(rects, mark_org, cent, R, png)

    # ---- report + asserts ----------------------------------------------
    rail_xs = sorted({hx for (hx, hy) in cent if hy > st["chin_top"]})
    print(f"  field : {len(cent)} hexes, {HEX_AFLAT}mm aflat / {HEX_WEB}mm web, "
          f"{st['area']:.1f} mm2")
    print(f"          dx {st['dx']:.3f}  dy {st['dy']:.3f}  depth {HEX_DEPTH}")
    print(f"          chin lattice {st['chin']}  |  rail chains {st['rails']} "
          f"at x={rail_xs}, pitch {st['pitch']:.3f}")
    print(f"          {st['buried']} ({100*st['buried']/len(cent):.0f}%) buried in the "
          f"stand below y={STAND_TOP_Y:.2f}")
    print(f"          nearest hex to the mic flare: {d_mic_hex:.2f} mm")
    print(f"  mark  : {len(rects)} rects, {mark_w:.2f} x {mark_h:.2f} mm, "
          f"{mark_area:.2f} mm2, depth {MARK_DEPTH}")
    print(f"          opening k={k} loses {100*loss:.2f}% -> features >= "
          f"{2*k/RES:.2f} mm")
    print(f"          clearances  pilot {d_pilot:.2f}  boss {d_boss:.2f}  "
          f"mic {d_mic:.2f}  window {d_win:.2f}  outline {d_out:.2f}")
    verify_field_geometry(cent, R)
    verify_against_ember_case()
    print(f"  -> {os.path.relpath(out, REPO)}")
    print(f"  -> {os.path.relpath(png, REPO)}")

    assert loss < 0.005, (f"{100*loss:.2f}% of the mark is thinner than {2*k/RES:.2f}mm "
                          f"-- grow it more or enlarge the eye")
    assert d_pilot > 1.0, f"mark is {d_pilot:.2f}mm from a screw pilot -- thins the roof"
    assert d_mic > 2.0, f"mark is {d_mic:.2f}mm from the mic flare"
    assert d_win > 1.5, f"mark is {d_win:.2f}mm from the screen window"
    assert d_out > 1.5, f"mark is {d_out:.2f}mm from the outer silhouette"
    assert d_mic_hex > 1.0, f"a hex is {d_mic_hex:.2f}mm from the mic flare"
    # float modulo: 0.48 % 0.16 == 0.1599999... Compare the layer COUNT instead.
    for nm, dv in (("MARK_DEPTH", MARK_DEPTH), ("HEX_DEPTH", HEX_DEPTH)):
        n = dv / LAYER
        assert abs(n - round(n)) < 1e-6, f"{nm}={dv} is {n:.3f} layers, not a whole number"
    assert MARK_DEPTH < BEZEL_T / 2 and HEX_DEPTH < BEZEL_T / 2, "deboss too deep"
    assert HEX_WEB >= NOZZLE, f"web {HEX_WEB} is under one extrusion width"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
