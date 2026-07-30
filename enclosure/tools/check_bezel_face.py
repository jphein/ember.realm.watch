"""
Cut the front-face deboss into the REAL bezel and look at it.

Four defects on this project were invisible in correct-looking source and obvious in the
output, so this does not check parameters -- it builds the actual solid, measures it, and
renders it from a raking angle where a 0.32mm recess is something you can SEE.

It is also the integration test for ember_case.py: the deboss block it applies is exactly
the block that belongs in front_bezel(), printed at the end of the run so it can be pasted
rather than retyped.

Run:  ../cadenv/bin/python tools/check_bezel_face.py
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from build123d import *
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "enclosure"))
sys.path.insert(0, HERE)

import bezel_face as F                              # noqa: E402
import ember_case as E                              # noqa: E402


# ---------------------------------------------------------------- the deboss
def deboss(p):
    """Apply the front-face deboss. THIS IS THE INTEGRATION BLOCK."""
    hexes = None
    for (hx, hy) in F.FRONT_HEX:
        h = Pos(hx, hy, E.FRONT_Z - F.FRONT_HEX_DEPTH) * extrude(
            RegularPolygon(F.FRONT_HEX_R, 6, rotation=F.FRONT_HEX_ROT),
            F.FRONT_HEX_DEPTH + 0.01)
        hexes = h if hexes is None else hexes + h
    p -= hexes
    ox, oy = F.MARK_ORIGIN
    mark = None
    for (rx, ry, rw, rh) in F.MARK:
        b = E.bx(ox + rx, ox + rx + rw, oy + ry, oy + ry + rh,
                 E.FRONT_Z - F.MARK_DEPTH, E.FRONT_Z + 0.01)
        mark = b if mark is None else mark + b
    p -= mark
    return p


# ---------------------------------------------------------------- rasteriser
def tris(shape, tol=0.02):
    f = os.path.join(HERE, "_chk.stl")
    export_stl(shape, f, tolerance=tol, angular_tolerance=0.2)
    n = int.from_bytes(open(f, "rb").read(84)[80:84], "little")
    d = np.fromfile(f, dtype=np.uint8, offset=84)
    rec = 50
    n = min(n, len(d) // rec)
    T = np.frombuffer(d[:n * rec].reshape(n, rec)[:, 12:48].tobytes(),
                      dtype="<f4").reshape(n, 3, 3).astype(np.float64)
    os.remove(f)
    return T


def render(T, path, tilt=22.0, yaw=14.0, ppm=26.0, light=(-0.55, 0.45, 0.70)):
    """Z-buffered lambert. Tilted ON PURPOSE: in a straight-on orthographic view a vertical
    recess wall projects to zero width and the whole deboss is invisible."""
    tx, ty = math.radians(tilt), math.radians(yaw)
    Rx = np.array([[1, 0, 0], [0, math.cos(tx), -math.sin(tx)], [0, math.sin(tx), math.cos(tx)]])
    Ry = np.array([[math.cos(ty), 0, math.sin(ty)], [0, 1, 0], [-math.sin(ty), 0, math.cos(ty)]])
    M = Ry @ Rx
    P = T.reshape(-1, 3) @ M.T
    P = P.reshape(-1, 3, 3)
    mn, mx = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    W = int((mx[0] - mn[0]) * ppm) + 8
    H = int((mx[1] - mn[1]) * ppm) + 8
    zbuf = np.full((H, W), -1e9)
    img = np.zeros((H, W), np.float32)
    L = np.array(light, float)
    L /= np.linalg.norm(L)
    sx = (P[:, :, 0] - mn[0]) * ppm + 4
    sy = (mx[1] - P[:, :, 1]) * ppm + 4
    e1 = P[:, 1] - P[:, 0]
    e2 = P[:, 2] - P[:, 0]
    nrm = np.cross(e1, e2)
    ln = np.linalg.norm(nrm, axis=1)
    ok = ln > 1e-12
    nrm[ok] /= ln[ok, None]
    shade = np.clip(nrm @ L, 0, 1) * 0.82 + 0.18
    for i in range(len(P)):
        if not ok[i]:
            continue
        x0 = max(int(np.floor(sx[i].min())), 0); x1 = min(int(np.ceil(sx[i].max())) + 1, W)
        y0 = max(int(np.floor(sy[i].min())), 0); y1 = min(int(np.ceil(sy[i].max())) + 1, H)
        if x1 <= x0 or y1 <= y0:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1]
        ax, ay = sx[i, 0], sy[i, 0]; bx_, by_ = sx[i, 1], sy[i, 1]; cx_, cy_ = sx[i, 2], sy[i, 2]
        den = (by_ - cy_) * (ax - cx_) + (cx_ - bx_) * (ay - cy_)
        if abs(den) < 1e-9:
            continue
        w0 = ((by_ - cy_) * (gx - cx_) + (cx_ - bx_) * (gy - cy_)) / den
        w1 = ((cy_ - ay) * (gx - cx_) + (ax - cx_) * (gy - cy_)) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any():
            continue
        z = w0 * P[i, 0, 2] + w1 * P[i, 1, 2] + w2 * P[i, 2, 2]
        sel = m & (z > zbuf[y0:y1, x0:x1])
        if sel.any():
            zb = zbuf[y0:y1, x0:x1]; ib = img[y0:y1, x0:x1]
            zb[sel] = z[sel]; ib[sel] = shade[i]
            zbuf[y0:y1, x0:x1] = zb; img[y0:y1, x0:x1] = ib
    bg = zbuf <= -1e8
    v = np.clip(img * 255, 0, 255).astype(np.uint8)
    rgb = np.dstack([v, (v * 0.995).astype(np.uint8), (v * 0.975).astype(np.uint8)])
    rgb[bg] = (18, 16, 15)
    Image.fromarray(rgb).save(path)
    return W, H


def main() -> int:
    print("building the bezel with the front-face deboss ...")
    plain = E.front_bezel()
    v0 = plain.volume
    cut = deboss(E.front_bezel())
    v1 = cut.volume
    removed = v0 - v1
    want = (len(F.FRONT_HEX) * (math.sqrt(3) / 2 * F.FRONT_HEX_AFLAT ** 2)
            * F.FRONT_HEX_DEPTH) + F.MARK_AREA * F.MARK_DEPTH
    print(f"  volume {v0:.1f} -> {v1:.1f} mm3   removed {removed:.2f}  "
          f"predicted {want:.2f}  delta {100*(removed-want)/want:+.2f}%")
    print(f"  solids: {len(cut.solids())}   faces: {len(cut.faces())}")

    assert len(cut.solids()) == 1, (
        f"deboss produced {len(cut.solids())} solids -- something detached")
    assert abs(removed - want) / want < 0.02, "removed volume disagrees with the prediction"
    # the deboss must not reach the glass side of the bezel
    assert F.MARK_DEPTH < E.BEZEL_T and F.FRONT_HEX_DEPTH < E.BEZEL_T
    zmin = cut.bounding_box().min.Z
    assert abs(zmin - plain.bounding_box().min.Z) < 1e-6, "deboss changed the bezel underside"

    T = tris(cut)
    print(f"  tessellated: {len(T)} triangles")
    p1 = os.path.join(HERE, "bezel_face_3d.png")
    w, h = render(T, p1)
    print(f"  -> {os.path.relpath(p1, REPO)}  ({w}x{h})")
    # a close raking view of the brow, where the mark is
    brow = T[(T[:, :, 1].min(axis=1) > 70.0)]
    p2 = os.path.join(HERE, "bezel_face_3d_brow.png")
    w, h = render(brow, p2, tilt=52.0, yaw=8.0, ppm=64.0)
    print(f"  -> {os.path.relpath(p2, REPO)}  ({w}x{h})")

    print("\n" + "=" * 76)
    print("INTEGRATION BLOCK for ember_case.front_bezel(), verified above:")
    print("=" * 76)
    print("""
    # ---- FRONT FACE: debossed hex field + the Ember mark ----
    # tools/make_bezel_face.py owns both. The bezel prints FRONT FACE DOWN at 0.16mm, so
    # every one of these is a recess in layer 1: no supports, no overhangs, no print cost.
    # >>> rotation=FRONT_HEX_ROT IS NOT OPTIONAL. RegularPolygon(R,6) is FLAT-top and this
    # lattice is POINTY-top; without it the 0.45mm web collapses to 0.210mm. <<<
    _hx = None
    for (hx, hy) in _F.FRONT_HEX:
        _h = Pos(hx, hy, FRONT_Z - _F.FRONT_HEX_DEPTH) * extrude(
            RegularPolygon(_F.FRONT_HEX_R, 6, rotation=_F.FRONT_HEX_ROT),
            _F.FRONT_HEX_DEPTH + 0.01)
        _hx = _h if _hx is None else _hx + _h
    p -= _hx
    _ox, _oy = _F.MARK_ORIGIN
    _mk = None
    for (rx, ry, rw, rh) in _F.MARK:
        _b = bx(_ox+rx, _ox+rx+rw, _oy+ry, _oy+ry+rh, FRONT_Z - _F.MARK_DEPTH, FRONT_Z + 0.01)
        _mk = _b if _mk is None else _mk + _b
    p -= _mk
""")
    print("with `import bezel_face as _F` beside the existing `import wyrm_spans as _W`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
