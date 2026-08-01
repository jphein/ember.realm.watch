# HANDOFF — 2026-07-30

State at the end of the session that built the enclosure and the operating modes. Everything
below is verified against the artifact, not against a report — that distinction mattered
repeatedly here, and the running log of the times it did is [`docs/verification.md`](docs/verification.md).

## ⛔ READ THIS FIRST — everything below predates 2026-07-31 00:00

**JP printed the back shell and found the board model wrong.** The sections below were written
before that and still describe four parts as ready. **They are not.**

| part | printed? | status |
|---|---|---|
| **front bezel** | yes | ✅ **correct, keep** — proven byte-identical through every change since |
| **back shell** | yes | ⛔ **superseded, reprint** — microSD slit was on the wrong edge and ~24 mm out; an opening exposed the LCD driver flex; the two button caps were on the wrong ends |
| **stand / dock** | yes | ⚠️ **superseded but FUNCTIONAL — see below. Do not reprint it to fix the buttons.** JP is reprinting by choice, for the next prototype |
| **stand base** | **never** | ✅ committed version is the fixed one (the previous was 1.40 mm too deep to seat) |

### ✅ THE PRINTED STAND STILL WORKS. Measured, `86748c6`.

The two finger pockets **had already merged into one scoop** spanning board x **6.94 … 43.51**, and
that scoop contains **both caps in their new swapped positions**:

| cap | new island x | cap spans | in the printed scoop? | 6 mm fingertip | 16 mm thumb |
|---|---|---|---|---|---|
| BOOT (big / volume) | 16.66 | 8.00 … 25.32 | **yes, wholly** | clear | clear |
| RESET (small) | 35.66 | 29.89 … 41.43 | **yes, wholly** | clear | 0.15 mm clipped |

The 0.15 mm on the small cap is irrelevant — RESET is deliberately *not* thumb-sized, and the
thumb-sized cap is fully clear. **The reprint is cosmetic.** Measured against the **committed
source that produced the STL JP actually printed** (old `CAP_CX` 33.05 / 14.51, `SCALLOP_CLR` 1.80,
`SCALLOP_MIN_RIB` 3.00), not against the new source. It survives only because the *merge rule*
made the scoop far wider than either cap needs — had the pockets stayed separate, the swap would
have missed both.

### ✅ The counterbore has landed (was "partial" when the line above was written)

`CBORE_D` / `CBORE_DEPTH` / `BOSS_FLARE_D` are all in `ember_case.py` as of `86748c6`, the conical
countersink and its entire rationale are deleted, and the back-shell STL is rebuilt. **Nothing to
check before slicing.** Labels (SD / MIC / VOL / ⏻) are **in** — see below.

**Fastener, fully measured by JP (not nominal):** M3 × 0.5 × 12 **ISO 4762 socket cap, hex recess**,
head **5.50 × 3.00**. Flush, in a flat-bottomed **counterbore**.

- Depth is **3.04 mm = 19 layers**, not 3.00: flush wants 3.00, which is 18.75 layers and cannot
  land a flat floor. 18 layers leaves the head **proud**, which stops the part sitting flat — so it
  rounds *deeper*, sinking the head 0.04 mm. Invisible.
- **Engagement 5.34 mm = 1.78 D**, clearing the end of the pilot by 0.86 mm. (An earlier note said
  5.30 / 1.77 D / 0.90 — that was computed at a 3.00 depth, before the layer rounding.)
- **The boss flare exists *because* the head is 3.00 mm.** A flush pocket floors **0.44 mm** into
  the cavity, where the d5.80 bore is wider than the d5.40 boss and the head has nothing to bear
  on. The boss flares to **d8.40** below the PCB face. ⚠️ **The permission is a distinction, not a
  licence: the vendor's ⌀5.60 pad keepout applies AT the PCB face, not below it.** Anyone
  "restoring" the boss to a uniform 5.40 to match the keepout comment silently deletes the seat.
  There is an annulus assert guarding it, with a control that reproduces the un-flared defect.

⚠️ **Slicer, unchanged and still critical: gap-closing radius / hole horizontal expansion must be
`0`.** The button moat is 0.60 mm and gap-closing welds it shut, fusing the printed-in-place caps
to the shell. The model cannot defend against this.

**Root cause, and the part worth carrying forward:** the vendor STEP had **four features missing or
fictional** — both switches absent, the mic port suppressed, and a 0.5 mm plate taken for the
microSD socket that is actually the **LCD driver flex**. The real socket is in the same file as
**zero-thickness faces**, invisible to any search over `.solids()`. And `SD_PLATE` **had no
consumers**: the openings were hand-typed literals, so nothing recomputed when it was wrong and no
assert could have caught it. Openings now derive from a component table.

Full orchestration state, including the three questions still open with JP:
`~/.claude/projects/-home-jp-Projects-familiar-realm-watch/scratch/hosyond-s3/HANDOFF-orchestration.md`

---

## Shipped and working

| | |
|---|---|
| **Device** | Conversation, multi-turn, no pop, responsive taps. Three operating modes, verified across a power cycle on hardware. Volume **and mic gain** are live controls in the single-press overlay. |
| **Repo** | <https://github.com/jphein/ember.realm.watch> |
| **Site** | <https://jphein.github.io/ember.realm.watch/> — page + print sheet |
| **STL downloads** | all **four** + `ember_case.py` from raw GitHub |
| **Enclosure** | boolean-verified 0.000 mm³ against the vendor solid; geometry asserts pass. Mesh: three parts watertight, `ember-front-bezel` at its documented baseline of 3 non-manifold edges and **zero** boundary edges. **`ember-front-bezel` has been printed and its dimensions are good** — one part of four; nothing assembled |
| **Standing guards** | five, all green — see below. Four of them exist because "committed" turned out not to mean "deployed" or "served" |

`~/Projects/ha` is clean and in sync. Ember has been fully extracted from it.

## Firmware: three operating modes

**Normal** (speech + chimes) → **No talking** (chimes only) → **Hush** (silent). Monotonic:
progressively quieter, and nothing else varies. Conversation works fully in all three and the
reply still displays on screen — only what leaves the speaker changes.

> **Hush changed meaning.** It used to mean *"do not listen to me"* and gated the talk gesture.
> It now means *"do not make noise"*. If you find a doc, dashboard tile or icon that says
> otherwise — `mdi:microphone-off` is the tell — it is stale and was true once. The mode select
> belongs beside Hush wherever Hush appears, because Hush as a view can only reach Normal and
> Hush, so "No talking" is otherwise unreachable from HA.

`op_mode` is the thing that persists; the select and the Hush switch are lambda views over it,
re-published at boot so a device rebooted while quiet cannot come back disagreeing with itself.
That fault was found by rebooting the real device in Hush, not by reading the config.

## The enclosure, current state

**Four** printable parts in [`enclosure/`](enclosure/) — bezel, back shell, stand, stand base.
**`ember_case.py` is the artifact; the STLs are output.** Rebuild:

```bash
cd enclosure
python3 -m venv cadenv && ./cadenv/bin/pip install -r tools/requirements.txt
./cadenv/bin/python ember_case.py            # STLs + clearance check + geometry asserts
./cadenv/bin/python tools/make_renders.py    # the site figures
```

Both scripts are anchored to their own location rather than to the working directory. They were
not, and the documented build command was therefore a claim rather than a fact — it only ever
worked because a stale `__pycache__` was lying around. The venv is `cadenv`, excluded in **both**
`.gitignore` and `~/Projects/.stignore`; note that Syncthing's `(?d)venv` pattern does **not**
match `cadenv`, which is how the whole toolchain vanished once.

**Buildable from a fresh clone** — see [`enclosure/README.md`](enclosure/README.md).
`tools/requirements.txt` pins the exact set the shipped STLs were built with. The 17.7 MB
vendor STEP is linked rather than committed; without it the STLs still build and only the
clearance check is skipped.

### What landed most recently

- **Thumb-sized hexagonal button caps, debossed rather than raised.** BOOT **15.00 mm across
  the flats** (17.32 across corners) at 0.90 mm deep, RESET **10.00** (11.55) at 0.50. Flat-top,
  against the motif, because the pad is a living hinge and a pointy-top hex would put a *vertex*
  where the hinge must be. They were 9.01 / 6.58 mm, and the reason to grow them was **strain,
  not looks**: a wider hex puts the hinge further from the pip, so θ falls with it and both
  hinges dropped to ~1.20% (from 2.29% / 2.18%). The assert was tightened 2.5% → **2.0%** in the
  same change, because a threshold calibrated to what the *old* caps could achieve is a ratchet
  pointing the wrong way.
- ⛔ **NUMBERS IN THIS ITEM ARE VOID as of `86748c6` — the switches swapped and the islands are now
  SOLVED, not typed.** Current: islands **16.66 / 35.92→35.66**, switches **BOOT 13.45 / RESET
  36.58** (BOOT and RESET are the *opposite* ends from what this item says). The obstruction is no
  longer a countersink but a d5.80 counterbore *plus* a d8.40 boss flare. Marked here rather than
  left to the header caveat, per `docs/verification.md` §12: **a caveat is read once and an
  instruction is read at the moment of acting on it.** The reasoning below still holds; only the
  figures and the sides are wrong.
- **The cap islands are offset from their switches** — centres at x 33.05 and 14.51 against
  switches at 36.58 and 13.45 — because a 17.32 mm island centred on the switch would eat into
  the M3 countersink. `PIP_D` shrank 4.00 → **3.00** to make that placeable: the island narrows
  toward its bottom flat, exactly where the pip sits, so a 4.00 mm pip left a 0.40 mm window of
  legal island X. The back hex field's lower boundary moved to a named `HEX_FIELD_Y0 = 19.00`
  to clear them — and the assert that checks the caps against it had been reading a hardcoded
  `11.0`, firing against a boundary the part no longer had.
- **Finger scallops in the stand's rear slot wall.** At the old cap size both caps were
  completely buried — BOOT's top edge 3.81 mm below the stand's rim, with 0.40 mm between the
  cap face and solid wall. A taller cap could not have helped: the obstruction is *beside* the
  cap, not above it. With the thumb-sized caps BOOT's top edge now stands 2.19 mm *proud* of
  the rim and RESET's is still 2.81 mm under it, so the scallops still do the work.
- **Debossed honeycomb + the hearth-wyrm on the bezel face.** 57 cells in the chin, a 16-cell
  chain up each rail, the wyrm **25.65 × 11.25 mm** in the brow. All **0.48 mm** deep — exactly
  three layers at the bezel's 0.16 mm, where 0.45 was 2.8125 layers and left the recess floor
  wherever the slicer's rounding fell. Recesses at all because on a
  bed face relief can only go inward. The chin was 75 until the screw-boss keepout was
  actually *applied* rather than merely listed in a comment; nine cells per boss, two bosses
  in the chin. The wyrm was also shipping as **two disconnected pieces** — head floating
  1.215 mm above the shoulders — while the minimum-feature check read a healthy 1.23 mm,
  because **a gap is not a thin feature** and morphological opening cannot see absent
  material. `WYRM_COMPONENTS == 1` is now asserted.
- **The mark is mirrored and centred on the face centreline, and it is not at top-left.** The
  creature is drawn facing left, so unmirrored its *tail* pointed at the mic port and the
  gesture ran off the face. Mirrored, the head faces the flare. Ink 7.700–33.351 plus the
  flare's right edge at 42.300 centres the group on **x 25.000** exactly, and that centring is
  **asserted** — every other check on this face is a clearance, and a clearance is satisfied by
  any amount of slack in the wrong place. The cost, accepted knowingly: this hands the creature
  relative to its other three renderings.
- **A mesh check that can actually fail.** The repo used to assert *"all parts watertight, 0
  non-manifold edges"* on a check that imported each STL with build123d and counted boundary
  edges — but `import_stl` returns a single `Face` with **zero edges and zero volume**, so the
  count was zero because there was nothing to count. Measured properly: **three parts are
  genuinely watertight; `ember-front-bezel` carries 3 non-manifold edges** inside a solid that
  is otherwise valid with zero boundary edges — coplanar-seam artefacts where the mark's 104
  stacked row-spans meet, which every slicer repairs. Recorded as a number
  (`KNOWN_NONMANIFOLD = {"ember-front-bezel": 3}`), not a threshold, and reported on every
  build. **Do not raise the baseline to make a build pass.**
- **A new figure, `site/renders/case-docked-rear.svg`**, wired into the site — the slab docked,
  from behind. It exists because a question was asked that no existing figure could answer.
- **Mic gain is a live control** (`number.ember_satellite_mic_gain`), where it used to be the
  compile-time `mic_gain: 36db` and every adjustment cost a reflash. **0–42 dB in 6 dB steps,
  and the hardware forces the step**: the ES8311's REG16 takes a 3-bit field with exactly eight
  legal values, so nothing between them is representable and a continuous slider would report a
  setting the codec cannot hold. It lives in the **single-press overlay beside volume**. The set
  action writes REG16 directly as well as calling `set_mic_gain()`, because the setter only
  assigns a member — the driver writes the register once, in `setup()`, so the setter alone
  would present exactly like a control that does not work. The restore path had the mirror-image
  fault (`TemplateNumber::setup()` publishes but never calls `control()`, so a stored value never
  ran its set action, and **the only value immune was the default**); fixed with its own `on_boot`
  trigger and verified by reading REG16 back, not by inference.

### The speaker took three revisions — read this before changing anything

It is a **sealed-back module**, 40 × 27 × 10 mm, **double-sided tape on the back**, JST-1.25
pigtail. Each revision was a confident design built on an assumption the model could not test:

1. ⌀28 round flanged driver in a recess — wrong shape.
2. 40 × 27 rectangle, shallow lip on the baffle — wrong mount.
3. Tape is on the **back**, the non-radiating face — this **inverts** the mount. The
   bonding surface cannot be the baffle. It is now a flat pad standing 0.80 mm proud of
   the chamber's **rear** wall.

Because the module carries its own rear volume, **chamber volume barely matters
acoustically**. The front path is the acoustic design — hence the deliberately small
2.50 mm diaphragm-to-baffle gap and the 59-cell grille solved to 673 mm² nominal — measured
(`enclosure/tools/grille_area.py`), the **throat is 640.8 mm² across 53 apertures** (−4.8 %, so
the driver's ~700 mm² is 91.5 % matched, not 97 %) and the **mouth is 779.9 mm² across the same
53 apertures**: at the current 0.25 mm flare the mouth web is 0.4670 mm, positive, so the face
is discrete holes and *not* the single merged opening earlier notes described. The nominal
figure describes the throat, which is the restriction that governs level. **Skip the
wadding** (nothing to damp); **still seal the joints** (to stop the *front* cavity venting
anywhere but the grille).

### Three faults booleans could never catch

All three found by rendering and looking; all three now asserted in `_check_geometry()`:

- **The stand covered 19.5% of the screen.** Slot floor at `z=10` put the stand 31.1 mm
  *along* the tilted slab; the visible area starts at 19.76 mm. Nothing intersected — the
  stand was simply *in front of* the screen.
- **No room for the USB-C plug.** 6 mm available, ~18–20 mm needed. Unnoticed because no
  figure ever showed a cable.
- **Both buttons were unreachable while docked.** Nothing intersected there either. The assert
  is now a 6 × 6 × 4 mm fingertip probe at each cap demanding under 1 mm³ of stand in the way —
  a centreline sample would have passed straight through a slot a finger cannot enter.

**A test that measures interference is blind to occlusion**, and *"does it collide"* and
*"can you get at it"* are different questions. Every feature a human has to reach needs its
own reachability check. `SLOT_FLOOR` is now 24.0, with a 22 × 22 mm USB-C well beneath the slot.

## Standing guards — run these, they are not decorative

| guard | asks | when |
|---|---|---|
| `esphome/tools/check_restore_resync.py` | can a restoring control lie about the hardware after a reboot? | pre-commit, on the firmware yaml |
| `site/check_generated_current.py` | is the built page in the same commit as its source? | pre-commit, on `index.src.html` / `PRINT-SHEET.md` |
| `site/check_served_current.py` | is what a **visitor downloads** what `origin/main` would produce? | **after a push** — never a hook |
| `homeassistant/tools/check_dashboard_deployed.py` | is the dashboard **HA is serving** the one in git? | after a dashboard change |
| `status.realm.watch/check_deployed_current.py` | are the checks **actually running** the committed ones? | after a `deploy.sh` |

⚠️ **`.git/hooks` is not tracked, so a fresh clone starts unprotected.** Install line in
[`docs/verification.md`](docs/verification.md). Each guard fires only when its own source is
staged — *a hook that runs on every commit gets disabled, and a disabled hook protects nothing.*

None of them deploys. Where a fix has a cost, the guard's job is to make the cost visible, not
to pay it on somebody's behalf.

## Open

- [x] ~~**Print it.** Start with `ember-front-bezel.stl`~~ — **done, and the bezel is correct.**
      It has stayed **byte-identical** through every change since, verified by `git diff` on the
      STL across three rebuilds. 0.48 mm was legible. **Next print is `ember-back-shell.stl`** (the
      fix), then optionally the stand and the never-printed `ember-stand-base.stl`.
- [x] **Debossed labels — DONE, in `86748c6`'s successor. All four cut, all four verified.**

      JP chose the **power symbol** (IEC 5009) for the small cap, which resolved the one open
      decision and did it better than text would have: a symbol is drawn geometry, so its
      stroke width is set directly instead of inherited from a typeface.

      | label | where | size |
      |---|---|---|
      | `SD` | flat back, margin strip beside the slit, reads bottom-to-top | ink 6.40mm cap |
      | `MIC` | flat back, beside the mic bore | ink 6.40mm cap |
      | `VOL` | big cap face (the microSD side, per JP's bench test) | ink 4.70mm cap |
      | ⏻ | small cap face (the mic side) | 6.30mm dia |
      | USB-C | **skipped** — no room, and a USB-C port is self-evident | — |

      All grooves **0.48mm = 3 × `LAYER_H`**, same three layers as `BEZEL_DEBOSS`. Stroke
      **0.90mm everywhere**, the repo's nozzle floor.

      **Two sizes, forced not styled.** The big cap is 13.27mm across flats, which caps a
      three-letter label at ink 4.70. The flat back allows 6.40 and **SD needs it** — at ink
      6.00 the S's upper counter pinches to 0.843mm, under the floor.

      **A hand-cut stroke font** (`tools/strokefont.py`), not `Text()`. At these sizes 0.90mm
      of stroke is a stroke/height ratio of ~0.19, heavier than any real typeface's Bold, so
      with an outline font the stroke width is a *consequence* you can only measure and hope
      about. Here it is an argument. Two glyphs are not monospaced and the CHECK said so, not
      taste: **M** at 0.52 advance puts a 0.43mm rib between its valley and its stem at any
      size that fits, and **I** in a full-width box reads as a word break.

      **Verified, not asserted:** back shell **23308 tris, watertight, 0 non-manifold**;
      clearance **0.000 mm³** with the self-test firing at 1467.842; bbox still **14.40** deep,
      so nothing is raised. Bezel, stand and base plate are **byte-identical** — JP's printed
      bezel and stand are unaffected. Every label proves its own material clearance at import
      (`_label_ok`), and `tools/strokefont.py --self-test` carries four controls.

      ⚠️ **The mirror.** The back face is seen from −Z, so model +X runs to the viewer's LEFT
      and every label is mirrored on placement. This was reasoned out AND then looked at:
      `tools/slice_svg.py` slices the STL mid-groove and draws it with the same flip the eye
      applies, so a sign error shows up as backwards text. All four read correctly.

      Note the build takes **~9 minutes** and did so before the labels too — it is the hex
      field plus the vendor-STEP clearance boolean, not the new work.

- [ ] Button feel is the thing most likely to need a second print — but **the knob is
      `HINGE_L_BOOT` / `HINGE_L_RESET` (1.20 / 2.00), not `HINGE_T`.** Strain is `(t/2)·θ/L`
      with θ fixed by pip travel over the pip's lever arm, so thickening a hinge to firm it up
      moves it *toward* fracture. Cap size is the *other* lever and it moves the right way:
      both hinges are at ~1.20% since the caps went thumb-sized. See "the hinges are sized by
      strain" below.
- [ ] Touchscreen X handedness is still unconfirmed, but it is now **one tap away**: the raw
      touch X is captured *before* the clamp and shown on the telemetry band's idle line for 3 s
      after a tap. Tap near each edge — that answers sign *and* range together, where watching
      which coal flares only ever answered sign. Mirrored ⇒ `spark_col` needs `59 - tx/4`.
      There is no `transform:`, no `swap_xy` and no calibration anywhere in the config, so the
      orientation is **unknown**, not known-and-adjusted.
- [x] **Ember is registered in `status.realm.watch`** — `status.realm.watch@99dcc78`, deployed
      and reading **up**. It is a **TCP check on the ESPHome API**, `ember-satellite.lan:6053`,
      not HTTP: the firmware declares no `web_server:`, so there is no port 80 and no
      `/api/version` to poll, and forcing it into the realm-sigil pattern would have meant
      inventing an endpoint. TCP 6053 is also strictly better than ping — it proves the
      firmware is accepting connections, which is what HA needs; ping only proves the radio
      answers.
      > ⚠️ Not `binary_sensor.ember_reachable`, which was the other candidate: that polls
      > `familiar.lan:8091/health` and measures the **inference backend**, not the device.
      > Its name and its subject are different things.

- [ ] **`docs/verification.md` needs a summary, not more entries.** It is ~1,470 lines and 24
      sections. The early ones are load-bearing; the newest are marginal, and **every marginal
      entry dilutes the ones that would change somebody's behaviour.** It wants a short
      *"the mechanisms"* table at the top with instances beneath. **Do not add sections without
      applying the bar: would this change what somebody does?** — not what they would find
      interesting, and not what demonstrates rigour.
- [ ] **Two questions are with JP** and nothing here unblocks them: (1) **which slicer** printed
      the bezel and whether it reported the 3 non-manifold edges — that is the only thing that
      upgrades the mesh sentence from *one print, one slicer* to a claim about the class; and
      (2) the **six frozen bezel predictions** in
      `scratch/hosyond-s3/bezel-calibration.md`, which change sheet numbers if the web
      prediction lands. **Refining analysis while waiting for an observation is not progress.**

Full crash-recovery audit with ranked findings:
`~/.claude/projects/-home-jp-Projects-familiar-realm-watch/scratch/hosyond-s3/loose-ends.md`

## Done and closed

- **Lyra's grille motif is landed**, not deferred. It was re-derived rather than applied: as
  delivered it was 11 spines over a 50 × 15 field with 190 mm² open, sized for the round ⌀28
  driver that no longer exists, and applied as-is it would have cost 72% of the open area. The
  rake, the thick-to-thin gradient and the capsule ends survive; the length taper was moved
  into width. The grille is now a 59-cell field solved to the same 673 mm² nominal as the plain
  array it replaced (throat measured at 640.8 mm², −4.8 %), so the choice between it and the
  ridge is aesthetic, not acoustic.
- The HA long-lived access token in `configuration.yaml` is **revoked and verified dead**
  (old token → 401, `ha-llat` → 200, Ember still reachable).
- `~/Projects/esp3d` created for the Ender 3 Neo work. **It has no git remote yet.**

## The lesson that kept recurring

**Rendering and looking beat reading the source, five times out of five.** The trash-can Buy
icon, the `preload="none"` that was a lie, the exploded view rendered edge-on, the buried
screen, and the buried buttons — every one was invisible in correct-looking source and obvious
in the output.

Two corollaries earned the hard way:

- **A test that cannot fail is not a test.** The clearance checker returned a confident `CLEAR`
  for a while because the STEP and the parts were in disjoint coordinate frames; only a
  deliberately-sunk bezel exposed it. That self-test is permanent now and must report
  **1467.842 mm³**.
- **A total can absorb a complete regional absence.** The bezel honeycomb's first run put 75
  cells in the chin and *none* on the rails, and the assert passed because it read
  `count ≥ 60`. Count the regions, not the total.
- **A constant with no consumer cannot be wrong in a way anything detects.** `SD_PLATE` was read
  only by humans — the openings it named were hand-typed literals — so nothing recomputed when it
  was wrong, and a 26.50 mm channel with 18.54 mm of nothing behind it passed every check, because
  every check compared the *part* to the *board* and an opening over an absent component is
  agreement. It is the **second** instance in one file, a screenful from the dead `GRILLE_SLOT_W`
  already written up here. **Knowing the failure mode did not prevent it.** Openings now derive
  from a component table, with the converse asserted.
- **When a rounded number *is* a clearance, the direction of the rounding is part of the
  constraint.** `round(..., 2)` on a solved island position spent 0.0003 mm of the clearance it had
  just computed — and the new assert caught it on its first run, which is the *first* fault in this
  file's history found by a check rather than by a person holding a part. It rounds *away* from the
  obstruction now. A value sitting on a boundary has no slack to round into.
