#!/usr/bin/env python3
"""Slice an STL at a Z plane and draw it AS THE EYE SEES THAT FACE.

Built to answer one question that reasoning alone should not be trusted on: are the
back-face labels mirrored the right way round?

The back of this shell is viewed from -Z. For a viewer there with +Y up, their right-hand
direction is forward x up = (0,0,1) x (0,1,0) = (-1,0,0), so model +X runs to their LEFT.
ember_case.py mirrors every label on that basis. This script applies the SAME mapping
independently -- SVG x = -model x -- so if the mirror is right the text reads normally here,
and if the sign is wrong it comes out backwards. A render that did not flip X would show
mirrored text for CORRECT geometry, which is worse than no check.

Slicing mid-groove rather than rendering a shaded image is deliberate: at z just inside a
0.48mm deboss the section is solid everywhere EXCEPT the letters, so the glyphs appear as
closed outlines with nothing to interpret.

  python3 slice_svg.py <stl> <z> <out.svg>
"""
from __future__ import annotations

import struct
import sys


def read_stl(path):
    with open(path, "rb") as f:
        head = f.read(84)
        if head[:5] == b"solid" and b"facet" in head:
            f.seek(0)
            vals, tris = [], []
            for line in f:
                if line.strip().startswith(b"vertex"):
                    vals.append(tuple(float(x) for x in line.split()[1:4]))
                    if len(vals) == 3:
                        tris.append(tuple(vals))
                        vals = []
            return tris
        n = struct.unpack("<I", head[80:84])[0]
        tris = []
        for _ in range(n):
            d = struct.unpack("<12fH", f.read(50))
            tris.append(((d[3], d[4], d[5]), (d[6], d[7], d[8]), (d[9], d[10], d[11])))
        return tris


def slice_z(tris, z):
    """Marching triangles: the segment where each triangle crosses the plane."""
    segs = []
    for tri in tris:
        below = [v for v in tri if v[2] < z]
        above = [v for v in tri if v[2] >= z]
        if not below or not above:
            continue
        lone, pair = (below[0], above) if len(below) == 1 else (above[0], below)
        pts = []
        for other in pair:
            t = (z - lone[2]) / (other[2] - lone[2])
            pts.append((lone[0] + t * (other[0] - lone[0]),
                        lone[1] + t * (other[1] - lone[1])))
        segs.append(tuple(pts))
    return segs


def main(argv):
    stl, z, out = argv[1], float(argv[2]), argv[3]
    segs = slice_z(read_stl(stl), z)
    if not segs:
        print(f"no geometry at z={z} -- wrong plane?", file=sys.stderr)
        return 1
    # THE MIRROR, applied independently of the model: SVG x = -model x, SVG y flipped
    # because SVG's +y points down while the board's +y points up.
    xs = [-p[0] for s in segs for p in s]
    ys = [p[1] for s in segs for p in s]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad, k = 4.0, 9.0
    w, h = (x1 - x0 + 2 * pad) * k, (y1 - y0 + 2 * pad) * k

    def xf(p):
        return ((-p[0] - x0 + pad) * k, (y1 - p[1] + pad) * k)

    body = "".join('<path d="M{:.2f} {:.2f}L{:.2f} {:.2f}"/>'.format(*xf(a), *xf(b))
                   for a, b in segs)
    with open(out, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
                f'viewBox="0 0 {w:.1f} {h:.1f}"><rect width="100%" height="100%" '
                f'fill="#14110f"/><g stroke="#e8b25a" stroke-width="1.6" fill="none" '
                f'stroke-linecap="round">{body}</g></svg>')
    print(f"{len(segs)} segments at z={z} -> {out}   (viewed from -Z, +X drawn leftward)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
