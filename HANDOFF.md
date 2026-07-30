# HANDOFF — 2026-07-30

State at the end of the session that built the enclosure and the operating modes. Everything
below is verified against the artifact, not against a report — that distinction mattered
repeatedly here, and the running log of the times it did is [`docs/verification.md`](docs/verification.md).

## Shipped and working

| | |
|---|---|
| **Device** | Conversation, multi-turn, no pop, responsive taps. Three operating modes, verified across a power cycle on hardware. |
| **Repo** | <https://github.com/jphein/ember.realm.watch> |
| **Site** | <https://jphein.github.io/ember.realm.watch/> — page + print sheet |
| **STL downloads** | all **four** + `ember_case.py` from raw GitHub |
| **Enclosure** | boolean-verified 0.000 mm³ against the vendor solid; geometry asserts pass |

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

- **Hexagonal button caps, debossed rather than raised.** BOOT 10.40 mm across corners at
  0.90 mm deep, RESET 7.60 at 0.50. Flat-top, against the motif, because the pad is a living
  hinge and a pointy-top hex would put a *vertex* where the hinge must be.
- **Finger scallops in the stand's rear slot wall.** Both caps were completely buried — BOOT's
  top edge 3.81 mm below the stand's rim, with 0.40 mm between the cap face and solid wall. A
  taller cap could not have helped: the obstruction is *beside* the cap, not above it.
- **Debossed honeycomb + the hearth-wyrm on the bezel face.** 75 cells in the chin, a 16-cell
  chain up each rail, the wyrm 27.07 × 11.28 mm in the brow. All 0.45 mm deep, because on a
  bed face relief can only go inward.
- **A new figure, `site/renders/case-docked-rear.svg`**, wired into the site — the slab docked,
  from behind. It exists because a question was asked that no existing figure could answer.

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
2.50 mm diaphragm-to-baffle gap and the 33-hex grille solved to 673 mm² open. **Skip the
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

## Open

- [ ] **Print it.** Start with `ember-front-bezel.stl` — cheapest to reprint, and it now carries
      both the mic port and the whole debossed face, so it is the part most needing a fit check
      *and* the one that tells you whether 0.45 mm reads at arm's length.
- [ ] Button feel is the thing most likely to need a second print — but **the knob is
      `HINGE_L_BOOT` / `HINGE_L_RESET` (1.20 / 2.00), not `HINGE_T`.** Strain is `(t/2)·θ/L`
      with θ fixed by pip travel over the pip's lever arm, so thickening a hinge to firm it up
      moves it *toward* fracture. See "the hinges are sized by strain" below.
- [ ] Touchscreen X handedness is still unconfirmed, but it is now **one tap away**: the raw
      touch X is captured *before* the clamp and shown on the telemetry band's idle line for 3 s
      after a tap. Tap near each edge — that answers sign *and* range together, where watching
      which coal flares only ever answered sign. Mirrored ⇒ `spark_col` needs `59 - tx/4`.
      There is no `transform:`, no `swap_xy` and no calibration anywhere in the config, so the
      orientation is **unknown**, not known-and-adjusted.
- [ ] Ember is not in `status.realm.watch/checks.json`. Deliberately deferred pending a
      DHCP reservation; that reason has mostly expired.

Full crash-recovery audit with ranked findings:
`~/.claude/projects/-home-jp-Projects-familiar-realm-watch/scratch/hosyond-s3/loose-ends.md`

## Done and closed

- **Lyra's grille motif is landed**, not deferred. It was re-derived rather than applied: as
  delivered it was 11 spines over a 50 × 15 field with 190 mm² open, sized for the round ⌀28
  driver that no longer exists, and applied as-is it would have cost 72% of the open area. The
  rake, the thick-to-thin gradient and the capsule ends survive; the length taper was moved
  into width. The grille is now a 33-hex field solved to the same 673 mm² as the plain array
  it replaced, so the choice between it and the ridge is aesthetic, not acoustic.
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
