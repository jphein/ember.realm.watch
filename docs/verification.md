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

### 5. The right number, about a part that did not exist

The purest form of the pattern, and the closest one to being printed.

`RegularPolygon(R, 6)` is **flat-top** — two vertices share the maximum Y, so a cell is `2R`
across corners in X. Both hex lattices spaced columns at `dx = aflat + web`, which is
*pointy-top* spacing. At R = 3.75 that is a **7.500 mm cell on a 7.395 mm pitch**: the cells
overlapped, the web went negative, and the field fused into **one solid instead of 33**.
Flood-filling it showed 43 loose prisms of 2.53–5.38 mm² spanning the full wall. It would
have printed as a single 37 × 24 opening with loose triangles rattling in it.

**The asserted open area still measured ~673 mm², exactly on target.** Area is insensitive
to whether a region is *connected*, so the number was right while the part was ruined — and
the comment promising "0.80 mm of material remains between slots, still printable" was false
as built. The back panel's stated 0.80 mm web measured **0.305 mm**.

The assert is now on the property that actually matters:

```python
assert len(_cells.solids()) >= 30
```

> **Assert the property, not a proxy for it.** An aggregate — area, volume, a count of
> writes — can be exactly correct about something that is structurally broken.

**A postscript that sharpens this rather than softening it.** `len(_cells.solids())` counts the
**cutting tools**, not the holes they leave in the part. It is exactly right for the question it
was added to answer — *have the cells fused into one solid?* — and it is **not an aperture
count**, which is how the line reads. Measured on the field as built: **33 cells placed produce
27 openings**, six being clipped away by the field's rounded corners, and the assert would pass
identically at either number.

So the replacement for a proxy was another proxy, and that is fine as long as it is *named*.
The rule survives with a clause: **assert the property, and then say which property**, because
the next reader will take the count for the thing it superficially describes. The same field
also has two open areas — a **678.0 mm² throat** across those 27 apertures and an
**886.1 mm² mouth** in a single opening, since the flare merges the face on purpose — so
"the grille's open area" was ambiguous for as long as it went unqualified, while every number
attached to it was correct.

**A second postscript, and this one caught the person quoting the rule.** The back shell's
countersink is cut at **84.7°** against a standard 90° screw head. The instruction issued to fix
it was *"assert the included angle, not the mouth diameter"* — which sounds exactly like this
section's advice and is wrong, because **a flat head does not seat on an angle. It seats on an
angle *and* a diameter.**

The geometry is unforgiving about it. Two 90° surfaces have parallel flanks, so if the cone's
mouth is wider than the head, the head simply descends until its **rim** meets the wall, at
`s = (mouth − head) / 2`, touching along a line instead of over the cone:

| cone | 6.00 head | 6.40 head | 6.72 head |
|---|---|---|---|
| ⌀6.70 × 1.70 — 90°, mouth left free | sinks 0.35, rim only | sinks 0.15, rim only | proud 0.01 |
| ⌀6.40 × 1.55 — 90°, mouth = head | sinks 0.20, rim only | **flush, full conical seat** | proud 0.16 |

Widening the mouth to 6.70 makes the angle correct and the **seat worse** — a 6.00 head sinks
0.35 mm there against 0.22 in the part as built. **The corrected property was not the one that
governed the outcome**, which is this section's own failure mode, arriving inside an instruction
to avoid it.

The formulation that cannot be satisfied by the wrong thing is to **name the screw** and derive
the rest: `CSK_HEAD_D`, `CSK_HEAD_ANGLE`, depth computed from both. Then "which head is this cut
for?" has an answer in the source, and a different head becomes a *stated alternative* with its
own numbers rather than a caveat.

> **When a fit depends on two properties, asserting either one alone is a proxy.** The tell is
> that you can satisfy the assert and still be further from the goal than when you started.

### 6. A test that could not fail at all

The clearance checker once returned a confident `CLEAR` that meant nothing: the vendor
STEP lives in its own coordinate frame while the parts are in board coords, so the two
**never overlapped in space** and every boolean returned empty.

It surfaced only because a bezel was deliberately sunk 2 mm into the board and the
detector *still* said `0.000`.

> **There is now a permanent self-test doing exactly that, and it must report
> `1467.842 mm³`. If it ever reports zero, the checker is broken — not the parts.**

#### The same shape in a status probe: a query that answers about itself

Not an assert this time — a one-liner used to check whether a background job was alive:

```bash
pgrep -f make_renders >/dev/null && echo RUNNING
```

It reported `RUNNING` four times, over about an hour, for a process that **had exited within
seconds of starting.** `pgrep -f` matches against *full command lines*, and this command line
contains the literal `make_renders` — so pgrep found **itself**. The control makes it plain:

```
pgrep -f make_renders     -> MATCHED, and no such process exists
pgrep -f zzz_nonexistent  -> MATCHED (self)
```

A pattern that has never named anything still matches, which is the whole proof: the probe was
answering a question about **its own existence** rather than about the world, and it could not
return negative.

> **A process query whose pattern appears in its own invocation is querying itself.**

That single mechanism produced three different-looking bugs in one day, which is the reason to
name the family rather than any one instance:

| form | consequence |
|---|---|
| `pkill -f foo` | **kills its own shell** — the chained command after it silently never runs |
| `until ! pgrep -f foo; do …` | **never exits** — two waiters spun 46 and 35 minutes |
| `pgrep -f foo && echo RUNNING` | **always reports present** — four fabricated status lines |

Each reads as a different fault — a crash, a hang, a stuck job — and all three are one
self-reference. The fixes are trivial and worth having by reflex: bracket a character so the
pattern cannot match itself (`[m]ake_renders`), match on the interpreter and script path rather
than a bare word, or **do not ask about the process at all — ask about its output.**

The last is the one that would have worked here, and it connects to §26: *"no file yet" cannot
distinguish "still building" from "died on line one"* — but the **log** could, and it said so
from the first second. **When a cheap indecisive instrument and a cheap decisive one are both
available, the only reason to use the first is that it was already in your fingers.**

### 7. The reboot that verified the firmware also uninstalled it

The three-mode firmware was flashed OTA, and a hardware probe then rebooted the device to
check that the mode survived a power cycle. It did not: the mode select came back reading
`Normal` while the `Hush` switch still read `ON`. A real defect — the select was
`restore_value: false` with nothing re-syncing it from the persisted `op_mode`.

A fix was written, flashed, and the same probe re-run. **It reported the identical
failure.** The obvious reading — "the fix doesn't work" — was wrong, and the reason is
that the fix *was no longer on the device*:

```
[W][safe_mode:094]: OTA rollback detected! Rolled back from partition 'app1'
[W][safe_mode:094]:  The device reset before the boot was marked successful
```

`safe_mode` marks a boot good after **60 s**, and ESP-IDF rolls an unvalidated OTA image
back to the previous partition if the device resets first. The probe rebooted ~12 s after
upload. **The act of testing reverted the thing under test**, and the second measurement
was taken against the first binary — so it faithfully reproduced the bug the fix had
already removed.

Two claims were available and both would have been false: *"the fix doesn't work"*
(measured the wrong binary) and, had the probe happened to pass, *"the fix works"* (also
the wrong binary). The rollback was printed in the log the whole time.

> **After an OTA, read back what is running before concluding anything from its
> behaviour.** `[I][app:151] compiled on <timestamp>` must match the `build_time_str` the
> upload reported. Then wait for `[I][safe_mode:142] Boot seems successful` before any
> reboot-based test — until that line appears the device can silently revert underneath
> you.

Same family as the rest of this file, one turn further out: not an invariant satisfied by
the wrong mechanism, but a *test* satisfied by the wrong artifact. `esphome upload` ships
a stale binary; a rollback ships a stale binary *after* a correct upload.

### 8. The check's scope was one file; the claim's scope was the system

The mode patch carried a self-check that nothing still read `sw_hush` as state, and it
passed — proving all six touchpoints moved **inside `ember-satellite.yaml`**. The widened
meaning of `Hush` was then reported as handled.

It was not. Four tiles, one conditional card and two `mdi:microphone-off` icons in
`homeassistant/dashboards/ember-hearth.dashboard.json`, plus two sections of
`docs/home-assistant.md`, still told the reader that Hush *"gates the talk gesture"* and
that *"tapping the screen will not start a conversation"*. Every one became false the
moment the firmware booted — the same lie the spec had just deleted a dark-LED branch and
a telemetry string to avoid, surviving on a bigger screen.

An anchor assertion can only fail in a file it is pointed at. The count was also wrong on
the first attempt: the guard expected one stale icon and found two, because a fourth Hush
tile is named plainly `"Hush"` and only its *icon* carried the old meaning.

> **When a control changes meaning, the blast radius is every artifact that describes it,
> not every artifact that reads it.** Grep the entity id across the whole repo — docs,
> dashboards, packages — not just the firmware that implements it.

---

### 9. A total that absorbed a complete absence

The bezel's debossed honeycomb is generated by filtering a hex grid against keepouts, and it
is guarded by an assert. The assert read:

```python
assert _n >= 60, f"only {_n} hex cells landed on the bezel"
```

It passed. 75 cells landed, and 75 >= 60. **All 75 were in the chin and the rails had none** —
the nearest grid column missed the rail's 0.75mm-wide usable band by 0.05mm. The stand covers
86% of the chin and 0% of the rails, so the entire motif had landed on the one surface you
cannot see while the device is docked.

Applying the rule at the top of this file — *what could absorb a violation and still satisfy
this?* — the answer is immediate and should have been asked before the assert was written: **a
sum over regions can be satisfied entirely by one region.** The number was real. It was simply
not the property. The fix is a per-region dict with a non-empty assert on each, which no
single total can satisfy vacuously.

The same defect appeared twice more in the same afternoon, in different materials, which is
what makes it worth its own heading rather than a line in a list:

- **A raised feature on a bed face.** The button caps stood 1.20mm proud of the back shell's
  back face — which is the face that prints against the bed, so the part would have balanced
  on two hexagons totalling ~74mm2. What caught it was not a check but a **bounding box**: the
  part had grown from 14.40 to 15.60mm, exactly the cap height. Then the identical mistake was
  nearly made again on the *opposite* face of a *different* part, because the bezel prints
  front-face-down and the logo was going to be embossed. Twice in one session on two faces is
  a property of the process, not a slip: **on a bed face, relief only goes inward.**
- **A figure carrying its own copy of the geometry.** `make_renders.py` hand-wrote the button
  outline as a four-point rectangle instead of reading the part. Both copies happened to be
  rectangles, so they never disagreed and nothing was ever caught — until the part became
  hexagonal, at which point the *only thing anyone looks at* would have gone on drawing
  squares indefinitely. A second hand-drawn copy of geometry is not documentation of the
  geometry, it is a rumour about it.

### 10. A figure set that was individually accurate and collectively blind

Both buttons were **completely buried** by the stand: the BOOT cap's top edge sat 3.81mm below
the stand's rim with 0.40mm between the cap face and solid wall. Five figures existed. Not one
was wrong, and not one could show it — the exploded and print-layout views show the parts
separated, the hero shows the front, the back 3/4 shows the shell alone. **No figure put a
button and a stand wall in the same frame**, which is the only place the answer lives.

It was found by a person asking a question, not by a check: *"are those new hexagon buttons
tall enough? seems like there should be a tab to bring them taller to be more accessible when
in the stand."* The instinct was right and the diagnosis was better than the proposal — a
taller cap reaches nothing, because the obstruction is *beside* the cap rather than above it.

Two things follow. First, ask what each figure **cannot** show, and add the view that closes
the gap — the same discipline as asking what an assert would still pass on. That view is now a
permanent figure rather than a one-off check. Second, this is the **third** feature the stand
has quietly swallowed: the display, the USB-C plug, and now the buttons. There were asserts
for the first two. Nobody generalised. *"Does it collide"* and *"can you reach it"* are
different questions, and every feature a human has to touch needs the second one asked
explicitly — enumerate them rather than trusting that a previous assert's neighbourhood
covered them.

### 11. Every check passed; it breaks in your hand

The button pads are living hinges. A teammate, reasoning about how they would *feel*, observed
correctly that with equal hinge thickness the smaller hex always presses lighter — backwards
from the intent that RESET be shyer under the finger — and proposed thickening its hinge from
0.90 to 1.40 mm.

Bending strain in a flexure is `(t/2)·θ/L`, and **θ is not a free variable**: it is pip travel
over the pip's distance from the hinge. The *smaller* cap therefore has the *larger* angle,
because its pip sits on a shorter arm — 5.6° against 3.5°.

| | t=0.90, L=1.0 | t=1.40, L=1.0 | t=0.90, L=2.0 |
|---|---|---|---|
| BOOT | 2.75% | 4.28% | 1.37% |
| RESET | **4.37%** | **6.79%** | **2.18%** |

PLA yields near 2% and breaks in the 4–6% band. So the shipped RESET hinge was *already* over
strained, and the proposed cure took it further. **Strain scales with thickness — the fix
pointed the wrong way.** Lengthening the flexure fixes what actually breaks.

**What makes this its own entry is that no existing check objected to any of the three
variants.** The geometry is valid, nothing collides, the pad stays attached to its hinge, the
solid is watertight, it prints. Every assert in the file is about *shape*, and this is a
property of the *material* — it fails after a few dozen presses in a hand, which is not
somewhere a boolean can look. The lesson generalises past hinges: **ask which of your
invariants are about form and which are about matter, and notice if the second list is empty.**

A secondary point worth keeping: the diagnosis was right and the remedy was wrong. Accepting a
correct finding does not oblige you to accept the fix attached to it.

---

## The one variant no tool can catch

Every fault above yields to mechanism — a compile step, an assertion, a sanitizer, a
byte-comparison of rendered output. **One does not, and it is worth separating for exactly
that reason:** a list of failures that all submit to tooling invites the belief that tooling
is sufficient.

A report stated that `NC = 80` *"compiles clean and the harness reports ALL CHECKS PASSED."*
It was wrong. `NC = 80` had been run **only under AddressSanitizer**, and `NC = 40` **only
plain** — two real experiments, neither of them the configuration described. The claim
carried the authority of both and the coverage of neither.

**No tool can distinguish "I ran this configuration" from "I ran two adjacent ones and
described a third", because the artifact of a claim is prose.** There is nothing to compile,
nothing to diff, no assertion to add.

The two defences are procedural, and both were used the same afternoon:

> **Reproduce a teammate's result before building on it.** It cost one rebuild and caught
> this. The same discipline caught an issue about to be opened against already-finished work.
>
> **Say which configuration you ran, not which conclusion you reached.** A conclusion is
> compressed and its compression is where the coverage goes missing.

**And the same rule in the other direction, which is the one that is easy to skip: when a
teammate's report contradicts your own instrument, re-test before believing yourself.** The
forward form guards against inheriting someone else's error. The reverse form guards against
your own, and it is harder to apply, because the instrument is right there and it just ran.

It was worth exactly one re-check. A sweep reported that a control still lacked a boot resync;
the person who owned the file had said it was fixed. The regex was wrong (§18) and the report
about to be filed was false. **The disagreement itself was the signal** — not the confidence of
either party — and the cheap move was to spend one command finding out which side was broken
rather than to assume it was the other person's memory.

Both directions reduce to the same thing: a claim and an instrument are two artifacts, and when
they disagree, *either* may be the defective one. Nothing about having just run something makes
it the reliable half.

A related instance from the same session, self-audited: a twelve-row truth table reported as
verifying the audio gate in fact checked **a transcription of the watchdog, not the
watchdog** — so it proved the design coherent over its input space and said nothing about
whether the firmware implements it. It also hardcoded one input to its default, and that
input was the documented A/B knob for disabling amp gating entirely — precisely the case
where the other half of the gate carries it alone. True about what was run; overstated about
what it covered.

**Both failures share a shape: a claim one step wider than its evidence.** Neither author was
careless and neither claim was false — each was assembled from true parts.

### 12. A blanket caveat does not correct a specific wrong instruction

An improvement document listed, as its most urgent item, an instruction to gate wake-word start
on "the mode's listen bit" — warning that otherwise `ANNOUNCE`/`DISPLAY` would open the
microphone. Every noun in it referred to a **Revision-1 design that no longer exists**: there
are no such modes, there is no listen bit, and the current spec says explicitly that wake word
needs no mode gate at all. Following the instruction would have reintroduced the exact axis the
spec had deleted.

The document *did* carry a caveat at the top — "notes now read one mode narrower". That caveat
is true in aggregate and wrong about this item, which is not narrower but **void**.

**The asymmetry is the whole finding: a header is read once, and an instruction is read at the
moment of acting on it.** By the time someone is executing item four, the caveat is thirty
lines and several minutes behind them, and it did not say "some items are void" — it described
a uniform, milder drift. A caveat that under-describes the damage is worse than no caveat,
because it licenses exactly the confidence that skips verification.

So: when a document is superseded in a way that makes specific items *wrong* rather than merely
*dated*, mark the items. A note at the top does not reach the reader at the point of use, and
the point of use is the only place it would have helped.

Related, from the same pass: a comment claimed the DAC mute *slews*, citing register 37 as "the
ramp rate, 0x08". The ramp-rate field is bits 7:4, so `0x08` **disables** soft ramp — bit 3 is
`DAC_EQBYPASS`. The mute is a hard step. The comment reached the right conclusion (the amp, not
the codec, is what makes the silence gate work) **by accident, with the mechanism inverted** —
and it sat precisely where the next person would reason about the audio path.

### 13. A search that proves absence, with no control

An issue was closed with the comment *"zero occurrences … so both stale rationales are gone."*
Neither clause was true, and it only came out because a colleague happened to be editing the
very lines that were supposedly already gone.

- `grep -cE "REG37 is the DAC ramp rate"` returned **0 because the sentence spans a line
  break.** `grep` is line-oriented, so a claim wrapped across two lines matches nothing — and
  reports it as a confident zero, indistinguishable from real absence.
- The comment said **"both"** on the strength of checking **one** phrase. The second stale
  claim was still sitting at line 427, unlooked-for.

**The rule, and it costs one command: a check that proves ABSENCE must be run once against a
case where the thing is PRESENT.** A negative result from an instrument you have never seen
produce a positive is not evidence. `check_tiling` in this repo has exactly such a control;
that grep had none.

This was the **second** search the same day to hand the same person a confidently wrong count.
The other returned `1` — and the single match was **his own comment asserting there were no
callers.** A search that finds its own documentation and reports it as a usage is the same
failure wearing the opposite sign: the instrument answered a question about the text when the
question was about the code.

Note the shape it shares with §5 and §9: the number was real, the tool worked exactly as
designed, and the claim built on it was false. **`grep` counts lines matching a pattern. It
does not tell you whether a thing is true of a program**, and every step between those two
propositions is yours to justify.

### 14. "0 non-manifold edges", counted over an empty object

The repo asserted, in three documents, that **all parts are watertight with 0 non-manifold
edges.** The check behind it imported each STL with build123d and counted boundary edges.

`import_stl` returns a **single `Face` with zero edges, zero vertices and zero volume.** So the
count was 0 because there was nothing to count. Every part passed, always, including parts that
did not.

Run properly — arithmetic on the triangles, no CAD kernel required, every undirected edge shared
by exactly two and every directed edge appearing once — three parts were genuinely clean and the
front bezel had **9 non-manifold edges and 22 mis-oriented ones.**

This is §6 again, and the person who wrote it had spent the day maintaining this file. That is
the honest lesson: **knowing the failure mode does not confer immunity to it.** The tell was
available and unexamined — a *suspiciously* perfect result, reported instantly, over four parts
of wildly different complexity. A 12-triangle plate and a 10,000-triangle bezel with 107
debossed cells do not usually agree exactly.

The cause of the real defect was worth having: the mark is built from 104 stacked row-spans, and
wherever one row's run **ends** at exactly the x where the next row's run **begins**, two boxes
touch along a single edge. Edge-only contact between solids is non-manifold by definition, not a
rounding artefact. Inflating each span by 20 µm took 9 to 3.

#### The same trap in the vendor's file, and the rule that survives it

`import_stl` returning a `Face` with no edges is a search finding nothing because it looked in
the wrong representation. **The vendor's STEP does the same thing to whoever reads it.** Its
microSD socket is authored as **zero-thickness faces**, so a solid-only search returns nothing —
and the largest back-side *solid* near that region, an 11.15 × 14.15 mm plate standing
**0.50 mm** off the PCB, got taken for the socket instead. A microSD socket is 1.4–2.8 mm tall,
so the height ruled it out and nobody checked the height. It is the LCD driver flex.

> **A face-authored component is invisible to a solid-only search, and its absence looks exactly
> like the component not being there.** Two indistinguishable outcomes, one of which is a bug in
> the instrument. **Measure that file's faces, not only its solids.**

The consequence went further than a misnamed constant, and this is the part worth carrying. The
switch identification was built as: *the readable switch is the one on the microSD side* — a
direct bench observation — **plus** *the microSD is at x 33.68–44.83*. Correct observation,
correct inference, **fictional anchor**: the socket is on the other long edge, so the conclusion
inverted, and the published consequence was a big thumb-sized cap over the switch that reboots
the device.

> **A relative claim cannot be broken by mislabelling the thing it points at. An absolute one
> can.**

The bench fact was always relational — *this switch, that socket, same edge* — and **converting it
to a coordinate is what made it falsifiable by a component misidentification.** It never needed
an X value. When an observation is naturally relative, resolving it against a landmark buys
precision and takes on the landmark's error; if the landmark is only *believed*, that is the whole
of the claim's reliability, spent for nothing.

### 15. Four hypotheses, none tested before it was believed

Chasing the last three, four causes were proposed and each was acted on before being checked:
tessellation tolerance, diagonal-only pixel connectivity, the fusion method, checkerboard
corners at the outline. **All four were wrong.** Each cost a build.

What settled it was measurement rather than reasoning: the BRep is **valid** — one solid, 986
faces, zero boundary edges — and the count is 3 whether the union is built in 2D or 3D, at
tessellation tolerances from 0.1 to 0.001, before or after `clean()`. It is a mesher artefact at
coplanar face seams in a correct solid.

Two things generalise. **A fix that helps but does not finish is information** — 9 → 3 → 3 said
the remaining defect had a different cause, and that was visible after the second attempt rather
than the fourth. And **the project's own rule was available the whole time**: rendering and
looking beats reasoning about the source, and the pixel dump that ended the guessing could have
been the first step instead of the fifth.

It is now recorded as a **number, not a threshold** — `KNOWN_NONMANIFOLD = {"ember-front-bezel":
3}` — with the cause documented, a boundary edge failing the build outright, and an explicit
instruction not to raise the baseline to make a build pass. A known defect with a stated cause is
honest; a green light over an unmeasured one is not.

### 16. A measurement that was right along one axis and wrong along the others

A new variant, and the first one here where the check **fired correctly and reported the wrong
number**. Not a check that could not fail — a check that failed *selectively*, along directions
nobody had enumerated.

A print-readiness audit reported two features below the 0.80 mm two-extrusion floor: **0.75–0.90 mm**
in the stand and **0.60–0.75 mm** in the back shell. Both were real features in real places. Both
numbers were wrong, and both were wrong in the alarming direction. Re-measured, they are the
**stand's grille web at 0.900 mm** and the **back panel's web at 0.808 mm** — i.e. `HEX_WEB = 0.90`
and `_hex_panel`'s `web=0.80`, exactly as declared, to within 8 µm. **Neither part has a
sub-nozzle feature.** A day went into hunting for a structural sliver that was a documented print
floor with a bad ruler held against it.

Two causes, both in the metric this file already recommends:

**The structuring element is anisotropic.** `opening_loss` erodes and dilates with a
**4-connected** neighbourhood, whose k-step ball is an L1 diamond. Its width in direction **n** is
`2k·px·max(|nx|,|ny|)` — full across the axes, only `1.41·k·px` across the diagonals. So it
measures an axis-aligned wall correctly and a 45° wall as up to **29 % thinner than it is**, or
misses it entirely. This part is 15° slot faces, 24° raked grille bores and hex webs at 0/60/120°:
of the 226 webs in the back panel, **186 have normals at 60°** — the population the diamond
mis-measures. The metric was validated on the wyrm silhouette, which is axis-aligned pixel art.
**It was correct for the shape it was written against and was then reused on tilted geometry.**

**And it under-reports at the bin edge, so the quantisation caveat points the wrong way.** The
documented caveat is that a reported 0.60 means `[0.60, 0.75)`. It does not: a band survives
erosion by k only if its *rasterised* width exceeds `2k·px` **everywhere along its length**, so a
band at or just above the bin edge erodes to nothing wherever rasterisation rounds down. A true
0.900 reports 0.75 and a true 0.800 reports 0.60. **The true value can be above the bin, not
inside it** — which is exactly the direction a caveat must not be wrong in.

**What settles it is a positive control with an orientation in it.** Plant a 0.600 mm rib twice,
once axis-aligned and once at 45°, and require both found at that width and a 1.500 mm rib
ignored. The diamond finds the first and **misses the second completely**. That control is four
lines and it would have caught this the day the metric was written — the existing one asserted
`k2_loss < 0.005` on a shape whose answer nobody knew independently.

The replacement is not a fourth metric. **Opening was always the right idea**; only the ball was
wrong. Open with a **Euclidean disc** — two distance transforms, exact and O(n): a disc of radius
`r` fits at `p` iff `EDT(mask)[p] ≥ r`, and the opening is everything within `r` of that set. Then
**read the thickness off the EDT rather than off the threshold that found it**: `2·max(EDT)` inside
a located blob *is* its local thickness, continuous-valued, so the `2k·px` ladder and its caveat
both disappear. That is where 0.900 and 0.808 come from.

Three things generalise:

- **A metric has a domain of validity, and orientation can be part of it.** "Thinner than 0.80 mm"
  sounds orientation-free and is not. Anything built from a discrete neighbourhood inherits that
  neighbourhood's geometry, and the inheritance is invisible in the call site.
- **A wrong number is more expensive than a missing one**, because it is actionable. "No result"
  gets re-measured; "0.75 mm in the load path" gets hunted. The first hypothesis on record placed
  the stand's feature between the slab slot and the USB-C well — and those two cuts share one
  `Pos·Rot` frame with `align=MIN` and `align=MAX` at the same local `z = 0`, so **they are
  coplanar and no sliver between them is geometrically possible.** Two lines of source refuted it;
  the number's authority meant nobody read them.
- **Localise before attributing.** A z-range is not a finding. Labelling the thin material as
  connected components in 3-D gives each feature its own XY extent and its own bounding planes,
  and then the attribution is read off the mesh instead of argued. The stand's web was confirmed
  by predicting the *whole lattice* from the constants — five rows at 6.4044 mm pitch, alternate
  rows offset by exactly `dx/2` — and finding all five. One blob that fits a story is §15 again;
  a periodicity that matches to within a pixel is a fingerprint.

A fourth, found while writing this up and belonging to the same family: the first version of the
new locator reported a blob of 7.804 mm³ over 13 layers — 3.0 mm² per layer — alongside a "max
layer area" of 38.01 mm². Those cannot both describe one feature, and the blob's z range ended at
exactly `z = ST_H`, the rim's horizontal top face. It was the tangential-slice artefact already
recorded above, surviving a ≥3-layer persistence filter because the spurious sheet was
3-D-connected to a genuine sliver beneath it. **Summarising a profile by its maximum is how ~90
separate bridges became one 55.9 mm bridge**; print the profile.

**And the replacement metric has its own direction of blindness, which is stated in the tool
rather than left to be discovered.** A smooth surface running nearly *tangent* to the voxel grid
produces a false thin region: rasterising a smooth convex boundary makes a staircase, and a
staircase is locally **concave** at every riser, so disc-opening clips the long shallow treads
that appear where the surface is almost parallel to the grid. On the stand it shows at the left
rear corner where the R10 arc leaves the straight side x = 0 tangentially — 0.36 mm² per layer
over the full 40 mm height, reported at 0.618 mm. **The solid runs continuously from x = 0.00 to
63.90 behind it.** The discriminator is *void on both sides*: a real thin feature has void within
the threshold on two opposing faces, a tangency artefact has void on one and the whole part on
the other. This is the Z tangential-slice artefact arriving in XY. **Every discretised metric has
a direction in which it lies; the work is knowing which one, not believing there isn't one.**

Two smaller lessons from landing the fixes, both about numbers rather than checks:

- **A coefficient captured at one operating point, reused as if it were the law.** The grille's
  flared bores merge when `sqrt(3)·flare` exceeds `HEX_WEB`. The merge *threshold* was derived
  correctly as `HEX_WEB/√3 = 0.5196`, but the residual web at a candidate flare was then computed
  as `0.90 − 1.0392·flare` — and **1.0392 is √3 × 0.60, the growth at the flare that happened to
  be in the file.** It gave 0.432 mm where the truth is 0.1206 mm, and it survived because it was
  the right number one line earlier. A constant lifted out of a worked example carries that
  example's operating point with it, invisibly. The guard is now the general form written out:
  `GRILLE_MOUTH_WEB = HEX_WEB - sqrt(3)*GRILLE_FLARE`, evaluated at import.
- **An area floor in pixels is not a tolerance.** The new metric's artefact filter was
  `AREA_FLOOR_PX = 44 # ~0.25 mm2 at px=0.075`. The enclosure grids at 0.075 mm/px; the wyrm
  silhouette grids at 0.3083, where the same 44 px is **4.18 mm² — a floor 17× larger**, which
  swallowed the tail extremities and reported a minimum four times too coarse. It is now derived
  from the threshold (`2r²`, ~9× the unavoidable corner loss) and therefore scale-free. The
  earlier version of this same mistake is in the file above: a metric validated at one scale and
  reused at another.

Landed with each new guard **proved at its boundary**: 40 sweep cases, every PASS/FAIL flip
landing exactly on a limit computed independently of the assert's own expression. Two of them
reject the geometry that shipped — the pip clearance goes negative at the previous `PIP_D = 4.00`,
and the wire saddle's rim rule rejects the previous `WIRE_X = 57.0` for the 0.85 mm fin it left on
the bearing rim.

**And then the replacement metric was wrong twice more, in the same family as the three before
it, written by the person who had just catalogued them.** Recorded in full because the pattern is
the point — *knowing a failure mode confers no immunity; only a control that can express it does.*

- **v1 took the maximum over a blob at a fixed ceiling.** On a located rib that is exact, and it
  is where the two correct enclosure numbers came from. On a *whole object* it returns the fattest
  point: at r = 10 px a 50 px-tall silhouette does not survive opening at all, every pixel became
  one region, and `2·max(EDT)` over it returned **5.2688 mm — precisely the creature's own
  thickest half-width doubled.** That is failure #2 above, verbatim, recommitted. It reached a
  generated file and a commit message before anyone measured it.
- **v2 swept the threshold upward and took the first region.** That fixes the whole-object case and
  introduces a quieter error: below its true thickness a feature is only *partially* opened, so
  what appears first is its 1–2 px **edge shell**, whose max EDT is a fraction of the real
  thickness. On a planted 0.600 mm rib it returned 0.450. Granulometry under-reads the same rib for
  the same reason, so **both agreed and both were wrong** — agreement between two methods that
  share a bias is not corroboration.
- **v2 also carried a `max_frac` guard** meant to reject "the region is the object". The control
  caught that too: in a shape where the thin rib is legitimately 67 % of the area, the guard
  rejected the correct answer. **A crude proxy for "void on both sides" rejects real features as
  readily as artefacts.**
- **v3 has no threshold at all.** The thickness at a feature's medial axis is `2·EDT`, so the
  thinnest feature is twice the smallest *ridge* value of the distance transform. Exact on a rib,
  independent of the object's size, independent of any upper bound, with no tolerance absorbing
  anything. It returns 0.600 on both planted shapes.

Two tells generalise, and both were sitting in plain output. `nebula-site` reached the same
tautology from another direction and their formulation is the sharper one: **a measurement landing
exactly on its own threshold is a question, not a pass** — their harness printed `minfeat 0.900`
to three decimals. Mine landed on **the object's own thickest dimension** to four. Neither of us
looked at the column that said so. And **a volume and a layer count that disagree about the same
feature** — 7.804 mm³ over 13 layers is 3.0 mm² per layer, reported beside a "max layer area" of
38.01 — is the same tell in arithmetic form.

The consequence outside the tooling was a **wrong explanation given to the user twice**: that the
bezel mark "cannot fill the brow because the print floor pins it" and is "as large as printability
allows". Both have the sign inverted. **Scaling up multiplies every feature size, so a larger mark
is strictly safer to print — the print floor bounds the scale from below and cannot cap it.** The
mark's real thinnest feature at the shipped scale is **1.800 mm against a 0.90 mm floor**, twice
the limit. The geometry was left untouched (a physical part exists and is fine); only the reason
was corrected, in the docstring that carried it.

> **The magnitude moved three times — 4.27× → 1.12× → 2.00× — and the SIGN survived all three
> unexamined.** That is the finding, not the arithmetic. A quantity being re-measured is normal
> and healthy; a *direction* that every one of three successive measurements took for granted is
> a different kind of error, because each re-measurement felt like scrutiny and none of it was
> pointed at the assumption. **Check which way the inequality runs before refining the number in
> it.**

And the reason a positive control is necessary rather than sufficient:

> **Two methods agreed and both were wrong; shared bias is not corroboration.** The granulometric
> bound and the upward threshold sweep both under-read a planted 0.600 mm rib as 0.450, *for the
> same underlying reason* — below its true thickness a feature is only partially opened, so both
> were reading its edge shell. Their agreement was not evidence; it was the same mistake counted
> twice. **Agreement between two instruments that share an assumption is the most convincing
> available form of being wrong**, and it is why the control has to plant a shape whose answer is
> known independently rather than compare two derivations of the unknown.

Two smaller notes from the same pass, both about *how* a correction is phrased rather than whether
it is right:

- **"Stale" and "wrong" are different accusations, and the difference is this file's whole
  subject.** A hazard comment on a duplicated constant was written up as having been *wrong*; it
  had been **true when written** — the constant really was on two consecutive lines — and a later
  partial fix (deleting one line, keeping the comment) is what made it stale. Recording it as
  wrong misattributes the fault to the author instead of to the fix that left its own explanation
  behind. **A fix that does not update its rationale manufactures the next stale comment.**
- **A corrected number placed next to an uncorrected one, with neither subject named, reads as a
  contradiction.** The bezel mark's *ink* centre is 20.525 and the *mark-plus-port group* centre
  is 25.000, exactly; both are true and an assert protects the second. Reporting "not centred on
  25.000" refuted a claim nobody had made. **State the subject, not just the value** — especially
  when correcting someone.

### 17. Absence of a log is not absence of execution

A boot-time resync was added and instrumented with a log line. The line never appeared. It was
re-instrumented unguarded — nothing. Moved to its own trigger so no earlier action could block
it, and raised to ERROR level so nothing could filter it — still nothing. Three flashes, each
concluding the code had not run.

**The code had been running the whole time.** `esphome logs` subscribes over the device API
*seconds after the device boots*, so a line emitted during `setup()` has no connected listener
and is simply gone. The transport was never live at the moment being measured, and that was
assumed rather than established.

Every check along the way was sound and every conclusion drawn from them was wrong: the
generated code was confirmed present in `main.cpp`, the logger was confirmed at DEBUG with no
tag filter, and the boot log was confirmed captured across a reboot with a client attached. All
true. None of them established the one thing that mattered — **whether a listener existed at
the instant the line was emitted.**

The fix was to stop testing the messenger and test the thing: wait until a client is certainly
attached, then **read the hardware register back** and print it beside the value it should hold.
That returned `number=42dB | codec REG16=0x07 (42dB) | MATCH` on the first try — and 42 dB is
not the default, so it is the case that was actually broken.

**The general form: when an observation is negative, ask what would have to be true for a
positive to reach you.** A silent instrument and a silent subject are indistinguishable until
you prove the instrument can speak. §13 is the same rule for `grep` — a search proving absence
needs a positive control — and this is that rule for logging, arrived at again by paying for it.

Worth noting the cost honestly: four flash cycles on a diagnostic line, versus one on the
measurement that settled it. The measurement was available from the beginning and was reached
only after the inferences ran out.

### 18. Four searches, each returning a true number about a narrower question

The faults in this entry are not in any artifact under test. They are in the **instruments
written to check it** — four of them, in one afternoon, by one person who spent that afternoon
reading this file. Every number they produced was real. Every one answered a question narrower
than the one being asked, and three of them had a claim already drafted on top.

- **A `grep -c` whose positive control could not run.** Checking whether a commit contained a
  fix: `git show …| grep -c "boot resync" && echo control… && grep -c mic_gain_num`. `grep -c`
  **exits 1 when the count is zero**, so the `&&` chain broke and the control never executed.
  The bare `0` came from an instrument that had never been shown to produce a positive — §13
  exactly, committed in the act of applying §13. Re-run with `|| true` per count, the control
  returned 4 and the 0 became trustworthy. **A control downstream of the thing it controls for
  is not a control.**
- **An `innerText` slice that cut before the match, then a shadow boundary that hid the rest.**
  A DOM probe classified cards by `innerText.slice(0, 34)`. The card it was hunting begins
  `0 · 6 · 12 · 18 · 24 · 30 · 36 · 42` — the matched word sits past character 34. Widening the
  slice did not fix it either, because `innerText` **does not cross a shadow boundary**, so
  every markdown card returned `''` and was invisible to any text filter at all. The probe
  visited them and reported them absent.
- **A denominator counting things that were never eligible.** "card-mod injected into **0 of 12
  tile cards**" was reported as a repo-wide styling regression, with a request that someone go
  and look. Only **3** of those 12 carry a `card_mod` at all; the other 9 correctly receive
  nothing. On the loads that were measured it was **3 of 3 eligible** — a working system. §9's
  shape from the other side: there, a sum was satisfied by one region; here, a ratio was
  poisoned by counting nine cards that had never asked for anything.
- **A regex matching one of two spellings of the same reference.** Sweeping for restoring
  controls that lacked a boot resync, `id:\s*spk_volume` found nothing, because that control is
  resynced through a lambda — `id(spk_volume).state` — not a YAML key. The draft finding read
  *"the identical bug is still live for Speaker Volume."* It was false.

**The general form: a search returns a true fact about its own pattern, and every step from
there to a claim about the program is yours to justify.** §13 says this for absence; this entry
says it for *shape*. `grep -c` counts matching lines. A slice matches a prefix. A ratio counts
whatever you put underneath it. None of them was wrong, and none of them was asked the question
the report went on to answer.

**A search can be caught by its own arithmetic, with no need to know the right answer in
advance.** A later probe grepped generated C++ for `ui_mode->value != 0`, got **0**, and was one
keystroke from reporting that a patch had not made it into the binary. What stopped it was that
the same file matched `ui_mode->value` **28 times** — and no file can contain 28 occurrences of a
substring and zero occurrences of *every* string beginning with it, so the fault had to be in the
pattern rather than in the build. (ESPHome generates globals as `->value()`, a method call. The
patch was there; two spellings in a row were not.)

That is a different instrument from a positive control, and worth keeping beside it because it
applies where a control cannot. **A positive control needs a case whose answer you already know**,
which for a one-off search you usually do not have. **A self-consistency check needs only two of
your own queries that cannot both be true**: broaden the pattern, and confirm the count moves the
way the narrow one implies. If a strictly broader pattern does not match at least as much, the
pattern is the defect and no further reasoning about the subject is warranted. It costs one
command and it is available even at the moment you are about to file the finding.

**What caught them is the uncomfortable part: three of the four were caught from outside the
instrument.** The `innerText` failure surfaced because a *screenshot* showed an ember-styled pill
on screen while the probe was calling the palette dead. The denominator failure surfaced by
counting eligibility statically, in the source, where no page-load timing was involved. The regex
failure surfaced only because **a teammate's message contradicted the instrument, and the
instrument was re-tested instead of trusted** — the reproduce-before-building rule running
backwards, and the only defence in this list that was not a better check. An instrument cannot
audit itself; something with a different failure mode has to disagree with it.

A fifth fault compounded the third and is a different shape worth naming separately: the page was
**sampled before it had settled.** card-mod applies on a delay — at an 8 s settle 0 cards are
styled, at 14 s and beyond all eligible ones are. The screenshots were taken at 11 s and 20 s. The
same wrong answer then arrived three times and **repetition was read as confirmation**, when three
samples from one biased instrument are one sample. The tell was available and ignored: a system
reported as *totally* broken, while a correctly-styled element was plainly visible in a screenshot
already looked at. §14's lesson, again — knowing the failure mode confers no immunity — and the
firmware discipline that would have caught it existed in this repo already: **read back what is
running before concluding anything from its behaviour**, applied to a browser rather than a device.

The cost asymmetry runs the same way as everywhere else in this file. Each of these checks took
about a minute to write and none took longer than a minute to falsify once the right question was
asked. The expensive part was never the checking — it was a confident report sent to a colleague,
twice, and once with a request that he go investigate something that was not broken.

> **Verify your verifier.** The artifacts under test in this repo are checked, rendered, measured
> and read back off hardware. The greps and probes that check them have historically been written
> once and trusted immediately — which makes the checking apparatus the **least-verified thing in
> the project**, and it is the apparatus every other claim rests on.

---

## The cheapest countermeasure found so far: ask, don't assemble

Variant five above — a claim assembled from two adjacent true facts — has no mechanical
defence. But it has a cheap procedural one, and it was demonstrated rather than theorised.

An agent held two grep results that together suggested a conclusion about which code branch a
downstream artifact had modelled. **She declined to build the semantics, and asked a question
instead of filing a finding** — saying in as many words that assembling a conclusion from
adjacent true facts is exactly the failure the team had just catalogued.

That question got the tracing done by the person who owned the code, and it surfaced an
overstatement in an issue *he* had filed: he had written that a switch was "consulted nowhere
at runtime", which turned out to be true of the shipped default and false unconditionally —
the same shape, arriving from the other direction.

**The asymmetry is the point.** Her cost was one question. His was four greps and a case
analysis. And a guess that happened to land correct would have been indistinguishable from the
failure until somebody checked; the question was distinguishable immediately.

So: when you notice you are one inference away from a claim, the cheap move is to spend the
inference on a question to whoever owns the code, not on the claim.

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

**But looking is not sufficient, and knowing what to ask of the picture is the whole
skill.** The fused hex field was *rendered and inspected* before it shipped. At 2× the
flat-top cells are visibly interpenetrating — edges crossing, no material between them. The
inspection asked *"does this read as a honeycomb?"*, concluded yes, and wrote that it "reads
as a texture rather than as holes." It never asked *"is there material between the cells?"*
**The defect was in the pixels that were examined.**

> **A picture can confirm topology and composition. It cannot confirm a tolerance.** For a
> dimensional claim — a web width, a clearance, a minimum feature — measure the geometry:
> count solids, take a bounding box. 0.5 mm of web at figure scale is a handful of white
> pixels, and a reader reads texture, not calipers.

That is the same lesson as the open-area failure, arriving from the other side: **area is
insensitive to connectivity, and a picture is insensitive to tolerance.** Both were the
right measurement of the wrong property.

**Most of these were correct signals with wrong explanations attached, not missing signals.**
Three of the five faults found in a single afternoon had a true observation already in hand:
a `-Wunused-variable` documented as expected noise; a correct comment about mouth-variant
arrays transplanted onto `CW`, carrying the file's authority with it; and the flat-top
rendering *observed and reported* — as a styling inconsistency between the button caps and
the fields, one step from the defect. **The observation survives; the interpretation kills
it.** Invention has a tell. Transplantation doesn't. This is the class most worth mechanising,
because the signal was already there every time.

**A correct warning with a plausible explanation attached is harder to recover from than an
unexplained one.** This is the *inverted* form of the pattern — not a check that passed for
the wrong reason, but a warning that **fired for the right reason and got explained away.**
A `-Wunused-variable` on `CW` was documented as expected noise, kept for mirror fidelity.
The compiler was telling the truth: `CW` is unused because the hot loop indexes `x >> 2`,
hardcoding `CW == 4`, so the file's own tuning advice (`NC 60->40 with CW 4->6`) silently
does nothing to `CW` and makes `NC = 40` read uninitialised memory — the right third of the
flame band renders from stack garbage while the harness reports `ALL CHECKS PASSED`, because
every pixel really is written exactly once, with rubbish.

The suppressing rationale was **true but incomplete**, which is precisely what made it
convincing. A false explanation gets challenged; a true-but-partial one gets accepted and
closes the question. It then compounded across three steps in a few hours: partial rationale
in the file → a second, invented rationale layered on top by someone who pattern-matched a
real comment from elsewhere in the same file → nearly recorded in an issue as settled
expected output. Two people actively hunting this exact shape, neither careless, each one
step short.

**Reachability is a lens none of these checks have.** Four faults share a kind that tiling,
compiling and clearance all miss, because they are about whether a *path exists* — and those
checks only confirm that code *on* a path is well-formed: the stand in front of the screen;
the buttons sealed inside it; a menu cursor advancing `% 4` onto a row that is never drawn;
and a submenu **enterable from the hardware button but not exitable from it** — a mode you
could not leave without a working touchscreen, in the menu that exists *because* recovery
must not need one. Output equivalence (`diff -rq` on rendered frames) proves pixels match.
**Nothing yet proves navigability.**

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
| **restore-without-resync** | `esphome/tools/check_restore_resync.py` | a restoring control cannot come back from a reboot lying about the hardware |
| **chime preempt guard halves agree** | `esphome/tools/check_chime_guards.py` | a chime case cannot be guarded in the enumeration and unguarded where the guard bites |
| **button-only navigability** | `esphome/tools/check_navigability.py` | every `ui_mode` is reachable, exitable and *actionable* without touch |
| **shipped art *tables* == harness art tables** | `esphome/tools/check_art_sync.py` | the 30 generated span tables the device runs are the ones the harness sanitises and tiling-checks. ⚠️ **Tables only.** The ~250 lines of painter *logic* are also duplicated and deliberately **not** guarded — the two copies are legitimately different text (`it.` stubs vs `id(...)`), so a diff would be noise rather than signal. That half closes when #10 removes the copy |
| **generated pages are current** | `site/check_generated_current.py` | the **published** page matches the source in the same commit |
| **served surface matches the remote** | `site/check_served_current.py` | what a **visitor downloads** is what `origin/main` would produce — 24 artifacts, incl. every STL download link |
| **dashboard is deployed** | `homeassistant/tools/check_dashboard_deployed.py` | the dashboard **HA is serving** is the one in git |
| **monitoring config is deployed** | `status.realm.watch/check_deployed_current.py` | the checks **actually running** are the checks committed |

### Two guards that exist because a note was not enough

Both of these started as documentation, and documentation is what failed.

**`check_restore_resync.py`** — `TemplateNumber::setup()` calls `publish_state()` and never
`control()`, so a `restore_value: true` control comes back after a reboot *showing* its stored
value while its `set_action` — the thing that writes the hardware — never runs. The entity and
the device disagree, and the entity is the one people read.

That was diagnosed for `spk_volume`, fixed, and written up **in a comment carrying the exact
source line numbers**. Then `mic_gain_num` was added 700 lines below that comment with the
identical defect. **The fix had been applied to an instance rather than turned into a rule**,
and a note saying "this component behaves like X" does not protect the next component that
behaves like X. The script is the rule: every `number`/`select`/`switch` with `restore_value`
*and* an action must be named by some `on_boot` trigger.

⚠️ **Its failure mode is quiet and the one immune case is the one you would test with.** For
mic gain the codec kept its compile-time default, so the divergence only appeared after storing
a *non-default* value. Set it to the default, reboot, and everything looks perfect.

It **deliberately does not check that the resync is correct**, only that one exists — claiming
more than it verifies is the thing this file catalogues. Current state: `number.spk_volume` and
`number.mic_gain_num`, both resynced. That the class has exactly two members was reached
independently by a second method, which is the only reason it counts as known.

**`check_generated_current.py`** — `docs/` is rendered, not written. `site/build.py` produces
`docs/index.html` from `site/index.src.html`, and `site/build_print_sheet.py` produces
`docs/print-sheet.html` from `enclosure/PRINT-SHEET.md`. Editing a source without re-running
its build leaves the **published** page stale while the repo looks entirely correct — so every
check that compares the repo against the truth passes, and only a visitor sees the old text.

Three instances in one day, escalating:

1. `docs/assets/case-hero.png` was one render behind the case geometry. Cosmetic.
2. The live status page ran **8 checks behind its own committed config** — four projects
   registered and not monitored.
3. `docs/print-sheet.html` kept saying **"⛔ DO NOT PRINT `ember-stand.stl`"** after the source
   had been cleared. That is the document somebody reads *while a printer is running*, and it
   was wrong in the direction that costs a part you could have had.

⚠️ **Nobody made a mistake in any of the three.** `enclosure/PRINT-SHEET.md` does not look like
a build input — it is a markdown file sitting in the enclosure directory, and nothing at the
point of editing says a page depends on it. **The coupling is invisible exactly where the
editing happens**, which is why the countermeasure has to be mechanical rather than a note
asking people to remember. That generalises past this repo: when a defect keeps recurring
without anyone being careless, look for a dependency that is real but unstated at the site of
the change.

Both scripts take `--self-test`, and both self-tests are written to **exercise the path that
runs in anger** rather than a parallel one. `check_generated_current.py` routes its real check
and its self-test through the same `_compare()`, and requires *two* results: zero reports when
the pages are current, and one report per pair when deliberately-stale bytes are fed in. **A
detector that always fires is as useless as one that never does**, and the first draft of that
self-test compared a string with itself plus a suffix — which would have passed forever while
proving nothing. That is §6 and §14 in a file whose whole subject is §6 and §14.

### Installing the hooks — `.git/hooks` is not tracked, so a fresh clone has none

```bash
printf '%s\n' '#!/usr/bin/env bash' \
  'root="$(git rev-parse --show-toplevel)"' \
  'staged() { git diff --cached --name-only; }' \
  'if staged | grep -q "^esphome/ember-satellite[.]yaml$"; then' \
  '  python3 "$root/esphome/tools/check_restore_resync.py" || exit 1' \
  '  python3 "$root/esphome/tools/check_chime_guards.py"   || exit 1' \
  '  python3 "$root/esphome/tools/check_navigability.py"   || exit 1' \
  '  python3 "$root/esphome/tools/check_art_sync.py"        || exit 1' \
  'fi' \
  'if staged | grep -qE "^(site/index[.]src[.]html|enclosure/PRINT-SHEET[.]md)$"; then' \
  '  python3 "$root/site/check_generated_current.py" || exit 1' \
  'fi' > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

Each guard fires **only when its own source is staged**, and that is deliberate rather than
lazy: **a hook that runs on every commit gets disabled, and a disabled hook protects nothing.**
The obvious improvement — make it run always — is the change that ends with someone typing
`--no-verify` by reflex.

### `check_served_current.py` is not a hook, and must not become one

It belongs to the **third** category above — *deployed is not served* — and it cannot run at
commit time, because at commit time there is nothing published to compare against. Run it
**after a push**:

```bash
python3 site/check_served_current.py                 # 24 artifacts, with the confirm pass
python3 site/check_served_current.py --no-confirm    # fast, and will lie right after a push
python3 site/check_served_current.py --prove-confirm # positive control: must stay STALE
```

⚠️ **`--no-confirm` immediately after a push measures the edge, not the push.** With confirm on
(the default) a mismatch is re-read after a delay and reported only if it persists, because one
read cannot tell a stale artifact from a stale edge. It prints `age=` / `cache-control=` on the
re-read so you can see which you hit.

### On measuring minimum feature size

**Three** metrics were tried and all three returned confident, wrong numbers:

1. *"Grow until the thinnest row-run clears the floor"* — never terminates usefully.
   Dilation always creates 1 px boundary rows, so the measure never improves. It ran to
   6 px and **tripled** the silhouette's area before anyone noticed.
2. *"The k at which erosion empties the mask"* — that is the **thickest** feature. The last
   region standing is the fattest one. It cleared a 0.6 mm tail tip as though it were
   4.9 mm.
3. *"Opening with a 4-connected structuring element"* — right idea, wrong ball. See §16: the
   L1 diamond is `2k·px` wide across the axes and only `1.41·k·px` across the diagonals, so on
   this part's 15°/24°/60° geometry it reported a 0.900 mm web as 0.75 and a 0.800 mm web as
   0.60. It also under-reports **at** the bin edge, so "0.60 means [0.60, 0.75)" is wrong in
   the unsafe direction.

**Opening is the honest test — with a Euclidean disc, and with the thickness read off the
distance transform rather than off the threshold that found it.** A disc of radius `r` fits at
`p` iff `EDT(mask)[p] ≥ r`, and the opening is everything within `r` of that set: two distance
transforms, exact, isotropic, O(n), and no `2k·px` ladder to caveat. `2·max(EDT)` inside a
located blob is its true local thickness — measured that way, the two webs above come out at
0.900 and 0.808 against declared 0.90 and 0.80.

**None of the three wrong metrics was ever checked against a shape whose answer was already
known**, and the fourth is only trustworthy because it is: a control plants a 0.600 mm rib
axis-aligned **and at 45°**, requires both found at that width, and requires a 1.500 mm rib
ignored. Orientation belongs in that control — it is what caught fault 3.

### 19. A null result that contradicted someone else's positive one

A teammate reported the stand's speaker-wire pass **92 % blocked** — a 0.474 mm membrane of
tape-pad material standing across its mouth, leaving a slit too small for the lead. Before
repeating that anywhere, it was re-measured independently: ray-cast the committed STL along
**+y** across the pass footprint and read off where material actually is.

**The re-measurement said the pass was clear.** Every sample point, every height, nothing in
the way.

The re-measurement was wrong. The ray test had been windowed to `y > 19.4` — *"inside the
pass"* — and the membrane sits at **y 18.50–19.00**, at the **mouth**, four tenths of a
millimetre before the window opened. Run over the full range it appears immediately and
unambiguously, the same interval at every sample:

```
x = 30 / 32 / 34,  z = 6.5 .. 10.5   ->  material y-interval (18.500, 19.000)
x = 30 / 32 / 34,  z = 6.1, 6.3      ->  no material          (the 0.40mm slit)
```

Had the first run been trusted, the finding would have been closed as *"cannot reproduce"* and
a 93 cm³ part — three quarters of the whole print — would have gone to the bed with its speaker
chamber sealed shut.

**Distrust your own null result, and check the instrument before you check the claim.** The
asymmetry is what makes this dangerous and it is not symmetric with a false positive: a wrong
*positive* finding gets scrutinised by whoever receives it, because it asks them to do work. A
wrong *negative* asks nobody for anything. It gets filed, it closes a thread, and the person it
convinces first is the one who produced it.

It pairs with §14 rather than repeating it. There, the tell was a **suspiciously clean pass** —
four parts of wildly different complexity agreeing exactly, instantly. Here the tell is a
**suspiciously clean absence**, and it arrived while someone else was holding a positive result
about the same object. Two people measuring the same part and disagreeing is not a tie to be
broken by seniority or by who measured second; it is a statement that at least one instrument
is pointed wrong, and the cheapest next move is to find out which.

The generalisable form: **an instrument's window is part of the instrument.** `y > 19.4` was
not a bug in the arithmetic — every ray was traced correctly and every intersection was real.
The defect was a bound chosen from an assumption about *where the answer would be*, which is
the one thing a measurement is not allowed to assume. Widen the window before concluding the
thing is not there.

#### The same lesson twice more, from the other side — and a limit on controls

A second instrument, built the same day to sweep the published site, reported **three stale
artifacts and all three were false.** It compared the served bytes against the **working
tree**, and a teammate had committed locally without pushing — so *"served differs from my
disk"* was perfectly true and completely uninteresting. The reference had to be **what the
remote would produce**, not what happened to be on one machine.

Then, fixed and pointed at `origin/main`, it produced a **fourth** false stale — this time
because it ran within a minute of a push:

```
t+25s   served = d5f4b1816960   want = c6083b3e3970   stale
t+50s   served = c6083b3e3970   want = c6083b3e3970   match
```

**Run immediately after a push, a served-surface check measures the edge, not the push.**

> ⚠️ **A positive and a negative control prove the method can detect a difference. They do not
> prove it is comparing the right two things.**

Both controls passed in every one of those runs, and were right to: the method *could*
distinguish identical from different. The defect was one level up, in the choice of what to
compare and when — which no control of that shape can reach. This is a real limit on
control-based verification and it is worth stating plainly, because a passing control feels
like a licence to trust the result.

Three defects, one family: **the window** (`y > 19.4`), **the reference** (working tree vs
remote), **the timing** (before the edge caught up). Each time the arithmetic was correct and
an unstated precondition was not. *An instrument is only as good as the assumptions it does not
check — so enumerate them, because they will not announce themselves.*

Both surfaces are ordinary Fastly/Varnish edge caches: GitHub Pages sends
`cache-control: max-age=600` with an `age:` header, and `raw.githubusercontent.com` sends
`cache-control: max-age=300`. `age:` is usually absent on `raw` because `x-served-by` changes on
nearly every request — a fleet of edge nodes, so requests keep landing on cold ones.

#### A fourth member of the family, found by two people disagreeing about a header

The paragraph above previously said something else, confidently: that `raw` sends
`cache-control: no-cache`, and that its staleness was therefore **not** an HTTP cache but
backend replication lag with *no header able to bound it*. Another engineer measured
`max-age=300` on the same object, four times, and said so rather than deferring.

Both readings were accurate. They were **of different objects.** The `no-cache` came from

```
curl -sI https://github.com/<owner>/<repo>/raw/main/<path>      # note: no -L
```

which is a **302** to `raw.githubusercontent.com`. **`curl -I` without `-L` reports the headers
of the redirect**, and `github.com` sends `no-cache` on that hop. Follow the redirect, or
address `raw.githubusercontent.com` directly, and it is `max-age=300` every time. The
measurement was correct about an object nobody downloads.

So the family gains a fourth member, and it is the one that generalises furthest:

| | the unstated precondition |
|---|---|
| **the window** | that the answer lies inside `y > 19.4` |
| **the reference** | that the working tree is what the remote would produce |
| **the timing** | that the edge has caught up |
| **the object** | **that the bytes measured are the bytes served** |

A redirect is a different resource with different headers, and the tool hands you the first
response without comment. **Before trusting a measurement, confirm it is of the thing you
meant** — not merely that the arithmetic on it was right.

⚠️ **The fix did not change, and that is why it survived the correction.** *Re-read and report
only what persists* is correct against an edge cache and against replication lag alike, and
needs no header to work. What changed was the **stated reason**, and this repo has already
recorded why that matters: **a confident wrong reason attached to a correct fix is worse than
no reason, because it licenses the wrong change later.** Someone reading "there is no TTL here"
would have rejected a perfectly good TTL-based wait.

The sweep therefore still never reports a mismatch on a single observation: it re-reads after a
delay and reports only what persists, because **one read cannot distinguish a stale artifact
from a stale edge, and those need opposite responses.**

The other half is worth stating too. **Two people measuring the same thing and getting
different answers is not a tie to be broken by seniority or by who measured last.** It is a
statement that at least one instrument is pointed at the wrong object, and the cheapest next
move is to find out which — which took one `curl -L` and settled it in under a minute.

#### A fifth member: repeating a measurement inside its own correlation window

The remedy built for the timing problem had the same defect as the problem.

A served artifact came back stale immediately after a push. The sweep's confirm pass re-read it,
and it was re-read by hand three times more — **same digest every time**, which read as
confirmation that the artifact really was wrong. It was not. `raw.githubusercontent.com` sends
`cache-control: max-age=300`, so **three reads eight seconds apart are one observation taken
three times.** Repetition inside a single cache window is not independent evidence of anything;
it is the same cached object, reported repeatedly.

What settled it was a different question, and a cheaper one — **which commit's blob do the
served bytes match?**

```
92161e7  0dc232a8…
2237684  0dc232a8…
3aac7ac  dda906b5…   ← what the edge was serving, 2 commits behind
```

> **Ask what the bytes ARE before asking whether they will change.**

Identification is free and decisive; waiting costs a TTL and, inside one window, proves nothing.
So the check now identifies first: bytes matching a recent ancestor are reported as
**`edge behind (N)`** — named and counted, not swallowed — and only bytes matching *nothing* in
history earn the expensive re-read, because that is the only case where time can change the
answer.

**The tell that the original design was wrong is that removing a step made the tool more
correct.** `--no-confirm` had been documented as *"fast, and will lie right after a push"*. It is
now simply accurate. **The lie was never the speed — it was the confirm pass owning a diagnosis
it could not make**, which is the same shape as a detector with a single failure verdict
applying that verdict to every anomaly it meets.

And the general form, which reaches past caches: **waiting is not sampling.** A loop that polls
until something changes is a fine way to wait and a worthless way to corroborate, because every
iteration inside the correlation window carries the same information as the first. If a repeat
is meant as evidence rather than patience, it has to be separated by more than the thing that
makes repeats agree.

#### And the class this all belongs to: committed is not deployed, and deployed is not served

Four instances in one day, each found by accident while looking for something else:

| | the repo said | the world said |
|---|---|---|
| `docs/assets/case-hero.png` | current render | one render behind |
| `status.realm.watch/checks.json` | 8 checks registered | never deployed — **four projects registered and unmonitored** |
| `docs/print-sheet.html` | "✅ CLEARED" | **"⛔ DO NOT PRINT"**, on the page read while a printer runs |
| the stand STL after its fix | fixed blob at HEAD | the blocked blob, for about a minute |

**Every check that compares the repo against the truth passes in all four.** That is what makes
the class invisible: the artifact under version control is correct, the reasoning about it is
correct, and the thing a person actually receives is not. Ask the question at the point of
delivery — fetch the URL, read the config off the host that runs it, hash what a visitor
downloads — or the answer is about a different object than the one that matters.

**All four now have a guard, and each asks the far end rather than the repo:**

| surface | guard | what it interrogates |
|---|---|---|
| generated pages | `site/check_generated_current.py` | pre-commit: the source and its built page in one commit |
| the served site | `site/check_served_current.py` | the URLs, after a push |
| the HA dashboard | `homeassistant/tools/check_dashboard_deployed.py` | HA's own `.storage`, over the WebSocket API |
| the monitoring config | `status.realm.watch/check_deployed_current.py` | the status VM's live `/api/config` |

⚠️ **None of them deploys, and that is a decision rather than an omission.** A guard that fixes
what it finds turns a visible choice into an invisible one, and two of these would be actively
dangerous if they did: pushing the dashboard silently overwrites a UI edit somebody made on
purpose, and `deploy.sh` overwrites entries added through the status page's own editor. Each
reports what it found and names the command; a person runs it. **Where a fix has a cost, the
guard's job is to make the cost visible, not to pay it on someone's behalf.**

They also each refuse the larger claim. None checks that the checks are *correct*, that the
dashboard's entities exist, or that cron is running — only that the far end holds what git
holds. **A guard that checks a proxy for deployment is worse than none, because it reads as
coverage** — which is the `_cells`-versus-flared-field lesson from §5, arriving in the tooling
instead of the geometry.

### 20. A correction that expired, and was re-derived by the person it was given to

Every other entry in this file is about a **claim** going stale. This one is about a
**correction** going stale, which turns out to be a different mechanism with a different remedy.

A reviewer offered the sentence *"slicers repair this class of mesh defect"* as a conclusion
from the front bezel having printed successfully. It was declined, precisely and in writing:
the evidence supported **"one print, one slicer, no problem observed"** and nothing wider,
because nobody had established whether the slicer repaired it silently, repaired it with a
notice, or never noticed. That reasoning was correct, it was accepted, and it was acted on.

**Several hours later the same person wrote the wider sentence into the print sheet anyway** —
*"every slicer tried repairs it without comment"* — and did not notice, because it did not feel
like ignoring a caution. It felt like writing a sentence about a fact.

> **A refusal recorded in a message decays. The same refusal written next to the claim does
> not.**

The shape is worth being precise about, because the obvious diagnosis is wrong. **Nobody
re-read the caution and misinterpreted it.** The caution simply **was not present at the moment
of writing**, while the underlying fact — *the bezel printed and it was fine* — was still fully
available and still supported the over-reading on its own. A correction is a fact plus a
boundary; **the fact persists in your head and the boundary does not.** So the same person can
re-derive the same over-claim from the same evidence, in good faith, having already agreed not
to.

This is the identical structure to the stale-generated-page defect two sections up: **the
coupling is invisible exactly where the work happens.** `PRINT-SHEET.md` does not look like a
build input at the moment you edit it; "the bezel printed" does not look like a bounded claim at
the moment you cite it. Both were solved the same way — **move the constraint to the point of
use.** The boundary now lives inline on the page, beside the sentence it bounds:

> *"That is one print on one slicer — it is not a claim that every slicer repairs this
> silently."*

Two things generalise.

**Write the boundary where the claim lives, not where the conversation happened.** A caveat in
a review comment, a chat message or a commit body protects the edit in front of it and nothing
after. If a limit matters, it belongs adjacent to the assertion, in the artifact, where it is
re-read every time the assertion is.

### 21. A detector with one failure verdict will name that verdict for any anomaly

A pre-print probe asked the highest-consequence question on the back shell: **can the 0.60 mm moat
around each printed-in-place button actually separate?** If it cannot, the part looks perfect and
the buttons are welded solid.

The probe walked the moat layer by layer, found the void gaps either side of each island, and
counted them. Two gaps of about 0.60 mm meant open. It printed **`NO GAP — fused`** for both
buttons at z = 2.50.

**They were not fused. There was nothing there.** z = 2.50 is inside the board pocket, so the
whole region is void — no island, no shell, no moat. The probe had one failure verdict available,
found no separating gaps, and reported the only bad thing it knew how to say.

> **A detector that can express exactly one failure will report that failure for every anomaly,
> including the total absence of its subject.**

That is §14's empty-object problem with a direction added. §14 counted edges on an object that was
not there and returned *zero*, which reads as success. This returned *the loudest available
failure*, which reads as a catastrophe. **Both are the same defect and they point opposite ways**,
so neither "it passed" nor "it failed" is evidence until the detector can distinguish *absent* from
*present-and-bad*.

The fix generalises to every binary check in this repo and costs nothing: **report the positive and
the negative explicitly, so the answer is unambiguous in both directions.** The rewritten probe
prints the material runs *and* the void runs on every sampled row, and the reading was then
immediate and certain — twelve consecutive wall layers with a clean 0.60 mm void on both sides of
both islands, then all-void above, exactly as the pocket requires. The same numbers that had been
called *fused* now read *open*, because the output finally contained enough to tell them apart.

Two notes on how it was caught, both uncomfortable.

**It was caught by disbelief, not by the check.** `fused` was the answer the probe was written to
fear, and it arrived for both buttons simultaneously at exactly one height with every layer below
it clean. **A failure that appears everywhere at once, at a single boundary, after a clean run, is
a question about the instrument** — the same tell as a suspiciously perfect result in §14, from the
other side.

**And it was written four hours after §14 was written up, by the same author.** Knowing a failure
mode does not confer immunity, because the mode is a *fact* in your head and the *boundary* is a
property of the code in front of you — the point §20 makes about an expired correction, arriving
here as an unexpired one that simply was not in view at the moment of writing.

### 22. A review that was complete for every question it knew to ask

The button caps were enlarged from 9.01/6.58 mm to 15.00/10.00 mm across flats. That change was
reviewed carefully and by more than one person, against four properties: **hinge strain, lever
ratio, countersink clearance, and the hex field's boundary.** Every one of those was measured,
argued and recorded, and every one of them is right.

The debossed cap face is a recess in the part's *bed* face, so its floor is unsupported and must
bridge. Enlarging the cap enlarged the recess with it. **The bridge span went 7.2 mm → 13.20 mm —
an 83 % increase — and nothing looked, because printability of the recess floor was not one of the
four questions.**

This is not a missed check, and that is what makes it worth its own entry. Every check that
existed ran, passed, and was correct. **The review was complete with respect to its own list.** A
missing check announces itself the moment somebody asks "what tests this?"; a complete-but-bounded
review answers that question satisfactorily and is still wrong.

> **When a dimension changes, enumerate what *derives* from it, not what you were worried about.**
> The four properties reviewed were the ones the cap change was *expected* to threaten. The recess
> floor was threatened by simple proportionality and nobody had it on a list.

The span still prints — 13.2 mm is routine bridging over a 0.90 mm-deep recess — so the cost here
was not a ruined part. It is that **the number was unknown for as long as it existed**, on the one
face of the enclosure a person looks at and presses, and it was found by a pre-print pass that
nobody had asked for until the part was about to go on a bed.

**And prefer stating the narrow version to deleting the claim.** Deleting it would have left
silence, and silence is what the *watertightness* entry (§14) is about: the defect there was
**the absence of an honest statement, not the presence of a false one**. A claim with its limits
attached is strictly better than either an overclaim or a gap — and it is the only one of the
three that survives being re-read by someone who was not in the conversation.

### 23. A replacement is two edits wearing one diff

Twice in one day a paragraph was replaced with a better one and something quietly went missing —
in both cases not a fact, but an **obligation** the old text had been carrying.

**First:** the mesh note said the front bezel's three known non-manifold edges are repaired by
*"every slicer tried, without comment."* Nobody had established that. The evidence was one
print, on one slicer, with no one checking whether it reported anything — and that boundary had
been explicitly stated and accepted hours earlier (§20). Replacing the paragraph re-introduced
the over-claim.

**Second, and the cleaner instance:** publishing the corrected countersink, the whole bullet
reading *"84.7°, do not over-torque, it craters"* was replaced with a table of what each screw
head does. Every number in the table was right. But the caution had a **residual reason** that
survived the fix — a ⌀6.00 head still bears on its *rim*, a line contact, so the load is still
concentrated — and the table did not carry it. **The warning was deleted rather than softened**,
and nothing in the change looked like a deletion.

> **A replacement diff shows you the facts that changed. It does not show you the obligations
> that vanished.**

That is the mechanism, and it is specific to *replacing* rather than *amending*. An amendment
leaves the old text visible beside the new, so anything it was doing is still on screen. A
replacement presents as a single improvement, and review reads the improvement: the added lines
are scrutinised, the removed lines are skimmed as "the old version of that". Warnings, caveats,
scope limits and provenance notes are exactly the content that lives in prose *around* the
facts, so they are exactly what a replacement drops without a trace.

It generalises past prose. Rewriting a function loses the guard clause nobody could explain;
regenerating a config loses the one hand-added exception; replacing a comment block loses the
record of why a dead constant is dead. In every case the new version is better at its job and
silently worse at a job nobody restated.

**The countermeasure is a question, not a discipline:** when you replace a block rather than
edit it, read the *old* text once more and ask **what was it doing that the new text is not?**
Not *is the new text correct* — it usually is, and that is what makes this hard to catch.

And a note on how both were found: **not in the diff.** Both were caught by someone reading the
*result* — the rendered page, days of context later, without the old version in view. That is an
argument for the review pass existing at all, rather than for reviewing more carefully. A diff
shows you what an edit did; only the finished artifact shows you what it no longer says.

### 24. A correct measurement of the wrong object

Three times this month a number was right, its arithmetic was right, and the sentence built on it
described something that does not exist in the world.

**The grille.** The model places 33 hexagonal cells, and the assert counting them is correct. But
each bore is flared 0.60 mm at its mouth, and the flare grows a cell faster than the pitch
allows — so the outer 0.40 mm of the baffle is **one merged opening**, 886.1 mm² of an 886.1 mm²
field. "33 apertures" is true of the *cell list* and false of the *face you can touch*.

**The countersink.** With the mouth matched to a named head, the head sits on a **full conical
seat** — geometrically exact. Sliced at 0.20 mm, that cone is a **staircase of 8 annular steps**,
so the head bears on 8 step corners. Better than the single line contact it replaced, and not
what "full conical seat" makes a reader picture.

**The layer count.** `14.40 / 0.20 = 72` exactly, from the constants. Measure the same height off
the exported binary STL and you get **71.999998**, because float32 cannot represent 14.4. The
claim is about the design; the mesh is a lossy transcription of it.

In all three the CAD figure is correct. **What differs is which object the sentence is about** —
and the two objects share a name, which is what makes the slip invisible.

> **Ask what the process does to a number before repeating it.** Between the model and the thing
> a person holds there is a mesher, a slicer, a nozzle and a float — and each of them is entitled
> to change the answer.

This is a near neighbour of §5 and worth keeping distinct from it. §5 is a **metric measuring the
wrong property**: open area was insensitive to whether a region was connected, so the number was
about something other than what mattered. Here the metric is right and the *referent* has moved —
a **correct measurement of the wrong object**.

The countermeasures differ, which is the practical reason to separate them. §5 wants a **better
assert**: measure connectivity, not area. This one cannot be asserted away, because the model
genuinely does contain 33 cells and a true cone — there is nothing in the source to catch. It
wants a **question**, asked when writing the sentence rather than when writing the code:

- *Is this a property of the model, or of the part?*
- *Which of the mesher, the slicer, the nozzle and the float touches it on the way out?*
- *Would somebody holding the object recognise the description?*

The last one is the cheapest and the most reliable. A reader with the printed bezel in their hand
counts one grille opening, not thirty-three — and no amount of correct arithmetic upstream makes
the sentence true for them.

---

## A rule whose exemption covers exactly the cases it exists to catch

The back-face labels needed one check: *is any material between two strokes thinner than the
0.90mm the nozzle can resolve?* It took four versions, and the third is the one worth keeping.

**v1 — skip pairs that share an endpoint.** Three of four labels failed instantly: O's top edge
vs its right edge read −0.052mm of material, D's stem vs its bowl 0.392, S's two right corners
−0.292. Every one of those pairs is bridged by the single chamfer *between* them, so the gap is
packed with ink. v1 computed the distance between two strokes correctly and called it material
without ever asking what was in there.

**v2 — skip pairs up to N segments apart along the contour.** This is v1's mistake with a dial
on it. N=2 still flagged O's counter diagonal, which is a chain of three chamfers. N=3 would
have swallowed the power symbol's ring, whose subdivision puts genuinely-adjacent ink four
segments apart. There is no N, because N is a proxy for *is there ink in between* and the proxy
fails at both ends — too small for a chamfered corner, too large for a subdivided arc.

**v3 — the midpoint test: a gap is material only if the point halfway across it is not itself
ink.** Correct, principled, no constant to tune. Every false positive vanished. And both
controls went blind:

```
control  S@h=2.30   (counters collapsed)  ->  +inf   DETECTOR IS BLIND
control  power gap=30 (break too narrow)  -> +1.009  DETECTOR IS BLIND
```

**A gap narrower than the stroke width has its own midpoint inside its own two strokes.** So
every genuinely-too-thin gap read as ink and exempted itself. The rule was not merely weak at
the failure — it was *strongest-looking exactly where it was blind*, because the thinner the
defect, the more certainly the midpoint fell inside ink.

**v4** is v3 asking the question over *third* strokes only: the two strokes forming a gap cannot
bridge their own gap. One clause, and the controls fire.

### What generalises

The trap is not geometric. It is that **an exemption clause was written from the passing cases**
— corners, chamfers, arcs — and never evaluated against the failing ones. Every version was
tested by running it on the four real labels and reading the numbers, and all four numbers looked
plausible every time. v1 through v3 differ only in which *wrong* answer they give.

- **An exemption is a claim and needs its own control.** "Skip corners" silently became "skip
  anything tight" and nothing said so. The question to ask of any skip/ignore/tolerate clause is
  not *does it exclude what I meant* but *what does it exclude that I did not mean* — and the
  cheapest way to answer is a deliberately-broken input that must trip the check.
- **A check reporting `inf` or `n=0` is not a pass.** A squeezed S at h=2.60 has no measurable
  pair left because every counter has fused, and "nothing was thin" is what "nothing was
  measured" looks like from the outside. `min_gap` now returns a count and every caller asserts
  `measured > 0`. Any check with a "no findings" path needs to distinguish *looked and found
  nothing* from *did not look*.
- **A tolerance that has to be loosened for a legitimate case is a warning.** The abandoned
  granulometry version needed `tol` at 1.5% to tolerate the unavoidable taper at an acute
  concave vertex, and at 1.5% a genuinely collapsed S passed. When the threshold that admits the
  benign case also admits the malignant one, the metric is not separating them — reach for a
  different instrument rather than a better number.

---

## `str.replace` returns a string; it does not return whether it replaced anything

Two label cuts were wired into `back_shell()` by a patch script that did two `str.replace` calls
and printed `cuts wired`. It printed. One of the two anchors did not match — an earlier edit had
reflowed a call onto two lines with sixteen spaces of continuation indent and the anchor carried
twenty — so **half the change silently did not happen** and the script reported success, because
the only thing it verified was that Python reached the end.

The corroborating evidence agreed with the wrong conclusion. The rebuilt back shell went from
15168 to 18852 triangles: the labels that *did* land accounted for that, and a partial
application is exactly as consistent with "triangle count rose" as a complete one. The error was
caught only by slicing the STL and seeing two of four labels — a check against the artefact, not
against the intent.

- **A silent-no-op API needs a counted assertion.** `assert s.count(anchor) == 1` before, or an
  edit tool that errors on a missing anchor. The final `print` in a patch script proves the
  interpreter ran, nothing more.
- **Verify per-edit, not per-script.** `grep -c` for each new call site takes a second and would
  have caught this before a nine-minute rebuild.
- **A metric that moves in the right direction is not confirmation.** "Triangles increased" was
  true, expected, and uninformative about the thing in question. The confirming check has to be
  able to come out *wrong* if the change is partial — counting call sites can, counting triangles
  cannot.

### Amendment to the `pgrep -f` self-match note above

The `[p]attern` trick protects `pgrep`/`pkill` from matching **its own** argv. It does not protect
against matching the **enclosing shell**, whose command line contains the pattern further along.
`pkill -f "[e]mber_case.py" ; time python ember_case.py` killed the shell that was about to run
the build — the compound command's own argv contained the literal string. The patch it was
chained to never ran, and the next step was taken believing it had. Kill and re-run in separate
invocations, or match on a pidfile.

---

## An assert that measures the variable you controlled, not the one that binds

The label work produced three errors with one shape between them, and the sharpest is this.

The plan of record for checking the labels was: *"measure the realised minimum stroke and assert
it is ≥ 0.90 mm."* That is a reasonable-sounding check and it is **structurally incapable of
failing**. The stroke is an argument to the stroke font — it is set to 0.90 and then asserted to
be ≥ 0.90. It passes because it was constructed to.

Meanwhile the dimension that actually decides whether the label prints is the **counter** — the
material between the three bars of an S, the hole in an O — and nothing measured it. A 4.5 mm
`SD` passes the stroke assert and prints as mush, because its counter is **0.330 mm**.

### Why the intuition points the wrong way

Shrinking type does not shrink a glyph uniformly, because **the stroke is pinned at the nozzle
floor while everything else scales**. So making a label smaller *raises* stroke/height, and what
gets eaten is the counters. The binding dimension of a bold small glyph is its counter, never its
cap height — which is exactly backwards from how type is normally specified.

Measured on the shipped S, counter against ink cap height:

```
ink 4.50  ->  0.330 mm     (proposed size; unprintable)
ink 6.00  ->  0.843 mm
ink 6.40  ->  0.980 mm     (shipped)
```

0.342 mm of counter per mm of cap height. Two people arrived at 0.980 for the shipped size
independently — one by measuring, one by extrapolating the other two points — which is the sort
of agreement worth having on a number that governs a visible face.

### The same shape, three times, one session

- **Stroke satisfied, counter unexamined.** Above.
- **Thickness compared, stiffness unexamined.** "The 1.22 mm cap pad is thicker than the 0.90 mm
  hinge" was offered as a sufficiency argument. It is not a stiffness test: a cap must be far
  *stiffer* than its hinge, not merely thicker, and stiffness goes as t³ over a 15 mm span
  against 1.2 mm. It does pass — 0.033 mm of bow against ~0.25 mm of switch travel — but it
  passes *because computed*, not because 1.22 > 0.90.
- **Tool located, sensitivity unexamined.** `min_feature` was recommended for the material check
  on the grounds that it is "reusable and carries its own control." It is area-averaged, so it
  cannot fail on that defect at all. **Having a control proves an instrument can fire at
  something. It does not prove it can fire at yours.** The caveat now lives in
  `tools/minfeature.py`'s own docstring rather than in a handoff, per §12.

The through-line, in one sentence: **the constraint that was designed for got verified, and the
second constraint was never enumerated.** Every one of these checks was correct about what it
measured. The failure was in the list of things to measure, and no amount of rigour inside a
check repairs an incomplete list outside it.

### And it recurred inside the correction

The material check that replaced all this took four versions, and **the third was blind precisely
at the defects it existed to catch** (see the previous section). That is the same failure, one
level up, committed while fixing it — and it is worse than the original, because the original at
least failed loudly on its first run. The countermeasure is not "be more careful". It is the
**deliberately-broken input**: every check here now carries a control that must trip it, and two
of the four controls in `tools/strokefont.py --self-test` exist only because an earlier version
of that check passed them when it should not have.

---

## Authorship gives you no index of your own work

"Nothing catches the flare" was written about `GRILLE_FLARE`. There is an assert for it, and a
second guard downstream. `git log -S` attributes the assert to `338a900` — **written by the same
person, the same night, and forgotten by morning.**

This is not the lesson-fading failure that the rest of this file records. The forgotten thing was
not a principle, it was **a line of code with your own commit hash on it.** What survived in
memory was the assert's *reasoning* — an argument about fins being too thin to print and too
thick to be a deliberate merge — with no pointer from the token "flare" back to "there is an
assert for that." `grep` had it in half a second. Recall did not have it at all.

**The countermeasure is unglamorous and complete: before writing "nothing checks X", grep for X.**

The concrete damage the claim would have caused is worth naming, because it is not embarrassment:
the next reader adds a **second** assert for a property already asserted. Duplicate invariants are
worse than missing ones — they drift apart, and then the two disagree and neither is trusted.

### The correction underneath it, which is the reusable half

The accurate statement was not "nothing checks the flare" but:

> **The assert checks printability. The issue is about appearance.** A check correct about what it
> measures, where the thing in question is something else.

And that reframing is what made the issue tractable, because it produced a consequence the
original framing hid. The mouth-merge threshold is `HEX_WEB/√3 = 0.5196`; the web stays 0.90 when
the lattice is rescaled, so **the threshold does not move with the scale.** At any aperture size
the face still presents as one opening. The lever is the flare, not the hex size — and since
`0.2598 < flare < 0.5196` is the fin the assert already refuses, **there is no partial version of
the change**: either both move together or neither is worth making.

Then the cost nobody had computed: dropping the flare to the only permitted value keeps **43 %**
of today's mouth relief, and the flare exists because a sharp-edged slot mouth sheds vortices and
chuffs at level. So the request is **an acoustic-versus-visual trade, not a geometry problem** —
which is a decision for whoever owns how it sounds, not something to resolve in CAD.

Note the shape: a check was mischaracterised, the correction of the mischaracterisation exposed
the real constraint, and the real constraint turned out to live in a different domain from the
one the issue was filed in. **Getting the description of a check right is not bookkeeping.**

### 25. The assert an issue asked for was insensitive to the bug the issue was filed about

Every entry above is about a check that measured the wrong thing. This one is about a check
that measured **a different right thing** — a real property, correctly asserted, chosen in
good faith by the person who had just found the bug, and structurally unable to fail on it.

#23 asked for a button-only navigability walk. It named the invariant precisely, and it
named it from the symptom: the mode submenu was *"enterable from the BOOT button but not
exitable from it"*, so the check should assert that **every `ui_mode` is exitable**. That
reasoning is sound, the requirement it appeals to is written down elsewhere in the repo, and
the bug it describes was real.

The walk was built, the assert was implemented, and then the original defect — the missing
`ui_mode == 3` long-press branch — was written back in as a control. **It reported
nothing.**

```
self-test: ui_mode == 3 long-press branch removed (#4) -> DETECTOR IS BLIND (0 finding(s))
```

> ⚠️ **That output is the intermediate state, not the shipped one.** Running
> `check_navigability.py --self-test` today prints `DETECTED (3 finding(s))` for that same
> control, because the actionability assert described below was added in response to it. The
> `BLIND` line is quoted here as the thing that was learned; it is not a current result, and
> the tool would be broken if it were.

Because mode 3 was never unexitable. With that branch absent a long press fell through to
the `else`, which **re-opens the power menu** — and the power menu dismisses normally, so
the device escapes in two more presses. Every mode really was reachable and really was
exitable, before and after the fix. The assert was true of the broken firmware and true of
the fixed one.

What was actually unreachable was not the exit. It was **the menu's purpose**: you could
not pick a mode. `ui_mode == 3` could be entered from the button and could not be
*resolved* from it, in the menu that exists precisely because recovery must not require the
touchscreen.

So the property that binds is **row actionability** — a long press on a drawn row must not
do merely what a long press with nothing selected does. `ui_sel == -1` already means
"nothing aimed at, dismiss", so a drawn row whose outcome is byte-identical to the -1
outcome is a row that does nothing, and that is expressible without any per-row model of
what each row *ought* to do. (Which matters: a per-row expectation table would have been
another hand-written copy of the firmware, the hazard #23 itself warns about.) The
exitability assert was kept, because it is a real if weaker property — but it is documented
in the tool as **not** the one that catches this.

#### Why this is not just "the check was too weak"

A weak assert is one that could fail and rarely does. This one **could not fail on the
motivating defect at all**, and the reason is upstream of the code: the *description of the
invariant* was wrong. "Not leavable" was an inference from a symptom — a long press
appeared to do the wrong thing, and re-opening the power menu looks, from the outside, a
great deal like being trapped. The inference was never tested against the state machine,
because it arrived attached to a genuine bug and a correct fix.

That has a consequence worth stating plainly, because it cuts against how work gets
delegated here:

> **"Implement the check this issue specifies" is not a safe instruction.** An issue is
> written by someone reasoning from a symptom, and the invariant they name can be a
> different property from the one that was violated. Implementing it faithfully produces a
> check that passes, reads as coverage, and is silent on the defect it was commissioned
> for.

This is §22's neighbour and the difference is worth keeping. There, a review was **complete
with respect to its own list** and the list was short. Here the list had exactly one item,
that item was the right *shape* of thing to check, and it was still the wrong property —
so enumerating harder would not have helped. Nothing about the requirement was missing. It
was mis-identified.

#### What caught it, and what did not

Not review. Not reading the issue more carefully — the issue is persuasive and its
description of the trap is vivid. What caught it was the **control**: writing the original
bug back into the file and requiring the check to fail. That took one line and produced the
word `BLIND`, which is not a result any amount of care would have produced by reading.

> **A control does not only prove the detector works. It proves the detector is pointed at
> the defect you think it is** — and those come apart precisely when the defect has already
> been fixed and you are reconstructing it from a description.

The corollary for this file's own practice: **the control has to be the original defect,
not a plausible stand-in for it.** Three of the four controls on that walk are synthetic
mutations (hardcode the modulus, delete the summon, shrink the paint loop). **Two fired on
the first attempt; the third could not run at all** until an anchor was fixed — its author
had written the *resolved* `4` where the file says `${ui_pm_n}`, so the mutation matched
nothing — and then it fired. **None of the three ever disagreed with the design.** Only the
control built from the real `git` history did, because a synthetic mutation is derived from
the same mental model as the assert, so it tends to be exactly the thing the assert already
catches. Two artifacts sharing an assumption again, in the shape §16 records as *the most
convincing available form of being wrong*.

That distinction is load-bearing rather than pedantic: **a control that cannot run and a
control that runs and finds nothing are different results, and only one of them is evidence
about the detector.** It is §21's absent-versus-present-and-bad, arriving in the controls
themselves. The only reason the difference is known is that the anchor mismatch was
*reported* rather than silently replacing nothing — a counted assertion on a `str.replace`,
earning its keep.

#### And a second-order note, from the same afternoon

The same walk's first reporting pass classified the haptic acknowledgement chime as a side
effect, so all ten non-idle states announced *"exits only via bank/rouse"* — naming the one
consequential verdict it knew for an event that was merely feedback. That is §21 exactly,
committed by someone who had read §21 that morning, and it was caught only because ten
identical notes on states with nothing in common is not a plausible finding. **Ten
identical results are one result.**

The fix was to make acknowledgement-versus-consequence an explicit allow-list in which
anything unlisted defaults to *loud*, so a newly added action is over-reported rather than
silently absorbed — the same direction of failure this file argues for everywhere else.

### 26. A true explanation for an anomaly is not a reason to stop looking at it

The cheapest failure in this file, and the only one committed twice in the same hour.

Writing a new section into the site source, a tag-balance check was run over the inserted text.
It reported a mismatch:

```
<div> open 2 close 2 OK
<p>   open 6 close 5 MISMATCH
<h3>  open 1 close 1 OK
```

The mismatch had an obvious and **correct** explanation: the checked segment ended part-way
through a paragraph, so of course one `<p>` looked unclosed. That was true. It was also
irrelevant, because **the `<p>` in question was one this edit had opened around text that was
already inside a `<figcaption>`** — the whole new section, a heading and two note blocks, had
landed inside a figure's caption. The commit went out on the strength of the explanation.

> **A plausible reason for an anomaly is not a reason to stop looking at it.** The dangerous
> case is not a mismatch you cannot explain; it is one you *can*, where the explanation is true
> and answers a different question than the one the anomaly raised.

What is worth extracting is *why the check could not settle it*, because that is structural
rather than a lapse of attention. **A balance count over a fragment cannot distinguish
"truncated mid-element" from "broken element".** The two produce identical evidence. So the
instrument was not being read carelessly — it was **incapable of answering**, and no amount of
staring at its output would have improved it. The fix is a different instrument:

```python
from html.parser import HTMLParser        # over the whole BUILT document
# -> </figcaption> at (1595,4) but open is <p> from (1586,2)
```

Which located it in one line, with both positions. It now runs on the built page rather than on
the diff — the same move as §19's *ask what the bytes are before asking whether they will
change*: prefer the instrument that can be decisive over the one that is convenient.

**And the second commission, thirty minutes later, in the verification of the fix.** Grepping
the served page for a sentence from the new section returned **0**. The available explanation —
the phrase wraps across a line in markdown — was, again, true; and this time checking it took
one flattened search, which found the sentence present. Same hour, same shape, opposite
outcome: once the explanation concealed a real defect, once it was the whole story. **Which is
the point.** The explanation's truth carries no information about whether anything else is
wrong, so it cannot be the reason to stop — only a measurement can.

#### And flattening is not enough, which took a third instance to learn

The remedy above has its own blind spot, found the same day by someone searching this file for a
sentence they had written themselves:

```
"could not run at all until an anchor was fixed"
  raw text                    0
  whitespace-flattened        0      <- the remedy, and it still fails
  flattened + markup stripped 1
```

The phrase was intact. **An editor — me — had closed a `**` bold span in the middle of it**, so
the literal characters never occur consecutively no matter how the whitespace is normalised.

> **Flattening whitespace fixes wrapping. It does nothing about inline markup splitting a
> phrase.** Two different mutilations of the same prose, needing two different remedies: for
> wrapping you normalise, and for markup you either strip the marks too or **read the region
> instead of counting a literal.**

Note which direction this runs. The file already records literal `**` surviving onto a *rendered*
page — markup leaking outward. This is the mirror: markup sitting correctly in the source and
breaking a search *for* the prose it decorates. Same class, opposite direction, and the second
one is quieter, because a search returning zero looks like an answer.

The general form, and the reason it belongs in this section rather than beside the flattening
advice: **each fix to a search widens what it can find and leaves a new class it cannot.** A
zero from a hardened instrument is more persuasive than a zero from a naive one and is not more
conclusive. Ask what the *current* version cannot see before believing its absence.
