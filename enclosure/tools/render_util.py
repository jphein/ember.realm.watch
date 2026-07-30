"""
Shaded orthographic renders of build123d solids. Look at the output.

Extracted from the retired tools/check_bezel_face.py, which had become a stale integration
test for a motif ember_case.py now cuts itself. These two helpers were the part worth
keeping: four defects on this project were invisible in correct-looking source and obvious
in a picture, so having a renderer one import away is the difference between checking and
assuming.

    import render_util as R
    R.render(R.tris(shape), "out.png", tilt=28.0, ppm=22.0)
"""
from __future__ import annotations

import math
import os

import numpy as np
from build123d import *
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def tris(shape, tol=0.02):
    f = os.path.join(HERE, "_rt.stl")
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


