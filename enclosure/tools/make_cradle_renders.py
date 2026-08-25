"""Renders for the captive-plug cradle (#49). Look at the output — five of five defects
on this project were invisible in correct-looking source and obvious in a picture.

    ./cadenv/bin/python tools/make_cradle_renders.py

Writes STRAIGHT into site/renders (make_renders.py's rule: emitting into a staging
directory a human must copy from is how a stale copy starts):

    plug-cradle.png          the insert alone, outside and pocket side
    plug-cradle-cutaway.png  stand + insert + plug phantom + docked slab, cut at the
                             stand's centreline — the whole mechanism in one section
"""
import os, sys

import numpy as np

_TOOLS = os.path.dirname(os.path.abspath(__file__))
_ENC = os.path.normpath(os.path.join(_TOOLS, ".."))
for _p in (_TOOLS, _ENC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from build123d import *          # noqa: E402
from PIL import Image            # noqa: E402
import render_util as R          # noqa: E402
import ember_case as E           # noqa: E402
import ember_plug_cradle as C    # noqa: E402

OUT = os.path.join(_ENC, "..", "site", "renders")

# part colours, 0..1 — ember palette on coal, one hue step apart so the section reads
COL_STAND = (0.62, 0.34, 0.12)   # the stand: ember orange, as everywhere else
COL_INSERT = (0.95, 0.72, 0.25)  # the new part: brighter, it is the subject
COL_PLUG = (0.55, 0.60, 0.68)    # plug phantom: cold steel — it is not a printed part
COL_SLAB = (0.30, 0.24, 0.20)    # docked slab envelope: barely-there context


def _tinted(shape, col):
    T = R.tris(shape)
    return T, np.tile(np.array(col, float), (len(T), 1))


def main():
    insert = C.plug_cradle() + C._grip_ribs() + C._outer_ribs()

    # ---- solo: outside (ribs, chamfers) and the pocket side ----
    a = R.render(R.tris(insert), os.path.join(OUT, "_solo_a.png"),
                 tilt=24, yaw=32, ppm=30.0)
    b = R.render(R.tris(Rot(0, 0, 180) * insert), os.path.join(OUT, "_solo_b.png"),
                 tilt=-30, yaw=28, ppm=30.0)
    ia, ib = Image.open(os.path.join(OUT, "_solo_a.png")), \
             Image.open(os.path.join(OUT, "_solo_b.png"))
    h = max(ia.height, ib.height)
    combo = Image.new("RGB", (ia.width + ib.width + 12, h), (18, 16, 15))
    combo.paste(ia, (0, (h - ia.height)//2))
    combo.paste(ib, (ia.width + 12, (h - ib.height)//2))
    combo.save(os.path.join(OUT, "plug-cradle.png"))
    os.remove(os.path.join(OUT, "_solo_a.png"))
    os.remove(os.path.join(OUT, "_solo_b.png"))
    print("  plug-cradle.png",
          round(os.path.getsize(os.path.join(OUT, "plug-cradle.png"))/1024, 1), "KB")

    # ---- cutaway: everything the mechanism touches, cut at the stand centreline ----
    # keep x < ST_W/2 and view the open face; the cut runs straight through the pocket,
    # the seat, the shell and the well, which is the drawing this feature needs
    print("building the stand for the section (takes a minute)...")
    stand = E.desk_stand()
    slab = E.dock_pose(Pos(E.OX0, E.OY0, E.BACK_Z) *
                       Box(E.OX1 - E.OX0, E.OY1 - E.OY0, E.FRONT_Z - E.BACK_Z,
                           align=(Align.MIN, Align.MIN, Align.MIN)))
    # per-part cut planes differ by a hair so nothing z-fights on the section face:
    # the camera looks straight down the +x axis, so the offsets are invisible as
    # geometry and decisive as depth
    def keep(x_at):
        return Pos(x_at, 0, 0) * Box(200, 400, 400,
                                     align=(Align.MAX, Align.CENTER, Align.CENTER))
    parts = [
        (stand & keep(E.ST_W/2), COL_STAND),
        (C.place_in_stand(insert, C.YSHIFT) & keep(E.ST_W/2 + 0.10), COL_INSERT),
        (C.place_in_stand(C.plug_phantom_rigid(), 0.0) & keep(E.ST_W/2 + 0.25), COL_PLUG),
        (C.place_in_stand(C.plug_phantom_flex(), 0.0) & keep(E.ST_W/2 + 0.25), COL_PLUG),
        (slab & keep(E.ST_W/2 - 0.10), COL_SLAB),
    ]
    Ts, Cs = [], []
    for shp, col in parts:
        T, cc = _tinted(shp, col)
        Ts.append(T); Cs.append(cc)
    T = np.concatenate(Ts); cols = np.concatenate(Cs)
    # R.render's camera looks down +z of whatever frame it is handed, so hand it a
    # frame whose z IS the section normal: (x,y,z) -> (y,z,x). The stand then sits
    # upright, viewed square-on from its +x side, section toward the camera.
    T = T[..., [1, 2, 0]]
    R.render(T, os.path.join(OUT, "plug-cradle-cutaway.png"),
             tilt=8, yaw=-12, ppm=14.0, cols=cols, light=(-0.40, 0.55, 0.73))
    print("  plug-cradle-cutaway.png",
          round(os.path.getsize(os.path.join(OUT, "plug-cradle-cutaway.png"))/1024, 1), "KB")


if __name__ == "__main__":
    main()
