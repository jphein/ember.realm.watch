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

4. THE FAILING CONTROLS ARE BUILT MESHES, AND THEY COST A BUILD EACH. Neither is synthesised
   from strokefont, deliberately: a control that never crosses the slice->loop front end
   proves only that the arithmetic works. There are two because #35's chamfer changed the
   shipped geometry under this tool and blinded it -- an instrument proven only against
   geometry that no longer ships is not evidence either. See tests/fixtures/README.

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
#
# NO "BAT" — corrected 2026-08-25, and the defect was THIS LIST, not the shell. d18e17c
# (2026-08-01) blocked the desk's BAT flank (SIDE_BLOCK: the connector has no consumer;
# there is no cell in the stand) and the shell's own rule — "NO LABEL MAY NAME AN OPENING
# THAT IS NOT THERE" — correctly deleted the label with the opening. This spec predated
# that rule and kept demanding 20 glyphs of a face that honestly says 17; the check then
# FAILED for 24 days against a correct part (issue #92; verified by mesh archaeology:
# the missing boxes are exactly BAT's three, the BAT band has wall where UART's has
# channel, and the MIC strip is byte-identical across every revision suspected). The
# tool's independence doctrine stands — this list is still hand-written truth, not an
# import — it just has to be CURRENT truth. Scope note: this default spec is the DESK
# shell's; the mobile midframe additionally drops MIC and SPK and is not this tool's
# default target.
FLAT_LABELS = ["SD", "MIC", "UART", "I2C", "SPK", "IO"]

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


def drop_silhouette(boxes, tol=0.05):
    """Remove the loops that ARE the part's outline, keeping the ones cut INTO it.

    >>> THE CRITERION IS "REACHES AN EXTREME OF THE SILHOUETTE", NOT "IS BIG". <<<
    A label groove is interior by construction -- LABEL_MARGIN holds every label 0.80mm off
    any edge -- so nothing that is text can touch the part's own bounding box. Sizing would
    be the wrong test and a dangerous one: a merged `BATUARTSD` run is ALSO large, and a rule
    that threw away the biggest loop would throw away the defect this tool exists to catch.
    Same selector `chamfer_outline()` uses in ember_case.py, for the same reason.

    ⚠️ WHY THIS IS NEEDED AT ALL, because it was not, until #35. The depth difference assumed
    the outline is the same shape at both slice planes. A chamfer makes it a function of z:
    measured on the shipped shell the perimeter is 54.700mm wide at z_in and 55.300mm at
    z_below, 0.600mm apart, so the two no longer match and the whole perimeter survived the
    difference as one enormous loop. It then swallowed the entire text -- every glyph is
    nested inside the outline, so the counter-dropping step discarded all twenty of them and
    left `1 loops`. The tool went BLIND rather than wrong, which is the one thing that went
    right, but blind on the shipped part is still broken."""
    if not boxes:
        return boxes
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    return [b for b in boxes
            if not (b[0] <= x0 + tol and b[1] <= y0 + tol
                    and b[2] >= x1 - tol and b[3] >= y1 - tol)]


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
    if not inside:
        raise Blind(f"no geometry at z={z_in:.3f} -- the back face is not where it was")

    # The silhouette goes FIRST, at both planes, before anything is compared or nested.
    # On a chamfered part it differs between the two planes and would otherwise survive the
    # difference and swallow the text.
    inside_b = drop_silhouette([_bbox(l) for l in inside])
    below = drop_silhouette([_bbox(l) for l in _loops(tris, z_below)])
    if not inside_b:
        raise Blind(f"nothing but the part outline at z={z_in:.3f} -- no interior feature to read")

    shallow = []
    for b in inside_b:
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


def check(stl_path, verbose=True, spec=None):
    spec = spec if spec is not None else FLAT_LABELS
    """Returns (ok, report). Raises Blind if it could not measure -- which callers treat as
    a failure, never as a skip."""
    glyphs, ink_h = glyph_boxes(stl_path)
    ls = lines(glyphs, ink_h)

    pool = list(spec)
    rows, worst = [], None
    total_glyphs = sum(len(l["ink"]) for l in ls)
    if total_glyphs != sum(len(x) for x in spec):
        raise Blind(
            f"found {total_glyphs} glyphs but the spec {spec} needs "
            f"{sum(len(x) for x in spec)} -- a label is missing, doubled, or fused")

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
        for t in spec:
            amb.setdefault(round(_width(t), 3), []).append(t)
        for wv in sorted(k for k, v in amb.items() if len(v) > 1):
            print(f"    note: {'/'.join(amb[wv])} are both {wv:.2f}mm wide — the names above "
                  f"are one consistent reading of the widths, not an identification")
        print(f"    widest letter space {mx_intra:.2f}mm | tightest word space "
              f"{mn_inter:.2f}mm | ratio {ratio:.2f} (need >= {MARGIN})")
        for t, pred, got in predicted_vs_rendered():
            print(f"    note: ink_size({t}) predicts {pred:.2f}mm, the font draws {got:.2f}mm "
                  f"({pred - got:+.2f}) — the design asserts run on the prediction")
    return ok, {"ratio": ratio, "max_intra": mx_intra, "min_inter": mn_inter, "rows": rows,
                "glyphs": len(glyphs)}


# ---- controls --------------------------------------------------------------------------------

def _fx(name):
    return os.path.join(HERE, "..", "tests", "fixtures", name)


# (path, must_pass, why). Every glyph count must be GLYPHS_EXPECTED -- see the note below.
CONTROLS = [
    (DEFAULT_STL, True, None,
     "the shipped part, chamfered (#35), must PASS"),
    (_fx("back-shell-chamfered-wordgap-0.80.stl"), False, "FIXTURE",
     "CURRENT geometry at word gap 0.80, must FAIL"),
    (_fx("back-shell-wordgap-0.80.stl"), False, "FIXTURE",
     "PRE-CHAMFER geometry at word gap 0.80, must still FAIL"),
]

# The FIXTURES are frozen pre-d18e17c geometry and still carry the desk's BAT label —
# deliberately: the controls test the INSTRUMENT (loop recovery, fusion sensitivity),
# not the current design truth, and re-cutting fixtures every time a label legitimately
# dies would let a filter regression hide inside the churn. Each control judges its STL
# against ITS OWN spec (2026-08-25, when the live spec dropped BAT and both 0.80 controls
# started BLIND-failing on count instead of failing on ratio as designed).
FIXTURE_LABELS = ["SD", "MIC", "UART", "I2C", "SPK", "BAT", "IO"]


def selftest():
    """Three controls: one that must pass, two that must fail, and a glyph count on all of
    them. An instrument that has never produced a positive is not evidence -- and after #35,
    an instrument proven only on geometry that no longer ships is not evidence either.

    ⚠️ THE GLYPH COUNT IS NOT DECORATION. `drop_silhouette()` throws loops away, and the
    failure it was written for -- the chamfer's outline swallowing the entire text -- looked
    exactly like "fewer loops than expected". Asserting all twenty glyphs survive on every
    control is what stops a future filter tweak from quietly eating text and leaving a check
    that still says OK. A merged `BATUARTSD` run is large AND interior, so it must survive
    the silhouette filter; the two 0.80 controls are what prove it does."""
    rc = 0
    for i, (path, must_pass, which, why) in enumerate(CONTROLS, 1):
        spec = FIXTURE_LABELS if which == "FIXTURE" else FLAT_LABELS
        expected = sum(len(t) for t in spec)
        print(f"control {i}/{len(CONTROLS)} -- {why}")
        if not os.path.exists(path):
            print(f"  BLIND: fixture missing at {path}")
            print("  A control that cannot run is the failure this project keeps finding.")
            rc = 1
            continue
        try:
            ok, rep = check(path, spec=spec)
        except Blind as e:
            print(f"  BLIND -> FAIL: {e}")
            rc = 1
            continue
        n = rep["glyphs"]
        if n != expected:
            print(f"  FAIL: {n} glyphs recovered, expected {expected} — a filter is "
                  f"eating text")
            rc = 1
            continue
        if ok != must_pass:
            print(f"  FAIL: expected {'PASS' if must_pass else 'FAIL'}, got "
                  f"{'PASS' if ok else 'FAIL'} (ratio {rep['ratio']:.2f})")
            rc = 1
            continue
        print(f"  pass ({'passed' if ok else 'failed'}, as it must — "
              f"ratio {rep['ratio']:.2f}, {n} glyphs)\n")
    if rc == 0:
        print("all controls behaved. The instrument fires at the defect, on the geometry that "
              "ships, and not at the good part.")
    return rc


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
