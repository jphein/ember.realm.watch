# Verification notes

Four faults on this project shared one structure, and naming it is worth more than the four
fixes: the fixes are specific, the structure keeps recurring. It has now appeared in
geometry, in rendering, in audio and in prose.

The corollaries below are separate lessons, collected here because each was learned once and
written into a commit message that nobody would ever read again.

---

## The pattern: an invariant that holds because something else absorbed the error

> **For each invariant, ask what could absorb a violation and still satisfy it.**

None of the checks below is a weak assertion. Each is an assertion whose **success
condition is insensitive to the failure mode it appears to guard**. They pass, and the
passing is sometimes *caused* by the defect's own symptom.

### 1. `check_tiling` passes on a flame that is silently clipped

The clearest instance, and the one the rule was derived from.

The display asserts a **write-once invariant**: every pixel in the flame band written
exactly once. Set `GRATE` 3→8 and `MAXH` is forced down. **`MAXH = 65` passes
`check_tiling` and is still wrong** — it lets a flame reach into the fuse rows. But the
fuse branch runs *before* the fire logic:

```cpp
if (r < FUSE_H) { …; continue; }
```

So an over-tall flame is not rejected, it is **clipped flat**. Every pixel is still
covered exactly once — by the fuse. **The assertion is satisfied by the very mechanism
that conceals the defect.**

(The correct value is `MAXH = 64`, not 63: a 5.9% flame-height loss, not 7.4%.)

### 2. A boolean clearance check cannot fail on empty space

The enclosure's boolean check reported **0.000 mm³** interference through every
revision — correctly — while the stand covered **19.5% of the screen**. Nothing
intersected. The stand was simply *in front of* the display.

**A test that measures interference is structurally blind to occlusion.** No amount of
tightening it would have helped; it was answering a different question.

The same check was blind to the buttons being **100% buried** inside the stand, and to
there being **6 mm** of room where a USB-C plug needs 18–20 mm.

### 3. Sampling the one locus where the discrepancy vanishes

The USB-C well was cut as a flat box while the slab slot's bottom face **tilts** — front
corner at z ≈ 26.4, rear at ≈ 21.6 — leaving a wedge of material exactly where the plug
emerges.

It measured as "20 mm clear" because the check **point-sampled the centreline**, which is
the single locus where that discrepancy is zero. A plug has width; its front corner hit
the wedge.

### 4. `esphome config` passes with a broken `static_assert`

The same shape in a *tool*, and it invalidated a verification instruction I had given.

Adding a `static_assert` to a display lambda, I asked for it to be verified with
`esphome config` — no device touched, returns `Configuration is valid!` with the two known
GPIO45/46 strapping warnings and nothing else.

**It also returns exactly that with the assert deliberately broken.** `config` validates
YAML and *never builds the lambda*, so its success condition is entirely insensitive to
whether the C++ compiles at all.

`esphome compile` is the stage the change actually lives in, and also needs no device. It
reported the assert firing, attributed to the **YAML line** with the arithmetic spelled out:

```
esphome/ember-satellite.yaml:3369:35: error: static assertion failed: MAXH is too tall
for GRATE: the tallest flame reaches into the fuse rows and will be silently clipped flat.
note: the comparison reduces to '(74 <= 73)'
```

> **Know which stage of a toolchain your change lives in, and verify at that stage.** A
> green result from an earlier stage is not weak evidence — it is *no* evidence.

### 5. A test that could not fail at all

The clearance checker once returned a confident `CLEAR` that meant nothing: the vendor
STEP lives in its own coordinate frame while the parts are in board coords, so the two
**never overlapped in space** and every boolean returned empty.

It surfaced only because a bezel was deliberately sunk 2 mm into the board and the
detector *still* said `0.000`.

> **There is now a permanent self-test doing exactly that, and it must report
> `1467.842 mm³`. If it ever reports zero, the checker is broken — not the parts.**

---

## Corollaries earned the hard way

**A test that cannot fail is not a test** — and the refinement: a test that cannot fail *for
the property you care about*, while passing for one you don't. Prove the detector detects,
with a case whose answer you already know, on every run.

**Prove it at the boundary, not just somewhere past it.** "Fails at 65" is much weaker than
"passes at 64 and fails at 65", because the first is satisfied by an assert objecting to
something adjacent. The flame-height assert was checked across three `GRATE` values — limits
69, 64 and 56 computed independently — and the PASS/FAIL flip landed **exactly** on the
limit in all eight cases.

**Prefer measuring the artifact to reasoning about the source.** Four defects here were
invisible in correct-looking source and obvious in the rendered output — including a "Buy
the board" icon that was valid SVG and rendered as a trash can, an `<audio preload="none">`
over a `data:` URI that could not be lazy because the bytes are part of the document, and
an exploded view rendered edge-on because the camera was placed to satisfy an aspect ratio.

**Adding a caveat can invalidate a claim elsewhere in the same document — and the source
view is the one place you will not see them together.** Writing the vendor-STEP caveat into
`docs/enclosure.md` (*"contains no small holes, not one via, and no switch body of any
kind"*) left it sitting directly beneath an older claim that the same file makes *"the mic
port, speaker header, SD mouth, BOOT/RESET positions and rear LED all land correctly by
construction."* Two adjacent claims in direct conflict, which is worse than either alone: a
confident assertion followed by a contradiction, with nothing telling the reader which
governs. They are far enough apart in the markdown to seem unrelated and adjacent enough on
a rendered page to be obviously wrong. **Render the document you just edited.**

**Ask the hardware, not a model of the hardware.** Three separate audio fixes converged on
this: guard on `spk->is_running()` rather than a per-call-site flag; hold the DAC muted
whenever the speaker is stopped rather than at enumerated sites; gate the amp on the
speaker. Each covered failure modes nobody had enumerated, and the tell that the shape was
right is that the *specific* guards became redundant.

**A cost argument a profiler can dissolve is worse than none.** A hex field behind the
flames was rejected twice on cost — first at +2000–3000 runs/frame, then on a per-pixel
argument — and *both reasons evaporated under measurement*. The runs axis does not bill
(`horizontal_line` is a bare per-pixel loop with no span fast path) and per-pixel does not
grow either, because the row is pre-assembled into `drow[]` by span memsets, which a
background field would reuse. The real objection was never cost: **the flame band is a
status display read at a glance across a room, and texturing its background degrades the
figure-ground contrast that is the band's entire function.** Argue on the axis that actually
decides it, or someone with a profiler will overturn a correct conclusion.

**Refuse to inherit a conclusion whose stated reason has been retracted.** When the runs
figure was withdrawn, the rejection it supported was re-examined rather than kept — even
though the rejection turned out to be right. A conclusion held for a reason you have
abandoned is indistinguishable from one held for no reason.

**Do not propose a middle option you have not looked at.** "Squashed hexes at GRATE=3, no
`base_row` move, no `MAXH` change, strictly better" was suggested untested — by the same
person who had just criticised an untested cost estimate. Implemented and rendered, it cost
+96 runs and tiling passed, and it **did not read as a honeycomb at all**: at three rows a
hexagon has no room for a silhouette and renders as a perforated dark rule, visually
identical to the option it was meant to beat. The original instinct it overrode was correct.

**A falsified conditional is worse than an open question**, because it reads as analysis.
If "if X dominates, then Y" resolves false, delete it — do not leave it in a document
looking measured.

**Do not produce a number you know will mislead.** Host-timing a display harness whose
mock writes to host DRAM understates the per-pixel term against octal PSRAM, and would
have pointed at the wrong dominant axis *with a stopwatch attached to look authoritative*.
Declining is harder than measuring and was the right call.

**When you delete something, grep for what was waiting on it.** A guard whose premise has
been removed does not become harmless — it becomes a timeout. Removing the tone from the
talk path left a `wait_until: speaker.is_playing` with nothing to wait for; it burned its
full 1500 ms before every tap, and the microphone opened too late to hear anything.

**A report goes stale like any other artifact — and nothing sits beside it to disagree.**
One agent told another she had *deliberately not* added a flame-height assert, with sound
reasons. She was then asked to do it, solved the structural objection rather than accepting
it, and never amended the earlier message. **True when sent, false when read.** The second
agent avoided opening an issue against finished work *only* by reading the file instead of
trusting the report.

This is the same failure as a stale comment or a superseded print sheet, with one difference
that makes it worse: a stale comment sits next to code that contradicts it, so a careful
reader has a chance. **A stale message has no artifact beside it.** Two disciplines, and both
are needed: when something you told someone stops being true, tell them — and when a report
claims something about an artifact, check the artifact.

**Verify against the remote, not the local tree.** Everything can look finished locally —
commits present, tree clean, device confirmed by ear — while the remote still contains
every bug. And when grepping a *rendered* document for a phrase, flatten whitespace first:
a per-line search on wrapped text gives false negatives, which is how literal `**` markers
survived on a published page.

---

## Where the invariants live

| check | file | what it proves |
|---|---|---|
| boolean clearance + sunk-bezel self-test | `enclosure/ember_case.py` | parts do not intersect the board, **and the detector works** |
| `_check_geometry()` | `enclosure/ember_case.py` | no screen occlusion; ≥16 mm for a USB-C plug; ≥12 mm slot engagement |
| grille web + open area asserts | `enclosure/ember_case.py` | printable material between apertures; open area above the driver's radiating area |
| minimum feature by **morphological opening** | `enclosure/tools/make_wyrm_spans.py` | traced art is printable — see the note below |
| `check_tiling`, write-once | `esphome/art/dragon_harness.cpp` | every pixel in the band written exactly once |
| `CLAIMS` / `BLOCKED` provenance guard | `site/og_card.py` | the build **refuses** to emit a known-wrong engine name |

### On measuring minimum feature size

Two metrics were tried and both returned confident, wrong numbers:

1. *"Grow until the thinnest row-run clears the floor"* — never terminates usefully.
   Dilation always creates 1 px boundary rows, so the measure never improves. It ran to
   6 px and **tripled** the silhouette's area before anyone noticed.
2. *"The k at which erosion empties the mask"* — that is the **thickest** feature. The last
   region standing is the fattest one. It cleared a 0.6 mm tail tip as though it were
   4.9 mm.

**Morphological opening is the honest test:** a feature thinner than 2k does not survive
erode-then-dilate by k. Neither wrong metric was ever checked against a shape whose answer
was already known.
