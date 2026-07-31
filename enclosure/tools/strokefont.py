"""A stroke font for debossed panel labels, plus the checks that make it safe to print.

WHY A STROKE FONT AND NOT A REAL TYPEFACE
-----------------------------------------
A debossed label is a groove, and a groove narrower than about one nozzle width does not
print -- the slicer bridges it and you get a smudge where the letter was. This repo already
fixes that floor at 0.90mm (the wyrm mark asserts it).

At the cap height these labels have to live at (4.7mm ink, set by a 13.27mm hexagon), 0.90mm
of stroke is a stroke/height ratio of 0.19. No real typeface is that heavy -- a normal Bold is
~0.14 and even a Black is ~0.19 at the extreme. So with an outline font the stroke width is a
CONSEQUENCE of the font and the size, and the only way to learn it is to rasterise and measure
and then hope the next size change does not quietly go under.

Here the stroke width is an ARGUMENT. `w` is the groove width, everywhere, exactly. The floor
is satisfied by construction, and the measurement below is a confirmation rather than a search.
That is the whole reason for hand-cutting eight glyphs instead of calling Text().

WHAT IS ACTUALLY CHECKED, AND WHY IT IS TWO DIFFERENT INSTRUMENTS
------------------------------------------------------------------
A label can be unprintable in two independent ways, and they do not answer to the same tool:

  1. THE GROOVE TOO NARROW -- fixed by construction (the groove IS `w`), confirmed by
     granulometry on a rasterised mask via tools/minfeature.py. See min_feature().

  2. THE MATERIAL BETWEEN GROOVES TOO THIN -- the counter of an O, the gap between the three
     bars of an S, the space between two letters. NOT fixed by construction: it falls out of
     the glyph shapes and the size, and it is the one that actually bites, because it appears
     only at small sizes and looks perfect in the CAD render.

     ⚠️ GRANULOMETRY CANNOT SEE #2, which matters because reaching for the tool already in
     the repo is the obvious move. `min_feature` reports the largest disc-opening that loses
     no more than `tol` of the AREA. Run it on the complement and the complement is dominated
     by the unbounded surround: a disc that completely annihilates an O's counter costs a
     fraction of a percent and passes. The metric is not wrong -- it answers a question about
     a whole region when the question is about one small part of it. min_feature's own
     docstring records this repo shipping that same mistake once already.

     Framing the complement tightly makes granulometry able to see counters, and that was
     tried here first. It was abandoned because the tolerance has to be loosened to ~1.5% to
     tolerate the unavoidable taper at every acute concave corner (the valley of an M), and at
     1.5% the CONTROL went blind: a deliberately-collapsed S at h=2.30 reported 1.560mm and
     passed. An area-averaged metric cannot separate "a counter closed" from "a corner is
     pointy" -- so #2 is measured EXACTLY instead, by pairwise segment distance. See min_gap().

Run `python3 strokefont.py` for the self-test.
"""
from __future__ import annotations

import math

# Advance width, as a fraction of the centreline cap height. Deliberately condensed (0.52
# rather than a normal ~0.62): the budget that binds is the big cap's 13.27mm across flats,
# and narrowing the glyphs buys width without touching the stroke, which is the one dimension
# not allowed to move.
GW = 0.52

# TWO GLYPHS CANNOT BE MONOSPACED AT 0.52 AND THE CHECK IS WHAT SAID SO, not taste.
#
#   M  its valley vertex sits half an advance from each stem, so the material between stem and
#      valley is 0.26*h - w. Clearing the 0.90 floor needs h >= 6.92 (a 7.8mm label) at 0.52.
#      At 0.72 it is 0.36*h - w and clears at h = 5.0, which is a size that fits. M is simply
#      a wide letter; condensing it uniformly with the others put a 0.43mm rib in it.
#   I  a bare stem in a 0.52 box floats in ~2.3mm of space on each side and reads as a word
#      break. 0.16 puts its sidebearings on the same 1.00mm as every other pair.
GW_OVERRIDE = {"M": 0.72, "I": 0.16}


def gw(ch: str) -> float:
    """Advance width of `ch` as a fraction of the centreline cap height."""
    return GW_OVERRIDE.get(ch, GW)

# Centrelines in a normalised box: u in [0, GW], v in [0, 1] with v=0 the baseline. Each
# glyph is a list of POLYLINES. Curves are octagonal rather than round because a stroke font
# at 0.19 stroke/height reads as a technical/stencil mark anyway, and straight segments make
# the pairwise-distance check exact instead of an approximation over subdivided arcs.
GLYPHS: dict[str, list[list[tuple[float, float]]]] = {
    "S": [[(0.52, 0.82), (0.40, 1.00), (0.12, 1.00), (0.00, 0.82), (0.00, 0.66),
           (0.12, 0.50), (0.40, 0.50), (0.52, 0.34), (0.52, 0.18), (0.40, 0.00),
           (0.12, 0.00), (0.00, 0.18)]],
    "D": [[(0.00, 0.00), (0.00, 1.00), (0.34, 1.00), (0.52, 0.78),
           (0.52, 0.22), (0.34, 0.00), (0.00, 0.00)]],
    "V": [[(0.00, 1.00), (0.26, 0.00), (0.52, 1.00)]],
    "O": [[(0.12, 1.00), (0.40, 1.00), (0.52, 0.78), (0.52, 0.22), (0.40, 0.00),
           (0.12, 0.00), (0.00, 0.22), (0.00, 0.78), (0.12, 1.00)]],
    "L": [[(0.00, 1.00), (0.00, 0.00), (0.52, 0.00)]],
    "M": [[(0.00, 0.00), (0.00, 1.00), (0.36, 0.40), (0.72, 1.00), (0.72, 0.00)]],
    "I": [[(0.08, 1.00), (0.08, 0.00)]],       # centred in its narrow 0.16 advance
    "C": [[(0.52, 0.78), (0.40, 1.00), (0.12, 1.00), (0.00, 0.78),
           (0.00, 0.22), (0.12, 0.00), (0.40, 0.00), (0.52, 0.22)]],
    # ---- added for the connector labels (issue #27): UART, I2C, SPK, BAT, IO ----
    #
    # Every join below is EXACT, and that is a requirement of min_gap rather than tidiness.
    # A stroke that lands part-way along another (A's crossbar, T's stem, R's leg, K's
    # diagonals) is skipped only when their distance is <= 1e-9 — an intentional join that
    # misses by a hundredth reads as the worst possible defect, 0.000mm of material. So the
    # crossbar's ends are computed ON the diagonals, not eyeballed near them:
    #   A's left diagonal is (0,0)->(0.26,1), so at v it sits at u = 0.26v.  At v = 0.30 that
    #   is 0.078, and the right diagonal mirrors to 0.52 - 0.078 = 0.442.
    "U": [[(0.00, 1.00), (0.00, 0.22), (0.12, 0.00), (0.40, 0.00), (0.52, 0.22), (0.52, 1.00)]],
    "A": [[(0.00, 0.00), (0.26, 1.00), (0.52, 0.00)],
          [(0.078, 0.30), (0.442, 0.30)]],       # crossbar LOW on purpose — see the note below
    "R": [[(0.00, 0.00), (0.00, 1.00), (0.34, 1.00), (0.52, 0.82),
           (0.52, 0.68), (0.34, 0.50), (0.00, 0.50)],
          [(0.26, 0.50), (0.52, 0.00)]],         # leg starts ON the bowl's bottom stroke
    "T": [[(0.00, 1.00), (0.52, 1.00)], [(0.26, 1.00), (0.26, 0.00)]],
    "P": [[(0.00, 0.00), (0.00, 1.00), (0.34, 1.00), (0.52, 0.82),
           (0.52, 0.68), (0.34, 0.50), (0.00, 0.50)]],
    # B's WAIST IS 0.42 AND THE CHECK IS WHAT CHOSE IT, TWICE. At the natural 0.66/0.34 the two
    # right-hand verticals sit 0.32 apart, which is 0.86mm of material at h=5.50 — under the
    # floor, and min_gap failed it on the first run. 0.36 fixed that; then the connector labels
    # moved to LABEL_H_CONN = 4.50 and it failed again at 0.72.
    # ⚠️ THE BOUND IS h-DEPENDENT AND THAT IS THE WHOLE TRAP: the glyph is normalised and the
    # stroke is not, so separation >= 2w/h — 0.327 at 5.50, 0.400 at 4.50, 0.474 at LABEL_H_CAP.
    # A glyph that passes at one label height is not thereby safe at another. 0.42 clears
    # 4.50 at 0.99mm; a B on a button cap would still fail, and should.
    "B": [[(0.00, 0.00), (0.00, 1.00), (0.34, 1.00), (0.52, 0.84),
           (0.52, 0.71), (0.34, 0.50), (0.00, 0.50)],
          [(0.34, 0.50), (0.52, 0.29), (0.52, 0.16), (0.34, 0.00), (0.00, 0.00)]],
    "K": [[(0.00, 1.00), (0.00, 0.00)],
          [(0.52, 1.00), (0.00, 0.45), (0.52, 0.00)]],   # both diagonals meet ON the stem
    "2": [[(0.00, 0.78), (0.12, 1.00), (0.40, 1.00), (0.52, 0.78),
           (0.52, 0.62), (0.00, 0.00), (0.52, 0.00)]],
}
# ⚠️ A's CROSSBAR SITS AT 0.30, NOT THE CONVENTIONAL ~0.38, AND IT IS NOT A STYLE CHOICE.
# The counter of an A is a triangle that tapers to nothing at the apex, so min_gap cannot
# score it — the two diagonals share the apex vertex and are skipped, and the crossbar joins
# both exactly and is skipped. NOTHING MEASURES IT. What sets the crossbar height is therefore
# arithmetic done here rather than a number the check will catch:
#
#   perpendicular separation of the diagonals at v  =  0.52*(1-v)*h*cos(atan 0.26)
#   material there                                  =  that, minus w
#
# At h = 5.50 and w = 0.90 the counter is 1.04mm wide at v = 0.30 and closes at v = 0.675 —
# a triangle ~1.0 x 2.1mm, comparable to the M valley this font already ships. At the
# conventional 0.38 it would be 0.81mm at its widest, i.e. UNDER the floor, and every
# instrument in this file would have called it fine.


def ink_size(text: str, h: float, w: float, gap: float) -> tuple[float, float]:
    """(width, height) of the INK -- what a caliper would read, stroke included.

    `h` is the CENTRELINE cap height, so the ink is h + w tall. Keeping the argument on the
    centreline is what makes the pairwise distances below say what they appear to say."""
    return (sum(gw(c) for c in text) * h + (len(text) - 1) * gap + w, h + w)


def text_paths(text: str, h: float, w: float, gap: float) -> list[list[tuple[float, float]]]:
    """Centrelines in mm, in READING space, centred on the ink box.

    Reading space means u runs to the right AS THE LABEL IS READ. On a face seen from -Z that
    is not model +X -- see _back_label() in ember_case.py, which owns the mirror."""
    tw = sum(gw(c) for c in text) * h + (len(text) - 1) * gap
    out, u0 = [], -tw / 2.0
    for ch in text:
        if ch not in GLYPHS:
            raise KeyError(f"no glyph for {ch!r}; this font carries exactly {sorted(GLYPHS)}")
        for poly in GLYPHS[ch]:
            out.append([(u0 + u * h, v * h - h / 2.0) for (u, v) in poly])
        u0 += gw(ch) * h + gap
    return out


def power_paths(r: float, w: float, gap_deg: float, step_deg: float = 6.0):
    """IEC 5009 power symbol: a ring broken at the top, with a bar down the break.

    `gap_deg` is the FULL break angle. It is not a style choice -- it is bounded from below by
    printability, and the bound is derived in ember_case.py where the numbers are known.
    The ring ends sit at +-(90 - gap_deg/2) from +X, so the material between a ring end and
    the bar is r*sin(gap_deg/2) - w, and that has to clear the same floor everything else does.
    """
    half = gap_deg / 2.0
    a0, a1 = 90.0 + half, 450.0 - half          # the long way round, through the bottom
    n = max(2, int(math.ceil((a1 - a0) / step_deg)))
    ring = [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    # Bar top flush with the ring's OUTER ink radius, so the glyph's bounding circle is the
    # ring's and the symbol centres cleanly in a hexagon.
    return [ring, [(0.0, 0.0), (0.0, r)]]


# ---------------------------------------------------------------------------
# INSTRUMENT #2 -- material between strokes, measured exactly
# ---------------------------------------------------------------------------

def _seg_seg_dist(p, q, r, s) -> float:
    """Minimum distance between segments pq and rs. Exact, including the parallel case."""
    def sub(a, b):
        return (a[0] - b[0], a[1] - b[1])

    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1]

    u, v, wv = sub(q, p), sub(s, r), sub(p, r)
    a, b, c = dot(u, u), dot(u, v), dot(v, v)
    d, e = dot(u, wv), dot(v, wv)
    den = a * c - b * b
    if den < 1e-12:                      # parallel (or a degenerate segment)
        sc, tc = 0.0, (e / c if c > 1e-12 else 0.0)
    else:
        sc = max(0.0, min(1.0, (b * e - c * d) / den))
        tc = max(0.0, min(1.0, (a * e - b * d) / den))
    # One clamp is not enough: clamping sc moves the true foot on the other segment.
    for _ in range(2):
        tc = max(0.0, min(1.0, (b * sc + e) / c)) if c > 1e-12 else 0.0
        sc = max(0.0, min(1.0, (b * tc - d) / a)) if a > 1e-12 else 0.0
    dx = (wv[0] + sc * u[0] - tc * v[0], wv[1] + sc * u[1] - tc * v[1])
    return math.hypot(*dx)


def _closest_pair(p, q, r, s):
    """((point on pq, point on rs), distance). Exact, including the parallel case."""
    def sub(a, b):
        return (a[0] - b[0], a[1] - b[1])

    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1]

    u, v, wv = sub(q, p), sub(s, r), sub(p, r)
    a, b, c = dot(u, u), dot(u, v), dot(v, v)
    d, e = dot(u, wv), dot(v, wv)
    den = a * c - b * b
    sc = 0.0 if den < 1e-12 else max(0.0, min(1.0, (b * e - c * d) / den))
    # One clamp is not enough: clamping sc moves the true foot on the other segment.
    for _ in range(2):
        tc = max(0.0, min(1.0, (b * sc + e) / c)) if c > 1e-12 else 0.0
        sc = max(0.0, min(1.0, (b * tc - d) / a)) if a > 1e-12 else 0.0
    pa = (p[0] + sc * u[0], p[1] + sc * u[1])
    pb = (r[0] + tc * v[0], r[1] + tc * v[1])
    return (pa, pb), math.hypot(pa[0] - pb[0], pa[1] - pb[1])


def _seg_seg_dist(p, q, r, s) -> float:
    return _closest_pair(p, q, r, s)[1]


def _point_is_ink(pt, segs, w: float, exclude=()) -> bool:
    """Is `pt` covered by ink from some segment OTHER than the ones in `exclude`?

    ⚠️ `exclude` IS NOT AN OPTIMISATION AND REMOVING IT BLINDS THE CHECK. Without it, the
    midpoint of a gap NARROWER THAN w is within w/2 of both strokes bounding it, so it reads
    as ink and the pair is skipped -- which means the rule silently exempts exactly the gaps
    that are too thin. Both controls proved it: a collapsed S reported `inf` (nothing measured
    at all) and a 30-degree power break reported +1.009mm. The rule was not merely weak there,
    it was strongest-looking precisely where it was blind.

    The question is whether something BRIDGES the gap, and the two strokes forming the gap
    cannot bridge their own gap. Only a third stroke can."""
    half = w / 2.0
    for k, (a, b) in enumerate(segs):
        if k in exclude:
            continue
        if _closest_pair(pt, pt, a, b)[1] <= half:
            return True
    return False


def min_gap(paths, w: float):
    """(thinnest MATERIAL between two strokes, the offending pair). Exact, no rasterising.

    THE RULE, and it is one line: the gap between two strokes is material only if the point
    HALFWAY ACROSS IT is not itself ink.

    That sounds obvious. It took three tries to get here, and the two rules it replaces both
    looked right:

      v1  "skip pairs that share an endpoint."  Three of four labels failed instantly --
          O's top edge vs its right edge read -0.052mm, D's stem vs its bowl 0.392, S's two
          right corners -0.292. Every one of those pairs is bridged by the single chamfer
          BETWEEN them, so the gap is packed with ink. v1 computed the distance between two
          strokes correctly and called it material without ever asking what was in there.

      v2  "skip pairs up to N segments apart along the contour."  This is v1's mistake with
          a dial on it. N=2 still flagged O's counter diagonal (a chain of THREE chamfers);
          N=3 would have swallowed the ring of the power symbol, whose 3-degree subdivision
          puts genuinely-adjacent ink four segments apart. There is no N: N is a proxy for
          "is there ink in between", and the proxy fails at both ends -- too small for a
          chamfered corner, too large for a subdivided arc.

      v3  the midpoint test, but asking "is the midpoint ink" over ALL strokes including the
          two being compared. A gap narrower than w has its own midpoint inside its own two
          strokes, so every genuinely-too-thin gap exempted itself and both controls went
          blind -- see _point_is_ink's `exclude`. A rule can be right about the cases you
          sampled and inverted on the cases you built it for.

    The midpoint test over THIRD strokes only asks the question directly, so it needs no N, no
    tolerance, and no special case for the arc. It also correctly KEEPS the pairs that matter: S's top bar and
    middle bar have clear air between them and are measured; the counter of an O is measured;
    two adjacent letters are measured.

    RETURNS (worst, pair, measured). `measured` is not decoration: a glyph squeezed until its
    counters FUSE has no measurable pair left and `worst` comes back +inf, which reads as a
    pass. An S at h=2.60 does exactly that. Callers must require measured > 0.

    Known and deliberate: an acute concave vertex -- the valley of an M, the inside of a V --
    tapers to zero material at the vertex, and there the midpoint is ink right up to the tip,
    so it is skipped. That is true of every typeface ever cut and is not a defect."""
    allsegs = [(poly[i], poly[i + 1]) for poly in paths for i in range(len(poly) - 1)]
    worst, who, measured = float("inf"), None, 0
    for i in range(len(allsegs)):
        a0, a1 = allsegs[i]
        for j in range(i + 1, len(allsegs)):
            b0, b1 = allsegs[j]
            # Two strokes meeting AT a vertex are one corner of one letter. Their distance is
            # 0 by construction and there is no material between them to measure. This is the
            # one part of v1 that was never in doubt -- dropping it when the midpoint rule
            # went in made all four labels read -0.900mm, which is the corner, not a defect.
            if (_touch(a0, b0) or _touch(a0, b1) or _touch(a1, b0) or _touch(a1, b1)):
                continue
            (pa, pb), dist = _closest_pair(a0, a1, b0, b1)
            # A T-JUNCTION IS NOT A GAP. Sharing an endpoint is not the only way two strokes
            # meet: `A`'s crossbar and `T`'s stem land PART-WAY ALONG another stroke, so
            # _touch misses them and the pair reads as 0.000mm of material -- an intentional
            # join scored as the worst possible defect. Strokes that actually intersect or
            # touch have no material between them by definition.
            #
            # The threshold is EXACT contact, not "close": a real defect sits somewhere in
            # (0, w) and must still be caught, so anything above numerical noise is measured.
            # Widening this to `dist < w` would skip every gap thinner than the stroke, which
            # is the same self-defeating exemption as v3's midpoint rule (see above).
            if dist <= 1e-9:
                continue
            mid = ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0)
            if _point_is_ink(mid, allsegs, w, exclude=(i, j)):
                continue
            measured += 1
            if dist - w < worst:
                worst, who = dist - w, ((a0, a1), (b0, b1))
    return worst, who, measured


def _touch(a, b, eps=1e-9) -> bool:
    return abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps


# ---------------------------------------------------------------------------
# INSTRUMENT #1 -- groove width, by rasterising and handing the mask to granulometry
# ---------------------------------------------------------------------------

def raster(paths, w: float, px: float = 0.05, pad: float = 1.0):
    """Boolean mask of the INK, for tools/minfeature.min_feature(mask, px)."""
    import numpy as np

    xs = [p[0] for poly in paths for p in poly]
    ys = [p[1] for poly in paths for p in poly]
    x0, x1 = min(xs) - w - pad, max(xs) + w + pad
    y0, y1 = min(ys) - w - pad, max(ys) + w + pad
    nx, ny = int(math.ceil((x1 - x0) / px)), int(math.ceil((y1 - y0) / px))
    gx = x0 + (np.arange(nx) + 0.5) * px
    gy = y0 + (np.arange(ny) + 0.5) * px
    X, Y = np.meshgrid(gx, gy)
    mask = np.zeros(X.shape, dtype=bool)
    for poly in paths:
        for i in range(len(poly) - 1):
            (ax, ay), (bx, by) = poly[i], poly[i + 1]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 < 1e-12:
                t = np.zeros_like(X)
            else:
                t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0.0, 1.0)
            mask |= ((X - (ax + t * dx)) ** 2 + (Y - (ay + t * dy)) ** 2) <= (w / 2.0) ** 2
    return mask


def selftest() -> int:
    """A check that has never produced a positive is not evidence (verification.md S13)."""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from minfeature import min_feature

    W, GAP = 0.90, 1.90
    H_CAP, H_FLAT = 3.80, 5.50       # cap-face labels vs flat-back labels; see ember_case.py
    bad = 0

    # -- MATERIAL, and its CONTROLS. Two controls, because there are two ways to be thin.
    for text, h in (("VOL", H_CAP), ("SD", H_FLAT), ("MIC", H_FLAT),
                    # the connector set (#27). Every new glyph appears in at least one.
                    ("UART", H_FLAT), ("I2C", H_FLAT), ("SPK", H_FLAT),
                    ("BAT", H_FLAT), ("IO", H_FLAT)):
        d, _, n = min_gap(text_paths(text, h, W, GAP), W)
        print(f"  material  {text:<4} h={h:.2f}  {d:6.3f}mm  ({n} pairs measured)")
        if d < 0.90 or n == 0:
            print(f"    FAIL {text} at h={h}: "
                  + ("no measurable pair -- counters have fused" if n == 0
                     else "below the 0.90 floor"))
            bad += 1
    d_pw, _, n_pw = min_gap(power_paths(2.70, W, 84.0), W)
    print(f"  material  power      {d_pw:6.3f}mm   (ring end to bar)")
    if d_pw < 0.90 or n_pw == 0:
        print("    FAIL the power symbol's break is too narrow for its bar")
        bad += 1
    for what, paths, why in (
            ("S@h=3.20", text_paths("S", 3.20, W, GAP), "counters pinched"),
            ("S@h=2.60", text_paths("S", 2.60, W, GAP), "counters FUSED -> n=0"),
            ("SD gap=1.00", text_paths("SD", H_FLAT, W, 1.00), "letters jammed"),
            ("power gap=30", power_paths(2.70, W, 30.0), "break too narrow"),
            # ⚠️ A REAL DEFECT THIS CHECK CAUGHT, kept as the control for the glyph it caught
            # it in. B's two right-hand verticals were 0.32 apart, which is 0.86mm of material
            # at flat-back height; the waist is 0.36 now. Shrinking the label to cap height
            # reproduces the same failure, because the bound scales as 2w/h.
            ("BAT@h=3.80", text_paths("BAT", H_CAP, W, GAP), "B's waist closes at cap height")):
        d, _, n = min_gap(paths, W)
        ok = d < 0.90 or n == 0
        print(f"  control   {what:<12} {d:6.3f}mm n={n:<3d} ({why}) -> "
              f"{'DETECTOR WORKS' if ok else 'DETECTOR IS BLIND'}")
        if not ok:
            bad += 1

    # -- GROOVE, and its CONTROL. Granulometry should read the groove back as `w`; a
    #    deliberately thin groove should read back thin.
    for probe_w, want in ((W, W), (0.40, 0.40)):
        mf = min_feature(raster(text_paths("SD", H_FLAT, probe_w, GAP), probe_w, px=0.02), 0.02)
        ok = abs(mf - want) <= 0.08
        print(f"  groove    w={probe_w:.2f} -> min_feature {mf:.3f}mm  {'ok' if ok else 'MISREAD'}")
        if not ok:
            bad += 1

    print("strokefont selftest:", "PASS" if not bad else f"{bad} FAILURE(S)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
