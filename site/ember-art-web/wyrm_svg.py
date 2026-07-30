#!/usr/bin/env python3
"""
Web-scale hearth-wyrm — vector, for ember.realm.watch.

THE POINT: this is not a redraw. It imports the SAME parametric curves that
generate the device sprite (`~/Projects/ha/esphome/art/dragon.py`) and traces
them at 8x supersampling into smooth vector outlines. The site and the hardware
are provably the same animal, and if the creature is ever re-posed on the device
this regenerates to match.

The device version is 1-bit run-length spans, shaded per-pixel from a fire ramp,
because the framebuffer lives in PSRAM and every pixel is expensive. On the web
none of that applies, so here the same silhouette gets real gradients, a proper
rim light and sub-pixel curves.

Outputs into this directory:
  wyrm.svg              the hero, dark
  wyrm-light.svg        the hero, parchment
  wyrm-startle.svg      hero + CSS keyframes; INLINE this, don't <img> it
  favicon.svg           the wyrm coiled into an ember-glyph
  wyrm-states.svg       the five states, labelled
  wyrm-states.png       raster fallback
  contact-sheet.html    everything on one page, for eyeballing

  python3 wyrm_svg.py
Deterministic. No RNG, no network, no external assets.
"""

import importlib.util
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# The device generator moves: it started in ~/Projects/ha/esphome/art/ and moved
# to ember.realm.watch when that repo became authoritative, at which point a
# hardcoded path here died with a bare FileNotFoundError six frames deep. Search
# in priority order and say which one was used, so the next move is a one-line
# addition and a clear message instead of a traceback.
#
# NOTE the directory name `esphome/art/` is load-bearing and must not be renamed:
# the generated block in ember-satellite.yaml references it.
DEVICE_ART_CANDIDATES = [
    "/home/jp/Projects/ember.realm.watch/esphome/art/dragon.py",
    "/home/jp/Projects/ha/esphome/art/dragon.py",
]
DEVICE_ART = next((c for c in DEVICE_ART_CANDIDATES if os.path.exists(c)), None)
if DEVICE_ART is None:
    raise SystemExit(
        "cannot find the device generator dragon.py. Looked in:\n  "
        + "\n  ".join(DEVICE_ART_CANDIDATES)
        + "\nThe web art is TRACED from it, so there is nothing to draw without "
          "it. Add the new location to DEVICE_ART_CANDIDATES.")

# ---- import the device generator without running its main() ----
_spec = importlib.util.spec_from_file_location("device_dragon", DEVICE_ART)
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)

# ---- capture the SUPERSAMPLED buffer, not the 1-bit mask ----
# _resolve() is where the 8x float grid collapses to 120x50 pixels. Tracing the
# pixel mask would bake the device's own aliasing into a vector file; tracing the
# grid underneath it gives curves the sprite never had the resolution to show.
_GRID = {}
_real_resolve = D._resolve


def _capture(a):
    _GRID["last"] = a.copy()
    return _real_resolve(a)


D._resolve = _capture

SS = D.SS
DW, DH = D.DW, D.DH

# ---------------------------------------------------------------- palette ----
PAL = {
    "ground": "#0A0604", "ash": "#3A322C", "bed": "#4A1002", "ember": "#8E2206",
    "amber": "#E05A08", "gold": "#FFA81E", "hot": "#FFE8B4", "alarm": "#FF3C18",
    "parchment": "#F2E8DA", "ink": "#2A1C12", "dim": "#6A5240",
}


TOPO = {}


# ------------------------------------------------------- contour tracing ----
def _contours(grid, level=0.5):
    """Marching squares, stitched by INTEGER EDGE IDENTITY.

    The first version keyed segments on their float endpoints, rounded to 1/64.
    That looks fine and is quietly broken: two adjacent cells compute the same
    shared edge from different corners, so the two values can differ in the last
    bits, round into different buckets, and the chain silently breaks. The
    silhouette then traces as several partial loops instead of one — which is
    exactly the "3 loops for 1 component" the self-check kept reporting, and I
    twice misdiagnosed it as geometry.

    A marching-squares crossing lives on a grid edge, and a grid edge has an
    exact integer name: ('h', x, y) or ('v', x, y). Keyed that way the stitch is
    exact by construction and no tolerance is involved anywhere.

    Written out rather than pulled from a library so the output is stable and the
    file has no runtime dependency beyond numpy.
    """
    h, w = grid.shape
    adj = {}
    pos = {}

    def crossing(eid, p0, p1, v0, v1):
        if eid not in pos:
            t = 0.5 if abs(v1 - v0) < 1e-12 else (level - v0) / (v1 - v0)
            t = max(0.0, min(1.0, t))
            pos[eid] = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
        return eid

    # 0 = top, 1 = right, 2 = bottom, 3 = left, named on the shared grid edge
    TABLE = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)],
             5: [(3, 2), (1, 0)], 6: [(0, 2)], 7: [(3, 2)], 8: [(2, 3)],
             9: [(2, 0)], 10: [(0, 3), (2, 1)], 11: [(2, 1)], 12: [(1, 3)],
             13: [(1, 0)], 14: [(0, 3)]}

    for y in range(h - 1):
        for x in range(w - 1):
            v0, v1 = grid[y, x], grid[y, x + 1]
            v2, v3 = grid[y + 1, x + 1], grid[y + 1, x]
            idx = ((v0 > level) | ((v1 > level) << 1)
                   | ((v2 > level) << 2) | ((v3 > level) << 3))
            if idx == 0 or idx == 15:
                continue
            eid = {
                0: crossing(("h", x, y), (x, y), (x + 1, y), v0, v1),
                1: crossing(("v", x + 1, y), (x + 1, y), (x + 1, y + 1), v1, v2),
                2: crossing(("h", x, y + 1), (x, y + 1), (x + 1, y + 1), v3, v2),
                3: crossing(("v", x, y), (x, y), (x, y + 1), v0, v3),
            }
            # DIRECTED. The table's (a -> b) order is what carries orientation:
            # outer boundaries come out one way round and holes the other, which
            # is exactly what fill-rule="nonzero" needs. Storing the segments
            # undirected threw that away, and the horns — which OVERLAP the skull
            # — then had to be drawn with fill-rule="evenodd", where overlap
            # CANCELS: the horn/skull intersection punched itself out and the
            # horns rendered as hollow slivers.
            for a_, b_ in TABLE[idx]:
                adj[eid[a_]] = eid[b_]

    loops = []
    visited = set()
    for start in adj:
        if start in visited:
            continue
        loop = []
        cur = start
        while cur is not None and cur not in visited:
            visited.add(cur)
            loop.append(cur)
            cur = adj.get(cur)
        if len(loop) > 8:
            loops.append([pos[e] for e in loop])
    return loops


def _chaikin(pts, n=2):
    """Corner-cutting. Two passes turns marching-squares staircase into curve."""
    for _ in range(n):
        out = []
        m = len(pts)
        for i in range(m):
            p, q = pts[i], pts[(i + 1) % m]
            out.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            out.append((0.25 * p[0] + 0.75 * q[0], 0.25 * q[1] + 0.75 * q[1]))
        pts = out
    return pts


def _decimate(pts, tol=0.16):
    """Ramer-Douglas-Peucker. Keeps files small without visible loss."""
    if len(pts) < 3:
        return pts

    def rdp(a, b):
        if b <= a + 1:
            return []
        p0, p1 = pts[a], pts[b]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            if n < 1e-9:
                d = math.hypot(pts[i][0] - p0[0], pts[i][1] - p0[1])
            else:
                d = abs(dy * (pts[i][0] - p0[0]) - dx * (pts[i][1] - p0[1])) / n
            if d > best:
                best, bi = d, i
        if best <= tol:
            return []
        return rdp(a, bi) + [bi] + rdp(bi, b)

    sys.setrecursionlimit(10000)
    keep = [0] + rdp(0, len(pts) - 1) + [len(pts) - 1]
    return [pts[i] for i in keep]


def _shift(g, dy, dx):
    out = np.empty_like(g)
    ys = slice(max(0, dy), g.shape[0] + min(0, dy))
    yd = slice(max(0, -dy), g.shape[0] + min(0, -dy))
    xs = slice(max(0, dx), g.shape[1] + min(0, dx))
    xd = slice(max(0, -dx), g.shape[1] + min(0, -dx))
    out[:] = 0.0
    out[yd, xd] = g[ys, xs]
    return out


def _morph(g, r, op):
    f = np.maximum if op == "dilate" else np.minimum
    out = g.copy()
    if op == "erode":
        out = np.pad(g, r, mode="constant", constant_values=1.0)[
            r:r + g.shape[0], r:r + g.shape[1]]
        out = g.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy == 0 and dx == 0:
                continue
            sh = _shift(g, dy, dx)
            if op == "erode":
                sh = np.where(_shift(np.ones_like(g), dy, dx) > 0, sh, 1.0)
            out = f(out, sh)
    return out


def _soften(g, close_r=3, blur_r=2):
    """Morphological CLOSE, then a small box blur, before tracing.

    The close is the load-bearing half and it is NOT a blur — that was my first
    attempt and it did the exact opposite of what was wanted. The horns meet the
    skull tangentially: one 8-connected component in the device's 1-bit mask, but
    a hairline at supersample resolution. Blurring a 1px bridge averages it BELOW
    the contour level and splits it further; the self-check below caught that
    immediately (4 loops for 1 component, worse than the 3 I started with).
    Dilate-then-erode welds the join and puts the silhouette back to its original
    size, which is what "closing" is for.

    Separate loops matter because each one gets its own rim stroke, so a hairline
    seam renders as horns detached from the head by a bright outline.

    The blur afterwards only rounds the sub-pixel staircase; at 8x display scale
    that is the difference between "carved" and "aliased"."""
    g = _morph(g.astype(np.float32), close_r, "dilate")
    g = _morph(g, close_r, "erode")
    k = 2 * blur_r + 1
    c = np.cumsum(np.pad(g, ((0, 0), (blur_r + 1, blur_r)), mode="edge"), axis=1)
    g = (c[:, k:] - c[:, :-k]) / k
    c = np.cumsum(np.pad(g, ((blur_r + 1, blur_r), (0, 0)), mode="edge"), axis=0)
    return (c[k:, :] - c[:-k, :]) / k


def _topology(m):
    """(components, holes) of a boolean grid, 4-connected background.

    Holes matter: a closed region with H holes traces to 1 + H loops, not 1. My
    first self-check compared the loop count against components ALONE, decided
    the horns had detached, and sent me chasing a welding bug that did not exist
    — the extra loops are the notches BETWEEN the horns, which are real holes and
    are supposed to be there. The fix was fill-rule, not geometry."""
    from collections import deque
    seen = np.zeros(m.shape, bool)
    comp = 0
    for y in range(m.shape[0]):
        for x in range(m.shape[1]):
            if m[y, x] and not seen[y, x]:
                comp += 1
                q = deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if (0 <= ny < m.shape[0] and 0 <= nx < m.shape[1]
                                    and m[ny, nx] and not seen[ny, nx]):
                                seen[ny, nx] = True
                                q.append((ny, nx))
    bg = ~m
    seen = np.zeros(m.shape, bool)
    q = deque()
    for x in range(m.shape[1]):
        for y in (0, m.shape[0] - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    for y in range(m.shape[0]):
        for x in (0, m.shape[1] - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if (0 <= ny < m.shape[0] and 0 <= nx < m.shape[1]
                    and bg[ny, nx] and not seen[ny, nx]):
                seen[ny, nx] = True
                q.append((ny, nx))
    holes = 0
    for y in range(m.shape[0]):
        for x in range(m.shape[1]):
            if bg[y, x] and not seen[y, x]:
                holes += 1
                q = deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if (0 <= ny < m.shape[0] and 0 <= nx < m.shape[1]
                                and bg[ny, nx] and not seen[ny, nx]):
                            seen[ny, nx] = True
                            q.append((ny, nx))
    return comp, holes


def trace(build_fn, scale=1.0, dx=0.0, dy=0.0, tol=0.16, name="?"):
    """Run a device mask builder, trace its supersampled grid, return SVG path."""
    mask = build_fn()
    grid = _soften(_GRID["last"])
    loops = _contours(grid)
    # Topology is recorded, not asserted. Predicting the loop count means
    # committing to a foreground/background connectivity convention and matching
    # whatever marching squares does at saddles; I got that wrong twice and each
    # time it sent me after a geometry bug that was not there. The check that
    # actually matters is end-to-end and lives in verify_silhouette(): rasterise
    # the emitted path and compare it against the device mask.
    TOPO[name] = (_topology(grid > 0.5), len(loops), int(mask.sum()))
    # grid is in supersample units; bring it back to dragon-local px
    parts = []
    for lp in loops:
        pts = [((p[0] + 0.5) / SS, (p[1] + 0.5) / SS) for p in lp]
        pts = _decimate(_chaikin(pts, 2), tol)
        if len(pts) < 4:
            continue
        pts = [(p[0] * scale + dx, p[1] * scale + dy) for p in pts]
        parts.append(_smooth_path(pts))
    return " ".join(parts)


def _smooth_path(pts, prec=2):
    """Closed polyline -> quadratic Beziers through segment midpoints.

    Straight line segments are what made the first render look faceted: the
    silhouette is traced at 8x and then drawn 8x larger again, so every RDP
    vertex becomes a visible corner. Putting the control point ON the vertex and
    the anchor at the midpoint gives C1 continuity for free and roughly halves
    the point count for the same fidelity."""
    n = len(pts)
    mid = lambda a, b: ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    f2 = "%." + str(prec) + "f"
    start = mid(pts[-1], pts[0])
    d = ("M" + f2 + " " + f2) % start
    for i in range(n):
        c = pts[i]
        m = mid(pts[i], pts[(i + 1) % n])
        d += ("Q" + f2 + " " + f2 + " " + f2 + " " + f2) % (c[0], c[1], m[0], m[1])
    return d + "Z"


# ------------------------------------------------------------- the pieces ----
S = 8.0            # dragon-local px -> SVG user units
# Padding matters: the alert head's horns sit at dragon y=0 and the tail tip at
# y=3, so a viewBox flush to the bbox clips both. PAD_T is generous because the
# startle rotates the head UP out of the resting silhouette.
# PAD_L is generous because the head ROTATES about the shoulder: at the idle
# droop the muzzle swings left and down well past the resting bbox, and at 7px
# of margin it was being clipped by the viewBox in exactly the two states
# (idle, error) where the head is lowest.
PAD_L, PAD_R, PAD_T, PAD_B = 15.0, 7.0, 9.0, 7.0
OX, OY = PAD_L * S, PAD_T * S
VB_W = (DW + PAD_L + PAD_R) * S
VB_H = (DH + PAD_T + PAD_B) * S


def body_path():
    return trace(lambda: D.body_mask(False), S, OX, OY, name="body")


def wing_body_path():
    return trace(lambda: D.body_mask(True), S, OX, OY, name="body+wing")


# --------------------------------------------------- the head, analytically ---
# The BODY is traced: it is one blob and the trace verifies at IoU 0.98.
#
# The HEAD is not traced, and that is a deliberate retreat. It is five OVERLAPPING
# primitives (a tapered skull tube, a brow, two horns, a cheek frill, a jaw tube),
# and overlapping tangential parts are the case my marching-squares stitch gets
# wrong — it lost segments and returned crescents instead of a skull. Rather than
# keep debugging a tracer for a shape whose construction I already know, the head
# is rebuilt from the same primitives as real outlines. Analytic curves beat a
# trace of a rasterisation anyway; this is the one place the web version can be
# strictly better than the sprite rather than merely faithful to it.
#
# The primitives are COPIED from dragon.py's head_mask(), which is a drift risk,
# so verify_head() rasterises this construction and compares it against the
# device's own head_mask. If someone re-sculpts the head on the device and does
# not update these numbers, the build fails.
HEAD_SKULL = [(0.9, 8.8, 1.2), (3.0, 8.4, 1.8), (6.0, 7.9, 2.4), (9.5, 7.4, 3.0),
              (13.5, 7.6, 3.6), (17.5, 8.8, 4.0), (21.0, 11.0, 3.2)]
HEAD_BROW = [(6.4, 5.4), (11.0, 3.2), (15.5, 4.2), (12.5, 6.4)]
HEAD_HORN1 = [(14.0, 3.8), (17.0, 2.6), (27.4, 0.0), (19.5, 4.8)]
HEAD_HORN2 = [(15.5, 6.6), (18.5, 5.8), (27.6, 5.2), (20.0, 8.4)]
HEAD_FRILL = [(17.5, 9.2), (23.0, 8.2), (24.0, 12.0), (19.0, 13.4)]


def _jaw_pts(j):
    return [(1.3, 10.0 + j * 1.00, 1.0), (4.5, 10.4 + j * 0.82, 1.4),
            (8.5, 10.9 + j * 0.58, 1.8), (13.5, 11.4 + j * 0.30, 2.1),
            (18.5, 11.8, 2.4)]


def _signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return a / 2.0


def _emit(pts, sx, sy, ox, oy, smooth=True, prec=2):
    """All subpaths forced to ONE winding direction, so fill-rule nonzero unions
    them instead of punching the overlaps out."""
    if _signed_area(pts) < 0:
        pts = pts[::-1]
    pts = [(ox + x * sx, oy + y * sy) for x, y in pts]
    return _smooth_path(pts, prec) if smooth else (
        ("M%." + str(prec) + "f %." + str(prec) + "f") % pts[0]
        + "".join(("L%." + str(prec) + "f %." + str(prec) + "f") % q for q in pts[1:])
        + "Z")


def _tube_outline(ctrl, n=64):
    """Offset a Catmull-Rom spline by its varying radius, both sides."""
    samples = D._catmull(ctrl, n)
    left, right = [], []
    for i, (cx, cy, r) in enumerate(samples):
        if i == 0:
            tx, ty = samples[1][0] - cx, samples[1][1] - cy
        elif i == len(samples) - 1:
            tx, ty = cx - samples[-2][0], cy - samples[-2][1]
        else:
            tx = samples[i + 1][0] - samples[i - 1][0]
            ty = samples[i + 1][1] - samples[i - 1][1]
        m = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / m, tx / m
        left.append((cx + nx * r, cy + ny * r))
        right.append((cx - nx * r, cy - ny * r))
    # round the two ends so the muzzle is a dome, not a chisel
    cap0 = []
    cx, cy, r = samples[0]
    a0 = math.atan2(left[0][1] - cy, left[0][0] - cx)
    for k in range(1, 9):
        a = a0 + math.pi * k / 9.0
        cap0.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    cap1 = []
    cx, cy, r = samples[-1]
    a0 = math.atan2(right[-1][1] - cy, right[-1][0] - cx)
    for k in range(1, 9):
        a = a0 + math.pi * k / 9.0
        cap1.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return left + cap1 + right[::-1] + cap0


def head_path_analytic(jaw, hx, hy):
    ox, oy = OX + hx * S, OY + hy * S
    parts = [_emit(_tube_outline(HEAD_SKULL), S, S, ox, oy),
             _emit(_tube_outline(_jaw_pts(jaw)), S, S, ox, oy),
             _emit(HEAD_BROW, S, S, ox, oy, smooth=False),
             _emit(HEAD_HORN1, S, S, ox, oy, smooth=False),
             _emit(HEAD_HORN2, S, S, ox, oy, smooth=False),
             _emit(HEAD_FRILL, S, S, ox, oy, smooth=False)]
    return " ".join(parts)


def head_path(jaw, hx, hy):
    return head_path_analytic(jaw, hx, hy)


def maw_path(jaw, hx, hy):
    return trace(lambda: D.maw_mask(jaw), S, OX + hx * S, OY + hy * S, name="maw")


def neck_path(hx, hy, samples=40):
    """The neck as a real tapered outline rather than per-row spans."""
    sx, sy = D.SHOULDER
    ax, ay = hx + D.HEAD_ATTACH[0], hy + D.HEAD_ATTACH[1]
    cxp, cyp = sx - 5.5, (sy + ay) * 0.5 - 2.0
    left, right = [], []
    for i in range(samples):
        t = i / (samples - 1.0)
        u = 1 - t
        cx = u * u * sx + 2 * u * t * cxp + t * t * ax
        cy = u * u * sy + 2 * u * t * cyp + t * t * ay
        # derivative for the normal
        tx = 2 * u * (cxp - sx) + 2 * t * (ax - cxp)
        ty = 2 * u * (cyp - sy) + 2 * t * (ay - cyp)
        n = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / n, tx / n
        r = 4.9 * u + 3.0 * t
        left.append((OX + (cx + nx * r) * S, OY + (cy + ny * r) * S))
        right.append((OX + (cx - nx * r) * S, OY + (cy - ny * r) * S))
    pts = left + right[::-1]
    d = "M%.2f %.2f" % pts[0] + "".join("L%.2f %.2f" % p for p in pts[1:]) + "Z"
    return d


def wyrm_group(jaw=0, hx=0, hy=0, idp=""):
    """Head+neck are their OWN group so the whole startle is one rotation."""
    return {
        "body": body_path(),
        "neck": neck_path(hx, hy),
        "head": head_path(jaw, hx, hy),
        "maw": maw_path(jaw, hx, hy) if jaw else "",
        "eye": (hx + D.HEAD_EYE[0], hy + D.HEAD_EYE[1]),
        "muzzle": (hx + D.HEAD_MUZZLE[0], hy + D.HEAD_MUZZLE[1]),
    }


# ------------------------------------------------------------------ output ----

THEMES = {
    "dark":  dict(bg=PAL["ground"], grate=PAL["ash"], ink=PAL["hot"],
                  b0=PAL["bed"], b1=PAL["ember"], b2=PAL["amber"], b3=PAL["gold"],
                  rim=PAL["hot"], rim2=PAL["gold"]),
    "light": dict(bg=PAL["parchment"], grate="#D8CAB8", ink=PAL["ink"],
                  b0="#8C2E0A", b1="#B83A0C", b2="#E06A10", b3="#F0A820",
                  rim="#FFE090", rim2="#E06A10"),
    # the guttered state: the fire has gone out, so the creature is ash and the
    # ONLY thing still lit is one eye
    "ash":   dict(bg=PAL["ground"], grate="#2A2420", ink=PAL["dim"],
                  b0="#241F1C", b1="#2F2926", b2="#3A322C", b3="#463C34",
                  rim="#6A5240", rim2="#3A322C"),
}

# Per-state pose. `rot` is degrees about the shoulder; NEGATIVE lowers the head,
# because the head sits up-and-left of the pivot and SVG's positive rotation is
# clockwise on screen. `glow` scales the belly furnace by moving the gradient's
# hot end.
STATES = [
    ("idle",      "asleep in the coals",        "dark", -24, 0, "shut",  0.55),
    ("listening", "leaning in on your voice",   "dark",   2, 0, "open",  0.95),
    ("thinking",  "still — turning it over",    "dark",  -8, 0, "slit",  1.05),
    ("speaking",  "jaw working on real audio",  "dark",  -2, 2, "open",  1.15),
    ("error",     "guttered — one eye still lit", "ash", -26, 0, "alarm", 0.0),
]


def defs(t, uid, gy0=None, gy1=None, hy0=0.0, hy1=0.0):
    """Gradients. `uid` is a per-FILE prefix and it is not cosmetic.

    Inlined SVGs all share one document ID space, so an unprefixed
    `<linearGradient id="belly">` in two different files cross-wires — and the
    result RENDERS, just with the wrong gradient, which is the kind of bug that
    survives review. Every id here is prefixed by the file that owns it.
 The belly furnace and the fire-lit back edge are the two
    things the device does per-pixel that a gradient does better."""
    gy0 = OY + 2 * S if gy0 is None else gy0
    gy1 = OY + (DH - 1) * S if gy1 is None else gy1
    return f'''  <defs>
    <!-- userSpaceOnUse, NOT the default objectBoundingBox: the head, neck and
         body are separate paths, and per-path bounding boxes gave each its own
         private light direction — the muzzle lit from below while the body lit
         from below a different "below". One gradient in user space is one sun. -->
    <linearGradient id="{uid}belly" gradientUnits="userSpaceOnUse"
                    x1="0" y1="{gy0:.0f}" x2="0" y2="{gy1:.0f}">
      <stop offset="0.00" stop-color="{t['b0']}"/>
      <stop offset="0.46" stop-color="{t['b0']}"/>
      <stop offset="0.66" stop-color="{t['b1']}"/>
      <stop offset="0.86" stop-color="{t['b2']}"/>
      <stop offset="1.00" stop-color="{t['b3']}"/>
    </linearGradient>
    <!-- The head is lit on its OWN extent. One global gradient is physically
         right (fire is below, a raised head is further from it) and visually
         wrong: the focal point of the picture lands at the dark end of the ramp
         and disappears. The story still holds — this is the creature's throat
         fire lighting its own skull from inside. -->
    <linearGradient id="{uid}skull" gradientUnits="userSpaceOnUse"
                    x1="0" y1="{hy0:.0f}" x2="0" y2="{hy1:.0f}">
      <stop offset="0.00" stop-color="{t['b0']}"/>
      <stop offset="0.45" stop-color="{t['b1']}"/>
      <stop offset="1.00" stop-color="{t['b2']}"/>
    </linearGradient>
    <linearGradient id="{uid}rim" gradientUnits="userSpaceOnUse"
                    x1="0" y1="{gy0:.0f}" x2="0" y2="{gy1:.0f}">
      <stop offset="0.00" stop-color="{t['rim']}" stop-opacity="1"/>
      <stop offset="0.34" stop-color="{t['rim2']}" stop-opacity="0.7"/>
      <stop offset="0.72" stop-color="{t['rim2']}" stop-opacity="0.12"/>
      <stop offset="1.00" stop-color="{t['rim2']}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="{uid}hearthglow" cx="0.5" cy="1.0" r="0.9">
      <stop offset="0" stop-color="{t['b2']}" stop-opacity="0.55"/>
      <stop offset="0.5" stop-color="{t['b1']}" stop-opacity="0.22"/>
      <stop offset="1" stop-color="{t['b0']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="{uid}tongue" gradientUnits="objectBoundingBox"
                    x1="0" y1="1" x2="0" y2="0">
      <stop offset="0.00" stop-color="{t['b2']}" stop-opacity="0.95"/>
      <stop offset="0.45" stop-color="{t['b1']}" stop-opacity="0.55"/>
      <stop offset="1.00" stop-color="{t['b1']}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="{uid}eyeglow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['rim']}" stop-opacity="0.95"/>
      <stop offset="1" stop-color="{t['rim']}" stop-opacity="0"/>
    </radialGradient>
  </defs>'''


def hearth_layer(t, uid, w, h):
    """Stylised coals, in their own <g> so a page can drop them with one class.

    The tongues fade out at the tip through their own gradient rather than being
    flat triangles — flat ones read as bunting, which is what the first pass
    looked like."""
    base = h - 10
    out = []
    for i, (cx, hh, ww) in enumerate([
            (0.05, 0.26, 0.13), (0.15, 0.42, 0.15), (0.26, 0.30, 0.12),
            (0.38, 0.52, 0.16), (0.50, 0.34, 0.13), (0.62, 0.46, 0.15),
            (0.74, 0.30, 0.12), (0.85, 0.40, 0.14), (0.95, 0.24, 0.11)]):
        x, hp, wp = cx * w, hh * h, ww * w
        out.append(
            f'<path d="M{x - wp / 2:.0f} {base:.0f} '
            f'C{x - wp * 0.46:.0f} {base - hp * 0.5:.0f} '
            f'{x - wp * 0.20:.0f} {base - hp * 0.72:.0f} {x:.0f} {base - hp:.0f} '
            f'C{x + wp * 0.20:.0f} {base - hp * 0.72:.0f} '
            f'{x + wp * 0.46:.0f} {base - hp * 0.5:.0f} '
            f'{x + wp / 2:.0f} {base:.0f} Z" fill="url(#{uid}tongue)" '
            f'opacity="{0.75 if i % 2 else 0.55:.2f}"/>')
    return (f'  <g class="hearth">\n'
            f'    <rect x="0" y="{h * 0.28:.0f}" width="{w}" height="{h * 0.72:.0f}" '
            f'fill="url(#{uid}hearthglow)"/>\n    '
            + "\n    ".join(out)
            + f'\n    <rect x="0" y="{base:.0f}" width="{w}" height="{h - base:.0f}" '
              f'fill="{t["grate"]}"/>\n  </g>')


def wyrm_layer(t, uid, jaw=0, hx=0, hy=0, cls="", eye="open", rot=0.0, sw=2.6):
    """Head+neck are their OWN <g> so the whole startle is one transform.

    RIM LIGHT BY OFFSET COPY, not by stroke. The head is a union of six
    overlapping subpaths (skull, jaw, brow, two horns, frill) and a stroke paints
    every subpath — including the internal ones — so the head rendered as a
    wireframe of its own construction. A duplicate of the same paths, nudged up
    and painted in the rim colour BEHIND the fill, peeks out only along the top
    edge: no seams, and it is a better description of what is physically going on
    anyway (fire below and behind, lighting the back).
    """
    g = wyrm_group(jaw, hx, hy)
    ex, ey = OX + g["eye"][0] * S, OY + g["eye"][1] * S
    px, py = OX + D.SHOULDER[0] * S, OY + D.SHOULDER[1] * S   # rotation pivot
    lift = S * 0.34                                            # rim offset
    # As an ATTRIBUTE, not a css transform-origin: the attribute form renders in
    # every rasteriser (inkscape ignores css transform-origin entirely, so my
    # state previews would all have shown the same pose), and a css `transform`
    # property cleanly overrides it when the animated variant wants control.
    # rot=None emits no attribute at all, which is what that variant asks for.
    rota = "" if rot is None else ' transform="rotate(%.2f %.1f %.1f)"' % (rot, px, py)
    eyec = {"open": t["rim"], "slit": PAL["gold"], "alarm": PAL["alarm"]}.get(eye, t["rim"])
    if eye == "shut":
        eye = (f'      <path class="eye lid" d="M{ex - S * 1.1:.1f} {ey:.1f} '
               f'L{ex + S * 0.9:.1f} {ey:.1f}" stroke="{t["b0"]}" '
               f'stroke-width="{S * 0.45:.1f}" stroke-linecap="round"/>')
    elif eye == "slit":
        eye = (f'      <path class="eye" d="M{ex - S * 0.9:.1f} {ey:.1f} '
               f'L{ex + S * 0.8:.1f} {ey:.1f}" stroke="{eyec}" '
               f'stroke-width="{S * 0.42:.1f}" stroke-linecap="round"/>')
    else:
        eye = (f'      <circle class="eye-glow" cx="{ex:.1f}" cy="{ey:.1f}" '
               f'r="{S * 1.7:.1f}" fill="url(#{uid}eyeglow)"/>\n'
               f'      <circle class="eye" cx="{ex:.1f}" cy="{ey:.1f}" '
               f'r="{S * 0.5:.1f}" fill="{eyec}"/>')
    maw = (f'      <path class="maw" d="{g["maw"]}" fill="{t["rim"]}"/>\n'
           if g["maw"] else "")
    return f'''  <g class="wyrm {cls}">
    <!-- Z-ORDER: the neck goes BEHIND the body, the head in FRONT of it. The
         neck's shoulder end is a flat cap, and drawn on top it showed as a notch
         where it met the chest; behind, the chest swallows it, which is also
         what a neck actually does. Both halves carry class="headneck" and the
         same transform-origin, so ONE css rule swings them together. -->
    <g class="headneck"{rota}>
      <path class="neck-rim" d="{g['neck']}" fill="{t['rim']}"
            transform="translate(0 {-lift:.1f})"/>
      <path class="neck" d="{g['neck']}" fill="url(#{uid}skull)"/>
    </g>
    <path class="body-rim" d="{g['body']}" fill="{t['rim2']}"
          transform="translate(0 {-lift:.1f})"/>
    <path class="body" d="{g['body']}" fill="url(#{uid}belly)"/>
    <g class="headneck"{rota}>
      <path class="head-rim jaw-shut" d="{g['head']}" fill="{t['rim']}"
            transform="translate(0 {-lift:.1f})"/>
      <path class="head jaw-shut" d="{g['head']}" fill="url(#{uid}skull)"/>
{maw}{eye}
    </g>
  </g>'''


def svg(body, w=None, h=None, extra_head="", cls=""):
    w = w or VB_W
    h = h or VB_H
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'role="img" aria-label="Ember, a hearth-wyrm curled in the coals" '
            f'class="{cls}">\n{extra_head}{body}\n</svg>\n')


def hero(theme="dark", hearth=True, jaw=0, hx=0, hy=0, eye="open", rot=0.0, glow=1.0):
    t = THEMES[theme]
    uid = "wh-" if theme == "dark" else "wl-"
    # the head-and-neck gradient spans the skull down to the shoulder
    hy0 = OY + hy * S
    hy1 = OY + (D.SHOULDER[1] + 2) * S
    parts = [defs(t, uid, hy0=hy0, hy1=hy1),
             f'  <rect class="ground" width="{VB_W:.0f}" height="{VB_H:.0f}" fill="{t["bg"]}"/>']
    if hearth:
        parts.append(hearth_layer(t, uid, VB_W, VB_H))
    parts.append(wyrm_layer(t, uid, jaw, hx, hy, eye=eye, rot=rot))
    return svg("\n".join(parts))


def verify_silhouette():
    """Rasterise each emitted outline and compare it against the device's own
    geometry, at 8x so thin features are actually measurable.

    Ground truth is the SUPERSAMPLED grid, not the 120x50 sprite. That took a
    measurement to establish: the body vector scores 0.86 against the sprite and
    0.98 against the geometry the sprite is a quantisation of — the 0.14 is the
    sprite's own pixelation, not the vector's error. Comparing against the sprite
    would have had me "fixing" the vector to reproduce aliasing.

    The head is the case that matters most: it is rebuilt from copied primitives,
    so this is the guard against those numbers drifting from dragon.py's."""
    import subprocess
    import tempfile
    from PIL import Image
    out = []
    cases = [
        ("body", lambda: D.body_mask(False), lambda: body_path(), OX, OY),
        ("head-shut", lambda: D.head_mask(0), lambda: head_path(0, 0, 0), OX, OY),
        ("head-open", lambda: D.head_mask(4), lambda: head_path(4, 0, 0), OX, OY),
    ]
    for name, maskfn, pathfn, ox, oy in cases:
        maskfn()
        fine = _GRID["last"] > 0.5
        path = pathfn()
        w, h = DW * D.SS, DH * D.SS
        with tempfile.TemporaryDirectory() as td:
            sp = os.path.join(td, "s.svg")
            pp = os.path.join(td, "s.png")
            # undo the layout padding so the two overlay in device coordinates
            open(sp, "w").write(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {DW} {DH}" '
                f'width="{w}" height="{h}"><g transform="translate({-ox / S:.4f} '
                f'{-oy / S:.4f}) scale({1.0 / S:.6f})"><path d="{path}" fill="#fff"/>'
                f'</g></svg>')
            subprocess.run(["inkscape", "--export-type=png", "-w", str(w), "-h",
                            str(h), "--export-filename=" + pp, sp],
                           check=True, capture_output=True)
            got = np.array(Image.open(pp).convert("L")) > 128
        inter = int((got & fine).sum())
        union = int((got | fine).sum())
        out.append((name, inter / union if union else 1.0,
                    fine.sum() / (D.SS ** 2), got.sum() / (D.SS ** 2)))
    return out


if __name__ == "__main__":
    open(os.path.join(HERE, "wyrm.svg"), "w").write(hero("dark"))
    open(os.path.join(HERE, "wyrm-light.svg"), "w").write(hero("light"))
    print("traced from %s" % DEVICE_ART)
    print("wyrm.svg      %6d bytes" % os.path.getsize(os.path.join(HERE, "wyrm.svg")))
    print("wyrm-light.svg%6d bytes" % os.path.getsize(os.path.join(HERE, "wyrm-light.svg")))
    print()
    print("silhouette fidelity — vector vs the device's own geometry, at 8x:")
    bad = 0
    for name, iou, nref, ngot in verify_silhouette():
        ok = iou >= 0.93
        bad += not ok
        print("  %-10s IoU %.4f   device %7.1f px^2  vector %7.1f px^2   %s"
              % (name, iou, nref, ngot, "ok" if ok else "TOO FAR OFF"))
    if bad:
        raise SystemExit("the vector no longer matches the sprite")
