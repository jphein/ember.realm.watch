"""Minimum-feature measurement, done honestly. ONE implementation, imported not copied.

>>> THIS IS THE FOURTH METRIC THIS PROJECT HAS USED, AND THE FIRST WITH A CONTROL. <<<

The three before it all returned confident wrong numbers. The first two are recorded in
make_wyrm_spans.py and docs/verification.md; the third is the one that made this file:

  1. "Grow until the thinnest ROW-RUN clears the floor" — never terminates usefully. Dilation
     always creates 1px boundary rows, so the measure never improves. It ran to 6px and
     TRIPLED the silhouette's area.
  2. "The k at which erosion empties the mask" — that is the THICKEST feature. The last region
     standing is the fattest one. It cleared a 0.6mm tail tip as though it were 4.9mm.
  3. "Opening with a 4-CONNECTED structuring element" — right idea, wrong ball, and wrong in a
     way that is invisible at the call site. A 4-connected k-step ball is an L1 DIAMOND, whose
     width in direction n is 2*k*px*max(|nx|,|ny|): full across the axes and only 1.41*k*px
     across the diagonals. So it measures an axis-aligned wall correctly and passes a diagonal
     one up to 29% thinner. It was validated on the wyrm silhouette, which is axis-aligned
     pixel art, and then reused on the enclosure — 15deg slot faces, 24deg raked grille bores,
     hex webs at 0/60/120deg. Of the back panel's 226 webs, 186 have 60deg normals.
     It reported the stand's 0.900mm grille web as 0.75 and the shell's 0.800mm panel web as
     0.60, and two agents went looking for a structural sliver that was a documented print
     floor with a bad ruler held against it.

     It also under-reports AT the bin edge, so the documented caveat "0.60 means [0.60, 0.75)"
     points the wrong way: a band survives erosion by k only if its RASTERISED width exceeds
     2*k*px everywhere along it, so the true value can be ABOVE the bin, not inside it.

WHAT THIS CANNOT ANSWER, WRITTEN HERE BECAUSE THIS IS WHERE IT GETS REACHED FOR.
This measures the thinnest part OF THE MASK YOU HAND IT. It does not measure the thinnest
MATERIAL BETWEEN parts of the mask, and it cannot be made to by passing the complement,
because the metric is AREA-AVERAGED: it reports the largest disc-opening that loses no more
than `tol` of the region. On a complement the region is dominated by the unbounded surround,
so a disc that completely annihilates a letter's counter costs a fraction of a percent and
PASSES. Framing the complement tightly helps and is not enough -- at the `tol` needed to
tolerate the unavoidable taper at an acute concave vertex, a deliberately-collapsed S still
came back +1.560mm.

This is recorded because it was recommended, in a handoff, for exactly that job: "reusable and
carries its own control" -- the tool was checked for EXISTENCE and not for SENSITIVITY to the
defect it was being pointed at. Having a control proves an instrument can fire at something;
it does not prove it can fire at YOUR something. For material between strokes use exact
pairwise segment distance -- tools/strokefont.py `min_gap()` -- which has no tolerance, no
rasterisation, and never looks at the surround.

WHAT THIS DOES INSTEAD. Opening was always the right idea; only the ball was wrong.

  * OPEN WITH A EUCLIDEAN DISC, exactly, via two distance transforms: a disc of radius r fits
    at p iff EDT(mask)[p] >= r, and the opening is everything within r of that set. Isotropic,
    O(n), and any real radius is available so there is no 2k*px ladder to caveat.
  * READ THE THICKNESS OFF THE DISTANCE TRANSFORM, not off the threshold that found it.
    2*max(EDT) inside a located region IS its local thickness, continuous-valued. Measured that
    way the two enclosure webs come out at 0.900 and 0.808 against declared 0.90 and 0.80 —
    errors of 0 and 8 micrometres.
  * LOCATE, don't just score. A minimum with no coordinates cannot be attributed, and a
    z-range is not a finding. Labelled regions each carry their own extent and thickness.
  * AN AREA FLOOR, stated rather than hidden: opening a sharp convex corner always loses
    ~0.21*r^2 of it. Those artefacts are a few hundredths of a mm2; a real rib is 100x that.

  * AND A POSITIVE CONTROL, run by selftest(), which plants ribs of known width and
    ORIENTATION and requires them found at that width. The 45deg rib is the point: it is what
    caught metric 3, on the first run, before the metric could be trusted with a real part.
    None of the three wrong metrics was ever checked against a shape whose answer was known.

KNOWN LIMITATION OF THIS METRIC, stated here rather than discovered by the next person.

  A SMOOTH SURFACE RUNNING NEARLY TANGENT TO THE VOXEL GRID PRODUCES A FALSE THIN REGION.
  Rasterising a smooth convex boundary makes a staircase, and a staircase is locally CONCAVE
  at every riser — so opening by a disc clips the outer edge of the long shallow treads that
  appear where the surface is almost parallel to the grid. On the stand this shows up at the
  left rear corner, where the R10 arc leaves the straight side x=0 tangentially: 0.36mm2 per
  layer over the full 40mm height, reported at t=0.618mm. IT IS NOT THIN MATERIAL. The solid
  runs continuously from x=0.00 to x=63.90 behind it.

  THE DISCRIMINATOR IS VOID ON BOTH SIDES. A real thin feature has void within ~the threshold
  on two opposing sides; a tangency artefact has void on one side and the whole part on the
  other. So before believing any region, check what backs it — which is what bounding-surface
  extraction from the mesh does, and why locating beats scoring.

  This is the same family as the tangential-slice artefact in Z that this project already
  recorded (a layer sliced flush with a horizontal face yields a one-pixel sheet), arriving in
  XY instead. Every discretised metric has a direction in which it lies; the fix is to know
  which one, not to believe the metric has none.
"""
from __future__ import annotations

import math

import numpy as np
import scipy.ndimage as nd

# AREA FLOOR, DERIVED FROM THE THRESHOLD RATHER THAN TYPED IN PIXELS.
#
# Opening a sharp convex corner always removes about (1 - pi/4)*r^2 ~= 0.215*r^2 of it, so a
# threshold-proportional floor rejects those artefacts at every scale. 2*r^2 is ~9x the corner
# loss and still ~1/100 of any real rib.
#
# It was `AREA_FLOOR_PX = 44  # ~0.25 mm2 at px=0.075` first, and that was wrong for exactly
# the reason this file exists: a constant calibrated at one scale, presented as scale-free. The
# enclosure grids at px=0.075 where 44px is 0.25mm2; the wyrm silhouette grids at px=0.3083
# where the same 44px is 4.18mm2 — a floor 17x larger, which swallowed the tail extremities and
# reported a minimum four times too coarse. A pixel count is not a tolerance.
def area_floor_mm2(thr_mm: float, px: float) -> float:
    r = thr_mm / 2.0
    return max(2.0 * r * r, 3.0 * px * px)


def edt(mask: np.ndarray) -> np.ndarray:
    """Distance, in pixels, from each True cell to the nearest False cell.

    Padded with one False cell so a feature touching the array border is measured against the
    border. Unpadded, scipy reports a wall that runs off the edge of the grid as arbitrarily
    thick — which is the same "measured against nothing" fault as counting edges on an empty
    object.
    """
    p = np.pad(mask, 1, constant_values=False)
    return nd.distance_transform_edt(p)[1:-1, 1:-1]


def open_disc(mask: np.ndarray, r_px: float) -> np.ndarray:
    """Morphological opening by a Euclidean disc of radius r_px, exactly."""
    core = edt(mask) >= r_px
    if not core.any():
        return np.zeros_like(mask)
    p = np.pad(core, 1, constant_values=False)
    return (nd.distance_transform_edt(~p)[1:-1, 1:-1] <= r_px) & mask


def thin_regions(mask, px, thr_mm, floor_mm2=None):
    """Material in features thinner than thr_mm, as labelled regions with true thicknesses.

    Returns [{thick_mm, area_mm2, x:(lo,hi), y:(lo,hi)}, ...] thinnest first. `thick_mm` is
    2*max(EDT) inside the region — the measurement, not the threshold that found it.
    """
    floor = area_floor_mm2(thr_mm, px) if floor_mm2 is None else floor_mm2
    sliver = mask & ~open_disc(mask, (thr_mm / 2.0) / px)
    if not sliver.any():
        return []
    d = edt(mask)
    lab, n = nd.label(sliver)
    out = []
    for i in range(1, n + 1):
        sel = lab == i
        cnt = int(sel.sum())
        if cnt * px * px < floor:
            continue
        xs, ys = np.nonzero(sel)
        out.append(dict(thick_mm=float(2.0 * d[sel].max() * px),
                        area_mm2=cnt * px * px,
                        x=(float(xs.min() * px), float((xs.max() + 1) * px)),
                        y=(float(ys.min() * px), float((ys.max() + 1) * px))))
    out.sort(key=lambda r: r["thick_mm"])
    return out


def opening_loss(mask, thr_mm, px):
    """Fraction of area in features thinner than thr_mm, by EUCLIDEAN-DISC opening."""
    tot = mask.sum()
    if not tot:
        return 0.0
    return float((tot - open_disc(mask, (thr_mm / 2.0) / px).sum()) / tot)


def min_feature(mask, px, tol=0.005, hi_mm=None, iters=40):
    """Minimum feature size, by GRANULOMETRY: the largest threshold whose disc-opening
    loses no more than `tol` of the area. Bisected, so continuous-valued.

    >>> THIS IS THE SECOND VERSION OF THIS FUNCTION AND THE FIRST ONE WAS METRIC #2 AGAIN. <<<
    It used to take the ceiling as a threshold, label the thin set, and return 2*max(EDT)
    inside it. On a rib that is exactly right — the region IS the rib, so max(EDT) is half its
    thickness, and that is where the enclosure's 0.900mm and 0.808mm webs come from.
    On a WHOLE OBJECT it is nonsense, and nothing stopped the threshold exceeding the object:

        the wyrm silhouette is 50 px tall; the default ceiling was 20*px, so opening by a
        10 px disc removed 2034 of 2034 px -- 100.0% of the creature. `2*max(EDT)` over that
        set returned 5.2688 mm, which is EXACTLY the creature's own thickest half-width
        doubled. It reported the fattest point in the shape as its thinnest feature, and I
        emitted it into a generated file and a commit message.

    That is failure #2 in the docstring above -- "the last region standing is the fattest one"
    -- committed by the author of that sentence. Knowing a failure mode does not confer
    immunity to it; only a control that can express it does. selftest() now has one.

    So the global entry point no longer takes a max over anything. Granulometry asks the same
    question the original 4-connected metric asked, with the right ball, and it cannot return a
    number larger than the feature that actually failed.

    ON THE TOLERANCE, because it is doing real work and hiding a real limit: rasterising a
    smooth boundary leaves single-pixel staircase corners, and those are genuinely thinner than
    anything in the shape. On the wyrm they are 13 regions totalling ~1.4mm2 of 193mm2, so the
    loss sits on a 0.79% plateau from 0.90mm all the way to 1.5mm and `tol` is what steps over
    them. A returned value inside such a plateau is therefore a BOUND, not a measurement of the
    shape -- and no answer below 2*px means anything at all, because the grid cannot see it.
    Report the pixel size next to the result or the result is not interpretable.
    """
    lo = 2.0 * px
    hi = float(hi_mm) if hi_mm is not None else float(max(mask.shape) * px)
    if opening_loss(mask, lo, px) > tol:
        return lo                       # cannot resolve anything: grid-limited
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if opening_loss(mask, mid, px) <= tol:
            lo = mid
        else:
            hi = mid
    return lo


def thinnest_feature(mask, px, min_px=1.5):
    """The thinnest feature in `mask`, in mm, THRESHOLD-FREE: 2x the smallest EDT ridge value.

    >>> THIRD VERSION OF THIS FUNCTION. THE FIRST TWO WERE BOTH WRONG, EACH IN A WAY THE
    >>> CONTROL BEFORE IT COULD NOT EXPRESS. <<<

      v1, max-over-blob at a fixed ceiling: on a rib it is exact, on a whole object it returns
          the FATTEST point. It reported the wyrm silhouette's thickest half-width doubled
          (5.2688mm) as its thinnest feature, because at r=10px a 50px-tall creature does not
          survive opening at all and every pixel became one region. Metric #2, recommitted by
          the author of the sentence warning about metric #2.
      v2, sweep the threshold upward and take the first region: fixes the whole-object case and
          introduces a quieter error. Below the true thickness a feature is only PARTIALLY
          opened, so what appears first is its 1-2px EDGE SHELL, whose max EDT is a fraction of
          the real thickness. On a planted 0.600mm rib it returned 0.450. Granulometry
          under-reads the same rib for the same reason, which is why both agreed and both were
          wrong.
      v2 also carried a max_frac guard meant to reject "the region is the object", and the
          control caught THAT too: in a shape where the thin rib is legitimately most of the
          area, the guard rejected the answer. A crude proxy for "void on both sides" rejects
          real features as readily as artefacts.

    So: NO THRESHOLD AT ALL. The thickness of a feature at its medial axis is 2*EDT, so the
    thinnest feature is twice the smallest RIDGE value of the distance transform — a pixel whose
    EDT is a local maximum, i.e. a point of the medial axis. Exact on a rib, immune to the
    object's size, immune to the upper bound, and there is no tolerance absorbing anything.

    `min_px` discards ridge points the grid cannot resolve: below ~1.5px a "feature" is
    rasterisation. ANY RESULT NEAR 2*min_px*px IS GRID-LIMITED AND MUST BE REPORTED AS SUCH --
    at the wyrm's 0.3083mm/px that floor is 0.925mm, which is coarser than most things worth
    measuring. Report the pixel size beside the answer or the answer is not interpretable.

    Returns (thickness_mm, (axis0_mm, axis1_mm)) at the thinnest ridge point, or (None, None).

    >>> THE LOCATION IS IN THE CALLER'S OWN AXIS ORDER, NOT (x, y). <<< This function cannot
    know which way round the mask is indexed and must not pretend to: the enclosure occupancy
    grid is [x, y], the wyrm silhouette is [row, col] = [y, x]. Naming the tuple (x, y) is how
    I reported the shell's thinnest feature at "(21.87, 16.92)" — a point outside the hex field
    entirely — when the truth was (16.92, 21.87), dead centre of a web. The number was right and
    the label transposed it, which reads exactly like a different finding.
    """
    d = edt(mask)
    mx = nd.maximum_filter(d, size=3, mode="constant", cval=0.0)
    ridge = (d == mx) & (d >= min_px) & mask
    if not ridge.any():
        return None, None
    lo = float(d[ridge].min())
    i0, i1 = np.nonzero(ridge & (d <= lo + 1e-9))
    return 2.0 * lo * px, (float(i0[0] * px), float(i1[0] * px))


def selftest(px=0.075, verbose=True):
    """Plant ribs of known width, ORIENTATION and place; require them found at that width.

    Raises AssertionError if the measurement cannot be trusted. Called from make_wyrm_spans.py
    on every run: a detector that has not detected anything today is not known to work.
    """
    n = 300
    g = np.zeros((n, n), dtype=bool)
    g[10:70, 10:290] = True                                     # thick slab A
    g[150:220, 10:290] = True                                   # thick slab B
    w_thin, w_fat = int(round(0.60 / px)), int(round(1.50 / px))
    g[70:150, 40:40 + w_thin] = True                            # 0.600mm rib, void both sides
    g[70:150, 120:120 + w_fat] = True                           # 1.500mm rib, void both sides
    # A 45deg rib of 0.600mm PERPENDICULAR width. The distance from (x,y) to the line
    # x-y=30 is |x-y-30|/sqrt(2), so a perpendicular HALF-width of h pixels needs the
    # threshold h*sqrt(2). Getting this wrong first time planted a 0.30mm rib and the metric
    # correctly measured 0.335 — the control catching an error in the control, which is the
    # only reason it is safe to let a control excuse a metric.
    xx, yy = np.mgrid[0:n, 0:n]
    diag = (np.abs((xx - yy) - 30) <= ((0.60 / px) / 2) * math.sqrt(2)) \
        & (xx > 230) & (xx < 295) & (yy > 190) & (yy < 290)
    g |= diag

    got = thin_regions(g, px, 0.75)

    def inside(r, x0, x1, y0, y1):
        return (r["x"][0] >= x0 * px - 0.1 and r["x"][1] <= x1 * px + 0.1 and
                r["y"][0] >= y0 * px - 0.1 and r["y"][1] <= y1 * px + 0.1)
    ax = [r for r in got if inside(r, 60, 160, 39, 41 + w_thin)]
    fat = [r for r in got if inside(r, 60, 160, 119, 121 + w_fat)]
    dg = [r for r in got if r["x"][0] > 225 * px and r["y"][0] > 185 * px]

    if verbose:
        print(f"  [min-feature control] {len(got)} region(s) over the floor")
        for lbl, hits in (("0.600mm axis-aligned", ax), ("0.600mm at 45deg    ", dg)):
            if hits:
                t = min(h["thick_mm"] for h in hits)
                print(f"  [min-feature control] {lbl}: FOUND and localised, "
                      f"{t:.3f} mm ({(t-0.60)*1000:+.0f} um)")
            else:
                print(f"  [min-feature control] {lbl}: MISSED")
        print(f"  [min-feature control] 1.500mm rib       : "
              f"{'WRONGLY FLAGGED' if fat else 'correctly ignored'}")

    assert ax, "the planted 0.60mm axis-aligned rib was not found — metric untrustworthy"
    assert dg, "the planted 0.60mm 45deg rib was not found — metric untrustworthy"
    assert not fat, "the planted 1.50mm rib was flagged as thin — the metric says yes to anything"
    for h in ax + dg:
        assert abs(h["thick_mm"] - 0.60) < 0.09, (
            f"measured {h['thick_mm']:.3f}mm for a planted 0.600mm rib")

    # ---- AND THE CASE THAT CATCHES min_feature() RETURNING THE THICKEST THING ----
    #
    # The three ribs above are all THIN, so a metric that reports the fattest region would
    # still look right on them. This shape cannot be got wrong quietly: one 0.60mm rib joined
    # to one deliberately FAT lobe, in an object smaller than a careless threshold. If
    # min_feature() ever returns something near the lobe's thickness instead of the rib's, it
    # is measuring the wrong end of the shape -- which is exactly what it did to the wyrm
    # silhouette, returning that creature's thickest half-width doubled.
    # The shape must be SMALL relative to a careless threshold, or the failure cannot occur:
    # the wyrm broke because opening by r=10px on a 50px-tall creature wiped it out entirely
    # and every pixel became one region. So the lobes here are deliberately thin enough
    # (1.20mm -> max EDT 8px) that a 1.5mm threshold (r=10px) erases the whole object.
    n2 = 200
    g2 = np.zeros((n2, n2), dtype=bool)
    yy2, xx2 = np.mgrid[0:n2, 0:n2]
    lobe_r = int(round(1.20 / px / 2))                       # 1.20mm lobe -> max EDT 8 px
    for cx in (50, 150):
        g2 |= ((xx2 - cx) ** 2 + (yy2 - 100) ** 2) <= lobe_r ** 2
    g2[50:150, 100:100 + w_thin] = True                      # the 0.60mm rib between them
    lobe = 2 * lobe_r * px
    got2, at2 = thinnest_feature(g2, px)
    frac = 100.0 * (g2 & ~open_disc(g2, (20 * px / 2) / px)).sum() / g2.sum()
    gran = min_feature(g2, px)
    if verbose:
        print(f"  [min-feature control] {lobe:.2f}mm lobes bridged by a 0.600mm rib, in an "
              f"object a careless threshold erases ({frac:.0f}% flagged at 1.50mm):")
        print(f"  [min-feature control]   thinnest_feature -> {got2:.3f} mm  (rib 0.600, "
              f"NOT the lobe {lobe:.3f})   granulometry bound -> {gran:.3f} mm")
    assert got2 is not None and abs(got2 - 0.60) < 0.06, (
        f"thinnest_feature returned {got2} for a shape whose thinnest feature is 0.600mm and "
        f"whose fattest is {lobe:.3f}mm — it is measuring the wrong end of the shape")
    # the rib here is 67% of the object's area, so a "region must not be most of the mask"
    # guard would reject the correct answer. It did, in v2. Kept as a case.
    for nm, m3 in (("axis rib", g), ("lobe+rib", g2)):
        t3, _ = thinnest_feature(m3, px)
        assert abs(t3 - 0.60) < 0.06, f"{nm}: thinnest_feature {t3:.3f}, expected 0.600"
    return True


if __name__ == "__main__":
    selftest()
    print("  min-feature metric: control passed")
