#!/usr/bin/env python3
"""Export ASSEMBLED (model-frame) STLs for the 3D viewer — parts mated, not bed-flat.

The queue STLs are print-oriented; the models themselves are designed MATED in shared
board coordinates, so an assembly view is simply "export without the print transform."
Three clusters, offset along X so they sit side by side:

  desk case      bezel + back shell, mated as screwed together
  mobile case    bezel + midframe + back cover, the full backpack stack
  desk stand     stand + base, as press-fit

Output: enclosure/print/assembly/*.stl (gitignored, view-only artifacts — these never
go near the print queue; they exist for `make_3d_viewer.py --dir assembly`).

Runtime is real geometry building (~10-20 min). Run it in the background.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENC = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ENC, "print", "assembly")
sys.path.insert(0, ENC)

from build123d import Pos, Rot, export_stl                      # noqa: E402

import ember_case as E                                     # noqa: E402
import ember_mobile_case as M                              # noqa: E402


def dock(part):
    """A model-frame device part in its docked pose, in stand coordinates.
    VERBATIM the transform from _check_geometry's _dock() — the asserted pose,
    not an approximation. Applies to mobile parts too: they share board coords,
    and the docking band (y<18 slab) is profile-identical by design (check 8i)."""
    loc = Pos(-E.BW / 2, (E.FRONT_Z + E.BACK_Z) / 2, -E.OY0) * (Rot(90, 0, 0) * part)
    return Pos(E.ST_W / 2, E.SLOT_CY, E.SLOT_FLOOR) * (Rot(-E.TILT, 0, 0) * loc)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    print("[assembly] building parts (each once) ...", flush=True)
    bezel = E.front_bezel()
    shell = E.back_shell("desk")
    stand = E.desk_stand()
    base = E.stand_base()
    midframe = M.midframe()
    cover = M.back_cover()
    print("[assembly] placing docked scenes ...", flush=True)
    DX = 110.0   # second tableau offset
    # Two docked tableaus (desk + mobile seated in the stand), plus the two bare slabs
    # mated in board coordinates — JP's "see it all constructed": the case as screwed
    # together, without the stand, lying in its own frame.
    SLAB_DESK_X, SLAB_MOB_X = -110.0, 220.0
    scene = [
        ("desk-stand",      stand),
        ("desk-base",       base),
        ("desk-bezel",      dock(bezel)),
        ("desk-shell",      dock(shell)),
        ("mobile-stand",    Pos(DX, 0, 0) * stand),
        ("mobile-base",     Pos(DX, 0, 0) * base),
        ("mobile-bezel",    Pos(DX, 0, 0) * dock(bezel)),
        ("mobile-midframe", Pos(DX, 0, 0) * dock(midframe)),
        ("mobile-cover",    Pos(DX, 0, 0) * dock(cover)),
        ("slab-desk-bezel",      Pos(SLAB_DESK_X, 0, 0) * bezel),
        ("slab-desk-shell",      Pos(SLAB_DESK_X, 0, 0) * shell),
        ("slab-mobile-bezel",    Pos(SLAB_MOB_X, 0, 0) * bezel),
        ("slab-mobile-midframe", Pos(SLAB_MOB_X, 0, 0) * midframe),
        ("slab-mobile-cover",    Pos(SLAB_MOB_X, 0, 0) * cover),
    ]
    for name, solid in scene:
        export_stl(solid, os.path.join(OUT, name + ".stl"))
        print(f"[assembly]   exported {name}.stl", flush=True)
    print(f"[assembly] done -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
