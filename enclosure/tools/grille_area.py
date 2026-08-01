"""Grille open-area measurement — the throat, the mouth, and how many openings each is.

>>> THIS EXISTS BECAUSE THE LAST ONE DIDN'T. <<<

The published figures (throat 678.0 mm2 / mouth 886.1 mm2, 27 and 1 openings) were produced
in commit 491019b by a raster that was never committed. Three constants then moved —
GRILLE_INSET 1.5 -> 1.0, HEX_R 3.75 -> 4.50/sqrt(3), GRILLE_FLARE 0.60 -> 0.25 — and the
figures stayed, describing a grille that no longer exists, in six different files. A
measurement you cannot re-run is a measurement that will go stale silently.

So: same method, kept. `--historical` re-runs it at the old constants and checks it still
reproduces the old published numbers, which is what makes "the numbers changed" a statement
about the geometry rather than about the ruler.

THE METHOD. The bores run in Y, so the X-Z plane IS the aperture plane — no projection, no
foreshortening. Raster it at 0.01 mm and count.

  THROAT = un-flared cells   INTERSECT field     the acoustic restriction
  MOUTH  = flared cells      INTERSECT field     the face you can touch

Both terms are exactly what ember_case.py cuts: `_cells = _hex_field(dz)` and
`_flared = _hex_field(dz, flare=GRILLE_FLARE, ...)`, clipped by the same `field` rounded
rect. The lattice below is a transcription of `_hex_field`, and it is the one thing here
that can drift from the model — if that function changes, change this with it.

WHAT THE OPENING COUNT MEANS, since this project has been bitten by it. `len(_cells.solids())`
counts CUTTING TOOLS, not holes: it cannot see cells that the field's rounded corners clipped
away, and it cannot see flared cells that merged into one another. The connected-component
count here is over the RASTERISED APERTURE, so it counts holes in the part. Those are
different questions and the assert in ember_case.py is right to ask its one.

Areas are reported to 0.1 mm2. At 0.01 mm the quantisation on a ~900 mm2 region is far below
that, but the hex edges are non-axis-aligned, so treat the last digit as the ruler's, not the
geometry's.
"""

from __future__ import annotations

import argparse
import math
import sys

import numpy as np
from scipy import ndimage as nd

PX = 0.01           # raster pitch, mm — the pitch the published figures were taken at
MIN_OPENING = 0.01  # mm2; below this a "hole" is a raster graze, not geometry (see measure)


def _rrect_mask(X, Y, w, h, r):
    """Rounded-rectangle mask, centred on the origin. Standard rounded-box SDF."""
    hw, hh = w / 2 - r, h / 2 - r
    qx, qy = np.abs(X) - hw, np.abs(Y) - hh
    outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
    inside = np.minimum(np.maximum(qx, qy), 0.0)
    return (outside + inside - r) <= 0.0


def _hex_mask(X, Y, cx, cy, circumradius):
    """Pointy-top regular hexagon: RegularPolygon(R, 6, rotation=30) in _hex_field.

    Vertices at 30/90/150/... so a vertex points +Z. The three edge normals are therefore
    at 0/60/120 deg, and the half-width across each is the apothem, R*sqrt(3)/2. Testing
    those three |projections| is exact — no polygon fill, no winding rule.
    """
    apothem = circumradius * math.sqrt(3) / 2
    dx, dy = X - cx, Y - cy
    m = np.abs(dx) <= apothem
    for ang in (math.radians(60), math.radians(120)):
        np.logical_and(m, np.abs(dx * math.cos(ang) + dy * math.sin(ang)) <= apothem, out=m)
    return m


def _cell_centres(driver_w, driver_h, inset, hex_r, hex_web):
    """Transcribed from _hex_field() in ember_case.py. Keep in step with it."""
    aflat = math.sqrt(3) * hex_r
    dx = aflat + hex_web
    dy = 1.5 * hex_r + hex_web * math.sqrt(3) / 2
    fw, fh = driver_w - 2 * inset, driver_h - 2 * inset
    for j in range(-int(fh / dy) - 3, int(fh / dy) + 4):
        for i in range(-int(fw / dx) - 3, int(fw / dx) + 4):
            cx = i * dx + (dx / 2 if j % 2 else 0)
            cy = j * dy
            if abs(cx) > fw / 2 + aflat or abs(cy) > fh / 2 + hex_r:
                continue
            yield cx, cy


def measure(driver_w, driver_h, driver_r, inset, hex_r, hex_web, flare, px=PX):
    fw, fh = driver_w - 2 * inset, driver_h - 2 * inset
    fr = max(driver_r - inset, 0.8)

    # Half-pixel-centred grid over the field's bounding box, with a small margin.
    nx = int(round(fw / px)) + 4
    ny = int(round(fh / px)) + 4
    xs = (np.arange(nx) - (nx - 1) / 2) * px
    ys = (np.arange(ny) - (ny - 1) / 2) * px
    X, Y = np.meshgrid(xs, ys)

    field = _rrect_mask(X, Y, fw, fh, fr)
    centres = list(_cell_centres(driver_w, driver_h, inset, hex_r, hex_web))

    out = {
        "field_area": float(field.sum()) * px * px,
        "field_area_exact": fw * fh - (4 - math.pi) * fr * fr,
        "field_wh": (fw, fh, fr),
        "cells_placed": len(centres),
    }

    for name, f in (("throat", 0.0), ("mouth", flare)):
        cells = np.zeros_like(field)
        for cx, cy in centres:
            np.logical_or(cells, _hex_mask(X, Y, cx, cy, hex_r + f), out=cells)
        ap = cells & field
        # 4-connectivity: two apertures that meet only at a pixel corner are two holes.
        _lab, n = nd.label(ap)
        sizes = (nd.sum(ap, _lab, range(1, n + 1)) if n else np.array([])) * px * px

        # DISCARD THE GRAZES, AND SAY SO. Where a hex edge is tangent to the field's
        # rounded corner the two boundaries cross at a shallow angle, and the raster
        # leaves one or two isolated pixels behind. Those are artifacts of the ruler,
        # not holes in the part: at the live geometry there are 8 of them, ONE PIXEL
        # each, 0.0008 mm2 in total. Counting them would report 61 openings where the
        # part has 53. The threshold is 100x the pixel area, so it cannot swallow
        # anything a 0.01mm raster could legitimately resolve, and the discarded count
        # and area are always reported so the filter can never hide a real feature.
        keep = sizes[sizes >= MIN_OPENING]
        drop = sizes[sizes < MIN_OPENING]
        out[name] = {
            "area": float(ap.sum()) * px * px,
            "openings": int(keep.size),
            "smallest": float(keep.min()) if keep.size else 0.0,
            "grazes": int(drop.size),
            "graze_area": float(drop.sum()),
        }
    return out


def _report(tag, m):
    fw, fh, fr = m["field_wh"]
    print(f"  [{tag}]  field {fw:g} x {fh:g}, r{fr:g}   cells placed {m['cells_placed']}")
    print(f"    field itself   {m['field_area']:8.1f} mm2   "
          f"(closed form {m['field_area_exact']:.1f})")
    for k in ("throat", "mouth"):
        d = m[k]
        graze = (f"   (+{d['grazes']} sub-{MIN_OPENING:g}mm2 raster grazes discarded, "
                 f"{d['graze_area']:.4f} mm2)") if d['grazes'] else ""
        print(f"    {k:<13}  {d['area']:8.1f} mm2   {d['openings']:>3} opening(s)   "
              f"smallest {d['smallest']:.2f} mm2{graze}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--historical", action="store_true",
                    help="re-run at the 491019b constants and verify the published figures")
    ap.add_argument("--px", type=float, default=PX)
    a = ap.parse_args(argv)

    if a.historical:
        # The constants live at 491019b, when 678.0 / 886.1 were published.
        m = measure(driver_w=40.0, driver_h=27.0, driver_r=3.0,
                    inset=1.5, hex_r=3.75, hex_web=0.90, flare=0.60, px=a.px)
        print("HISTORICAL (491019b: inset 1.5, HEX_R 3.75, flare 0.60)")
        _report("then", m)
        want = [("throat area", m["throat"]["area"], 678.0, 0.1),
                ("mouth area", m["mouth"]["area"], 886.1, 0.1),
                ("field area", m["field_area"], 886.1, 0.1),
                ("throat openings", m["throat"]["openings"], 27, 0),
                ("mouth openings", m["mouth"]["openings"], 1, 0)]
        bad = [(n, got, exp) for n, got, exp, tol in want if abs(got - exp) > tol]
        if bad:
            for n, got, exp in bad:
                print(f"  MISMATCH {n}: got {got}, published {exp}")
            print("\nThis raster does NOT reproduce the published figures, so it is not the "
                  "same ruler and its live numbers cannot be compared with them.")
            return 1
        print("  reproduces the published figures exactly — same ruler  OK")
        return 0

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
    import ember_case as E  # noqa: E402  — needs the path above

    m = measure(driver_w=E.DRIVER_W, driver_h=E.DRIVER_H, driver_r=E.DRIVER_R,
                inset=E.GRILLE_INSET, hex_r=E.HEX_R, hex_web=E.HEX_WEB,
                flare=E.GRILLE_FLARE, px=a.px)
    print(f"LIVE (inset {E.GRILLE_INSET:g}, HEX_R {E.HEX_R:.4f} AF {math.sqrt(3)*E.HEX_R:.2f}, "
          f"flare {E.GRILLE_FLARE:g}, mouth web {E.GRILLE_MOUTH_WEB:.4f})")
    _report("now", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
