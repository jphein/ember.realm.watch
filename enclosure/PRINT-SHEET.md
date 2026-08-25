# Ember satellite case — print sheet

## ⚠️ WHICH FILE DO I PRINT — `enclosure/print/`, always

One file per part, the revision and content-sha in the filename, e.g.
`ember-front-bezel_r2_5f3fc539.stl`. The build refreshes this directory on every
successful run (it is the last step of `ember_case.py`'s gated commit), so it cannot go
stale by someone forgetting a step. Higher `r` = newer, readable straight from a slicer's
file picker — which is the interface where `enclosure/ember-front-bezel.stl` and a frozen
copy of the same name are indistinguishable, and on 2026-07-31 nearly got the superseded
bezel printed twice.

- `python3 tools/print_queue.py status` — what needs printing (⛔ REPRINT / 🖨 / ✅)
- `python3 tools/print_queue.py printed <part>` — record a finished, validated print
- History: git + `printed/<date>-…/` archives. The queue never holds old revisions.
- Prints run via OctoPrint on `serialhub` (USB-serial to the Ender 3).


> # ✅ CLEARED — `ember-stand-base.stl` seats. Fixed in `89001ea`. **REPRINT IT.**
>
> ⚠️ **If you printed the base plate before this, it is the wrong part — reprint it.** It was
> **1.40 mm too deep** and the sealed speaker chamber could not be closed with it. It is
> 2.8 cm³, the fastest part on the sheet.
>
> Re-measured here on the rebuilt solids, the same two ways the warning was raised:
>
> | | before | after |
> |:--|:--|:--|
> | plate Y extent | 4.30 – **20.70** | 4.30 – **19.00** |
> | interference with the stand | **269.136 mm³** | **0.000 mm³** |
> | plate size | 53.40 × **16.40** × 3.60 | 53.40 × **14.70** × 3.60 |
>
> **The cause is the part worth keeping.** The plate's `20.7` was `21.00 − 0.30` — the chamber's
> rear wall *was* 21.0 and 0.30 was the plate's clearance. That wall later became a *derived*
> value (baffle + front gap + driver body + tape pad = **19.30**) and **the plate kept its
> private copy of the old number.** The plate is now derived from the same constants and
> asserted, with a self-test: pushing it 0.5 mm deeper must be *detected*, because `0.000` is
> also what a broken detector returns.
>
> **Nothing in the build could have caught it.** Every clearance check compares a part to *the
> board*, and this plate never goes near the board; the mesh checks look at one STL at a time.
> **A part too big to fit its mate intersects nothing anybody was measuring.**

> # ✅ CLEARED — `ember-stand.stl` is printable. Fixed in `338a900`.
>
> This block used to read **DO NOT PRINT `ember-stand.stl` YET**: the speaker-wire pass into
> the sealed chamber was blocked by a 0.50 mm skin of the tape pad, leaving a slit ≈5.9 mm
> wide × 0.40 mm tall where a 1.2–2.0 mm lead has to pass. The pass was cut from y = 19.0,
> which is *behind* the pad's inner face, so the pad survived as a membrane over the mouth.
>
> Re-measured in the rebuilt mesh by the same ray-cast, so the numbers are comparable rather
> than two different questions:
>
> | | before | after |
> |:--|:--|:--|
> | Clear aperture into the chamber | **2.37 mm² of 30 (7.9 %)** | **28.69 mm² (95.6 %)** |
> | The blocking membrane | 0.474 mm, 12.4 mm³, 23 layers | **gone** — clear at z 6.5 / 8.0 / 10.0 |
> | Thinnest feature in the stand | 0.474 mm | 0.600 mm, 0.01 mm²/layer (a pre-existing 1-pixel corner) |
> | Features below 0.60 mm | 1 | **0** |
>
> The cut is now keyed to `PAD_PROUD` instead of a typed 19.0, and an assert intersects the
> finished solid with the pad's own plane over the channel's footprint and requires it empty —
> so it measures the **aperture**, not the constants. Two more slivers went with it: the wire
> groove's 25.6 mm knife edge against the R10 rear corner (`WIRE_X` 57.0 → derived 52.50) and
> the 0.85 mm fin the old saddle left on the bearing rim (now 5.35 mm).
>
> *Found and fixed by `morpheus-thin`. `ember-front-bezel.stl` had already been printed and is
> unaffected — that part is byte-identical across the fix, deliberately.*

Board: **LCDWIKI/QDtech ES3C28P** (Hosyond 2.8" ESP32-S3).
Source of truth: `ember_case.py` (build123d). The STLs are output, not the artifact.

Rebuild with:
```bash
cd enclosure && ./cadenv/bin/python ember_case.py
```
(That path was wrong here for a while — it still named the pre-extraction scratch directory
and a `../cadenv` that does not exist. See [`README.md`](README.md) for first-time setup.)

---

## Parts

| File | Qty | Print orientation | Supports | Notes |
|---|---|---|---|---|
| `ember-front-bezel.stl` | 1 | **front face DOWN** on the bed — ✅ **the STL is now exported already in this orientation, so load and print; no flip needed** (issue #25: it used to export face-UP, standing the part on four ⌀5.40 boss tips totalling 71.9 mm² with the whole 1847.9 mm² face in the air) | **none** | ⛔ **REPRINT — this part changed after JP printed one. The front-face deboss went 0.48 → 0.80 mm (#34): the wyrm, the side hexes and the bottom hex field were all too shallow to read at arm's length.** Sizes did **not** change — `BEZ_AFLAT` is still 2.60 — so a bezel already in hand is dimensionally fine and only reads faint. The visible face is the bed face — use a smooth PEI sheet. Mic flare + window are bed-side chamfers, so they self-support. **The debossed honeycomb and the wyrm mark are bed-side recesses**, 0.80 mm deep — exactly **five** layers at this part's 0.16 mm — and print as bridged voids, which is *why* they are recesses: on a bed face, relief only goes inward. Deeper means each recess now bridges over a 0.80 mm step instead of 0.48, so run the fan hard for the first few layers as you would on the shell's cap recesses. **2.20 mm of bezel is left over the glass** — measured on the exported mesh, not inferred: a 0.4 mm ray-cast grid found 3899 of 3901 debossed points sitting on a full-thickness slab, so no region is thinned from the back. |
| `ember-back-shell.stl` | 1 | **back face DOWN**, open side up | **none** *(measured)* | ⛔ **Set gap-closing radius / hole horizontal expansion to 0 before slicing — see below, a default will weld the buttons shut.** Hexagonal button pads + living hinges print in the first ~8 layers; the pips point up into the cavity. Counterbores are flat-floored ⌀5.80 pockets opening onto the bed. (This line said "countersinks widen downward" — a leftover from the deleted conical version; the head is cylindrical.) ⚠️ **REPRINT if you have not started this part yet — it gained five connector labels (#27) and a speaker-plug relief (#33).** The relief is a **through-opening in the back slab** over the speaker connector, x 44.54–50.35, y 31.79–40.94 — it prints as a bed-side aperture, so it costs nothing and needs no support. It stops at the *cavity* wall, not the outer edge, so the shell's outline is unbroken. **Labels** (`SD`, `MIC`, `VOL`, power symbol, and now `UART` `I2C` `SPK` `BAT` `IO`) are debossed **0.40 mm = 2 layers at the shell's own 0.20** (was 0.48 = 3 layers at the *bezel's* 0.16 — issue #26), and the two cap labels sit at the bottom of bridged recesses, so they are the first thing sag will blur. **The nine labels are exactly what the gap-closing warning above protects** — every one is a 0.90 mm groove, which is precisely the width a default gap-closer welds shut, and a welded label reads as a smudge rather than as a missing feature. **The debossed cap faces are bed-side recesses and they bridge 13.27 mm (BOOT) / 8.27 (RESET)** — expect visible sag in the middle of both, and run the fan at 100 % for the first ~5 layers. |
| `ember-stand.stl` | 1 | **bottom face DOWN** | **none** | ⛔ **REPRINT AGAIN. A stand printed from an earlier revision will not accept a battery backpack.** The mobile cover fouled the stand's rear top edge by **121.784 mm³** — and it was *pre-existing*, because the check for it had never actually executed; a check that has never fired is indistinguishable from one that passes. The cover could not be the fix (the interference is **mid-height on its chin end face and full width**, and its 2.20 mm wall with the contact leaf's kerf behind can yield 0.60 and no more), so **the stand takes a `DOCK_RELIEF` of 13.00 × 4.40 mm on its rear top edge**, sized by bisection against the real docked stack: 6.00 × 2.00 → 96.6, 9.00 × 3.00 → 28.8, 10.00 × 3.50 → 7.8, **13.00 × 4.40 → 0.000 mm³**. The check is a hard zero now. That is 250 mm³ off a part of over 100 cm³ — **the stand's slot was cut for a slab that existed before the backpack did.** ✅ **A desk-only build is unaffected in function**; the relief is on a hidden rear edge and removes nothing the slab uses. ⚠️ **REPRINT — this part is 16 mm taller than the one you have, and its grille is finer** (issues #29/#30/#31 + #28, see *The plinth* below). **Bridges, quoted by the span the printer actually crosses — the *narrow* dimension, since a bridge is laid the short way:** chamber ceiling **15.3 mm**, speaker-wire channel **24.7 mm** (both unchanged, both printed fine for JP), cable egress **6.0 mm**. ✅ **The baffle recess's top edge is a LEDGE, not a bridge, and needs nothing** — this row said "37.1 mm bridge, expect visible sag" and that was wrong. The 37.1 mm is its length **along an edge that is anchored for its whole run**: the recess is only **1.80 mm deep** and the 2.20 mm baffle sits directly behind it, so the lip is a **1.80 mm cantilever**, not a span. Measured — one layer above the edge there is 12.24 mm³ of lip and 14.96 mm³ of baffle behind it; one layer below there is **0.00 under the lip and 14.96 still under the baffle**. Expect minor droop on the top layer or two of the recess lip. ⚠️ **If you do see lip droop, do not attribute it to #28** — the grille rescale never touched this edge and could not have. **The egress figure is 6.0 and not 14** because the channel's R4 corners taper the void closed over the last 4 mm, leaving only 6 mm genuinely flat at the top — and it is a **true bridge** rather than an anchored ledge, because the channel is open through the plinth's full depth beneath it, so there is no material behind the span. Leave bridging on (slicer default). The plinth is **solid in the model on purpose**: a hollow one would have made the cradle floor bridge ~56 mm, whereas a solid one is just infill and the transition needs no bridge at all. Set infill by the *slicer*, not by hollowing the CAD. ✅ **The gap-closing / hole-horizontal-expansion warning on the shell row does NOT extend to this part's new features** — the egress is 14 mm wide and the corridor 18, three orders off anything that setting welds shut. Two features depend on it, not three; the grille's 0.90 mm webs are the ones to worry about. The **finger scoop** in the rear slot wall opens *upward*, so every wall is near-vertical: no bridge. (It is **one** opening, x 13.94–50.51, not two — `SCALLOP_MIN_RIB` merges them.) The **rear rim is now notched** across x 13.20–50.23 down to z 43.62 so you can reach the caps; the two full-height zones either side of it are what still holds the slab. The **wire saddle** merges into the notch's right-hand end — deliberate, same rule. |
| `ember-stand-base.stl` | 1 | flat | none | Closes the speaker chamber. Press fit. ⚠️ **Resized in `89001ea` — reprint if you made one earlier.** |
| `ember-mobile-midframe.stl` | 1 *(mobile only)* | **back face DOWN**, open side up — same face as the shell it is derived from | **none** | ⛔ **Inherits the shell's gap-closing warning in full** — it *is* `back_shell("mobile")`, so the same living-hinge buttons and 0.90 mm label grooves are in it, and the same default welds them. Two differences from the desk shell, both subtractive: the `BAT` **flank opening is blocked** and its label is **deleted with it** (a label beside solid plastic sends someone hunting for a port), and **two hex rows are dropped** near the chin screw — see the collar note below, it is a real defect and not tidying. Carries the speaker's **bond plateau** (fill the hex field flush, do not hollow it), the driver's 0.60 mm locating groove, two ⌀9.00 screw bosses, and the **+Y end-face cooling field**. Also carries the **LED wire pass** (one 4.75 hex at (32.0, 80.5), 100 % open) and the **internal labyrinth vent** in what is left of the divider. ⚠️ **The `MIC` bore and its label are both deleted on this variant** — buried under the backpack, the bore does nothing, and a back face reading `MIC` over no bore is the same lie told in ink. **19.69 cm³**, 33 352 tris, watertight (0 boundary, 0 non-manifold). Also carries **3 debossed flank labels** and the **driver witness outline** (151.3 mm², 0.40 deep) — ⚠️ if the flank labels look mirrored in your viewer, the viewer is showing you the −X flank *through* the part. |
| `ember-mobile-back.stl` | 1 *(mobile only)* | **OUTER face DOWN** — note this is the *opposite* convention to every other part on this sheet, and it is what makes the part support-free | **none** *(by construction)* | The cell trough opens **upward** as a concave cradle, the grille cells are **vertical prisms** rather than horizontal bores, the counterbore is a recess, and the screw bosses stand proud of what is the part's **top** while printing. ⛔ **The vent labyrinth's connecting band is 0.60 mm — the same width the gap-closer welds shut.** Weld it and the cell bay's failure vent becomes a dead end, which is the one feature on this part whose whole purpose is to not be closed. ⚠️ **The divider is now two stubs** (y 20.20–30.00 and 74.80–88.48); its middle is deliberately gone so the protection strip can lie flat beside the cell. **The chin pocket, its locating ribs, its hold-down detents and the crossing lane are all deleted** — do not look for them. ⚠️ **The divider is whole again, plus JP's double separator wall** — a partial wall and a stepped full wall, **0.90 thinning to 0.50**. Both are **below the 1.60 minimum-solid floor and both are EXPERIMENTAL**: the 0.50 band is the thinnest solid in this family and its thickness is set by the strip, not chosen. **Cost of failure is a floppy wall you can trim with scissors — nothing structural depends on it, and the print is the verdict.** **24.82 cm³**, 8 020 tris, watertight. Bed contact **3078.4 mm²**. |
| `ember-front-bezel.stl` | 1 | as above | none | ✅ **Reused bit-identical by the mobile build** — same STL, same four M3×12. If you have a good one, it serves either variant. |
| `ember-plug-cradle.stl` | 1 *(desk, optional)* | **bottom face DOWN**, exactly as exported — it prints standing in its in-well orientation | **none** | ⛔ **DO NOT PRINT THIS REVISION — four of its dimensions are ASSUMED, not measured (#49).** The captive-USB-C insert that press-fits into the stand's well so docking mates the plug one-handed. Before any print, put calipers on the actual cable's plug head and set `PLUG_W` / `PLUG_T` / `PLUG_L` / `TIP_TO_FACE` (plus `BOOT_D`/`BOOT_L`) in `ember_plug_cradle.py`, then re-run it — every height in the part derives from them, and 1 mm of `TIP_TO_FACE` error is 1 mm of mating error. **~15 min of print, so iterate here, never the 5.4 h stand.** Seat ledges bridge 7.0 mm over the boot channel (fan up, no support). The outer press ribs are the fit: if it slips in loose or needs a mallet, the knobs are `RIB_PROUD_*`, per-side crush is (proud − 0.15). Grip on the plug is deliberately **light** (posture (a) of the issue's extraction-force trade): insertion is one-handed, removal is steady-the-stand two-handed. Load the plug sideways through the open rear face, cable first down the well and out the egress arch. |

**All exposed exterior edges now carry a 0.80 mm 45° chamfer** (#35) — the shell's back face,
the stand's base and rim, and the base plate's one exposed edge. ⚠️ **The bed-side ones are
functional, not just cosmetic:** a chamfer there absorbs elephant's foot, which matters most on
the **stand's base**, because that is the bearing face and a bulged foot is what makes a stand
rock. It also matters more than usual right now — the Z-offset is running deliberately squished
at −2.14. **The bezel is not chamfered yet** (its own issues are in flight); when it is, it uses
the same constant. The parting line is deliberately left plain — chamfering one half of a butt
joint gives an asymmetric reveal.

Outer sizes: slab (bezel + shell assembled) **55.9 × 91.9 × 17.4 mm**; stand
**64 × 64 × 56 mm** (was 40 — the plinth, see below); **mobile backpack (bezel + board +
midframe + cover) 55.90 × 91.90 × 39.00 mm** — the same width AND the same length as the desk slab,
to the hundredth: there is no lip. Depth is the only difference. The story is in
[`docs/enclosure-mobile.md`](../docs/enclosure-mobile.md) §1.
Material use ≈ **166 cm³** total (~206 g in PLA), measured from the current STLs by
signed-tetrahedron volume — not an estimate. Per part: stand **137.6**, back shell 17.9, bezel
7.5, base **2.8** cm³. The stand is **83 %** of the print, because it is a speaker cabinet
standing on a 16 mm plinth, and both of those want mass. ⚠️ It was 93.1 cm³ before the plinth —
budget roughly half again as much filament and time for that part, and only that part.

> **Mesh state, stated honestly because a print sheet is where it matters.** Three of the four
> STLs are watertight: zero boundary edges, zero non-manifold edges. **`ember-front-bezel.stl`
> carries 3 non-manifold edges** — coplanar-seam artefacts from the wyrm mark's 104 stacked
> row-spans, inside a solid that is otherwise valid with **zero boundary edges**. There is no
> hole. **Observed rather than predicted: JP has printed this part and the dimensions are
> good**, so those 3 edges did not stop a real print on a real slicer. That is one print on one
> slicer — it is *not* a claim that every slicer repairs this silently. If yours reports it,
> that is the expected number and not a download problem. Anything *above* three, or any boundary edge at
> all, means something new broke — the build asserts on exactly that.

---

## Slicer settings

| | Bezel | Shell | Stand | Base |
|---|---|---|---|---|
| Layer height | **0.16 mm** | 0.20 mm | 0.20 mm | 0.20 mm |
| Perimeters | 3 | 3 | **4** | 3 |
| Infill | 15 % gyroid | 15 % gyroid | **25–30 %** | 20 % |
| Supports | no | no | no | no |
| Bridging | — | — | **on** | — |

The bezel gets the fine layer height because its front face is the one you look at, and
because the mic bore is only ⌀2.40 mm — at 0.2 mm layers it starts to close up.

⚠️ **These two numbers are now CONSUMED BY THE MODEL, not just advice to the slicer.**
`ember_case.py` carries `LAYER_H_BEZEL = 0.16` and `LAYER_H_SHELL = 0.20`, and every recess floor,
the counterbore and the living-hinge thickness are whole multiples of *their own part's* value —
asserted, with a control. **So changing a number in this table changes the geometry**, and the
build will refuse rather than silently put a floor mid-layer.

⚠️ **AND SET THE FIRST-LAYER HEIGHT TO THE SAME VALUE — the alignment math assumes a UNIFORM
stack.** Every "exactly N layers" claim above is `N x LAYER_H` measured from z = 0; a different
first layer shifts every boundary up the part by the difference, and then no floor lands on one.
Measured, not hypothetical: the first r2 bezel (PrusaSlicer 2.9.6, 2026-07-31) went out with the
profile's default **0.20 first layer + 0.16 rest**, which put the 0.80 deboss floor mid-layer.
PrusaSlicer slices at layer mid-planes, so it rounded the recess UP to five voids ending at
z = 0.84 — deboss printed 0.84 instead of 0.80, glass floor 2.16 instead of 2.20. Harmless
**that time**, because both errors pointed the direction JP wanted — a floor that rounded the
other way would have SHALLOWED a feature that was resized precisely to stop reading faint, and
nothing in the slicer would have said so. For the bezel: first layer **0.16**, not the default.

> Until issue #26 there was a single `LAYER_H = 0.16` labelled "the shell parts". It was the
> **bezel's** value wearing the shell's name, and it was load-bearing in both directions at once —
> correct where the bezel consumed it, wrong where the shell did. Three further depths
> (`DEBOSS_BIG`, `DEBOSS_SMALL`, `HINGE_T`) turned out to be mid-layer at **every** layer height
> this project uses, which is why nothing had ever caught them.
>
> **If the shell is ever moved to 0.16** — its only real cost is ~25 % more print time, and the
> counterbore stops being exactly flush — change `LAYER_H_SHELL` and rebuild. Everything
> re-derives. Do not change one depth by hand.

The stand wants **more walls and more infill than feels necessary**: it is a speaker
enclosure, and cabinet stiffness/mass is what stops a 2 W driver sounding like a rattle.
Heavier is better here.

**Filament:** matte **charcoal/coal PLA** for bezel + shell — best surface finish and the
tightest dimensional accuracy, which matters because the board pocket is a 0.35 mm fit.
Use **PETG** instead only if it will sit in direct sun (PLA creeps at ~50 °C).
**Print the whole case in WHITE if you want it to glow.** JP's choice, and it changes the
lighting design: white PLA is translucent, so the WS2812 lights the shell itself rather than
only escaping through holes. That is why there is no diffuser part — see the LED note under
*Speaker* / the hex back below.

### ⛔ Before you slice the back shell: one default will destroy the buttons

**Set "slice gap closing radius" (Cura) or "hole horizontal expansion" to `0`.**

**Two features depend on this setting, not one.** The button moat is the one that strands the
part; the **label grooves are the one you would not notice until the print is off the bed**,
because a welded label still looks like a label in the slicer preview. Every glyph on the back
face — `SD`, `MIC`, `VOL` and the power symbol — is cut at a **0.90 mm groove width**, the same
order as the moat and equally inside what a gap-closer exists to remove. Same fix, one setting,
both saved.

The moat around each button island is `SLOT_W = 0.60` mm — **1.50 nozzle widths** at 0.40 mm.
The geometry is clean: **0.60 mm of void on both sides of both islands, verified at all 12 wall
layers.** But a non-zero gap-closing radius exists specifically to **close narrow slots on
purpose**, and it is on by default in some profiles. That turns a correct STL into a shell whose
buttons look perfect and do not move — **the model is not the failure, the slicer is**, and no
amount of re-checking the STL would find it.

Even with it at zero, **expect some fusing.** At a realistic 0.45 mm bead the two perimeters
meet almost exactly, and the hinge shoulders are where it shows first.

- **Free the pads with a fresh blade at assembly step 3**, before anything else goes together.
- ⚠️ **Cut from the outside inward and stop at the hinge.** The hinge is the one feature designed
  to flex — a 0.80 mm membrane at a calculated 1.07 % strain against PLA's ~2 % yield. **A knife
  nick there is a stress riser the calculation does not include.**

### The cap-face bridges are 13.27 and 8.27 mm, and they grew 82 % without being noticed

The BOOT cap's deboss floor spans `R·√3` = **13.268 mm**; RESET's is **8.268**. Both bridge
routinely over a 0.80 / 0.40 mm recess — **this is a cosmetic note, not a defect.** Expect sag in
the middle of the faces you look at and press. Fan at 100 % for the first few layers.

> **Worth knowing how the number got there.** At the old caps that span was **7.275 mm**
> — both figures computed from `BTN_R_*` and `CAP_INSET` rather than measured, so the ratio
> is exact and end-to-end on one basis. *(Voxel-measuring both ends instead gives 7.20 → 13.20
> and +83 %; pairing one measured end with one computed end gives +84 %, which is wrong while
> looking like the most careful option. **State the basis, not just the value.**)*
> Growing the caps to thumb-size took it to 13.268 — **+82 %** — inside a change that was
> reviewed for hinge strain, lever ratio, countersink clearance and the hex-field boundary.
> **Printability of the recess floor was not on that list.** A checklist that is complete for
> the questions it knew about is a harder failure than an omission, because nothing about it
> looks incomplete.

### "Supports: none" for this part is measured, and now it is stronger than that

| band | area |
|---|---|
| overhangs 10–30° | **0 mm²** |
| overhangs 10–30° | **0.00 mm²** |
| overhangs 30–45° | **0.00 mm²** — the countersink cones were this band's only occupant and the counterbore replaced them |
| near-horizontal (bridged) | **499.12 mm²**, all of it |
| first-layer contact | 3727.9 mm², **one island**; 92.0 × 14.60 mm is 6.3:1, so **no brim** |
| thinnest feature | 0.750 mm — the hex web |
| side-channel roofs | 2.62 / 1.57 / 1.05 mm bridges — trivial |

**Nothing on this part sits in the awkward 10–45° range at all.** Every unsupported facet is
*near-horizontal* — i.e. bridged — which is a stronger statement than "no supports needed": there
is no shallow overhang anywhere to print badly. Where the 499.12 mm² is:

| printed z | area | what |
|---|---|---|
| 0.40–0.80 | ⚠️ **re-measure** | **the two cap-deboss floors — the only genuine bridges**, 13.27 and 8.27 mm. The band moved: the deboss depths were 0.90/0.50 and are now **0.80/0.40** (issue #26 — neither old value was a whole number of layers at any layer height this project uses). The 211.66 mm² figure was measured on the old depths and is **not** re-derived here |
| 3.00–3.50 | 71.44 mm² | the four counterbore floors — **annular ledges, not bridges** (see below) |
| 8.00–8.50 | 171.63 mm² | side channels + the USB-C relief roofs |
| 9.00–9.50 | 14.00 mm² | |
| 10.00–10.50 | 30.40 mm² | |

**So the fan note belongs to the cap faces and nowhere else.** Run it at 100 % for the first
~5 layers; nothing later on the part needs it.

---

> ⚠️ **Settled, and it moved: the large cap belongs at the LOW-x end.** `86748c6` derives the
> switch identification from the microSD socket instead of carrying it as a literal, and the
> answer inverted — **BOOT (the readable switch) is at x 13.45**, RESET at 36.58. The large
> 15.00 mm cap and its 13.27 mm bridge went with BOOT to the other end of the board; the island
> centres are now **16.66** (large) and **35.66** (small). Every *figure* on this page was a
> property of the cap and is unchanged — only which end it sits at moved. **If you printed a back
> shell before `86748c6`, its caps are on the wrong switches.**

## Fasteners

**4 × M3 × 0.5 × 12 mm ISO 4762 socket cap** (hex recess, cylindrical head), driven **from the
back** into a **flat-bottomed counterbore**, so no heads appear on the front face.

> ⛔ **This changed, and the previous guidance would send you to the wrong shelf.** This sheet
> used to specify a **countersunk (flat) head** for a conical countersink. The part now has a
> **⌀5.80 × 3.00 mm flat counterbore** for a **cylindrical** head. **A conical head in a flat
> counterbore does not seat on anything** — it contacts the bore edge on a circle, or bottoms on
> its point. That is worse than either geometry the old text analysed, so all of it is deleted
> rather than adjusted, including its length table: see the length note below.

| | |
|---|---|
| Screw | `M3 × 0.5 × 12` **ISO 4762** socket cap, hex recess |
| Head | ⌀**5.50** measured, not tabulated |
| Counterbore | ⌀**5.80** (0.30 diametral clearance, 0.15 a side) × **3.00 mm** deep — **15 layers exactly** at the shell's 0.20, and **exactly the measured 3.00 mm head height**, so the head is dead flush with no rounding |
| Through-hole | ⌀3.30 |
| Pilot in the bezel boss | ⌀**2.50**, blind |

Load path: head bears on the **flat counterbore floor** in the back shell → 5.5 mm standoff →
through the PCB's ⌀3.20 hole → **self-taps into the blind ⌀2.50 pilot in the bezel boss**.

⚠️ **The length convention changed with the head, and this is the trap.** A **countersunk**
screw's stated length **includes** its head; an **ISO 4762 socket cap's does not** — 12 mm is
**under-head**. So the old ×14/×15/×16 table is not mislabelled, it is on the wrong basis
entirely, and none of its numbers transfer. Re-derived for the new screw:

| screw (under-head) | tip reaches | engagement | |
|---|---|---|---|
| M3 × 10 | z +3.34 | 3.34 mm = 1.11 D | short |
| **M3 × 12** | z +5.34 | **5.34 mm = 1.78 D** | **the spec**, 0.86 mm clear of the pilot end |
| M3 × 14 | z +7.34 | — | ⛔ **bottoms out** (pilot ends at 6.20) |

**×14 and ×16 still bottom out, and the failure still looks like success** — the tip hits the
bottom of a blind pilot before the head reaches its floor, so it feels tight while clamping
nothing. That hazard survived the redesign unchanged; only the numbers moved.

- **The counterbore is deeper than the back wall, and that is by design.** 3.00 mm of bore in a
  2.60 mm wall passes into the cavity — where the boss **flares to ⌀8.40** at the cavity floor,
  tapering to ⌀5.40 at the PCB face. The flare is what the bore lands in. ⌀8.40 comfortably
  surrounds ⌀5.80, so there is material all the way round.
- **The counterbore floor is an annular ledge, not a bridge — it prints essentially free.** It
  is tempting to call it a 3.30 mm span over the through-hole; measured, it is an **annulus
  supported on its full outer circumference, cantilevering 1.25 mm inward** — `(5.80 − 3.30)/2`.
  Four of them come to **71.44 mm²** against **71.47 predicted** for four OD 5.80 / ID 3.30
  rings, which is agreement to 0.03 mm². A ring like that needs no fan and no attention.
  > **The exact-layer-count depth is still right, for a smaller reason than a bridge.** 15 × 0.20
  > puts the floor on a **clean layer boundary**, so the head seats on solid material instead of
  > on a partial layer. That is worth having; "it bridges 3.30 mm" was not the reason.
  >
  > ⚠️ **This used to read 19 × 0.16 = 3.04, and that was issue #26.** 0.16 is the *bezel's* layer
  > height, borrowed by a shell feature. At the shell's own 0.20 the old 3.04 was 15.2 layers — a
  > mid-layer floor under a load-bearing head. The 0.04 mm of deliberate sink is also gone: 3.00
  > divides 0.20 exactly, so correcting #26 deleted a compromise rather than adding one.
- A head bearing on a **flat** floor gets a genuine full-face seat, so **no re-nip is needed** —
  that advice belonged to the conical staircase and went with it.
- **Heat-set inserts will NOT fit.** The vendor specifies a ⌀5.60 pad around each mounting
  hole, so bosses are capped at ⌀5.40 **at the PCB face**. An M3 insert needs a ⌀4.0–4.2 bore,
  leaving a 0.6 mm wall that will split. Self-tappers only.
- **Snug, not hard.** You are clamping a 12 g PCB. A cylindrical head on a flat floor spreads
  load over its whole face rather than a rim or a step, so this is now ordinary care in PLA
  rather than a design consideration.

Stand base: press fit. Seal the seam with a bead of silicone or a strip of tape — it needs
to be **airtight, not structural**.

---

## The slab in the stand

The slab drops into a tilted slot, **15° back from vertical** for a seated viewer.

⚠️ **Revised — it used to bury the screen.** The slot floor was at `z = 10.0`, which put
the stand **30 mm** up the slab — **31.1 mm along it** once tilt is accounted for
(30 / cos 15°). The visible area starts only 19.76 mm up from the slab's bottom edge, so
the stand covered **11.3 mm of screen: 19.5% of a 58.05 mm display**, hidden behind the
box. Caught by looking at a render; a boolean clearance check can never find this, because
nothing intersects — the stand was simply *in front of* the screen.

The same depth left just 6.0 mm between the slab's bottom edge and the stand floor, and a
straight USB-C plug body needs **~18–20 mm**. There was nowhere for the power lead to go.

**Slot floor is now `z = 24.0`:**

| | |
|---|---|
| Engagement | **16.6 mm** along the slab — a captive slot constraining both faces |
| Visible area | **entirely clear** of the stand |
| Room below for USB-C | **20.0 mm** |

There is a **USB-C well** under the slot — 22 mm wide × 12 mm deep, **tilted to follow the
slab's own axis** and running down it to the cradle's inner floor.

⚠️ **It was a flat box first, and that did not work.** The slot is a box rotated by the tilt
with `align=MIN`, so **its bottom face tilts too** — the front-bottom corner sits at
z ≈ 26.4 while the rear-bottom drops to ≈ 21.6. A well cut flat to z = 24 therefore left a
wedge of material exactly where the plug emerges. It measured as "20 mm clear" only because
the check point-sampled the **centreline**, which is the single locus where that discrepancy
vanishes. A plug has width, and its front corner hit the wedge.

Re-measured by sweeping a plug-shaped box down the insertion axis:

| plug | clears |
|---|---|
| slim / low-profile 12 × 6 mm | past 20.7 mm |
| typical moulded 14 × 7 mm | past 20.7 mm |
| chunky braided 16 × 9 mm | past 20.7 mm |
| very bulky 20 × 11 mm | past 20.7 mm |

20.7 mm is the stand floor; past that the well opens into the cable route. A straight plug's
overmould is 18–25 mm, so all of them fit.

**Depth is 12 mm, not 22, and that is solved rather than chosen:** the well drifts forward
`sin(15°)` per mm of descent, and at 22 mm wide its front face reached y = 20.6 — inside the
sealed speaker chamber, whose rear wall is at y = 22.0. `_check_geometry` asserts this, and
it is what caught it.

`ember_case.py` asserts all three of these on every run (`_check_geometry`), so the screen
cannot get buried again by a later tweak.

## The plinth — why the stand is 56 mm and not 40

⚠️ **This is a reprint of `ember-stand.stl`, and it is the reason for it.** Issues #29/#30.

JP measured the cable: **40 mm from the plug tip to the first point it can bend.** That is a
length of *straight corridor*, and its direction is not a free variable — the port fixes it,
15° off vertical, pointing **down and forward** along the slab's own axis.

On the 40 mm stand the port sat 25.92 mm above the desk, which offers 26.83 mm of straight
run. **A straight 40 mm tail therefore ended 13.2 mm below the desk**, which is why the
device would not seat and why the plug levered it out of the slot. Note what that rules out:
**recessing the slot floor cannot fix it at any depth** — the deficit is larger than the whole
floor thickness. The port has to sit higher.

| | |
|---|---|
| Stand height | **56.0 mm** (cradle 40.0 + **plinth 16.0**) |
| Straight corridor, port → desk | **43.40 mm** for a 40 mm requirement |
| End of the rigid run | y = 26.47, **3.28 mm above the desk**, still heading forward |
| Required there | **2.25 mm** = `CABLE_OD/2` — see below — so **1.03 mm of margin** |
| Cable meets the desk | y = 25.59, i.e. 25.6 mm behind the front face |

**⚠️ What must clear the desk is the cable's CENTRELINE, not its tip.** A tail whose lowest
surface just grazes the desk is a tail whose axis is half a diameter *below* it — meaning the
last few millimetres of the **rigid** run are already being deflected, which is the exact load
path that levers the device out of the slot. That `CABLE_OD/2` term is the difference between a
clearance and a coincidence, and it is what puts the derived floor at **54.97 mm** rather than
52.72.

> **Both figures that circulated during this work reconcile exactly on that term**, which is how
> it was found. The port's offset from the slab mid-plane was disputed in sign — 1.152 mm of
> height rides on it — and the two candidate heights turned out to be the two signs, each plus
> 2.25: **54.97** (port on the back-shell side, which is the settled and correct one) and
> **53.82** (the other). Neither was a rival model. The settled sign is the one needing the
> *taller* stand, because the back of a backward-leaning slab is its **low** side.

**Nothing in the cradle moved.** The slot, the well, the sealed chamber, the grille, the
driver seat and the wire route are the same geometry at the same numbers — the plinth is
modelled *below* the cradle's own z origin and lifted at export. ⚠️ **That means every height
in `ember_case.py` is 16 mm lower than the same height measured off the STL.** The rim notch
is `z = 27.62` in the source and `z = 43.62` in the file you slice. Both numbers are correct;
neither is correct in the other frame.

### The cable comes out the FRONT, and that is not a choice

The obvious routing is out the back. It is geometrically impossible at this height, and the
arithmetic is short enough to put here so nobody "fixes" it:

The tail is still travelling forward, 75° below horizontal, when it reaches the desk. Turning
that rearward is a 105° turn, and a circular arc of radius R descends **1.2588 × R** doing it.
The budget above the desk is **3.28 mm → R ≤ 2.6 mm**, against the ~18 mm a 4.5 mm USB-C cable
wants. Width does not substitute: a U-turn in the horizontal plane at R18 needs 40 mm of x.

> **A stand where the cable completes its bend *inside* the base is a different part** — it
> needs 22.7 mm below the end of the rigid run, i.e. ~75 mm tall. 56 mm accommodates the rigid
> run and lets the cable bend in **open air**, and that only works if the exit is where the
> cable is already pointing.

So the plinth carries a **14 mm wide × 10 mm tall channel** at desk level, opening through the
front face (R4 corners, so the visible mouth reads as an arch rather than a bite). Lead the
cable out of the front and away to either side. It is under the grille and mostly hidden by
the overhanging slab.

### What it costs, and what it does not

| | |
|---|---|
| Bearing footprint | **2922 mm²** of a 4010 mm² plan |
| Quadrants (front L/R, rear L/R) | **47 % / 47 % / 99 % / 99 %** of their plan |
| Contact behind the loaded CoM (y = 45.89) | **1116 mm²**, reaching to y = 64.0 |

The two front quadrants carry the speaker chamber's **access shaft** — 54 × 15.3 mm, which now
runs the full height of the plinth because the driver still goes in from below and the base
plate still closes the chamber at the top of it. That shaft plus the egress channel are the
*only* two openings in the underside, and `_check_geometry` holds a ledger of exactly those.

⚠️ **The old bearing check would have passed on a stand with no underside at all.** It probed
z 0–0.4, which under a plinth is a plane in the *middle* of the part. It now probes the real
bearing plane and tests the **distribution** as well as the area, with a 4 mm perimeter ring as
a control that must fail — because area alone cannot tell a ring from a face, and that
distinction is the whole point of the check.

## Speaker

It is a **sealed-back module**, not a bare driver: a plastic box carrying its own rear
cavity, diaphragm on one face, JST-1.25 2-pin pigtail, **double-sided tape on the back**.
**40 × 27 mm footprint, 10 mm thick** (measured).

> **That inverts the mount, and it took three revisions to get right.** The first cut
> assumed a round ⌀28 flanged driver in a recess. The second made it a 40 × 27 rectangle
> and kept a shallow lip on the baffle. Both were wrong, because a baffle-mounted driver
> needs adhesive on the face that *meets the baffle* — and this one has it on the
> opposite side. The bonding surface cannot be the front wall at all.

**How it mounts.** A flat **tape pad** stands 0.80 mm proud of the chamber's rear wall,
40 × 27 with matching corner radius. Stick the module's taped back to it; the diaphragm
then faces forward at the grille. The pad is *raised* deliberately, so the adhesive meets
one continuous plane — no fillet, no print artefact at the wall/floor junction to
interrupt the bond. **The baffle's inner face is left completely alone**: the module never
touches it, and anything cut there would only put a cavity edge in front of the diaphragm.

**Chamber depth is now derived, not chosen.** Baffle + 2.50 mm front gap + 10 mm module +
0.80 mm pad + margin → rear wall at **19.3 mm**. Previously it was pushed to 22.0 "as deep
as the slab slot allows", maximising sealed volume — the right goal for a baffle-mounted
driver and the wrong one here. With the module taped to the rear wall, extra depth is not
extra enclosure, it is **extra air in front of the diaphragm**, which is a cavity
resonance. There is an assert in the source so this can never silently foul the slot.

⚠️ **Two corrections to earlier advice in this file, now that the module is known:**

- **Skip the wadding.** It was recommended to damp standing waves in the sealed chamber.
  A sealed-back module brings its own rear volume, so there is no rear chamber to damp —
  stuffing the front cavity would just absorb output on its way to the grille.
- **Sealing still matters, for a different reason.** Not to hold bass in a rear chamber,
  but to stop the *front* cavity venting anywhere except through the slots. Any leak lets
  the front wave escape and cancel, which costs level. So still seal the wire
  pass-through and the base seam — the reason changed, the instruction didn't.

The **volume figures earlier in this file are about a rear chamber that no longer exists
in the acoustic sense.** They still describe the printed void; they no longer describe
what the module is loading into.

- The ES3C28P **speaker header is unpopulated** — you need a 1.25 mm 2P pigtail.
- Changing driver: edit `DRIVER_W`, `DRIVER_H`, `DRIVER_R` in `ember_case.py` and re-run.
  `GRILLE_INSET` (1.0 mm) keeps the slots inside the radiating area so the grille never
  opens onto the frame — an open slot over the flange is a dust path into the chamber and
  vents the enclosure.

⚠️ **Keep the driver magnet away from the top 8 mm of the board's back face** —
`ANT = (17.57, 32.21, 80.04, 85.70)` is the PCB Wi-Fi antenna. The stand geometry already
puts the magnet ~70 mm away, so this only matters if you relocate the speaker into the slab.

---

### Making it louder — and the grille is the wyrm's ridge

⚠️ *This subsection was lost once already: rewriting the Speaker section for the sealed-back
module replaced a span that happened to contain it. Restored, and updated.*

The bottleneck was never the box volume, it was the **baffle**. A slot behaves like a short
duct and its impedance scales with length ÷ width, so 2.20 mm slots through a 4.00 mm wall
(**1.82:1**) made the sound squeeze through slits nearly twice as deep as they were wide.

1. **The baffle is recessed to 2.20 mm** in the grille region only, cut from the *outside*
   so the inner face stays flat. Slot aspect 1.82:1 → **1.00:1**, roughly halving the
   impedance.
2. **The grille is a hexagonal honeycomb** — 59 cells placed, **53 open apertures** after the
   field's rounded corners clip them, **4.50 mm across the flats** on a
   5.40 mm pitch (2.598 mm circumradius), 0.90 mm web, in a 38 × 25 field.

   > ⚠️ **Rescaled in `980598d` (issue #28) — these numbers replace the 6.50 AF / 33-cell /
   > 27-aperture figures this section carried before, which described the part JP printed and
   > was unhappy with.** The complaint was *"sagging/messy but holes are open"*: the apertures
   > **formed**, so the defect was **droop, not collapse**, and droop scales with unsupported
   > **span length**. Two levers, both applied — `GRILLE_FLARE` 0.60 → **0.25**, which restores
   > the 0.90 mm webs at the mouth that anchor each span, and `HEX_R` down so across-flats is
   > exactly 4.50. Measured downward-facing span at the aperture band: **35.283 mm in one run →
   > 4.567 mm in eight. 87 % shorter.**
   >
   > **Counter-intuitive and worth keeping:** a finer lattice is *less* open per unit field,
   > because `HEX_WEB = 0.90` is a print floor that does not scale with the cells —
   > `(a/(a+w))²` goes 0.7714 → 0.6944. So shrinking the holes **spends** open area, which is
   > why `GRILLE_INSET` went 1.5 → 1.0 to grow the field and pay for it.

   Re-measured on the current geometry, in the X–Z plane, which *is* the aperture plane
   because the bores run in Y:

   | | area | openings |
   |:--|--:|--:|
   | **Throat** — un-flared cells ∩ field, the acoustic restriction | **640.8 mm²** | **53** |
   | **Mouth** — flared cells ∩ field, the face you touch | **779.2 mm²** | **53** |
   | the field itself (38 × 25, r2.0) | 946.6 mm² | — |

   > **The mouth is 53 separate apertures now, and that is the visible change.** At the old
   > 0.60 flare the mouth webs were consumed entirely and the whole field read as **one
   > 886 mm² opening** with a honeycomb sitting 0.40 mm behind it — finer cells would have
   > changed nothing you could see. At 0.25 the mouth web is **0.4670 mm** and survives, so the
   > honeycomb is a honeycomb from outside. `GRILLE_MOUTH_WEB` asserts ≥ 0.45 **or** fully
   > merged, and nothing in between: a 0.1 mm fin is the one outcome that is neither.
   >
   > ⚠️ **The acoustic solve is now 4.8 % under target, and that is a cost, not a rounding.**
   > The baffle was solved numerically for **673.0 mm²**; the throat measures **640.8**. It was
   > +0.7 % before the rescale. On a sealed-back module with Fs ≈ 650 Hz this is inaudible —
   > the baffle aspect ratio, fixed in item 1, was worth an order of magnitude more — but it is
   > spent, not free, and if the field is ever rescaled again it should be spent knowingly.

   **They are not louvers.** Both patterns are straight-through bores; the raked slots were
   angled *in the plane* of the wall, not through its thickness, so nothing about the angle
   ever steered sound. That is precisely why the pattern was free to change.

   Hex is the better engineering answer at equal open area, for two reasons: it is the
   **optimal packing** for a given web thickness, so it reaches the target with more
   material left between holes than parallel slots do; and it is **isotropic** — a slot
   array is slightly stiffer across the bars than along them, a hex field has no preferred
   direction.

   `GRILLE_STYLE = "ridge"` restores the raked dorsal-ridge array (9 slots, 24° rake,
   3.20 → 2.50 mm taper, also 673 mm²).

3. **0.60 mm flare on the bores — and at that value the mouths deliberately merge into one
   opening.** A sharp-edged bore sheds vortices and chuffs at level; the flare opens outward
   and is self-supporting in the print orientation. It does both of those jobs merged.

   The flare grows each cell's across-flats by `2·flare·cos30°`, so **merging begins at
   `HEX_WEB/√3 = 0.5196`** against the 7.3952 mm pitch. At 0.60 the flared cells interpenetrate
   by 0.1392 mm, and **the outer 0.40 mm of the baffle is therefore a single aperture with the
   hex pattern set back behind it.** From outside you are looking at one recessed opening, not
   at 33 chamfered ones.

   **That is a choice between three options, not a dial**, because *any* flare puts the web at
   the mouth under `HEX_WEB`'s own 0.90 mm floor:

   | flare | web at the mouth | |
   |:--|:--|:--|
   | `0` | 0.900 mm | keeps the floor, loses the relief entirely |
   | `0.2598` | 0.450 mm | printable, but a 0.45 mm feature on a part whose declared floor is 0.90 |
   | **`0.60`** *(shipped)* | *merged* | **no sliver at all** — a deliberate 0.40 mm recessed mouth |

   ⚠️ **`0.45` is the trap and it was nearly taken.** It leaves **0.1206 mm** of web — a fin too
   thin to print and too thick to be a clean merge, i.e. the one option that is neither. Worse,
   it would have made the cell-count assert start *passing* while the printer still merged the
   mouth. If you are tempted to "restore the individual chamfers", that is the value you will
   reach for, and it is the wrong one.

   > **The cell-count assert cannot see any of this.** It is computed on the *un-flared* field,
   > so it counts 33 separate cells no matter what the flare does to the mouth. It is guarding
   > the wrong object — the cells that merge are the flared ones.

**At assembly:**

- **Skip the wadding.** A sealed-back module brings its own rear volume, so there is no rear
  chamber to damp — stuffing the front cavity would just absorb output on its way out.
- **Seal every joint** — the wire pass-through and the base seam. Not to hold bass in a rear
  chamber, but to stop the *front* cavity venting anywhere except through the slots. A leak
  there lets the front wave escape and cancel, which costs level.
  > ⚠️ On the currently committed stand there is no wire to seal *around*, because the lead
  > cannot get through the pass at all — see the block at the top of this page. Sealing a
  > blocked pass would be sealing the chamber shut.
- **Print the stand with more walls and infill than feels necessary** (5–6 perimeters, 30%+).
  It is a speaker cabinet; stiffness is what stops a 2 W driver exciting a 64 mm panel.

**Not done, deliberately:** a bass-reflex port. At this volume a printable port tunes to
~390–460 Hz, useful only if it lands just below the driver's Fs — unknown. A port tuned
below Fs does nothing and a mistuned one is worse than sealed.
`Fb = (c/2π)·√(A / (V·Leff))`, `Leff = L + 0.85·d`.

## Assembly order

1. Plug the speaker pigtail into the board's **SPEAKER** 1.25 mm 2P header (long edge).
2. Seat the driver in the stand, wires out through the cable channel, press on
   `ember-stand-base`, seal the seam.
   > ⚠️ **Lay the speaker lead into the rear saddle _before_ the slab goes in.** There is
   > 0.40 mm between the slab and the wall against a 1.2–2.0 mm lead, so it cannot be threaded
   > afterwards — and a pinched lead presents as **intermittent audio**, which reads as a
   > firmware fault and will be debugged as one.
3. **Free the button pads first, with the shell still on its own.** `SLOT_W = 0.60` is
   **1.50 nozzle widths at 0.4 mm**, so expect some fusing across the printed-in-place slots,
   especially at the hinge shoulders. Run a fresh craft-knife blade round each pad and check
   both hinge properly. **Do this now** — later means working next to a taped driver inside a
   part that is mostly closed.
4. Lay the board **face down into the bezel**. The glass does **not** touch the bezel —
   there is a deliberate 0.40 mm gap. The four bosses land on the PCB's top face.
5. ⛔ **THE ROCK TEST — no screws yet, and this is the one irrecoverable failure on the page.**
   Set the bezel onto the shell dry and press the centre.
   > - **It rocks on the rim** → the glass gap is intact. Proceed.
   > - **It sits dead solid while the seam is still visibly open** → it is bearing on the
   >   **glass**. **Stop.** Shim the four bosses with 0.2 mm washers, or take 0.2 mm off the
   >   boss ends. **Do not "just tighten it".**
   >
   > Worst case the gap is ≈0.15 mm and still positive, but pressure on an LCD leaves a
   > permanent bright blotch, and it is the most expensive component in the build. Five
   > seconds.
6. Drop the back shell on. Check the five 1.25 mm connectors and the microSD sit in the
   side channels before pulling anything tight.
7. Four M3 × 15 (or × 14) countersunk from the back. Snug, not hard — you are clamping a PCB.
   **Tighten in two diagonal passes**, not one screw at a time: the screws pull the bezel
   down, and going round in order tips it and loads one corner of the glass on the way.
8. ~~Press `ember-diffuser` into the ⌀16 seat around the rear glow window.~~
   **REMOVED.** There is no diffuser and no seat. The ⌀12 rear glow window and its ⌀16
   diffuser seat were both deleted when the back shell became a fine hex field: the LED's
   light now leaves through the apertures over it — 8 within r6, 23 within r10, 32 within
   r12 — plus straight through the wall if you print in white. Many small apertures in a
   translucent panel scatter; one large bore behind a printed disc just shows you the die.
9. Slide the slab into the stand slot; **plug the cable in first, from underneath** — feed it up
   the egress channel and the well, then seat the slab onto it. Route the tail **out of the
   FRONT** of the plinth at desk level and away to either side; see *The plinth* for why the
   back is not an option. **The two button caps end up inside the slot**, but the rear rim is
   now **notched down to z 43.62 across the cap span**, so you reach them from behind over an
   open rim rather than down a 12 mm pocket. If a finger does not fit, that is the fault this
   feature exists to fix and something has regressed: `_check_geometry()` drives a 6 × 4 mm
   fingertip probe at each cap and fails if the stand blocks more than 1 mm³ of it.

---

## The mobile (battery) variant

Three printed parts, one of which you may already own: the **bezel is reused bit-identical**, the
**midframe** is `back_shell("mobile")`, and the **cover** is new. The desk stand and its base are
not used — but see the reprint warning at the end of this section, because **the stand changed for
this build even though the mobile does not include it.**

### Fasteners — 2 × M3 × 0.5 × 22 ISO 4762 socket cap

Same head and counterbore family as the bezel screws, driven **down** through the cover into
bosses in the midframe.

| | |
|---|---|
| Screws | **2 × `M3 × 0.5 × 22` ISO 4762** socket cap, hex recess — 2.5 mm key |
| Positions | one lane at **x 23.55**, which is the case's own centreline: chin **y 22.60**, top **y 85.98**, **63.38 mm baseline** between them |
| Boss | ⌀**9.00** at both ends — not 7.00: at 7.00 the annulus is 0.60 against a 1.00 minimum, because `CBORE_DEPTH` 3.00 exceeds the cover's 2.20 wall, so **the head bears on the boss and not on the wall** |
| Pilot | ⌀2.50 blind, **6.60 mm** deep |
| Engagement | **3.40 mm** — it clamps, and it cannot bottom out; both asserted |

⚠️ **The under-head length trap applies here exactly as it does to the bezel screws, and it is
why this is a 22 and not something rounder.** `M3 × 22` is an **under-head** length. The head
bears at z −28.30 and the tip lands at −6.30 in a pilot whose floor is at −3.00, so the numbers
that matter are the 3.40 of thread engaged and the 3.20 of empty pilot beyond it. **Fit a longer
screw and it bottoms on the pilot floor before the head seats** — the joint then feels tight while
clamping nothing, which is the failure mode that reads as success. That is the same reason the
desk build could not simply take a deeper back shell: deepening it moves the counterbore 21.80 mm
further from its pilot and invalidates the derivation while still looking correct.

⚠️ **Two screws is the whole fastener count, and the rest of the edge is carried by the cover's
21.60 mm closed box section.** The worst unheld point on the outline is **43.19 mm, at
(52.95, 54.34)** — mid-span of the +X long edge. If the cover's top edge gaps on your print, that
figure is where to look first, and it is a stiffness result rather than a fastener one.

### Assembly order — and the first two steps are why the geometry looks like this

1. **Lay the strip body flat in its channel beside the cell lane** — x 16.15–20.65, mid-bay
   y 42.83–64.33. It goes in **before the cell**, and the cell **drops on top of it**. Nothing is
   threaded down beside a cylinder that already fills the bore.
2. **Fold both nickel tabs into leaf springs** and seat them. 34.25 mm per side gives 22.62 of run
   and 11.63 of fold — about 3.2 limbs of a Z-fold. ⚠️ **Free height 3.60 is JP-tunable**: it is the
   one number here set by feel, and it sets the preload (1.75 mm on the shortest cell in tolerance,
   0.50 off fully closed on the longest).
3. **Solder the output wires on the body's +X side**, then thread them to the chin pass. That side
   sits past the cell's surface, so **the joints are where their thickness is not a dimension** —
   which is the whole reason the body sits where it does rather than a happy accident.
4. **Tape the driver** to the midframe's back face inside its 0.60 mm locating groove. That face is
   a printed **bed face**, so there is no proud pad and the groove is an outline only: the tape does
   the work.
5. **Route the driver leads through the SPK relief, then ⛔ SEAL THE RELIEF** — silicone, hot glue or
   putty. ⚠️ **That plug is half the seal, and it is the half no model can check.** A flood fill of
   the assembled stack returns *one* interior air volume including the outside; the boundary is this
   wall **plus this manual step**, so skipping it does not degrade the seal, it removes it.
6. **Fit board and bezel** exactly as the desk build. Four M3 × 12.
7. **Drop the bare cell on top of the seated strip.** Both ends land on leaf springs; there is no
   plate to orient against, so read the debossed marks.
8. **Seat the cover and drive both M3 × 22.**

### The polarity marks, and why they do not match each other

`+` is debossed on the **high-Y end wall at y 86.95**. `−` is on the **cover's mating face at
y 19.10**. They are deliberately **not** mirror images, and the asymmetry is the point:

> ⚠️ **The `−` mark was originally cut correctly and could not be seen.** It measured **34 %
> visible** — the folded leaf sits in front of it. Nothing about that geometry was wrong; the mark
> was at the right depth in the right place, and a person loading a cell could not read it. The
> deboss check passed, because it measures **volume** and the thing that mattered was **sightline**.
> The check gained a visibility lens with the old geometry as its rejected control.

⛔ **There is no mechanical reverse-insertion protection, and there cannot be.** A bare flat-top
18650 has geometrically identical ends, so any aperture that stops a reversed cell stops a correct
one. **The marks are the only protection, and they are advisory.** Making reverse insertion *safe*
is electrical and it is not built.

### ✅ The 1.25 mm web is PROVEN now — below the 1.60 minimum, and validated on a real print

> **JP: "we have proven two that collapse and none that survives."**

> **And then one did.** JP inspected the r10 cover's through-field bores — the horizontal-bore class,
> the #47 class, the worst case — and reported: **"Clean — webs crisp."**
>
> ✅ **So the 1.25 web is validated at 4.75 mm spans, and every field on these parts is at or below
> that** (3.20 top fields, 4.00 dock). Web collapse is governed by the **span each web bridges**, and
> a shorter span is strictly easier — so the verdict covers them *a fortiori*. The exemption stands
> as a proven one rather than a trial. **What is still unproven is any future field with spans above
> 4.75.**
>
> ⚠️ **Do not generalise it further than that.** The separator wall's **0.90 and 0.50** are a
> different matter entirely — a supported vertical wall, not a web spanning a bore — and they are
> still experiments awaiting this same treatment. The 0.80 blind deboss is exempt because a surface
> relief **has no rib to lose**, which is not a strength claim at all.

The +Y cooling field and the speaker grille both use **4.75 mm across flats on a 1.25 mm web** —
the stand's own grille constants, shared **deliberately**. This is the opposite call from the glow
window, which was *pinned away* from that same pair after #47, and the difference is what each
feature is for: the window's size is set by the cavity band it lives in, so inheriting another
part's lattice was pure accident there and broke the fit. **The cooling fields have no such
constraint and exist precisely to BE the pattern under test.** If the 1.25 web survives a real
print, that answers #47 for the whole family at once; if it collapses, it collapses everywhere in
one place.

⛔ **So this web is below the 1.60 mm minimum-solid floor, and it is deliberately NOT in the
minimum-solid check's list.** That is not an oversight and **must not be "fixed" by adding it** —
the check would then fail the build on a pattern that is on trial on purpose. The build prints it
as an `[exempt]` line instead, so it is loud rather than silent. **When you print these parts, the
web is the thing to look at.**

The end-vent cells are **flat-top in Z — 60.0° shoulders** measured from horizontal. Vertex-up
would give **30.0°**, which is issue #28's droop exactly, and the build keeps that orientation as a
**rejected control**.

### ⛔ The stand needs reprinting — even though the mobile does not use it

If you dock a backpack in the desk stand, **the stand you have will not accept it.** The cover
fouls the stand's rear top edge by **121.784 mm³**, and it was *pre-existing* — the check for it
had never actually executed, and a check that has never fired is indistinguishable from one that
passes.

The cover cannot be the fix: the interference is **mid-height on its chin end face and full
width**, not a corner a bevel could take off, and its 2.20 mm wall with the leaf's 0.35 kerf behind
can yield **0.60 and no more**. So the stand takes a **13.00 × 4.40 mm relief** on its rear top
edge, sized by **bisection against the real docked stack** — 6.00 × 2.00 → 96.6, 9.00 × 3.00 →
28.8, 10.00 × 3.50 → 7.8, **13.00 × 4.40 → 0.000 mm³** — and the check is now a hard zero.

250 mm³ off a part of over 100 cm³. **The stand's slot was cut for a slab that existed before the
backpack did**, and every part since inherited that opening as though it were a fact about the
world. It was a fact about a decision.

---

## Tunables (edit + re-run)

| Parameter | Default | Change it when |
|---|---|---|
| `FIT` | 0.35 | board is tight/loose in the pocket |
| `HINGE_L_BOOT` / `HINGE_L_RESET` | 1.20 / 2.00 | **buttons feel stiff → lengthen these, do not thin the hinge and above all do not thicken it.** This is the knob, and it was not obvious. |
| `HINGE_T` | 0.90 | ⚠️ **Read the strain note below before touching this.** Thicker is not stiffer-but-safer, it is *closer to fracture* — strain scales with `t`. |
| `GLASS_GAP` | 0.40 | never reduce below 0.25 — see below |
| `SLOT_CLR` | 0.40 | slab loose/tight in the stand |
| `TILT` | 15° | viewing angle |
| `GRILLE_STYLE` | `"hex"` | `"ridge"` swaps the 59-hex field for lyra's raked dorsal-spine motif. Both were solved to the same **673 mm²** nominal open area; the hex field's throat now measures **640.8 mm² (−4.8 %)** after the AF 4.50 rescale. Aesthetic, not acoustic — the rake never did acoustic work, since these are straight-through bores raked *in the plane* of the wall, not louvered vanes angled through its thickness |
| `HEX_R` / `HEX_WEB` | 2.598 / 0.90 | across-flats **4.50** (= `√3·HEX_R`), pitch 5.40. ⚠️ **`HEX_WEB` is a print floor and does not scale with the cells** — shrinking the hexes spends open area, it does not save it |
| `GRILLE_FLARE` | 0.25 | outward taper at the mouth. **0.25 keeps the mouth webs (0.467 mm) so the honeycomb reads as one; ≥ 0.5196 merges the whole field into a single opening.** `GRILLE_MOUTH_WEB` permits either and forbids the fin in between |
| `SCALLOP_D` / `SCALLOP_Z0` | 12.0 / 5.0 | the finger pockets over the button caps. Since the #31 rim notch these only govern the part of the scoop that dips *below* the notch floor — extra depth under the cap. Deeper reaches further behind the slab and eats the stand's rear wall; there is an assert holding 3 mm of wall |
| `STAND_TOTAL_H` | **56.0** | the whole stand. `PLINTH_H` derives as `56.0 − ST_H`, so the two cannot drift. The derived floor is **54.97**, so there is 1.03 mm of headroom for build tolerance and cable-OD uncertainty |
| `CABLE_RIGID` | 40.0 | JP's measurement: plug tip → first bend. Drives `STAND_TOTAL_H`. If a different cable is used, re-measure **this**, not the height |
| `CABLE_OD` | 4.5 | ⚠️ **assumed, not measured.** It buys the cable's *centreline* `OD/2` of clearance over the desk, so the sensitivity is exactly half: every mm of OD is 0.5 mm of stand height |
| `EGRESS_W` / `EGRESS_H` | 14.0 / 10.0 | the cable channel at desk level. `EGRESS_H` also sets how deep the tail corridor runs, and the corridor drifts *forward* toward the chamber shaft as it descends — there is an overlap-or-clear assert on the wall between them |
| `TAIL_W` / `TAIL_Y` | 18.0 / 8.0 | the corridor from the well down into the plinth. **`TAIL_Y` is the constrained one**: at 10.0 it leaves a 0.95 mm fin against the chamber shaft |
| `BEZEL_DEBOSS` | 0.80 | how deep the honeycomb and wyrm cut into the front face. **Keep it an exact multiple of the bezel's 0.16 mm layer height** — it was 0.45, which is 2.8125 layers, so the recess floor landed wherever the slicer's rounding fell rather than on a real layer boundary. **0.80 is 5 layers exactly.** It was 0.48 (3 layers) through the first print, and JP's verdict on that part was that none of the three regions read at arm's length — #34 raised the depth only, sizes untouched. An assert holds ≥2.00 mm of bezel over the glass; at 0.80 the measured floor is **2.20 mm**, so 6 layers (0.96 → 2.04) is the last one that would fit and there is no room to keep going. The shell runs `DEBOSS_BIG` at this same 0.80 on a thinner wall |
| `BTN_R_BIG / BTN_R_SMALL` | 8.6603 / 5.7735 | the hex caps — **15.00 and 10.00 mm across the flats.** Shrinking them moves the hinge closer to the pip, which raises θ and therefore strain; the thumb-sized caps are what took both hinges to ~1.20% |

---

## The connector labels — and the one thing worth checking by eye

Nine debossed labels now: `SD`, `MIC`, `VOL`, the power symbol, and the five connectors —
`UART`, `I2C`, `SPK`, `BAT`, `IO` (issue #27). Each connector label sits in the 9 mm margin
strip **beside the side channel it names**, rotated to read bottom-to-top like `SD`.

| label | board edge | port centre Y | silkscreen it matches |
|---|---|--:|---|
| `BAT` | **X = 0** (microSD side) | 23.20 | `BAT`, 2-pin, marked `− +` |
| `UART` | X = 0 | 34.98 | `UART`, 4-pin `RXD TXD GND 5V` |
| `SPK` | **X = 50** (mic side) | 36.36 | `SPEAKER`, 2-pin — ⚠️ **top-entry**, see below |
| `I2C` | X = 50 | 49.92 | `I2C`, `3.3V GND IO15(SCL) IO16(SDA)` |
| `IO` | X = 50 | 67.77 | `IO2 IO3 IO1x IO21` |

> ⚠️ **JP: this is the one thing in the part that no check can prove, so please glance at it.**
> `CONN_R` and `CONN_L` are anonymous Y-spans lifted out of the vendor STEP — the model has
> never known which connector is the battery and which is the UART. The names come from the
> **ES3C28P outline drawing's silkscreen**, and the order along each edge is pinned by that
> drawing's own dimension chains, which the build asserts against the STEP: they close to
> **0.02 mm** forward and miss completely when read from the other end, so the direction is
> established rather than assumed. The microSD closes the same chain to 0.06 mm, which is what
> ties the drawing's edge to this model's low-X edge.
>
> That is strong evidence and it is still not a bench test. **Hold the bare board next to the
> printed shell and check one label against the silkscreen** — `BAT` is the easiest, it is the
> one with the `− +` polarity marks. If `BAT` is right, the chain is right and so are the other
> four. This is the same discipline that caught BOOT and RESET being swapped: a physical
> observation anchored to a coordinate beats any amount of re-derivation from a drawing.
>
> ✅ **And one bench observation has already corroborated it.** JP reported (#33) that *the
> speaker plug is top-entry, unlike the side-entry connectors*. Measured out of the STEP,
> **exactly one connector is different** — `CONN_R[0]` is 4.70 mm tall where the other four are
> 3.40, and it is the only one reaching the board's own minimum Z. It is the one the drawing's
> chain names `SPEAKER`. A hands-on observation and a documentary one landing on the same solid
> is two witnesses of different kinds; the build asserts they keep agreeing.

### The speaker plug is top-entry — that is why there is a hole above it (#33)

Its plug and wires leave the board **into the shell**, not sideways, and there was only
**0.80 mm** of headroom above it (every other connector has 2.10). So the back slab is opened
over it: **x 44.54–50.35, y 31.79–40.94, straight through.**

> **A through-opening rather than a blind pocket, and the reason is a bound rather than a
> measurement.** Nobody has the plug's height — it is your speaker's own pigtail and it is not
> in the vendor model. A blind pocket leaving a printable floor caps headroom at **3.00 mm**; a
> 2-pin 1.25 mm plug protrudes ~1.5–2.5 mm past its header and the wires then have to turn.
> "Probably enough" fails an acceptance test that reads *the shell closes fully*. A
> through-opening cannot be too shallow.
>
> ⚠️ It reaches the **cavity** wall on purpose. The connector fills the cavity to within
> 0.80 mm, so the lead cannot pass over the top of it — a 1 mm wire in a 0.80 mm gap is the
> pinched-lead hazard the stand's wire saddle exists to prevent. Taking the opening out to
> x 50.35 lets the lead get outboard of the connector, rise into the cavity, and leave through
> the side channel that already serves this port.

**`SPK` is therefore the one label not level with its port** — its ink sits immediately *below*
the opening rather than on top of it. A label beside a visible hole points harder than a label
over an invisible connector.

**Some labels are not centred on their port, and that is deliberate.** `BAT` and `UART` are only
11.78 mm apart while their ink is 13.28 and 18.04 mm long, so centring both is arithmetically
impossible. They are packed apart **in port order** instead, and the build asserts that each
label's ink still **spans its own port's centreline** — which is what a reader actually does,
look across from the connector and read whatever is level with it — and that no label's ink
reaches into a *different* connector's channel. Order is preserved by construction.

> ⚠️ **They are also spaced by a word gap, not a keepout, and that distinction was found by
> slicing the finished mesh rather than by any check.** The first cut printed `SPKI2C` and
> `BATUARTSD`: every assert passed, but the gap *between* two labels (`LABEL_MARGIN`, 0.80 mm)
> was **smaller than the gap between two letters of one word** (1.00 mm), so the eye read each
> column as a single string. `LABEL_WORD_GAP` is now 2.00 mm — twice the letter space — and it
> is derived from the number it has to beat. If you are reading the printed part and the labels
> still run together, that is the defect to report.

---

## Why some numbers are what they are

- **The glass gap survives printer Z error structurally, not by tolerance stacking — and that
  is a design property somebody could destroy.** The bezel's underside is located by the
  **shell's wall top**, and the board by the **shell's standoffs**. Both are printed in the same
  part, on the same Z axis, from the same bed, so a global Z error scales them *together* and
  the gap is preserved. The stack is exactly consistent — standoff 5.50 + PCB 1.60 + bezel boss
  4.70 = **11.80**, and the shell's `CAV_FLOOR → SEAM_Z` is **11.80** — and the shell's 14.40 mm
  height is **72 layers exactly** at 0.20 mm, so there is no quantisation error either.
  > ⚠️ **Take that 72 from the constants, not from the mesh.** Binary STL stores float32 and
  > 14.4 is not representable, so measuring the exported part gives 14.399999… and
  > **71.999998 layers**. That is storage precision, not a geometry change — but it is exactly
  > the kind of number that makes someone think a datum moved.
  ⚠️ **Move either datum onto the bezel and that cancellation is gone**, and the gap starts
  stacking two parts' errors instead of one part's. What is left is the LCD/TP tolerance
  (−0.20 worst case) and first-layer squish (~−0.05): realistic worst case ≈ **0.15 mm**, still
  positive. Thin, but positive — which is why step 5's rock test exists rather than a caliper.
- **The board pocket starts at printed z 2.60 — 13.00 layers exactly — and that is deliberate.**
  The shell prints back face down, so the pocket floor sits 2.60 mm above the bed and
  **elephant foot lands in the 13 solid layers below it, not in the pocket.** That is the classic printed-pocket failure, *tight at the bottom
  only*, designed out. ⚠️ If you are tempted to extend the pocket down to the bed to save
  material, that is what you would be undoing.
- **`GLASS_GAP = 0.40` — the bezel never touches the capacitive glass.** The vendor tolerances
  the LCD at 2.3 ±0.1 and the touch panel at 1.0 ±0.1, so the glass front face can sit up to
  0.2 mm high. A rigid printed bezel bearing on glass is how you crack a display. The entire
  clamping load runs bezel → bosses → PCB → standoffs → shell; the glass is never in the load
  path. This was a bug in the first iteration, caught before export.
- **Button pads extend in +Y only.** The switches sit just 3.26 mm from the board edge, so a
  centred pad cut straight through the shell's bottom wall. Caught by rendering and looking.
- **The caps are debossed, not raised.** They were raised first, which is the obvious reading
  of "buttons you can feel" and is incompatible with this part's own print orientation: a
  proud cap on a bed face is the *lowest* feature, so the shell would balance on two
  hexagons with the whole back face 1.2 mm in the air. The bbox growing by exactly the cap
  height is what exposed it. Recessing costs nothing, prints unsupported, and means nothing
  resting on the case can hold BOOT low across a reset.
- **The bezel face is debossed too, and for the same reason on the opposite face.** 57
  honeycomb cells across the chin, a 16-cell chain up each rail (2.60 mm across the flats on a
  0.70 mm web), and the hearth-wyrm **25.65 × 11.25 mm** in the brow — all **0.80 mm** deep,
  which is exactly five layers at this part's 0.16 mm (it was three, and #34 found that too
  shallow to read on the printed part; the sizes above are unchanged). This part
  prints front face down, so a raised logo would be the lowest feature and the bezel would land
  on it. **On a bed face, relief only goes inward** — that it bit both shell parts in the same
  session, on opposite faces, is the tell that it is a property of the process, not a mistake.
  The wyrm's *size* is set by the print floor rather than the space available: the generator
  **declares** a minimum feature of 1.2333 mm at unit scale, the mark is scaled by
  `0.90 / 1.2333`, and scaling it any larger — to fill the brow — would take the thinnest part
  of the creature under the 0.90 mm floor.
  > ⚠️ **That 0.90 mm is placed there by arithmetic, not confirmed by measurement.** The build
  > prints the mark's min feature as `WYRM_MIN_FEATURE × scale`, and the scale is *defined* as
  > `0.90 / WYRM_MIN_FEATURE` — so the figure is 0.900 for any value of the constant, and the
  > assert that checks it is ≥ 0.90 is comparing a number with itself. It is sound while the
  > declared constant is a true lower bound on the shape, and **blind in exactly the direction
  > that would hurt**: if the constant were larger than the creature's real thinnest feature,
  > the mark would be scaled too big, the true minimum would land under the floor, and the
  > build would still report 0.900 and pass. If you are checking a printed bezel, check the
  > *creature*, not this number.
  **The mark is mirrored, and its placement is a centring rather than a margin.** The creature
  is drawn facing left, so unmirrored its *tail* pointed at the mic port and the gesture ran off
  the face. Mirrored, the head faces the flare. Ink runs x 7.700–33.351 and the flare's right
  edge is at 42.300, which puts the creature-and-port group dead on **x 25.000 — the face
  centreline** — and that is asserted, because every other check on this face is a clearance and
  a clearance is satisfied by any amount of slack in the wrong place. The cost, on the record:
  this is the one of the wyrm's four renderings that is handed the other way, and it is **not**
  at top-left.
- **Two of those cells used to sit on a screw boss, and it mattered for printing.** Nine chin
  cells per boss overlapped the fastener — four over the 2.50 mm pilot, five over the 5.40 mm
  pad — thinning the bezel roof over a self-tapper from 1.50 mm to **1.05 mm**. It was never a
  hole, which is why nothing flagged it. If you are checking a printed bezel against this
  sheet: the chin honeycomb should stop cleanly short of all four boss positions.
- **The hinges are sized by strain, not by feel — and the intuitive fix cracks them.** Bending
  strain in a flexure is `(t/2)·θ/L`, and **θ is not a free variable**: it is pip travel over
  the pip's distance from the hinge. The *smaller* cap therefore bends *further*, because its
  pip sits on a shorter arm. At 9.01 mm caps and a shared 1.00 mm flexure that put RESET at
  **4.37%**, past PLA's ~2% yield and into its 4–6% break band. The natural remedy, thickening
  RESET's hinge so it presses firmer, takes it to **6.79%**: strain scales *with* thickness, so
  the obvious fix points the wrong way. Lengthening the flexure works — and so, it turned out,
  does **making the caps bigger**, which was asked for on looks: a wider hex puts the hinge
  further from the pip, so θ falls with it. Shipped at 15.00 / 10.00 mm across the flats:
  **BOOT 1.20% (θ 1.83°, L = 1.20) and RESET 1.19% (θ 3.04°, L = 2.00)**, against an assert
  that was tightened from 2.5% to **2.0%** at the same time — the old threshold was calibrated
  to what 9 mm caps could achieve rather than to what the material wants, and an assert
  inherited from a worse version of the part is a ratchet pointing the wrong way. The force
  ordering stays mildly inverted and that is the accepted trade — an easy RESET is an
  annoyance, a cracked RESET hinge is a dead part, and findability is already carried by cap
  size and deboss depth, which cost no strain at all.
  > **Every other check in this file would have passed all three variants happily.** The
  > geometry is valid, nothing collides, the pad stays attached, the solid is watertight, it
  > prints. It just breaks in your hand after a few dozen presses. Every assert here was about
  > *shape*; this is a property of the *material*. Worth asking of any parts library: which of
  > your invariants are about form, which are about matter, and is the second list empty?
- **⚠️ Superseded in part by #31: the rear rim is now notched, not just scooped.** Everything
  below is still the correct diagnosis — the obstruction is *lateral* and a taller cap cannot
  reach past it — but the scoop only ever removed 12 mm of the wall's depth, leaving a pocket a
  finger had to descend into blind. The fix is **rim height**, and the relation is exact:
  `H_rear = SLOT_FLOOR + (PAD_Y0 − OY0)·cos(TILT)`, cutting the wall right through across the
  cap span (stand x 13.20–50.23) down to **z 43.62 in the STL** (27.62 in the source frame —
  see *The plinth*). `PAD_Y0` **is** both caps' bottom edge for any cap radius, because they are
  flat-top hexagons centred at `PAD_Y0 + R√3/2`, so a cap resize carries the notch with it.
  **It removes approach, not retention:** the slot's two x-extremes keep the full 16.56 mm of
  engagement over 19.67 mm of full-height rim, which is what still contains the lean. Lowering
  the *whole* wall to the same height would leave 3.75 mm everywhere and let the slab flop back
  ~6°. The scoop survives underneath the notch, adding depth below the cap.
- **The stand has finger scallops, and a taller cap would not have worked.** Docked, the stand
  swallows the first 16.56 mm of the slab. At the old 9.01 mm caps that put BOOT's cap 3.81 mm
  *below* the rim and RESET's 6.23 — with 0.40 mm between the cap face and a solid wall. The
  thumb-sized caps changed the arithmetic but not the conclusion: BOOT's top edge now stands
  **2.19 mm proud of the rim**, while **RESET is still 2.81 mm under it**, so the scallops are
  still what makes both buttons pressable while docked. A finger does not fit in
  0.40 mm, so **the obstruction is beside the cap, not above it**, and no amount of cap height
  reaches past material that is alongside it. A scallop rather than a through-window because
  the rear wall is ~19 mm thick there — a window would be a tunnel, not an access port. And a
  bottom-hinged lever with a thumb tab, which is the other obvious fix, is unbuildable here:
  the hinge angle is fixed at 0.40/2.46 = 9.3° by pip travel and does not improve with a longer
  lever, and holding PLA through 9.3° needs ~4 mm of thinned flexure where there are 2.46 mm.
- **Side channels are deliberately generous.** See the open question below.
- **Shrinkage:** PLA ≈0.3 % over 86 mm = 0.13 mm/side, PETG ≈0.5 % = 0.22 mm/side — both
  inside the 0.35 mm pocket fit, so **no scaling compensation is needed**.

---

## One thing to check on the physical board

> ### ✅ The mic question is ANSWERED — do not go looking.
>
> **JP inspected the board: the microphone fires FORWARD, through the front face, and the
> hole is visible in the product photos.** The bezel's ⌀2.40 mm port and its acoustic collar
> are the working path. The ⌀3.00 mm relief through the back shell is redundant — it stays
> because it costs nothing and this board is resold under several brands, so a variant with
> a rear-firing mic is plausible.
>
> Recording *why* it needed a human, because it is the most reusable thing on this page: the
> vendor STEP contains **no small holes at all — not a single via**, because the CAD export
> suppressed them. The absence of a port in the model was never evidence there wasn't one.
> **A model's silence is not an answer.** Five seconds of looking settled what a 17 MB solid
> could not.
>
> ⚠️ This section has now been corrected **twice**. The first fix was overwritten by copying
> a stale working copy over the repo — the same stale-copy failure this project has logged
> six times. If you are editing this file, edit it *here* and copy outward, never inward.

**2. Where does the microSD card actually go in?** The STEP simplifies the socket to a flat
11.15 × 14.15 × 0.5 mm plate at x 33.68–44.83, y 15.84–29.99, which doesn't resolve the
insertion direction. That's why both long edges get a continuous channel across y 14–75 and
y 14–42 rather than a neat per-connector cutout. If the card turns out to be blocked, the fix
is one parameter, not a redesign.

---

## What this sheet cannot tell you

Named explicitly, because **a checklist that implies it covered everything is worse than one
that marks its own edges.** None of these is measurable from the geometry, and no amount of
re-checking the model will settle them:

1. **Whether the printed-in-place button slots opened.** 1.50 nozzle widths is above the point
   where a slicer refuses and below the point where it is safe. See step 3.
2. **Your actual printed pilot diameter.** Modelled 2.50 and printed holes come out 0.1–0.3 mm
   undersize, which lands it mid-band for thread-forming — **measure one boss before you drive
   four screws.**
3. **Thread quality in your PLA at your temperatures** — brittle when cold, gummy when hot.
4. **Your module's real LCD + touch-panel stack height.** This is the entire glass-gap risk, and
   it is why step 5 is a feel test rather than a number.
5. **Whether the driver's own pigtail reaches the wire pass.** A property of the module, not of
   the case.
6. **Whether the seal actually seals.** A leaky "sealed" box costs exactly the low end the
   chamber exists to produce, and an audible A/B sealed-vs-unsealed is the only test.
7. **The well/channel junction (fixed in r3, was a real defect in r2).** r2 printed a thin
   membrane straight across the USB-C bore where the egress channel's roof passed it — JP had
   to carve it out before the plug would pass. The corridor now runs `(TAIL_Y/2)*tan(TILT)`
   past the channel ceiling so the two voids merge and no roof plane crosses the bore. Verified
   by sectioning: material inside the bore footprint used to spike to 85.1 mm² at the roof
   plane with void beneath it, and is now monotonic into the junction. **Leave bridging on** —
   the channel's own 6.0 mm roof span is unchanged and still bridges.
8. **Acoustics.** The throat is 607.8 mm² against the driver's ~700 mm² — 86.8 % on paper,
   and 9.7 % under the 673 mm² the baffle was solved for (#47 spent 4.9 of those points on a
   printable web, deliberately). The finer lattice spends open area
   on webs that do not scale with the cells; whether that is audible is not predictable from
   area, and it is the one number here most worth trusting your ears over.
9. **Your USB-C cable's overmould.** The well is generous — 22 × 12 mm, 20.7 mm along the tilt —
   but plugs vary more than the spec suggests.
10. **Cosmetics of the grille mouth.** 37 discrete flared holes across a 38 × 25 mm field.
   Earlier print sheets promised *one* merged aperture with the honeycomb behind it — that was
   true at the old 0.60 mm flare, and is not true at the current 0.25 mm (mouth web 0.4670 mm,
   positive, so the cells stand apart). You are getting a honeycomb face, not a single slot.

The one that has moved from this list to fact: **the bezel's 3 non-manifold edges did not
matter** — it printed, and the dimensions are good.

---
## Provenance

Everything structural was **measured from the vendor STEP solid**
(`ES3C28P_3D.step`, Altium→OpenCASCADE, 2025-06-10) — not transcribed from a datasheet
table: PCB outline, the 4 ⌀3.20 holes at (4,4)/(46,4)/(4,82)/(46,82), the 10.60 mm stack,
glass face at Z+4.30, deepest back component at −6.30, USB-C at X 20.53–29.47, both rear
switches and their plunger tips, the mic package at (40.0, 81.5), the WS2812 at (29.0, 45.6),
all five 1.25 mm connectors, and the antenna keepout.

Both shell parts are boolean-verified against that solid at **0.000 mm³ interference**, and
the checker is self-tested each run by deliberately sinking the bezel 2 mm into the board
(reports 1467.8 mm³ — so a real collision would not pass silently).
