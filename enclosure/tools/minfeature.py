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


def min_feature(mask, px, ceiling_mm=None, floor_mm2=None):
    """The thinnest feature in `mask`, in mm. Continuous-valued — no 2k*px quantisation.

    `ceiling_mm` bounds the search: features at or above it are not looked for, and the ceiling
    is returned if nothing below it exists. A returned value EQUAL to the ceiling therefore
    means "nothing thinner than this was found", not "the minimum is exactly this" — callers
    that need to tell those apart should use thin_regions() directly.
    """
    ceiling = ceiling_mm if ceiling_mm is not None else 20.0 * px
    regions = thin_regions(mask, px, ceiling, floor_mm2)
    return min([r["thick_mm"] for r in regions], default=float(ceiling))


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
    return True


if __name__ == "__main__":
    selftest()
    print("  min-feature metric: control passed")
