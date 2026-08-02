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

from build123d import Pos, export_stl                      # noqa: E402

import ember_case as E                                     # noqa: E402
import ember_mobile_case as M                              # noqa: E402


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    # X offsets chosen so clusters clear each other with daylight between.
    clusters = [
        ("desk",   0.0,    [("desk-bezel",  lambda: E.front_bezel()),
                            ("desk-shell",  lambda: E.back_shell("desk"))]),
        ("mobile", 90.0,   [("mobile-bezel",    lambda: E.front_bezel()),
                            ("mobile-midframe", lambda: M.midframe()),
                            ("mobile-cover",    lambda: M.back_cover())]),
        ("stand",  190.0,  [("stand",      lambda: E.desk_stand()),
                            ("stand-base", lambda: E.stand_base())]),
    ]
    for cname, dx, parts in clusters:
        for pname, build in parts:
            print(f"[assembly] building {pname} ...", flush=True)
            solid = Pos(dx, 0, 0) * build()
            export_stl(solid, os.path.join(OUT, pname + ".stl"))
            print(f"[assembly]   exported {pname}.stl", flush=True)
    print(f"[assembly] done -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
