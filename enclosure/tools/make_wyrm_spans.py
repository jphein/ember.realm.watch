"""
Emit the hearth-wyrm silhouette as mm-space rectangles for the stand's grille.

ONE CREATURE, RENDERED THREE WAYS. `esphome/art/dragon.py` is the source of the wyrm's
curves: the device renders them as RLE spans shaded per-pixel, the website traces the same
grid into SVG, and this turns them into geometry for the grille. They are not three drawings
that resemble each other — re-pose the wyrm in dragon.py and all three follow.

Run:  ../cadenv/bin/python tools/make_wyrm_spans.py   (writes wyrm_spans.py beside it)
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "esphome", "art"))
sys.path.insert(0, HERE)
import dragon as D  # noqa: E402
import minfeature as MF  # noqa: E402  -- the min-feature metric, with its control

# The grille field, from ember_case.py. Kept in sync by the assert at the bottom.
FIELD_W, FIELD_H = 37.0, 24.0
MIN_FEATURE = 0.90      # mm. Thinner than this and a printed rib is a sliver.


def silhouette(k: float = 0.0, jaw: float = 0.0) -> np.ndarray:
    """Body + NECK + head, composited as the DEVICE actually composites them.

    >>> THIS USED TO BE `body_mask() | head_mask(0)` AND THAT WAS TWO BUGS. <<<
    The result was a mark in TWO disconnected pieces — a body and a head floating 1.660mm
    away (1.215mm once scaled onto the bezel), which is far above any print floor, so it
    printed as a gap. Both causes are in what the one-liner left out:

      1. `head_mask()` returns the head SPRITE IN ITS OWN FRAME, sitting at dragon-local
         (0,0) — bbox x0..26, y0..13. It is not posed. The device translates it by
         HEAD_POS_SLEEP..HEAD_POS_ALERT interpolated on wakefulness k. Unioning it raw put
         the head at (0,0), which is neither pose and is nowhere near the shoulder.
      2. `dragon.py` draws the neck with its own function, `neck_spans()` (a tapered
         capsule chain, SHOULDER -> head), and the device composites it at the same time as
         the body and head. It is not a *_mask() function, so `body|head` misses it
         entirely. The creature has no neck.

    WHY NOBODY CAUGHT IT: on the device the flame band renders FIRE in the gap, so the wyrm
    reads as a creature against a glow and the missing neck is invisible. In plastic nothing
    fills it. And A GAP IS NOT A THIN FEATURE — the minimum-feature test measures how thin
    the material gets, never how far apart two pieces are, so 1.23mm and 0.19% opening loss
    were both true and both blind. That is why components are now measured and asserted
    separately; see components() and the assert in main().

    Composited properly the mark is ONE piece and, at k=0, 5.7% SMALLER than the broken
    version (193.4 vs 205.0 mm2) — because the head lands tucked against the body instead of
    floating off in the corner. Joining it by dilation instead would have taken 5px and +43%
    area, the trade the DILATION IS A TRADE note below explicitly warns against.

    k = wakefulness: 0 asleep (nose tucked to the chest), 1 alert (head raised, neck
    extended). k=0 for a static mark — it is the most compact of the three and nothing
    clips the canvas edge, where k=1 puts the head hard against x=0.
    """
    hx = D.HEAD_POS_SLEEP[0] + (D.HEAD_POS_ALERT[0] - D.HEAD_POS_SLEEP[0]) * k
    hy = D.HEAD_POS_SLEEP[1] + (D.HEAD_POS_ALERT[1] - D.HEAD_POS_SLEEP[1]) * k
    hx, hy = int(round(hx)), int(round(hy))

    lo, hi, _ = D.neck_spans(hx, hy)          # same maths the display lambda uses
    neck = np.zeros((D.DH, D.DW), dtype=bool)
    for r in range(D.DH):
        if hi[r] > lo[r]:
            neck[r, lo[r]:hi[r]] = True

    sprite = D.head_mask(jaw).astype(bool)    # jaw_drop, NOT wakefulness
    head = np.zeros((D.DH, D.DW), dtype=bool)
    ys, xs = np.nonzero(sprite)
    yy, xx = ys + hy, xs + hx
    ok = (yy >= 0) & (yy < D.DH) & (xx >= 0) & (xx < D.DW)
    head[yy[ok], xx[ok]] = True

    return D.body_mask().astype(bool) | neck | head


def thicken(m: np.ndarray, px: int) -> np.ndarray:
    """Grow the mask by `px` in each direction — 4-connected, repeated."""
    out = m.copy()
    for _ in range(px):
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        out = g
    return out


def components(m: np.ndarray):
    """(count, nearest_gap_px) for the 8-connected components of the mask.

    >>> EXPORTED BECAUSE "IS THIS ONE CREATURE?" IS NOT A SAFE ASSUMPTION. <<<
    It WAS false. `body_mask() | head_mask(0)` unioned an unposed head sprite onto the body
    and omitted neck_spans() entirely, so the silhouette was TWO regions 5.4px apart — see
    silhouette() for both causes. It is one region now, and main() asserts that.

    This stays exported and asserted because the failure was invisible to every other check
    in the file: on the device the flame band renders fire between the pieces, and A GAP IS
    NOT A THIN FEATURE, so the minimum-feature test — which measures how thin material gets,
    never how far apart two pieces are — reported 1.23mm and 0.0% loss while the mark was
    broken. A property no existing metric can express needs its own number.
    """
    from collections import deque
    h, w = m.shape
    seen = np.zeros_like(m)
    comps = []
    for (sy, sx) in np.argwhere(m):
        if seen[sy, sx]:
            continue
        q, P = deque([(sy, sx)]), []
        seen[sy, sx] = True
        while q:
            y, x = q.popleft()
            P.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
        comps.append(np.array(P))
    comps.sort(key=len, reverse=True)
    gap = 0.0
    if len(comps) > 1:
        A, B = comps[0], comps[1]
        gap = min(math.dist(a, b) for a in A for b in B)
    return len(comps), gap


def runs(row: np.ndarray):
    """[(x0, x1_exclusive), …] for the True runs in one row."""
    out, x = [], 0
    n = len(row)
    while x < n:
        if row[x]:
            s = x
            while x < n and row[x]:
                x += 1
            out.append((s, x))
        else:
            x += 1
    return out


def main() -> int:
    m = silhouette()
    h, w = m.shape
    scale = FIELD_W / w                      # mm per px

    # THICKEN A LITTLE, AND MEASURE THE RIGHT THING.
    #
    # A first attempt grew the mask until the thinnest ROW-RUN cleared the floor. That
    # metric is wrong and it ran away: growing a shape always creates new boundary rows
    # one pixel wide at the extremities, so the thinnest run never improves however much
    # you grow. It reached 6px and tripled the silhouette's area (113 -> 318 mm2), which
    # would have cost a third of the grille.
    #
    # The honest measure of "can this print" is EROSION: if eroding by k pixels deletes a
    # region, that region was at most 2k thick. Grow by one pixel for a clean edge, then
    # report the true minimum thickness so the number in the header is meaningful.
    # DILATION IS A TRADE, and the numbers decide it rather than taste:
    #   1px -> area 170mm2, thinnest feature 0.62mm  (tail tip below the print floor)
    #   2px -> see the header of the generated file
    # Every millimetre of silhouette is a millimetre of grille that is no longer open, so
    # dilate the minimum that makes the creature printable and no more.
    m = thicken(m, 2)

    def opening_loss(mask, k):
        """Fraction of area in features thinner than 2k px — 4-CONNECTED, i.e. WRONG.

        Kept only so the generated header can report what the old number was. Do not use it
        to decide anything: its structuring element is an L1 diamond, so it is right across
        the axes and up to 29% narrow across the diagonals. See minfeature.py.
        """
        e = mask.copy()
        for _ in range(k):
            t = e.copy()
            t[1:, :] &= e[:-1, :]; t[:-1, :] &= e[1:, :]
            t[:, 1:] &= e[:, :-1]; t[:, :-1] &= e[:, 1:]
            e = t
        o = e
        for _ in range(k):
            t = o.copy()
            t[1:, :] |= o[:-1, :]; t[:-1, :] |= o[1:, :]
            t[:, 1:] |= o[:, :-1]; t[:, :-1] |= o[:, 1:]
            o = t
        return (mask.sum() - o.sum()) / max(mask.sum(), 1)

    grow = 2
    # FOURTH VERSION OF THIS METRIC. The first three were all wrong, and the third is the one
    # that used to live in this function:
    #   1. "grow until the thinnest ROW-RUN clears the floor" — never terminates usefully,
    #      since dilation always creates 1px boundary rows. It ran to 6px and tripled area.
    #   2. "the k at which erosion empties the mask" — that is the THICKEST feature, not the
    #      thinnest; the last region standing is the fattest one.
    #   3. opening with a 4-CONNECTED element — right idea, wrong ball. It is anisotropic (see
    #      minfeature.py) and it under-reports at the bin edge, so "1.23mm" below was never a
    #      measurement of this shape at all: 4*scale is FOUR PIXELS, a statement about the grid.
    # Opening with a EUCLIDEAN DISC, with the thickness read off the distance transform, is the
    # honest test. minfeature.selftest() proves it on planted ribs — including a diagonal one,
    # which is what caught metric 3 — on every run, because a detector that has not detected
    # anything today is not known to work.
    MF.selftest()
    k2_loss = opening_loss(m, 2)                    # the OLD number, reported for comparison
    min_bound = 4 * scale                           # the OLD contract: a conservative bound
    min_true = MF.min_feature(m, scale, ceiling_mm=20 * scale)
    # THE BOUND MUST ACTUALLY BE A BOUND. Never once checked until now, and it is the property
    # every consumer of WYRM_MIN_FEATURE silently depends on: scaling by floor/bound only
    # guarantees >= floor if the true minimum is >= bound. It is, by 4.3x.
    assert min_true >= min_bound - 1e-9, (
        f"WYRM_MIN_FEATURE={min_bound:.4f}mm is NOT a lower bound — the silhouette's true "
        f"thinnest feature is {min_true:.4f}mm, so a consumer scaling by floor/{min_bound:.4f} "
        f"gets features BELOW its print floor")
    ncomp, gap_px = components(m)

    rects = []
    for y in range(h):
        for (x0, x1) in runs(m[y]):
            rects.append((round(x0 * scale, 4), round((h - 1 - y) * scale, 4),
                          round((x1 - x0) * scale, 4), round(scale, 4)))

    area = sum(r[2] * r[3] for r in rects)

    out = os.path.join(HERE, "wyrm_spans.py")
    with open(out, "w") as f:
        f.write('"""GENERATED by tools/make_wyrm_spans.py — do not edit.\n\n')
        f.write("The hearth-wyrm silhouette as (x, y, w, h) rectangles in mm, origin at the\n")
        f.write("bottom-left of the canvas. BODY + NECK + POSED HEAD, exactly as the device\n")
        f.write("composites them -- see silhouette() for the two bugs that made this a\n")
        f.write("two-piece mark with no neck.\n")
        f.write("bottom-left of the grille field. Traced from esphome/art/dragon.py, the same\n")
        f.write("curves the device and the website draw.\n")
        f.write(f'"""\n\n')
        f.write(f"# {len(rects)} rects, {area:.1f} mm2, dilated {grow}px, "
                f"canvas {w}x{h}px at {scale:.4f} mm/px.\n")
        f.write(f"WYRM_W, WYRM_H = {w*scale:.4f}, {h*scale:.4f}\n")
        f.write(f"WYRM_AREA = {area:.4f}\n")
        f.write(f"# MIN FEATURE. TWO NUMBERS, BECAUSE THEY ARE NOT THE SAME THING AND THE\n")
        f.write(f"# DIFFERENCE USED TO BE HIDDEN.\n")
        f.write(f"#\n")
        f.write(f"# WYRM_MIN_FEATURE is the CONSUMER CONTRACT and a conservative LOWER BOUND:\n")
        f.write(f"# scale this silhouette by (your print floor / this) and every feature comes\n")
        f.write(f"# out at or above your floor. It is 4*px = four pixels of the canvas, so it\n")
        f.write(f"# is a statement about the GRID, not a measurement of the shape -- which is\n")
        f.write(f"# why it errs safe. Erring safe is the whole reason it is still here.\n")
        f.write(f"#\n")
        f.write(f"# WYRM_MIN_FEATURE_MEASURED is the shape's ACTUAL thinnest feature, by\n")
        f.write(f"# Euclidean-disc opening with the thickness read off the distance transform\n")
        f.write(f"# (tools/minfeature.py, whose control runs on every regeneration). The build\n")
        f.write(f"# asserts MEASURED >= WYRM_MIN_FEATURE, i.e. that the bound IS a bound -- a\n")
        f.write(f"# check nobody had ever run.\n")
        f.write(f"#\n")
        f.write(f"# THE GAP MATTERS TO CONSUMERS: it is {min_true/min_bound:.2f}x, so a\n")
        f.write(f"# consumer scaling by floor/{min_bound:.4f} gets a mark whose thinnest\n")
        f.write(f"# feature is {min_true/min_bound:.2f}x its floor, not equal to it. Anything\n")
        f.write(f"# that reports `WYRM_MIN_FEATURE * s` as the result is ARITHMETIC, NOT A\n")
        f.write(f"# TEST -- it returns the floor by construction whatever the shape does.\n")
        f.write(f"# Use MEASURED * s for that.\n")
        f.write(f"WYRM_MIN_FEATURE = {min_bound:.4f}\n")
        f.write(f"WYRM_MIN_FEATURE_MEASURED = {min_true:.4f}\n")
        f.write(f"# The old 4-connected metric, kept only for comparison: it reported the loss\n")
        f.write(f"# at k=2 as {100*k2_loss:.1f}%. It is anisotropic -- see minfeature.py.\n")
        f.write(f"# CONNECTED COMPONENTS of the silhouette. {ncomp} means the mark is NOT one\n")
        f.write(f"# piece: body_mask()|head_mask(0) unions two sprites and the k=0 head pose\n")
        f.write(f"# leaves the neck clear of the body. On screen the fire fills the gap; in\n")
        f.write(f"# plastic nothing does. A gap is not a thin feature, so no minimum-feature\n")
        f.write(f"# test can see it.\n")
        f.write(f"WYRM_COMPONENTS = {ncomp}\n")
        f.write(f"WYRM_COMPONENT_GAP = {gap_px*scale:.4f}   # mm, largest two components\n")
        f.write("WYRM = [\n")
        for r in rects:
            f.write(f"    {r},\n")
        f.write("]\n")

    print(f"  {len(rects)} rects  |  {w*scale:.1f} x {h*scale:.1f} mm  |  area {area:.1f} mm2")
    print(f"  dilated {grow}px | bound 4*px = {min_bound:.4f} mm | MEASURED min feature "
          f"{min_true:.4f} mm ({min_true/min_bound:.2f}x the bound)")
    print(f"  old 4-connected metric, for comparison: k=2 loses {100*k2_loss:.1f}%")
    assert k2_loss < 0.005, (
        f"{100*k2_loss:.1f}% of the silhouette is thinner than {min_bound:.2f}mm — "
        f"increase the dilation")
    print(f"  {ncomp} connected component(s)"
          + (f" | body<->head gap {gap_px*scale:.3f} mm" if ncomp > 1 else ""))
    if ncomp > 1:
        print(f"  !! THE SILHOUETTE IS {ncomp} PIECES. Any consumer that renders it WITHOUT\n"
              f"     the fire behind it (deboss, grille island, sticker) gets a detached head.")
    # ONE PIECE IS NOW ACHIEVABLE, SO REQUIRE IT. This is not a style rule: a consumer that
    # cuts this silhouette in plastic has no fire to fill a gap, and no minimum-feature test
    # can see one. Re-pose the wyrm and this is the assert that tells you the neck let go.
    assert ncomp == 1, (
        f"the silhouette is {ncomp} pieces with a {gap_px*scale:.3f}mm gap — the head is "
        f"detached. Check silhouette(): the head must be POSED and the neck composited.")
    print(f"  -> {os.path.relpath(out, REPO)}")
    assert w * scale <= FIELD_W + 0.01, "wyrm wider than the grille field"
    assert h * scale <= FIELD_H + 0.01, f"wyrm {h*scale:.1f}mm taller than the {FIELD_H}mm field"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
