#!/usr/bin/env python3
"""Verify ON THE EXPORTED MESH that the back-face labels read as separate words.

WHY THIS EXISTS, AND WHY IT IS NOT A `LABEL_WORD_GAP` CHECK.
`LABEL_WORD_GAP` is already enforced three times in ember_case.py -- constructively in the
connector packing loop, and by two asserts, one of which names `SPKI2C` in its own failure
message. A fourth check of the same property would pass on day one and forever. See
minfeature.py's note on instruments that are checked for existence rather than sensitivity.

What is NOT checked anywhere is that any of it SURVIVES TO THE STL. Every one of those
asserts runs on `ink_size()` -- the placement math's PREDICTION of where the ink lands. The
chain `text_paths() -> mirror in X -> placement -> boolean cut -> export` is not verified end
to end by anything. `slice_svg.py` exists precisely because that chain was doubted once (the
mirror), and it was answered by a human eye, once, and never again automatically.

So this reads the mesh and asks the reader's question: does the space between two labels
beat the space inside one? It never imports a placement constant -- not `HEX_FIELD_X0/X1`,
not `LBL_*_Y`, not `_conn_place`. Re-importing the design's own placement would destroy the
independence that makes the check worth having. It uses only the FONT (stroke widths, via
strokefont.ink_size) and the SPEC (what the part is supposed to say).

HOW THE GLYPHS ARE FOUND, WITHOUT BEING TOLD WHERE THEY ARE.
The labels are the only features on that face debossed exactly LABEL_DEBOSS deep: the hex
apertures and the speaker relief are through, the counterbores are 3.00, the button-cap
recesses are deeper still. So the part is sliced TWICE -- once just inside the back face and
once just past the groove floor -- and a closed loop present in the first and absent from the
second is a label groove and nothing else. Depth does the discriminating, so no coordinate
has to.

    python3 label_export_check.py [stl]        # defaults to ember-back-shell.stl
    python3 label_export_check.py --selftest   # both controls, incl. the failing fixture

--------------------------------------------------------------------------------------------
WHAT THIS CANNOT ANSWER, written here because this is where it gets reached for.

1. IT DOES NOT SEE THE BUTTON-CAP LABELS. `BOOT`, `RESET`, `VOL` and the power symbol sit at
   the bottom of DEBOSS_BIG recesses, on a face this slice pair never crosses. They are the
   two labels the PRINT-SHEET already warns will blur from bridging sag, and they are exactly
   the ones measured here least. Scope is the flat back face.

2. IT MEASURES INK BOXES, NOT STROKES. Two labels whose bounding boxes clear each other can
   still collide stroke-to-stroke if one ever gains a descender or an accent. `min_gap()` is
   the tool for material between strokes; this one is about words.

3. A PASS IS NOT A LEGIBILITY GUARANTEE. It certifies a spacing RATIO, measured on the mesh.
   Contrast, sag on the bridged floor, and filament colour are not in the geometry and this
   cannot see any of them. The `⛔ gap-closing radius = 0` warning in PRINT-SHEET.md guards a
   failure mode -- a slicer welding a 0.90 groove shut -- that happens AFTER this check and
   which no STL-level test can reach.

4. THE FAILING CONTROL IS A BUILT MESH, AND THAT COST A BUILD. It is not synthesised from
   strokefont, deliberately: a control that never crosses the slice->loop front end proves
   only that the arithmetic works. See `--selftest` and tests/fixtures/README.

5. IT FINDS RUN BOUNDARIES, NOT WORD IDENTITY. Labels are matched by ink width, and `BAT` and
   `SPK` are both 13.28mm, so the matcher cannot tell which strip each is on and does not
   try. Swap those two silkscreen-wise and this still passes. That is deliberate -- it is a
   SPACING instrument, and the boundaries it needs are identical either way -- but it means a
   pass is not a guarantee that the right word labels the right port. The design-time
   nearest-port asserts in ember_case.py own that question and already answer it.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slice_svg import read_stl, slice_z          # noqa: E402  the slicing core, reused
import strokefont as SF                          # noqa: E402  the FONT, not the placement

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STL = os.path.join(HERE, "..", "ember-back-shell.stl")

# ---- the FONT, and the SPEC. Neither is a placement constant. -------------------------------
# These four mirror ember_case.py's font setup. They are duplicated rather than imported
# because importing ember_case.py runs the whole 9-minute build; and because a verifier that
# reads its expectations out of the thing it is verifying agrees with it by construction.
LABEL_H_FLAT = 5.50      # centreline cap height on the flat back
LABEL_W      = 0.90      # stroke width == groove width == the nozzle floor
LABEL_GAP    = 1.90      # centreline advance between glyphs -> 1.00mm of material
LABEL_DEBOSS = 0.40      # how deep the grooves cut. THE DISCRIMINATOR.

# What the flat back face must say. Order-free: the matcher works out which run is which.
FLAT_LABELS = ["SD", "MIC", "UART", "I2C", "SPK", "BAT", "IO"]

# The ratio a word space must beat a letter space by. NOT 2.0, and the reason is a finding of
# this tool rather than a choice: the nominal letter space is LABEL_GAP - LABEL_W = 1.00 and
# the nominal word space is 2.00, which looks like 2.0x of headroom. Measured on the mesh it
# is not, because `I` is a zero-advance glyph -- its ink is the bare 0.90 stroke, so the ink
# box beside it opens up to ~1.45mm. The true worst-case ratio on the shipped part is ~1.38,
# and a threshold set at the nominal 2.0 would fail the good part. See --selftest output.
MARGIN = 1.25


class Blind(Exception):
    """The check could not run. THIS IS A FAILURE, NOT A SKIP.

    A check that could not run has read as a check that found nothing three times in this
    project's history. Every raise site here is a case where the geometry did not look like
    what the checker knows how to measure -- which is itself a result worth failing on."""


# ---- geometry -------------------------------------------------------------------------------

def _loops(tris, z):
    """Closed polylines where the mesh crosses the plane z."""
    segs = slice_z(tris, z)
    q = 1e-4
    def key(p): return (round(p[0] / q), round(p[1] / q))
    adj, pos = {}, {}
    for a, b in segs:
        ka, kb = key(a), key(b)
        if ka == kb:
            continue
        adj.setdefault(ka, []).append(kb)
        adj.setdefault(kb, []).append(ka)
        pos[ka], pos[kb] = a, b
    seen, out = set(), []
    for start in adj:
        if start in seen:
            continue
        loop, cur, prev = [pos[start]], start, None
        seen.add(start)
        while True:
            nxt = [k for k in adj.get(cur, []) if k != prev and k not in seen]
            if not nxt:
                break
            seen.add(nxt[0])
            loop.append(pos[nxt[0]])
            prev, cur = cur, nxt[0]
        if len(loop) >= 3:
            out.append(loop)
    return out


def _bbox(loop):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    return (min(xs), min(ys), max(xs), max(ys))


def _inside(a, b, tol=1e-6):
    """a is strictly within b -- a glyph counter inside its own outline."""
    return (a[0] > b[0] - tol and a[1] > b[1] - tol
            and a[2] < b[2] + tol and a[3] < b[3] + tol and a != b)


def glyph_boxes(stl_path):
    """Every label-groove outline on the flat back face, as ink bounding boxes.

    Depth difference, then counters dropped, then anything that is not glyph-shaped. The one
    non-glyph survivor on this part is a button-cap recess whose bbox happens to shrink with
    depth; it is removed by the ink-height filter, which is SELF-CALIBRATED from the modal
    loop height rather than hardcoded, so a change to LABEL_H_FLAT does not silently blind
    this."""
    if not os.path.exists(stl_path):
        raise Blind(f"no such STL: {stl_path}")
    tris = read_stl(stl_path)
    if not tris:
        raise Blind(f"{stl_path} has no triangles")

    zmin = min(v[2] for t in tris for v in t)
    z_in = zmin + LABEL_DEBOSS * 0.5      # inside the groove
    z_below = zmin + LABEL_DEBOSS * 1.25  # past its floor

    inside = _loops(tris, z_in)
    below = [_bbox(l) for l in _loops(tris, z_below)]
    if not inside:
        raise Blind(f"no geometry at z={z_in:.3f} -- the back face is not where it was")

    shallow = []
    for lp in inside:
        b = _bbox(lp)
        if any(all(abs(b[i] - o[i]) < 0.15 for i in range(4)) for o in below):
            continue                      # persists below the groove floor: not a label
        shallow.append(b)
    if not shallow:
        raise Blind("depth difference isolated nothing -- no feature is LABEL_DEBOSS deep")

    outer = [b for b in shallow if not any(_inside(b, o) for o in shallow)]

    # self-calibrate the ink height: the modal long dimension of the surviving loops
    longs = sorted(round(max(b[2] - b[0], b[3] - b[1]), 2) for b in outer)
    best, n_best = None, 0
    for v in set(longs):
        n = sum(1 for x in longs if abs(x - v) < 0.05)
        if n > n_best:
            best, n_best = v, n
    if best is None or n_best < 4:
        raise Blind(f"no dominant glyph height among {len(outer)} loops -- cannot identify text")
    ink_h = best

    glyphs = [b for b in outer if abs(max(b[2] - b[0], b[3] - b[1]) - ink_h) < 0.05]
    if len(glyphs) < 2:
        raise Blind(f"only {len(glyphs)} glyph-shaped loops at ink height {ink_h:.2f}")
    return glyphs, ink_h


def lines(glyphs, ink_h):
    """Group glyphs into text lines and orient each one.

    A line is a set of glyphs sharing an interval on the axis the ink height runs along; the
    OTHER axis is the reading direction. Derived from the geometry, so a label that moved to a
    new strip is still found."""
    out = {}
    for b in glyphs:
        horiz = abs((b[2] - b[0]) - ink_h) < 0.05   # ink height along X -> reading along Y
        span = (round(b[0], 2), round(b[2], 2)) if horiz else (round(b[1], 2), round(b[3], 2))
        out.setdefault((horiz, span), []).append(b)
    res = []
    for (horiz, span), items in out.items():
        # reading coordinate = the axis the ink height does NOT occupy
        items.sort(key=lambda b: b[1] if horiz else b[0])
        runs = [(b[1], b[3]) if horiz else (b[0], b[2]) for b in items]
        res.append({"horiz": horiz, "span": span, "ink": runs})
    res.sort(key=lambda d: (not d["horiz"], d["span"]))
    return res


def _width(text):
    """The ink width the font ACTUALLY DRAWS, from the centrelines themselves.

    ⚠️ NOT `ink_size()`, and the difference is a live finding rather than a nicety.
    `ink_size()` computes `sum(gw)*h + (n-1)*gap + w` -- it assumes every glyph's ink fills
    its advance slot. `I` is the exception: `gw('I')` is 0.16, so it is given a 0.88mm slot,
    but the glyph drawn in it is a bare vertical stroke whose ink is just the 0.90 stroke
    width. For a label STARTING with `I` the ink therefore begins 0.44mm later than
    `ink_size()` predicts, and `I2C` and `IO` are both 0.44mm narrower on the mesh than the
    formula says. Measured: I2C 10.86 rendered vs 11.30 predicted, and the slice agrees with
    the rendering to 0.01mm.

    This matters because ALL THREE design-time asserts run on `ink_size()`. The error is in
    the safe direction -- they over-reserve -- so nothing is broken today, and it is not this
    tool's business to change ember_case.py. But a 0.44mm standing disagreement between what
    the placement math believes and what the exporter emits is exactly the class of thing
    this check exists to surface, and it was invisible until the mesh was measured."""
    paths = SF.text_paths(text, LABEL_H_FLAT, LABEL_W, LABEL_GAP)
    xs = [p[0] for path in paths for p in path]
    return max(xs) - min(xs) + LABEL_W


def predicted_vs_rendered():
    """Labels whose `ink_size()` prediction disagrees with the drawn ink. Reported, not fatal."""
    out = []
    for t in FLAT_LABELS:
        pred = SF.ink_size(t, LABEL_H_FLAT, LABEL_W, LABEL_GAP)[0]
        got = _width(t)
        if abs(pred - got) > 1e-6:
            out.append((t, pred, got))
    return out


def assign(ink, pool, tol=0.08):
    """Partition a line's glyph sequence into labels, matching each run's measured ink span
    against the FONT's own width for that word.

    This is what makes the check independent: it never asks where a label was placed, only
    whether some ordered run of glyphs on this line is exactly as wide as `SPK` should be.
    A part missing a label, or with a stroke eaten by the boolean, fails to match here -- and
    a failure to match is Blind, which is a failure."""
    n = len(ink)

    def rec(i, avail):
        if i == n:
            return []           # this LINE is covered; other lines claim the rest of the pool
        for lab in sorted(avail):
            k = len(lab)
            if i + k > n:
                continue
            got = ink[i + k - 1][1] - ink[i][0]
            if abs(got - _width(lab)) > tol:
                continue
            rest = rec(i + k, avail - {lab})
            if rest is not None:
                return [(lab, i, i + k)] + rest
        return None

    return rec(0, frozenset(pool))


def check(stl_path, verbose=True):
    """Returns (ok, report). Raises Blind if it could not measure -- which callers treat as
    a failure, never as a skip."""
    glyphs, ink_h = glyph_boxes(stl_path)
    ls = lines(glyphs, ink_h)

    pool = list(FLAT_LABELS)
    rows, worst = [], None
    total_glyphs = sum(len(l["ink"]) for l in ls)
    if total_glyphs != sum(len(x) for x in FLAT_LABELS):
        raise Blind(
            f"found {total_glyphs} glyphs but the spec {FLAT_LABELS} needs "
            f"{sum(len(x) for x in FLAT_LABELS)} -- a label is missing, doubled, or fused")

    for ln in ls:
        ink = ln["ink"]
        got = assign(ink, pool)
        if got is None:
            raise Blind(
                f"no arrangement of {sorted(pool)} matches the {len(ink)} glyphs on the "
                f"{'vertical' if ln['horiz'] else 'horizontal'} line at {ln['span']} -- "
                f"the export does not say what the spec says")
        for lab, _, _ in got:
            pool.remove(lab)

        intra, inter = [], []
        for a in range(len(ink) - 1):
            g = ink[a + 1][0] - ink[a][1]
            same = any(s <= a and a + 1 < e for _, s, e in got)
            (intra if same else inter).append((g, a))
        rows.append({"labels": [g[0] for g in got], "intra": intra, "inter": inter,
                     "axis": "y" if ln["horiz"] else "x", "at": ln["span"]})

    if pool:
        raise Blind(f"labels never found on the mesh: {sorted(pool)}")

    all_intra = [g for r in rows for g, _ in r["intra"]]
    all_inter = [g for r in rows for g, _ in r["inter"]]
    if not all_intra or not all_inter:
        raise Blind("the part has no two adjacent labels, or no multi-glyph label -- "
                    "there is nothing here to compare and that is not a pass")

    mx_intra, mn_inter = max(all_intra), min(all_inter)
    ratio = mn_inter / mx_intra
    ok = ratio >= MARGIN

    if verbose:
        print(f"  {os.path.basename(stl_path)}: {len(glyphs)} glyphs, ink height "
              f"{ink_h:.2f}mm, {len(rows)} text lines")
        for r in rows:
            let = f"{max(g for g, _ in r['intra']):.2f}" if r["intra"] else "  — "
            wrd = f"{min(g for g, _ in r['inter']):.2f}" if r["inter"] else "  — (alone)"
            print(f"    {'+'.join(r['labels']):<16} along {r['axis']} at {r['at']}  "
                  f"letter {let}  word {wrd}")
        amb = {}
        for t in FLAT_LABELS:
            amb.setdefault(round(_width(t), 3), []).append(t)
        for wv in sorted(k for k, v in amb.items() if len(v) > 1):
            print(f"    note: {'/'.join(amb[wv])} are both {wv:.2f}mm wide — the names above "
                  f"are one consistent reading of the widths, not an identification")
        print(f"    widest letter space {mx_intra:.2f}mm | tightest word space "
              f"{mn_inter:.2f}mm | ratio {ratio:.2f} (need >= {MARGIN})")
        for t, pred, got in predicted_vs_rendered():
            print(f"    note: ink_size({t}) predicts {pred:.2f}mm, the font draws {got:.2f}mm "
                  f"({pred - got:+.2f}) — the design asserts run on the prediction")
    return ok, {"ratio": ratio, "max_intra": mx_intra, "min_inter": mn_inter, "rows": rows}


# ---- controls --------------------------------------------------------------------------------

FIXTURE = os.path.join(HERE, "..", "tests", "fixtures", "back-shell-wordgap-0.80.stl")


def selftest():
    """Two controls. One must pass, one MUST FAIL -- an instrument that has never produced a
    positive is not evidence."""
    print("control 1/2 -- the shipped part, which must PASS")
    ok, _ = check(DEFAULT_STL)
    if not ok:
        print("  FAIL: the shipped part did not pass. The threshold is wrong, or the part is.")
        return 1
    print("  pass\n")

    print("control 2/2 -- LABEL_WORD_GAP built at LABEL_MARGIN (0.80), which must FAIL")
    if not os.path.exists(FIXTURE):
        print(f"  BLIND: fixture missing at {FIXTURE}")
        print("  A must-fire control that cannot run is the failure this project keeps finding.")
        return 1
    bad, _ = check(FIXTURE)
    if bad:
        print("  FAIL: the 0.80 build PASSED. The check cannot see the defect it exists for.")
        return 1
    print("  pass (it failed, as it must)\n")
    print("both controls behaved. The instrument fires at the defect and not at the good part.")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    stl = argv[1] if len(argv) > 1 else DEFAULT_STL
    try:
        ok, _ = check(stl)
    except Blind as e:
        print(f"BLIND -> FAIL: {e}")
        return 2
    print("OK" if ok else "FAIL: a word space is not clear of the letter spaces")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
