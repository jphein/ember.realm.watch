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

**`--- MESH CHECK ---`** is arithmetic on the exported triangles: every undirected edge shared
by exactly two, every directed edge appearing once. Current output, re-derived from the
committed STLs:

| part | triangles | boundary edges | non-manifold |
|---|---|---|---|
| `ember-front-bezel` | 10 162 | 0 | **3** (known, see below) |
| `ember-back-shell` | 12 628 | 0 | 0 — watertight |
| `ember-stand` | 3 268 | 0 | 0 — watertight |
| `ember-stand-base` | 12 | 0 | 0 — watertight |

⚠️ **This repo used to claim "all parts watertight, 0 non-manifold edges", and that claim was
worthless.** The check behind it imported each STL with build123d and counted boundary edges —
but `import_stl` returns a **single `Face` with zero edges and zero volume**, so the count was
0 because there was nothing to count. A perfect result about an empty object, over four parts
of wildly different complexity, reported instantly. Measured properly, the bezel had 9
non-manifold and 22 mis-oriented edges.

**Three parts are genuinely watertight. The bezel carries 3 non-manifold edges, in a solid that
is otherwise valid** — `is_valid` true, exactly one solid, zero boundary edges — and the
count is 3 whether the union is built in 2D or 3D, at tessellation tolerances from 0.1 to
0.001, before or after `clean()`. It is a mesher artefact at coplanar face seams, not a hole:
there is nothing for material to leak through, and every slicer tested repairs it silently.
The cause is the mark's 104 stacked row-spans touching edge-to-edge where one row's run ends
where the next begins; inflating each span by 20 µm took 9 to 3.

It is recorded as a **number, not a threshold** — `KNOWN_NONMANIFOLD = {"ember-front-bezel": 3}`.
A boundary edge fails the build outright; exceeding the baseline fails it too. **Do not raise
the baseline to make a build pass.**

**`[geometry]`** asserts the things a boolean is structurally blind to, because nothing
intersects:

| assert | why it exists |
|---|---|
| stand must not occlude the visible area | it once covered **19.5% of the screen** — the stand wasn't colliding with it, just in front of it |
| ≥16 mm under the slab | there was 6 mm, and a USB-C plug needs ~18–20. Missed because no figure ever showed a cable |
| ≥12 mm slot engagement | the fix for the first two is raising the slot floor, and that trades away retention |
| a fingertip must reach each button cap while docked | both caps were **completely buried** by the stand. Probed as a 6 × 6 × 4 mm patch, not a centreline sample — a point would pass straight through a slot a finger cannot enter |
| ≥3 mm of stand wall behind the finger scallops | the fix for the above is removing wall, and that is the thing it trades against |
| **the back shell must be exactly 1 solid** | the only assert here that tests the thing rather than a proxy. If the hinge-tab arithmetic is wrong the slot ring closes and a pad is not a printed-in-place hinge but a loose hexagon that falls out on the bed. A dimension check cannot see that, and neither can the clearance check — **a severed pad collides with nothing** |
| per-region bezel cell counts, never a total | the first honeycomb run put 75 cells in the chin and **zero** on the rails, and the assert passed because it read `count ≥ 60`. A total absorbed a complete regional absence |
| the wyrm mark must be **exactly 1 component** | it shipped as **two** — head floating 1.215 mm above the shoulders with no neck — while the minimum-feature check read a healthy 1.23 mm. **A gap is not a thin feature**: morphological opening measures where material *exists* and is blind to material that is *absent*, so every instrument was green about a logo that had come apart |
| the mark must clear the mic flare and fit the brow with real slack | it previously occupied 11.25 of 11.29 mm of usable brow and sat 1.21 mm from a 1.20 mm keepout. Both true, both luck, and neither would have survived the mark changing size. It now has 11.69 mm of brow and 0.44 mm of slack, against a 0.30 mm floor |
| **the wyrm-and-port group must centre on the face** | the one assert on this face that is not a clearance, and it exists because **a clearance is satisfied by any amount of slack in the wrong place**. Ink 7.700–33.351 plus the mic flare's right edge at 42.300 centres on **x 25.000**, the exact face centreline. Nothing else here would have noticed it drift |
| **mesh arithmetic on the exported STLs** | the check this replaced *could not fail* — see the mesh row in the table below |

**A test that measures interference cannot find occlusion**, and *"does it collide"* and
*"can you get at it"* are different questions — passing the first says nothing about the
second. Every fault above was caught by rendering the thing and looking at it, which is five
for five in this project on defects invisible in correct-looking source.

## Parameters most likely to need changing

| | |
|---|---|
| `DRIVER_W/H/R/T` | the speaker. Currently a 40 × 27 × 10 mm **sealed-back module** with tape on its back |
| `HINGE_L_BOOT / HINGE_L_RESET` | 1.20 / 2.00 — the thinned-flexure length, **and the correct knob for button feel.** Longer is softer *and* safer |
| `HINGE_T = 0.90` | ⚠️ not the feel knob. Strain is `(t/2)·θ/L` and θ is fixed by pip travel over the pip's arm, so **thickening a hinge moves it toward fracture**, not toward a firmer press. Asserted at ≤2.0% — the threshold was tightened from 2.5% when the thumb-sized caps made 2.5% an inheritance from a worse version of the part |
| `BTN_R_BIG / BTN_R_SMALL` | the hex caps, **8.6603 and 5.7735 mm circumradius — 15.00 and 10.00 mm across the flats.** Thumb-sized, and the reason is strain rather than taste: a bigger hex puts the hinge further from the pip, so θ falls with it. **Not free choices**: pinned between the island's bottom edge (below y=0.80 it cuts the shell's bottom wall) and the slot-and-hinge reach, which must clear the back hex field at `HEX_FIELD_Y0` (19.00) with 0.80 mm to spare. A flat-top hex spans `R·√3` in Y |
| `CAP_CX_BOOT / CAP_CX_RESET` | 33.05 / 14.51 — the island centres, which are **not** the switch coordinates (36.58 / 13.45). A 17.32 mm island centred on the switch would eat into the M3 countersink, so the islands are offset off-switch and the pip reaches across |
| `PIP_D = 3.00` | the pip that reaches the plunger. It was 4.00, and shrinking it is what made the offset islands placeable — the island narrows toward its bottom flat, exactly where the pip sits, so a 4.00 mm pip left a 0.40 mm window of legal island X. That is not a tolerance, it is a hope |
| `DEBOSS_BIG / DEBOSS_SMALL` | 0.90 / 0.50. Deliberately **unequal**, so a thumb has two discriminators in the dark — size and depth — on a case with no lettering |
| `GRILLE_STYLE` | `"hex"` or `"ridge"`. Both solved to the same **673 mm² nominal** open area, so it is aesthetic rather than acoustic. Measured on the hex field: **throat 678.0 mm² across 27 apertures** (+0.7 % on the solve — it holds), **mouth 886.1 mm² in one opening**, because `GRILLE_FLARE` merges the face on purpose. The nominal figure describes the throat, which is the restriction that governs level |
| `SCALLOP_D / SCALLOP_Z0` | the finger pockets that make the docked buttons reachable at all. Module scope on purpose: `_check_geometry()` asserts against them, and a second hand-typed `12.00` in the assert is exactly the duplicate-constant trap this file has been bitten by |
| `SLOT_FLOOR` | guarded by the asserts above — raising it clears the screen, lowering it buries it |
