# Ember satellite case — print sheet

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
| `ember-front-bezel.stl` | 1 | **front face DOWN** on the bed | **none** | The visible face is the bed face — use a smooth PEI sheet. Mic flare + window are bed-side chamfers, so they self-support. **The debossed honeycomb and the wyrm mark are bed-side recesses**, 0.48 mm deep — exactly three layers at this part's 0.16 mm — and print as bridged voids, which is *why* they are recesses: on a bed face, relief only goes inward. |
| `ember-back-shell.stl` | 1 | **back face DOWN**, open side up | **none** | Hexagonal button pads + living hinges print in the first ~8 layers; the pips point up into the cavity. Countersinks widen downward onto the bed. **The debossed cap faces are bed-side recesses** — a few layers bridge over each, no supports. |
| `ember-stand.stl` | 1 | **bottom face DOWN** | **none** | Chamber ceiling is a **17 mm bridge** and the cable channel a **16 mm bridge** — leave bridging on (slicer default) and they're fine. The **finger scoop** in the rear slot wall opens *upward*, so every wall is near-vertical and the pocket floor is solid: no bridge at all. (It is **one** opening, x 13.94–50.51, not two: `SCALLOP_MIN_RIB` merges them because the current caps would leave a 0.51 mm rib between, which is a fin rather than a wall. Measured as one span in the mesh.) The **wire saddle** merges into its right-hand end for the same reason — that is deliberate, and it is what keeps the rear bearing rim in two clean segments totalling 15.64 mm instead of leaving a 0.85 mm fin. |
| `ember-stand-base.stl` | 1 | flat | none | Closes the speaker chamber. Press fit. ⚠️ **Resized in `89001ea` — reprint if you made one earlier.** |

Outer sizes: slab (bezel + shell assembled) **55.9 × 91.9 × 17.4 mm**; stand **64 × 64 × 40 mm**.
Material use ≈ **121 cm³** total (~150 g in PLA), measured from the current STLs by
signed-tetrahedron volume — not an estimate. Per part: stand 93.1, back shell 17.6, bezel
7.5, base **2.8** cm³. The stand is three quarters of the print because it is a speaker cabinet,
and cabinets want mass.

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

---

## Fasteners

**4 × M3 × 15 mm countersunk (flat-head) self-tapping** — ×14 also works — driven **from the
back**, so no screw heads appear on the front face.

Load path: screw head countersunk in the back shell → 5.5 mm standoff → through the PCB's
⌀3.20 hole → **self-taps into a blind ⌀2.50 pilot in the bezel boss**.

**Buy ×15 if you are buying. ×14 works. ⛔ ×16 bottoms out.** The pilot ends at z 6.20 and
each screw's tip sits at `BACK_Z + length`:

| screw | tip reaches | engagement | |
|---|---|---|---|
| M3 × 12 | z +2.30 | 2.30 mm = 0.77 D | too short |
| M3 × 14 | z +4.30 | 4.30 mm = **1.43 D** | works — what this sheet has always said |
| **M3 × 15** | z +5.30 | 5.30 mm = **1.77 D** | **best**, and still 0.90 mm clear of the pilot end |
| M3 × 16 | z +6.30 | — | ⛔ **bottoms out** |

⚠️ **The usual "2 × diameter of engagement" is not reachable in this geometry at all** — there
is only 6.20 mm of pilot, so 6.0 mm is the whole hole. ×14 at 1.43 D is *adequate* rather than
wrong: you are clamping a 12 g PCB, not resisting a working load.

⛔ **And the natural instinct — a longer screw is safer — is exactly backwards here.** At ×16
the tip hits the bottom of the blind pilot before the head reaches its seat, so it **feels
tight while clamping nothing**. That failure reads as "tightened fine" and leaves a loose
bezel, which is the worst way for it to present.

- ⚠️ **The countersink is cut for a specific head, and the sheet now says which.** ⌀**6.40 mm
  at 90°** — `CSK_HEAD_D` / `CSK_HEAD_ANGLE` in the source, with the depth asserted against
  them rather than typed. Read off the landed constants:

  | your screw | what happens |
  |---|---|
  | **⌀6.40 head** | **flush, full conical seat** — the design point |
  | **DIN 965 M3** (⌀6.0 max) | sinks 0.20 mm below flush, bearing on its **rim** rather than the cone. Fine; slightly recessed |
  | **ISO 10642** socket countersunk (⌀6.72) | ⛔ **sits proud by 0.16 mm** |

  **Proud is worse than sunk**: it stops the shell sitting flat and stops the screw clamping.
  Same thread, same length, wrong head — and the packet often just says "M3 countersunk".
  If ISO 10642 is what you have, the countersink wants **6.72 / 1.71** instead; that is a
  named alternative, not a caveat.

  > **Two 90° surfaces have parallel flanks**, so a head narrower than the mouth does not seat
  > *deeper into the cone* — it descends until its **rim** touches the wall, at
  > `(mouth − head) / 2`, and contacts along a line instead of over the whole seat. That is why
  > the mouth is matched to a named head rather than opened up "to be safe": widening it
  > corrects the angle and makes the seat **worse**.
  >
  > What limits the mouth is **the outer r6.45 corner arc**, not the vendor's ⌀5.60 pad. From
  > the hole centre it is 5.743 mm to the outer surface, so a 6.40 mouth leaves **2.543 mm** of
  > wall and 6.70 would leave 2.393. *(The ⌀5.60 pad is a real constraint — on `BOSS_D`, two
  > bullets down, because the boss **bears** on the pad. The countersink is cut into the outer
  > face 2.60 mm of wall away and never reaches the cavity, let alone the pad.)*

- **Snug, not hard.** With a matched ⌀6.40 head this is now ordinary care in PLA rather than a
  design flaw — the head lands on a **full conical seat**. But a DIN 965 ⌀6.00 head still bears
  on its **rim**, a line contact, so the load is concentrated: over-torque there pulls the head
  into the back face and craters it. It will not fail at *snug*.
- 1.5 mm of solid skin remains under the bezel's front face at ×14.
- **Heat-set inserts will NOT fit.** The vendor specifies a ⌀5.60 pad around each mounting
  hole, so bosses are capped at ⌀5.40. An M3 insert needs a ⌀4.0–4.2 bore, leaving a 0.6 mm
  wall that will split. Self-tappers only.
- The boss OD (5.40) is inside the ⌀5.60 pad, so nothing bridges the annular ring. No
  washers needed — but if you substitute a metal-headed screw with a wide flange, add a
  nylon washer.

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
slab's own axis** and running 30 mm down it into the rear cable route.

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
  `GRILLE_INSET` (1.5 mm) keeps the slots inside the radiating area so the grille never
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
2. **The grille is a hexagonal honeycomb** — 33 cells placed, **27 open apertures** after the
   field's rounded corners clip them, **6.50 mm across the flats** on a
   7.40 mm pitch (3.75 mm circumradius), 0.90 mm web. Open area **673.0 mm²** nominal, solved
   *numerically* to match the slot array it replaces exactly, so the change is aesthetic
   rather than acoustic.

   > ✅ **Re-derived on the flared geometry.** That 673.0 mm² described the *un-flared* field,
   > and the mouth is not un-flared — see item 3. Rastered in the X–Z plane at 0.01 mm, which
   > *is* the aperture plane because the bores run in Y:
   >
   > | | area | openings |
   > |:--|--:|--:|
   > | **Throat** — un-flared cells ∩ field, the acoustic restriction | **678.0 mm²** | **27** |
   > | **Mouth** — flared cells ∩ field, the face you touch | **886.1 mm²** | **1** |
   > | the field itself (37 × 24, r1.5) | 886.1 mm² | — |
   >
   > **The throat figure holds: 678.0 against the stated 673.0, +0.7 %**, so the acoustic solve
   > survives and the driver's ~700 mm² radiating area is 97 % matched. **The mouth is the
   > entire field** — 886.1 of 886.1 mm², one aperture, because the flared cells cover the
   > rounded rect completely. From outside this is not 33 chamfered holes; it is one 37 × 24
   > opening with the honeycomb set 0.40 mm behind it.
   >
   > And **33 cells produce 27 openings**, not 33 — six are clipped by the field's rounded
   > corners. `len(_cells.solids()) >= 30` counts the *cutting tools*, not the holes in the
   > part: right for the question it asks (have the cells fused?) and not a count of apertures.
   > Smallest surviving opening 12.85 mm², so no clipped slivers.

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
9. Slide the slab into the stand slot; route the USB-C cable down the channel and out the back.
   **The two button caps end up inside the slot**, well below the stand's rim — reach them
   through the **finger scallops** in the rear wall, coming down the back of the slab from
   above. If a finger does not fit, that is the fault this feature exists to fix and something
   has regressed: `_check_geometry()` drives a 6 × 4 mm fingertip probe at each cap and fails
   if the stand blocks more than 1 mm³ of it.

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
| `GRILLE_STYLE` | `"hex"` | `"ridge"` swaps the 33-hex field for lyra's raked dorsal-spine motif. **Both are solved to the same 673 mm² nominal open area** (the hex field's throat measures 678.0 mm², +0.7 %), so this is aesthetic, not acoustic — the rake never did acoustic work, since these are straight-through bores raked *in the plane* of the wall, not louvered vanes angled through its thickness |
| `SCALLOP_D` / `SCALLOP_Z0` | 12.0 / 5.0 | the finger pockets over the button caps. Deeper reaches further behind the slab and eats the stand's rear wall — there is an assert holding 3 mm of wall at the rim. Raising `SCALLOP_Z0` keeps more of the lower rear grip and gives the finger less room |
| `BEZEL_DEBOSS` | 0.48 | how deep the honeycomb and wyrm cut into the front face. **Keep it an exact multiple of the bezel's 0.16 mm layer height** — it was 0.45, which is 2.8125 layers, so the recess floor landed wherever the slicer's rounding fell rather than on a real layer boundary. An assert holds ≥2.00 mm of bezel over the glass, so there is headroom, but this is the face you look at |
| `BTN_R_BIG / BTN_R_SMALL` | 8.6603 / 5.7735 | the hex caps — **15.00 and 10.00 mm across the flats.** Shrinking them moves the hinge closer to the pip, which raises θ and therefore strain; the thumb-sized caps are what took both hinges to ~1.20% |

---

## Why some numbers are what they are

- **The glass gap survives printer Z error structurally, not by tolerance stacking — and that
  is a design property somebody could destroy.** The bezel's underside is located by the
  **shell's wall top**, and the board by the **shell's standoffs**. Both are printed in the same
  part, on the same Z axis, from the same bed, so a global Z error scales them *together* and
  the gap is preserved. The stack is exactly consistent — standoff 5.50 + PCB 1.60 + bezel boss
  4.70 = **11.80**, and the shell's `CAV_FLOOR → SEAM_Z` is **11.80** — and the shell's 14.40 mm
  height is **72 layers exactly** at 0.20 mm, so there is no quantisation error either.
  ⚠️ **Move either datum onto the bezel and that cancellation is gone**, and the gap starts
  stacking two parts' errors instead of one part's. What is left is the LCD/TP tolerance
  (−0.20 worst case) and first-layer squish (~−0.05): realistic worst case ≈ **0.15 mm**, still
  positive. Thin, but positive — which is why step 5's rock test exists rather than a caliper.
- **The board pocket starts at printed z 2.60, and that is deliberate.** The shell prints back
  face down, so the pocket floor sits 2.60 mm above the bed — **elephant foot lands in solid
  wall, not in the pocket.** That is the classic printed-pocket failure, *tight at the bottom
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
  0.70 mm web), and the hearth-wyrm **25.65 × 11.25 mm** in the brow — all **0.48 mm** deep,
  which is exactly three layers at this part's 0.16 mm. This part
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
7. **Acoustics.** The throat is 678.0 mm² against the driver's ~700 mm² — 97 % on paper.
   Whether the merged 0.40 mm mouth chuffs at level is not predictable from area.
8. **Your USB-C cable's overmould.** The well is generous — 22 × 12 mm, 20.7 mm along the tilt —
   but plugs vary more than the spec suggests.
9. **Cosmetics of the grille mouth.** From outside it is *one* 37 × 24 mm aperture with the
   honeycomb 0.40 mm behind it, not 33 chamfered holes. Deliberate, and possibly not what you
   pictured.

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
