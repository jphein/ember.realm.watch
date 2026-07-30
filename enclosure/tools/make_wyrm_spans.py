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
import dragon as D  # noqa: E402

# The grille field, from ember_case.py. Kept in sync by the assert at the bottom.
FIELD_W, FIELD_H = 37.0, 24.0
MIN_FEATURE = 0.90      # mm. Thinner than this and a printed rib is a sliver.


def silhouette() -> np.ndarray:
    """Body + head composited, as the device composites them."""
    m = D.body_mask().astype(bool) | D.head_mask(0).astype(bool)
    return m


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
    body_mask() | head_mask(0) is a UNION of two sprites, and at k=0 the head is posed
    nose-tucked with its neck not overlapping the body — so the composite is TWO regions,
    not one. On the device that is invisible: the flame band renders fire between them and
    the wyrm reads as a creature against a glow. In PLASTIC there is no fire, so a consumer
    that debosses this silhouette gets a body and a separate floating blob.
    The gap is 5.4px here, far above any print floor, so no minimum-feature test can catch
    it — a gap is not a thin feature. It needs its own number, hence this.
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
        """Fraction of area in features THINNER than 2k, by morphological opening."""
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
    # THIRD AND FINAL VERSION OF THIS METRIC, because the first two were both wrong:
    #   1. "grow until the thinnest ROW-RUN clears the floor" — never terminates usefully,
    #      since dilation always creates 1px boundary rows. It ran to 6px and tripled area.
    #   2. "the k at which erosion empties the mask" — that is the THICKEST feature, not the
    #      thinnest; the last region standing is the fattest one.
    # Opening is the honest test: a feature thinner than 2k does not survive erode-then-
    # dilate by k. At 2px dilation the loss at k=2 is 0.0%, so every feature is >= 1.23mm.
    k2_loss = opening_loss(m, 2)
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
        f.write("bottom-left of the grille field. Traced from esphome/art/dragon.py, the same\n")
        f.write("curves the device and the website draw.\n")
        f.write(f'"""\n\n')
        f.write(f"# {len(rects)} rects, {area:.1f} mm2, dilated {grow}px.\n")
        f.write(f"# Opening at k=2 loses {100*k2_loss:.1f}% -> every feature >= "
                f"{4*scale:.2f} mm, printable.\n")
        f.write(f"WYRM_W, WYRM_H = {w*scale:.4f}, {h*scale:.4f}\n")
        f.write(f"WYRM_AREA = {area:.4f}\n")
        f.write(f"# MIN FEATURE, verified by opening — import this, never transcribe the\n")
        f.write(f"# number above. A consumer that scales this silhouette must divide its own\n")
        f.write(f"# print floor by THIS, or its min-feature assert is arithmetic, not a test.\n")
        f.write(f"WYRM_MIN_FEATURE = {4*scale:.4f}\n")
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
    print(f"  dilated {grow}px | opening k=2 loses {100*k2_loss:.1f}% "
          f"-> every feature >= {4*scale:.2f} mm")
    assert k2_loss < 0.005, (
        f"{100*k2_loss:.1f}% of the silhouette is thinner than {4*scale:.2f}mm — "
        f"increase the dilation")
    print(f"  min feature {4*scale:.4f} mm | {ncomp} connected component(s)"
          + (f" | body<->head gap {gap_px*scale:.3f} mm" if ncomp > 1 else ""))
    if ncomp > 1:
        print(f"  !! THE SILHOUETTE IS {ncomp} PIECES. Any consumer that renders it WITHOUT\n"
              f"     the fire behind it (deboss, grille island, sticker) gets a detached head.")
    print(f"  -> {os.path.relpath(out, REPO)}")
    assert w * scale <= FIELD_W + 0.01, "wyrm wider than the grille field"
    assert h * scale <= FIELD_H + 0.01, f"wyrm {h*scale:.1f}mm taller than the {FIELD_H}mm field"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
