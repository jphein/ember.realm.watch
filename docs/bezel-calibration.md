# Front bezel — predictions BEFORE looking at the printed part

Morpheus, 2026-07-30. **This is a calibration, not an audit.** Every tool built today forecasts
what a printer will do and **not one has been scored against a printer that has done it.** JP has
this part in hand.

So the predictions below are written **first, from the geometry alone**, and they are stated so
they can be **wrong**. Each one names what would falsify it. Nobody has looked at the physical
bezel for any of these features, and I have not asked.

Geometry as printed: **front face DOWN, 0.16 mm layers** (`PRINT-SHEET.md`), 8.00 mm tall in 50
layers. Measured from `ember-front-bezel.stl` at HEAD; the bezel is byte-identical to the one JP
printed, which is why this is a fair test.

> 🔒 **P1–P6 ARE FROZEN AS WRITTEN. Nothing in them has been edited since they were first
> recorded, and nothing will be.** Their whole value is that they were fixed before anyone looked,
> and a prediction improved while waiting for the observation cannot be scored against it — even
> if the improvement is correct. *Especially* if the improvement is correct.
>
> A later realisation about P3 exists and is in **Appendix A**, dated and marked as post-hoc, so
> the original stays scoreable and the refinement is visible as a refinement rather than blended
> in. **Appendix B is the scoring procedure, also written before the data**, because deciding what
> counts as a pass after seeing the answer is the same failure as adjusting the prediction.

---

## The one number the whole day turns on

```
wyrm silhouette, EDT ridge minimum   2.4667 mm at canvas scale
mark scale s = 0.90 / 1.2333       = 0.7297
                                     -----------
narrowest recessed channel on the bezel   1.800 mm   = 4.50 nozzle widths
narrowest MATERIAL between the wyrm's own parts   2.250 mm   = 5.63 nozzle widths
```

The declared `WYRM_MIN_FEATURE = 1.2333` is a conservative bound (4 px of the source canvas). The
measured minimum is **2.00× that**, so the mark sits at twice its print floor rather than on it —
and the print floor was never what capped its size, because scaling up multiplies every feature.

**If this is right, the wyrm should be completely unremarkable to look at: crisp everywhere, with
nothing near the edge of resolution.** That is a boring prediction and it is the point — it is
falsifiable by a single smeared feature.

---

## P1 — The wyrm will be crisp everywhere. No smearing, no closed gaps, no lost tip.

**Both directions are far above resolution:** the narrowest *recess* is 1.800 mm (4.5 nozzle
widths, 0.48 mm deep) and the narrowest *material* between the creature's own parts is 2.250 mm
(5.6 widths).

**Predicted, specifically:**
- the **tail tip** is fully formed and comes to a definite point — not rounded off, not missing
- every **leg gap** is open and reads as a gap, not filled or bridged over
- the **dorsal spikes** are individually distinct, not merged into a ridge
- the **neck** is continuous with the body (it is one connected piece by assert, and the gap that
  used to exist there is gone)

**Falsified by:** any of those features smeared, filled, rounded away, or missing. If the tail tip
is soft or a leg gap has closed, **1.800 mm is optimistic and the ridge measurement is wrong about
a rasterised silhouette** — which is exactly what I want to learn, because that measurement is now
load-bearing in three places.

**Confidence: high.** 4.5 nozzle widths is not a marginal feature by any standard.

---

## P2 — The honeycomb cell corners will be visibly rounded. That is not a defect.

The thinnest material anywhere on the **visible first layer** is **0.300 mm — 0.75 nozzle widths**,
and it is at the honeycomb cell corners, where two 0.70 mm webs meet at 120°.

A 0.4 mm nozzle cannot lay 0.30 mm. **The slicer will omit it.**

**Predicted:** under a raking light, the hexagons' **corners look rounded rather than sharp**. The
cells read as soft-cornered hexagons. **The webs are continuous with no gaps anywhere** — the
omission is at the corners only, and the first layer is a single connected island (measured:
1856.7 mm², **1 island**), so nothing can be missing in a way that breaks the lattice.

**Falsified by:** sharp crisp hexagon corners (would mean the slicer resolved 0.30 mm — surprising),
or by any *gap* in a web (would mean the omission went further than the corners).

**Confidence: high** on rounded corners, **very high** on continuous webs.

---

## P3 — The webs will be *wider* than drawn, so the cells are slightly *smaller* across flats.

`BEZ_WEB = 0.70` is **1.75 nozzle widths.** That is the awkward band: too wide for one nominal
bead, too narrow for two. A modern variable-width slicer lays **one ~0.70 mm extrusion**, not two
0.40 mm lines — and this is the **first layer**, where squish spreads every bead outward.

**Predicted:** webs measure **0.75–0.90 mm** on the part, against 0.70 drawn. Cells therefore
measure **~0.10–0.20 mm smaller across flats** than the nominal 2.60 — call it **2.40–2.50 mm**.

**Falsified by:** webs measuring at or under 0.70 (would mean no squish spreading, or the slicer
under-extruding a thin feature), or cells measuring 2.60+.

**Confidence: medium.** The direction is confident; the magnitude depends on JP's flow calibration
and first-layer squish, which I cannot see.

> Note this makes P2 and P3 consistent rather than contradictory: **the cell becomes a slightly
> smaller hexagon with rounded corners.** Corners lost, flats moved inward.

---

## P4 — Deboss depth is 0.48 mm, exactly 3 layers, and feels like a crisp step.

Measured from the occupancy grid, the debossed regions close at **layer 4**:

```
layer 1 (z=0.00)  1856.7 mm2      <- the visible face, WITH the recesses open
layer 2 (z=0.16)  1859.1 mm2      +2.4
layer 3 (z=0.32)  1861.4 mm2      +2.2
layer 4 (z=0.48)  2482.3 mm2   +620.9   <- every deboss floor bridges, all at once
layer 5 (z=0.64)  2484.0 mm2      +1.7
```

`BEZEL_DEBOSS = 0.48` is **exactly 3.00 layers at 0.16 mm** — no rounding, no partial layer.

**Predicted:** the recess depth measures **0.45–0.50 mm** and feels like a **distinct crisp step**
under a fingernail, not a soft dish. The floor is at a clean layer boundary so its surface should
look like ordinary solid infill rather than a sloped or stepped transition.

**Falsified by:** a measurably deeper or shallower recess, or a floor that feels dished/tapered
rather than flat with a sharp wall.

**Confidence: high.** 3.00 layers exactly is the cleanest possible case.

---

## P5 — The deboss floors bridge, and should not sag perceptibly.

**620.9 mm² of material starts in mid-air on layer 4** — every honeycomb cell floor and the wyrm
mark's floor, simultaneously.

Spans are small: a cell is **2.60 mm across flats**, and the mark's widest run is a few mm. Sag
scales steeply with span, and 2.6 mm at 0.16 mm layers over a 0.48 mm drop is nothing.

**Predicted:** cell floors feel **flat** to a fingernail. The **mark's floor** may show very slight
sag at its widest, **under 0.1 mm**, most likely imperceptible without raking light.

**Falsified by:** visible dishing in the cell floors, or stringing/drooping visible inside the
recesses.

**Confidence: high** for the cells, **medium** for the mark's widest span.

---

## P6 — Nothing came loose. The first layer is one connected island.

**Measured: 1856.7 mm² in exactly 1 island.** Every web, every boss ring, the mic collar and the
face are one piece from layer 1.

**Predicted:** no detached fragments, nothing rattling on the bed, no islands that had to survive
on their own adhesion. Whatever else the print did, **it cannot have lost a piece of the first
layer**, because there is no separate piece to lose.

**Falsified by:** any missing fragment of the visible face.

**Confidence: very high.** This is a topological statement, not a process one.

---

## What I am NOT predicting, and why

- **Colour, layer lines, surface finish, elephant foot.** Process, not geometry.
- **Whether it looks good.** Not measurable and not mine.
- **The 3 known non-manifold edges.** Already settled empirically — it printed and the dimensions
  are good. That is an observation and it needed no prediction; recorded as one print on one
  slicer, not a claim about slicers in general.
- **Warp.** The bezel is a 5 mm plate at 1856.7 mm² of contact; there is nothing interesting to say.

---

## The ask for JP — one look, six answers

Every question below is answerable with eyes, a fingernail and a raking light. **Calipers only for
P3.** No disassembly.

| | look at | the prediction |
|---|---|---|
| **P1** | the wyrm's **tail tip, leg gaps, dorsal spikes** | crisp, open, distinct — nothing smeared |
| **P2** | a **honeycomb cell corner**, raking light | corners **rounded**, webs continuous, no gaps |
| **P3** | **web width / cell width**, calipers or loupe | webs **0.75–0.90** (drawn 0.70); cells **2.40–2.50** (drawn 2.60) |
| **P4** | **recess depth**, fingernail | ~**0.48 mm**, crisp step, flat floor |
| **P5** | **inside a cell floor** and the mark's floor | flat; mark maybe <0.1 mm sag |
| **P6** | the whole visible face | nothing missing |

**P1 is the one that matters.** It tests the measurement that three separate conclusions now rest
on. **P3 is the one most likely to be wrong**, and I would rather be scored on it than leave it
unstated.

---

## Why this is worth doing at all

Everything in `scratch/hosyond-s3/` today has been a forecast. The stand's rib, the shell's web,
the wire pass, the base plate, the countersink, the 13.2 mm bridge — **all predictions, none
scored.** A printed part is the first opportunity to find out whether these tools are calibrated
or merely self-consistent, and self-consistent is exactly what two agreeing-and-both-wrong methods
looked like earlier today.

**If P1 holds, the ridge measurement is trustworthy and `WYRM_MIN_FEATURE`'s 2× conservatism is
real.** If P1 fails, the ridge metric is optimistic about rasterised art and three write-ups need
revising — including the one that says the mark could have been larger.

---

# Appendix A — post-hoc note on P3, written after P1–P6 were fixed

**2026-07-30, after the predictions above were recorded and before any observation.** Kept
separate rather than folded into P3, so P3 stays scoreable exactly as written.

**P3 under-specified where to measure, and the omission favours me.** The deboss is 0.48 mm = 3
layers, so the honeycomb webs exist as *thin features* only on layers 1–3; above the deboss floor
the face is solid and there is no web at all. **Layer 1 is the squished one**, so it is the widest
the web ever gets and the narrowest the cell ever reads.

Calipers on the visible outer face therefore measure **layer 1 — the extreme case of P3, not its
average.** If P3's direction is right, the reading should sit at the *far* end of the 0.75–0.90
band.

**This does not change P3's numbers and must not be used to rescue them.** It sharpens the
measurement instruction, and it removes an escape route I would otherwise have had: had the
reading come back at 0.70, "you measured the wrong layer" was available to me, and it no longer
is. **Recorded because a refinement that makes a prediction easier to falsify is worth having, and
one that makes it easier to pass is not — this is the first kind, and the distinction is the whole
reason it lives down here instead of up there.**

Measurement instruction, unchanged in substance: **across a web between two adjacent cells, on the
outer face, not down inside a cell.**

---

# Appendix A2 — DISPUTED: P2's 0.300 mm, unresolved at time of writing

**2026-07-30, after the predictions were frozen and committed, and before any observation.**
**P2 is not edited. Neither measurement is declared correct here. The printed part adjudicates.**

`nebula-site` cannot reproduce the **0.300 mm** figure that P2's reasoning rests on. Three
independent checks of theirs put the narrowest material on the visible face at **0.70 mm — the
web itself**:

| their check | method | result |
|---|---|---|
| chin lattice | 2 µm raster, Euclidean distance transform, ridge minimum | **0.696 mm** |
| rail stack | same, restricted to the vertex-to-vertex pinch band | **0.704 mm** |
| both lattices | real `_bezel_cells()`, all-pairs centre distance | closest pair **3.3000 mm = nominal pitch**; zero pairs closer |

## The two bases, named

- **Mine:** the **exported STL**, ray-cast to an occupancy grid in the print orientation, **layer 0**,
  EDT ridge minimum. `px = 0.075 mm`.
- **Theirs:** the **CAD model** (`_bezel_cells()`), rasterised at **2 µm**, EDT ridge minimum, plus an
  analytic centre-distance check.

**Different objects and a 37× resolution difference**, so agreement was never guaranteed.

## What a resolution sweep of my basis shows

Run after the dispute surfaced, on my basis only:

```
px=0.075   ridge min 0.3000 mm   (EDT 2.00 px)   at model (x 9.575, y 85.20)
px=0.050   ridge min 0.2000 mm   (EDT 2.00 px)   at model (x 9.550, y 85.20)
px=0.030   ridge min 0.1800 mm   (EDT 3.00 px)   at model (x 9.590, y 85.17)
px=0.020   ridge min 0.2000 mm   (EDT 5.00 px)   at model (x 9.610, y 85.17)
```

**It does not vanish as the raster refines** — it converges toward ~0.18–0.20 mm — **and it
localises to the same place every time.**

## And that place is not the honeycomb

```
located point            model (x ≈ 9.58, y ≈ 85.19)
_bezel_mark() bbox       x 7.680..33.371   y 76.240..87.530
point inside the mark's bbox?   TRUE
```

**The feature sits inside the wyrm mark's region, not in either honeycomb lattice.** `nebula-site`
scanned the chin lattice and the rail stack; this is neither. So the two measurements may be
correct about **different features in different places**, in which case the number survives and
**P2's stated attribution — "at the honeycomb cell corners" — is the part that is wrong.** That
attribution was inherited from `print-readiness.md`'s earlier "156 sub-0.45 mm slivers … at the
honeycomb cell corners" and carried forward without being located.

A candidate mechanism, **not verified:** the mark is built from **104 row-span rectangles inflated
by 20 µm** (see `docs/verification.md` §14), so its edges are a staircase of near-coincident steps.
That is the kind of geometry that produces sub-0.3 mm material features. **Untested.**

## Why this is still unresolved, stated plainly

Three possibilities remain open and the data above does not choose between them:

1. **the feature is real in both model and export**, at a location not yet scanned at 2 µm — both
   measurements right, P2's label wrong;
2. **the feature is real in the export but absent from the model** — a mesher artefact, and a
   `§24` instance rather than an error by either of us;
3. **it is a raster artefact of my method at every resolution tried.** The sweep argues against
   this — artefacts do not usually persist *and* localise — but does not eliminate it.

**Separating 1 from 2 requires a fine-raster check of the model at (9.58, 85.19), which is
`nebula-site`'s instrument and not mine.** Handing over the coordinate rather than the verdict.

## What this does and does not do to P2

**P2 predicts rounded cell corners with continuous webs. That prediction is unchanged and still
scoreable exactly as written.** Its *reasoning* is now disputed, which makes the test more
informative rather than less:

- if **0.300 mm** is right and about the corners, corners round because the slicer omits material;
- if **0.70 mm** is right, P2 may still hold — 0.70 mm is **1.75 nozzle widths**, and a single wide
  bead with squish rounds a 120° corner too — **or it may fail**;
- **one look settles which, at no cost.**

Per Appendix B rule 1, **neither `nebula-site` nor I adjudicate this.** Resolving it tonight would
route around that rule by a different door, since one of the two measurements is the basis of my
own frozen claim.

---

# Appendix B — the scoring procedure, written before the data

The half nobody writes. Deciding what counts as a pass *after* seeing the answer is the same
failure as adjusting the prediction, so it is settled here.

## The three rules that matter

1. **JP's plain description is the datum. I do not adjudicate my own predictions.** Where their
   description is ambiguous, the result is **INCONCLUSIVE** — not resolved in my favour, and not
   resolved by me going back and asking a leading question.
2. **Ambiguity resolves against the prediction.** If P2 could be read either way, P2 did not pass.
   I wrote it; the burden is mine.
3. **A prediction that turns out to be unscoreable with the evidence available is recorded as
   UNSCOREABLE, not as a pass.** "We learned less than hoped" is a legitimate outcome and it must
   be reportable, or the exercise only ever confirms itself.

**And the score is not an average.** Weights, fixed now: **P1 is the test** (it scores the metric
three conclusions rest on). **P3 is the risk** (most likely wrong, and I said so before looking).
P2, P4, P5 are secondary. **P6 is a sanity check and a pass there is weak evidence** — it is a
topological statement about the model, so it was nearly free.

## Per prediction

| | PASS requires | FAIL is | UNSCOREABLE if |
|---|---|---|---|
| **P1** | tail tip comes to a point **and** leg gaps open **and** spikes individually distinct — all three, named | any one smeared, filled, rounded away or missing | only *"looks fine"* is reported. A 0.3 mm-smeared tail tip also looks fine at arm's length. **P1 needs the features named, not a verdict.** |
| **P2** | corners **visibly rounded** under raking light **and** every web continuous | sharp crisp corners, **or** any gap in a web | rounding only visible under magnification → still a **direction pass**; I predicted direction, never a radius, so magnitude is not scoreable either way |
| **P3** | web **≥0.75** **and** cell **≤2.50** | web **≤0.70** **or** cell **≥2.60** | web 0.70–0.75 or cell 2.50–2.60 → **DIRECTION PASS / MAGNITUDE FAIL**, recorded as that split and not as a pass |
| **P4** | depth gauge reads **0.45–0.50** | outside **0.40–0.55**, or a dished/tapered floor | fingernail only → scores the *"crisp step, flat floor"* half; **the depth half is unscoreable without a gauge.** A fingernail cannot resolve 0.03 mm |
| **P5** | cell floors feel flat, no visible dishing or stringing | visible dishing in the cell floors | **the mark's "<0.1 mm sag" is declared unscoreable by eye, in advance.** It is below what anyone can see, so a "looks flat" answer does not confirm it |
| **P6** | no absent fragment on the visible face | any missing fragment | n/a |

**Measurement standard for P3, since it is the only one with a number tight enough to need one:**
three caliper readings at three different places on the face, **report the range not a single
value.** A single reading on a 0.70 mm feature with rounded edges is not repeatable, and a range
that straddles a boundary is an INCONCLUSIVE by rule 2.

## What each outcome changes — the work list

Stated now, so the result is a work list rather than a score.

**P1 FAILS** → the EDT-ridge metric is optimistic about rasterised art. **Four places become
wrong**, all of which currently assert 1.800 mm or its reasoning:
- `enclosure/tools/minfeature.py` — the docstring's claim that the ridge read is *exact* on a
  located feature
- `enclosure/tools/wyrm_spans.py` — `WYRM_MIN_FEATURE_MEASURED = 2.4667` and its "2.00×" comment
- `docs/verification.md` §16 — *"1.800 mm against a 0.90 mm floor, twice the limit"*
- `enclosure/ember_case.py` `_bezel_mark()` — *"the mark's real thinnest feature is 1.800 mm —
  TWICE the 0.90 mm floor"*, and with it the claim that printability never capped the mark

  ⚠️ It would **not** revive *"the floor bounds the scale from below"* — that is a sign argument
  and independent of the magnitude. Only the headroom claim dies.

**P1 PASSES** → the metric is scored once, on one part, against one silhouette. **Say exactly
that and resist generalising**: it does not license "the ridge metric is validated", only "it was
right about this mark at this scale".

**P3 FAILS (either direction)** → `enclosure/PRINT-SHEET.md`'s *"2.60 mm across the flats on a
0.70 mm web"* describes the model rather than the part, and `nebula-site` already holds the
drawn-and-as-built sentence form for it. Also `print-readiness.md`'s estimate that first-layer
squish spreads each bounding line *"~0.1 mm inward"* — that number would be the one that was
wrong, and it is the only quantitative claim about squish anywhere in these notes.

**P2 FAILS with sharp corners** → the slicer resolved 0.300 mm, and `print-readiness.md`'s
"156 sub-0.45 mm slivers will be omitted" is too pessimistic. **P2 FAILS with a web gap** → worse
than predicted and a real cosmetic defect: `BEZ_WEB = 0.70` is not printing solid, which is a
geometry change, not a note.

**P4 FAILS** → `BEZEL_DEBOSS = 0.48`'s claim of *"EXACTLY 3 layers at 0.16"* holds arithmetically
but not in the part, which would mean the bezel is not being sliced at 0.16 — a process finding
that invalidates the layer-exactness argument wherever it appears.

**P5 FAILS** → deboss floors need either a shallower recess or the bridging-specific slicer
settings the back-shell read recommends, and the same reasoning applies to the cap faces on the
back shell, where the span is **13.2 mm** rather than 2.6.

**P6 FAILS** → something much more interesting than a prediction is wrong, and everything above
is moot until it is understood.
