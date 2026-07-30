# enclosure — building it from source

`ember_case.py` is the artifact. **The STLs are output** — regenerate them, don't hand-edit
them.

## Setup

```bash
python3 -m venv cadenv
./cadenv/bin/pip install -r tools/requirements.txt
```

Nothing CAD-capable is installed system-wide on the workstation this was built on
(no OpenSCAD, no FreeCAD, no slicer), so the venv is the whole toolchain.

**Why build123d rather than OpenSCAD:** it sits on OpenCASCADE, which is what produced the
vendor's STEP file — so the board solid can be *imported* and clearances checked by boolean
subtraction. OpenSCAD cannot read STEP, which would mean hand-typing twenty-odd dimensions.
Every board number in `ember_case.py` is measured off the STEP, with a `VERIFIED{}` dict
recording the provenance of each.

## The vendor board model

Not committed — 17.7 MB of generated CAD does not belong in git. Download it to
`../ES3C28P_3D/ES3C28P_3D.step`:

<https://www.lcdwiki.com/res/ES3C28P/ES3C28P_3D.zip>

Verified genuine: an Altium → OpenCASCADE export, `PRODUCT('PCB','PCB')`, with connectors
modelled by part number. Without it the STLs still build; the clearance check is skipped.

## Build

```bash
./cadenv/bin/python ember_case.py      # STLs + clearance check + geometry asserts
./cadenv/bin/python tools/make_renders.py   # the figures used on the site
```

## What the checks actually do — and why there are two kinds

**`--- BOOLEAN CLEARANCE CHECK ---`** subtracts each part against the imported board solid
and reports the interference volume. Expect `0.000 mm³`.

⚠️ **It once returned a confident `CLEAR` that meant nothing.** The vendor STEP lives in its
own coordinate frame (X −52.75..−2.75) while the parts are in board coords, so the two never
overlapped in space and *every* boolean returned empty. It surfaced only because a bezel was
deliberately sunk 2 mm into the board and the detector **still** said `0.000`. There is now a
permanent self-test doing exactly that, and it must report **1467.842 mm³**. If it ever
reports zero, the checker is broken — not the parts.

**`[geometry]`** asserts three things a boolean is structurally blind to, because nothing
intersects:

| assert | why it exists |
|---|---|
| stand must not occlude the visible area | it once covered **19.5% of the screen** — the stand wasn't colliding with it, just in front of it |
| ≥16 mm under the slab | there was 6 mm, and a USB-C plug needs ~18–20. Missed because no figure ever showed a cable |
| ≥12 mm slot engagement | the fix for the first two is raising the slot floor, and that trades away retention |

**A test that measures interference cannot find occlusion.** Both faults were caught by
rendering the thing and looking at it — which is four for four in this project on defects
invisible in correct-looking source.

## Parameters most likely to need changing

| | |
|---|---|
| `DRIVER_W/H/R/T` | the speaker. Currently a 40 × 27 × 10 mm **sealed-back module** with tape on its back |
| `HINGE_T = 0.90` | the button pads must flex ~0.40 mm. **Most likely to need a second print** — if the buttons feel dead, drop to 0.70 |
| `GRILLE_SLOT_W2 / GRILLE_PITCH / GRILLE_FIELD` | a pure parameter block, so a motif can replace it without touching structure |
| `SLOT_FLOOR` | guarded by the asserts above — raising it clears the screen, lowering it buries it |
