# HANDOFF — 2026-07-30

State at the end of the session that built the enclosure. Everything below is verified
against the artifact, not against a report — that distinction mattered repeatedly here.

## Shipped and working

| | |
|---|---|
| **Device** | Conversation, multi-turn, no pop, responsive taps. All confirmed by ear. |
| **Repo** | <https://github.com/jphein/ember.realm.watch> — clean, in sync |
| **Site** | <https://jphein.github.io/ember.realm.watch/> — 200, print sheet 200 |
| **STL downloads** | all five + `ember_case.py` return 200 from raw GitHub |
| **Enclosure** | boolean-verified 0.000 mm³, all five parts watertight, 0 non-manifold edges |

`~/Projects/ha` is clean and in sync. Ember has been fully extracted from it.

## The enclosure, current state

Five printable parts in [`enclosure/`](enclosure/). **`ember_case.py` is the artifact;
the STLs are output.** Rebuild:

```
cd enclosure
python3 -m venv cadenv && ./cadenv/bin/pip install -r tools/requirements.txt
./cadenv/bin/python ember_case.py            # STLs + clearance check + geometry asserts
./cadenv/bin/python tools/make_renders.py    # the site figures
```

**Buildable from a fresh clone** — see [`enclosure/README.md`](enclosure/README.md).
`tools/requirements.txt` pins the exact set the shipped STLs were built with. The 17.7 MB
vendor STEP is linked rather than committed; without it the STLs still build and only the
clearance check is skipped.

### The speaker took three revisions — read this before changing anything

It is a **sealed-back module**, 40 × 27 × 10 mm, **double-sided tape on the back**, JST-1.25
pigtail. Each revision was a confident design built on an assumption the model could not
test:

1. ⌀28 round flanged driver in a recess — wrong shape.
2. 40 × 27 rectangle, shallow lip on the baffle — wrong mount.
3. Tape is on the **back**, the non-radiating face — this **inverts** the mount. The
   bonding surface cannot be the baffle. It is now a flat pad standing 0.80 mm proud of
   the chamber's **rear** wall.

Because the module carries its own rear volume, **chamber volume barely matters
acoustically**. The front path is the acoustic design — hence the recessed 2.20 mm baffle,
2.60 mm slots and 0.60 mm flares. **Skip the wadding** (nothing to damp); **still seal the
joints** (to stop the *front* cavity venting anywhere but the slots).

### Two faults booleans could never catch

Both found by rendering and looking, both now asserted in `_check_geometry()`:

- **The stand covered 19.5% of the screen.** Slot floor at `z=10` put the stand 31.1 mm
  *along* the tilted slab; the visible area starts at 19.76 mm. Nothing intersected — the
  stand was simply *in front of* the screen. **A test that measures interference is blind
  to occlusion.**
- **No room for the USB-C plug.** 6 mm available, ~18–20 mm needed. Unnoticed because no
  figure ever showed a cable.

`SLOT_FLOOR` is now 24.0, with a 22 × 22 mm USB-C well beneath the slot.

## Open

- [ ] **Print it.** Start with `ember-front-bezel.stl` — cheapest to reprint and it carries
      the mic port, so it is the part most needing a fit check.
- [ ] `HINGE_T = 0.90` is the parameter most likely to need a second print. If the buttons
      feel dead, drop to 0.70.
- [ ] Land Lyra's grille motif (`site/ember-art-web/case-motif.svg`) **after the first
      print** — deliberately deferred, since the slot array was just re-tuned for acoustics
      and changing open area while validating fit would confound two variables. Match the
      open area when you do.
- [ ] Touchscreen X handedness is still unconfirmed — tap near one edge and watch which
      coal flares. Opposite side ⇒ `spark_col` needs `59 - tx/4`.
- [ ] Ember is not in `status.realm.watch/checks.json`. Deliberately deferred pending a
      DHCP reservation; that reason has mostly expired.

Full crash-recovery audit with ranked findings:
`~/.claude/projects/-home-jp-Projects-familiar-realm-watch/scratch/hosyond-s3/loose-ends.md`

## Done and closed

- The HA long-lived access token in `configuration.yaml` is **revoked and verified dead**
  (old token → 401, `ha-llat` → 200, Ember still reachable).
- `~/Projects/esp3d` created for the Ender 3 Neo work. **It has no git remote yet.**

## The lesson that kept recurring

**Rendering and looking beat reading the source, four times out of four.** The trash-can
Buy icon, the `preload="none"` that was a lie, the exploded view rendered edge-on, and the
buried screen — every one was invisible in correct-looking source and obvious in the
output. Related: **a test that cannot fail is not a test** (the clearance checker returned
a confident `CLEAR` for a while because the STEP and the parts were in disjoint coordinate
frames, and only a deliberately-sunk bezel exposed it).
