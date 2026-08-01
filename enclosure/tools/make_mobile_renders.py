"""Website figures for the MOBILE (battery) Ember.

    ./cadenv/bin/python tools/make_mobile_renders.py        # from enclosure/

Writes straight into site/renders/ -- the directory site/build.py actually reads. There
is no second copy anywhere and no manual step, for the reason make_renders.py records:
regenerate, forget to copy, and the site serves the OLD figure while the repo shows the
new one. You would be looking at a correct file and a wrong page.

EVERY OUTLINE HERE IS SLICED OR PROJECTED OUT OF ember_mobile_case.py, and every
dimension label is measured off the geometry it sits under (see svg_util.dim). Nothing
is transcribed. That is not a style preference on this project: the back-face button
outline was once typed twice -- once as a solid in the model, once as a polygon in the
figure -- and both copies happened to be rectangles, so they were free to disagree
forever with nothing to notice. When the part was asked to become hexagons, the figure
would have kept drawing squares indefinitely, and the figure is the only thing anyone
looks at.

WHAT EACH FIGURE EXISTS TO SHOW, and what it cannot. The desk figure set taught this
discipline the hard way -- five individually-correct figures that were collectively blind
to a completely buried button, because not one of them put a button and a stand wall in
the same frame. So each figure below names the question it answers:

  exploded      what the variant IS: the bezel and the board clamp are the desk case's,
                bit-identical; only the midframe and the cover are new. Cannot show any
                internal feature -- everything interesting is inside the cover.
  cross         the transverse cut: cell in its cradle, the ONE shared divider, and the
                sealed front cavity on the other side of it. Cannot show the vent (it is
                at a different Y) or anything about length.
  vent          the labyrinth in plan, which is the only view in which "no straight path
                across this wall" is a thing you can see rather than a claim. Cannot show
                its height.
  glow          the window's two cells, the wall they are cut into, and -- deliberately
                in frame -- the cable channel that made "put it at the LED" unavailable.
  strip         the protection pocket: seat, locating ribs outside the footprint, flat
                floor under it. Cannot show the solder access, which is a property of
                assembly ORDER rather than of any one section.
  hero          the assembled device, shaded. The one figure whose job is the DEPTH the
                variant costs, read against the bezel it shares with the flat desk case.
  cover         the new part turned over with the cell in its cradle. Every internal
                feature in one frame, and the only figure that shows the cell at all in
                three dimensions. Cannot show how it meets the midframe.

⚠️ ONE KNOWN COSMETIC LIMITATION, recorded so the next reader does not re-investigate it.
`project_to_viewport` does not occlude between the CHILDREN of a compound, so the vendor
board's PCB edges draw through its own LCD stack in the exploded figure. It is the desk
figure's behaviour too (same `board_lite`, same helper) and the board is context there and
here, not the subject -- so this matches rather than diverges. What is NOT acceptable, and
was fixed, is one PART's edges crossing another: see the gap note on EX below.
"""
import os as _os
import sys as _sys

# Anchor on THIS FILE, not on the caller's cwd. The documented command puts tools/ on
# sys.path[0], not enclosure/, so a bare `import ember_mobile_case` fails from a clean
# checkout and succeeds on any machine with a stale enclosure/__pycache__ lying around.
# That is the nastiest shape of unreproducible build: it works where it has already run
# and nowhere else. The script's location is a fact; the caller's cwd is a guess.
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ENC = _os.path.dirname(_HERE)
_sys.path.insert(0, _ENC)
_sys.path.insert(0, _HERE)

import numpy as np
from build123d import *

import ember_case as E
import ember_mobile_case as M
import svg_util as S

OUT = _os.path.abspath(_os.path.join(_ENC, "..", "site", "renders"))
_os.makedirs(OUT, exist_ok=True)


def _out(name):
    return _os.path.join(OUT, name)


# ---------------------------------------------------------------- the parts, once
# Building the midframe is ~24s and the cover ~7s, so they are built ONCE and reused by
# every figure below. A figure that rebuilt its own part would also be free to build a
# DIFFERENT part -- same class of defect as a second copy of the geometry.
print("building parts (once) ...")
mid = M.midframe()
cover = M.back_cover()
bezel = E.front_bezel()          # THE CLAIM THE EXPLODED FIGURE MAKES: this is the desk
                                 # bezel, unmodified. It is imported, not re-derived, so
                                 # the figure cannot depict a bezel the variant does not
                                 # actually reuse.
cell = M.cell_phantom()
driver = M.driver_phantom()
strip = M.prot_phantom()
print(f"  midframe {mid.volume/1000:6.2f} cm3   cover {cover.volume/1000:6.2f} cm3   "
      f"bezel {bezel.volume/1000:6.2f} cm3 (reused)")

_STEP = E._find_step()
if not _os.path.exists(_STEP):
    _sys.exit(f"FATAL — aborting, no figures written.\n"
              f"  missing vendor board model: {_STEP}\n"
              f"  17.7MB, deliberately not committed; a git archive/clone NEVER has it.\n"
              f"  see enclosure/README.md")
_raw = Pos(52.750, -6.000, 0.0) * import_step(_STEP)
# For line art the full 1238-solid assembly projects thousands of edges. A reader needs
# the PCB + LCD + glass silhouette, not every 0402. Pick the structural solids by volume.
board_lite = Compound(children=sorted(_raw.solids(), key=lambda s: -s.volume)[:4])


# ============================================================ 1. EXPLODED (svg)
# Explode along the TRUE assembly axis (board Z), so the figure is a statement about how
# it goes together rather than a pleasing arrangement.
#
# ⚠️ THE CELL IS DELIBERATELY NOT IN THIS FIGURE, and it was here first. Each group is
# hidden-line-removed INDEPENDENTLY -- there is no inter-part occlusion -- so a part whose
# silhouette overlaps another part in the projection draws straight through it. The cell is
# a 65mm cylinder and its two silhouette lines ran the width of the whole drawing, over the
# midframe and the cover, reading as stray diagonals across four correct parts. The gaps
# were also too tight: the desk figure separates its three parts by ~58 units and this had
# five in less than half that.
#
# Widening the gaps fixes the crossing. Removing the cell is the better fix, because this
# figure's job is the ARCHITECTURE -- which parts are the desk case's and which are new --
# and the cell is not one of the parts. The cell has two figures of its own (the transverse
# section puts it in its cradle, the shaded view takes it out), so nothing is lost.
print("exploded:")
# ⚠️ THESE GAPS ARE A CORRECTNESS CONSTRAINT, NOT SPACING TASTE, and that is the whole
# lesson of this block. Because each group is HLR'd independently, two parts whose
# PROJECTIONS overlap draw through each other -- and the midframe's top rim is a 55.90 x
# 95.00 rectangle, so at a 19-unit gap its edges ran clean across the board's plate and read
# as stray diagonals over an otherwise correct figure. Nothing about the geometry was wrong
# and nothing in the build could have caught it: the defect existed only in the drawing.
# The desk figure separates three parts by ~58 units, which is why it never showed this.
#
# If a part is ever added here, check the OUTPUT for crossings rather than assuming the
# gaps still hold -- overlap depends on the camera as much as on the offsets.
EX = [(Pos(0, 0, 80) * bezel, "bezel"),
      (Pos(0, 0, 40) * board_lite, "board"),
      (Pos(0, 0, 0) * mid, "midframe"),
      (Pos(0, 0, -52) * cover, "cover")]
# A three-quarter eye, for the reason the desk exploded figure records: every part in
# this stack is flat in XY, so an eye near the X axis sees them edge-on and the figure
# becomes five vertical slivers with the aspect ratio of a landscape banner and the
# information content of none.
EX_TGT = (25.0, 45.0, 10.0)
EX_EYE = (EX_TGT[0] + 780.0, EX_TGT[1] - 1040.0, EX_TGT[2] + 660.0)
groups = []
for _s, _nm in EX:
    _p, _k = S.project(_s, EX_EYE, up=(0, 0, 1), target=EX_TGT)
    groups.append((_p, _k, _nm))
S.write_svg(_out("mobile-exploded.svg"), groups, "mobile-exp")


# ======================================================= 2. TRANSVERSE (svg)
# A cut across the case at mid-bay. This is the figure that shows the single fact the
# whole packaging argument rests on: the cell lane and the speaker cavity are side by
# side, separated by ONE wall that belongs to both. Two walls do not fit in 51.50mm.
print("transverse section:")
_CY = (M.BAY_Y0 + M.BAY_Y1) / 2                      # mid-bay, clear of the vent field
_gs = []
for _shape, _nm in ((mid, "midframe"), (cover, "cover"),
                    (cell, "cell"), (driver, "driver")):
    try:
        _gs.append((S.face_polys(S.section(_shape, "y", _CY), "y"), _nm))
    except ValueError:
        print(f"    (nothing at y={_CY:.2f} for {_nm} -- skipped)")
# Dimensions MEASURED off the model, never typed. The bore is dimensioned across the
# cell's own axis, the cavity across the rim's inner faces, so if a constant moves the
# label moves with it.
_bore_r = M.CELL_BORE_D / 2
dims = [
    S.dim((M.CELL_AXIS_X - _bore_r, M.CELL_AXIS_Z - _bore_r),
          (M.CELL_AXIS_X + _bore_r, M.CELL_AXIS_Z - _bore_r), off=-4.0, side="v"),
    S.dim((M.RIM_X0, M.CAV_Z0), (M.RIM_X1, M.CAV_Z0), off=-9.0, side="v"),
    S.dim((M.RIM_X1 + 2.0, M.CAV_Z0), (M.RIM_X1 + 2.0, M.BACK_Z), off=6.0, side="h"),
]
S.write_svg(_out("mobile-cross.svg"), _gs, "mobile-cross", dims=dims)


# ============================================================ 3. VENT (svg)
# THE ONLY VIEW IN WHICH "NO STRAIGHT PATH" IS VISIBLE RATHER THAN ASSERTED.
#
# Sliced in plan, mid-height through the labyrinth: each unit reads as an inner slot and
# an outer slot offset in Y by a rib, joined by a band -- so the wall's solid is one
# continuous zigzag ribbon and a straight line across it always meets material. The
# boolean check measures the obstruction; this shows the topology. Neither does the
# other's job: a picture cannot tell you 36%, and a percentage cannot tell you the band
# is open rather than welded shut.
print("vent labyrinth:")
_VZ = (M.VENT_Z0 + M.VENT_Z1) / 2
# CROPPED, so the detail is legible. The cover is 74mm tall and the labyrinth occupies
# 25.6mm of it; an uncropped plan renders the feature at a size nothing can be read from.
_crop = Pos(M.OX0 - 1.0, M.VENT_Y0 - 4.0, -50.0) * Box(
    (M.CELL_X0 + 1.2) - (M.OX0 - 1.0),
    (M.VENT_Y0 + M.VENT_N * M.VENT_PITCH + 4.0) - (M.VENT_Y0 - 4.0),
    100.0, align=(Align.MIN, Align.MIN, Align.MIN))
_vent_polys = S.face_polys(S.section(cover & _crop, "z", _VZ), "z")
_u = M._vent_units()
(_i0, _o0, _b0) = _u[0]
# Offsets are small ON PURPOSE. This section is 2.20mm of wall; a dimension standing 11mm
# off it (which is what these were first drawn at) sets the figure's extent and leaves the
# subject as a thread along one edge.
dims = [
    S.dim((M.OX0, _i0[0]), (M.OX0, _i0[1]), off=-1.4, side="h", tick=0.5),   # slot width
    S.dim((M.OX0, _i0[1]), (M.OX0, _o0[0]), off=-3.2, side="h", tick=0.5),   # the rib
    S.dim((M.OX0, _u[0][0][0]), (M.OX0, _u[1][0][0]),
          off=-5.4, side="h", tick=0.5),                                     # pitch
]
# THE SKIN GETS A LEADER RATHER THAN A DIMENSION, and only after trying it the other way
# twice. It is 0.80mm across on a part drawn at ~35mm wide, so a dimension line spanning it
# is shorter than its own label: placed on solid wall the label meant nothing, and placed on
# the surviving skin (which is the honest spot -- at a Y inside an inner slot the material
# left standing between OX0 and OX0+0.80 IS the outer skin) the glyphs sat on top of the
# outline they were pointing at. A leader keeps the label in clear air and still lands on
# the feature. The number is formatted from VENT_SKIN, so it is read from the model rather
# than typed, but note it is one step weaker than dim(): it cannot notice if the geometry
# and the constant ever disagree.
# The label goes on the BAY side of the wall, not the outside. The outside is where the
# three stacked dimensions live and it was already full -- the leader landed between two of
# them and all three became unreadable together. The bay side of this section is empty.
dims.append(S.leader((M.OX0 + M.VENT_SKIN / 2, (_i0[0] + _i0[1]) / 2),
                     (M.CELL_X0 + 0.6, M.VENT_Y0 - 3.4), f"skin {M.VENT_SKIN:.2f}"))
S.write_svg(_out("mobile-vent.svg"), [(_vent_polys, "vent")], "mobile-vent", dims=dims,
            swap=True)     # +Y across the page: the gas path runs the long edge


# ====================================================== 4. GLOW WINDOW (svg)
# The window's two cells, cut into the side wall -- and, deliberately in the same frame,
# the cable channel a little further up the wall. That channel is why "put the window at
# the LED" was never on offer: the LED's own Y lands inside one on BOTH walls, so the site
# is searched for the nearest solid span rather than typed. A figure showing only the
# window would make the position look like a choice.
print("glow window:")
_wx = (E.BW + E.FIT) if M.GLOW_WALL == "hi" else (-E.FIT)
_XS = _wx + (M.WALL - M.GLOW_MEMBRANE) / 2 if M.GLOW_WALL == "hi" else \
      _wx - (M.WALL - M.GLOW_MEMBRANE) / 2
_gcrop = Pos(-60.0, M.GLOW_CY - 17.0, -60.0) * Box(
    120.0, 44.0, 120.0, align=(Align.MIN, Align.MIN, Align.MIN))
_glow_polys = S.face_polys(S.section(mid & _gcrop, "x", _XS), "x")
dims = [
    # Across the flats, and it MEASURES itself. This is the dimension the #47 regression
    # broke: 4.75 across flats did not fit the cavity band and the export gate refused
    # the part, so the number under this line is the one that had to be pinned.
    S.dim((M.GLOW_CY - M.GLOW_SPAN_Y / 2, M.GLOW_CZ - M.GLOW_AF / 2),
          (M.GLOW_CY - M.GLOW_SPAN_Y / 2, M.GLOW_CZ + M.GLOW_AF / 2), off=-3.0,
          side="h"),
    S.dim((M.GLOW_CY - M.GLOW_SPAN_Y / 2, M.GLOW_CZ - M.GLOW_AF / 2 - 2.0),
          (M.GLOW_CY + M.GLOW_SPAN_Y / 2, M.GLOW_CZ - M.GLOW_AF / 2 - 2.0),
          off=-2.0, side="v"),
]
S.write_svg(_out("mobile-glow-window.svg"), [(_glow_polys, "wall")],
            "mobile-glow", dims=dims)


# ====================================================== 5. STRIP POCKET (svg)
# The 1S protection pocket, in plan through the locating ribs.
#
# ⚠️ THE LENGTH LABEL ON THIS FIGURE IS AN ESTIMATE AND SAYS SO. PROT_L is JP's eyeball
# figure ("20mm about"), carrying +/-2, and PROT_W / PROT_T are class placeholders awaiting
# calipers. A figure that renders an estimate in the same voice as a derived dimension is
# lying about its own confidence -- which is exactly the failure this project keeps
# catching in prose, so it is not going to be introduced in a drawing.
print("strip pocket:")
_PZ = M.CAV_Z0 + M.PROT_RIB_H / 2
_pcrop = Pos(M.RIM_X0 - 3.0, M.PROT_Y1 - M.PROT_W - 8.0, -60.0) * Box(
    (M.RIM_X1 + 3.0) - (M.RIM_X0 - 3.0), 20.0, 120.0,
    align=(Align.MIN, Align.MIN, Align.MIN))
_gs = [(S.face_polys(S.section(cover & _pcrop, "z", _PZ), "z"), "pocket")]
try:
    _gs.append((S.face_polys(S.section(strip & _pcrop, "z", _PZ), "z"), "strip"))
except ValueError:
    pass
dims = [
    S.dim((M.PROT_CX - M.PROT_L / 2, M.PROT_Y1 - M.PROT_W),
          (M.PROT_CX + M.PROT_L / 2, M.PROT_Y1 - M.PROT_W), off=-3.0, side="v",
          text=f"{M.PROT_L:.1f} est ±2"),
    S.dim((M.PROT_CX + M.PROT_L / 2 + 2.0, M.PROT_Y1 - M.PROT_W),
          (M.PROT_CX + M.PROT_L / 2 + 2.0, M.PROT_Y1), off=3.0, side="h"),
]
S.write_svg(_out("mobile-strip-pocket.svg"), _gs, "mobile-strip", dims=dims)


# ============================================================ 6. SHADED (png)
# Two raster views, and raster is right for exactly these two: they are photograph-like
# figures rather than line art, and nothing about them needs to change with the theme.
# The line drawings above are currentColor SVG for the opposite reason.
#
# Shading, lighting and camera are lifted from make_renders.py's hero so the mobile
# beauty shot reads as a SIBLING of the desk one rather than a different project's
# picture -- same coal background, same two-light rig, same 16:9.
print("shaded:")
import render_util as R

# ⚠️ NOT matplotlib, and the first version of this file was. Its 3D painter sorts triangles
# WITHIN a collection and not BETWEEN collections, so an assembly of four interpenetrating
# boxes came out with the cover's faces punched through the midframe in wedges -- artefacts
# that look exactly like modelling errors, on a page whose whole argument is that the
# geometry is checked. It is the same defect make_renders.py records for the desk hero
# (the stand painting over the slab it stood behind), and merging into one collection is
# only a workaround for convex-ish parts at that scale. These parts are not that.
#
# render_util is a TRUE Z-BUFFER, so occlusion is correct by construction rather than by
# luck of sort order. It grew a per-triangle colour argument for this, which is how four
# parts can share one image and still be told apart.
COAL = (10, 6, 4)                                   # #0A0604, the desk hero's background
BEZEL_C, MID_C, COVER_C, CELL_C = ((0.66, 0.63, 0.60), (0.50, 0.48, 0.46),
                                   (0.40, 0.38, 0.36), (0.74, 0.75, 0.78))


def shaded(pieces, path, tilt, yaw, ppm=13.0):
    Ts, Cs = [], []
    for sh, col in pieces:
        T = R.tris(sh, tol=0.05)
        Ts.append(T)
        Cs.append(np.tile(np.array(col, float), (len(T), 1)))
    T = np.concatenate(Ts)
    C = np.concatenate(Cs)
    w, h = R.render(T, path, tilt=tilt, yaw=yaw, ppm=ppm, cols=C, bg=COAL)
    print(f"  {_os.path.basename(path):28s} {_os.path.getsize(path)/1024:6.1f} KB   "
          f"{w}x{h}   {len(T)} tris")


# Assembled, front three-quarter: what it is like to hold. The screen side, because a rear
# view is informative and is not what "what does this look like" means -- and because the
# one thing this figure has to convey is the DEPTH the variant costs, which reads against
# the bezel it shares with the flat desk case.
shaded([(bezel, BEZEL_C), (mid, MID_C), (cover, COVER_C)],
       _out("mobile-hero.png"), tilt=18.0, yaw=28.0, ppm=20.0)

# THE NEW PART, INTERIOR UP, WITH THE CELL IN ITS CRADLE.
#
# This replaced a partly-exploded "cell coming out" view, which did not work and could not
# be made to: the cell lifts along +Z out of a trough in the cover, so from any viewpoint
# that shows the cover's inside the cover is BETWEEN the eye and the cell, and from any
# viewpoint that shows the cell the cover is edge-on. The figure spent its whole frame
# proving that one part hides another.
#
# Turning the cover over answers the same question better. One part, one cell, no occlusion:
# the cradle, the vent slots in the side wall, the protection pocket, the grille from the
# inside, the hooks and the counterbore are all in frame at once, and the caption can say
# the cell lifts out in one movement without the drawing having to mime it.
shaded([(cover, COVER_C), (cell, CELL_C)],
       _out("mobile-cover.png"), tilt=26.0, yaw=-20.0, ppm=20.0)

print(f"\nall figures -> {OUT}")
