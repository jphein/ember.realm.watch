# Ember satellite case — print sheet

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
| `ember-front-bezel.stl` | 1 | **front face DOWN** on the bed | **none** | The visible face is the bed face — use a smooth PEI sheet. Mic flare + window are bed-side chamfers, so they self-support. **The debossed honeycomb and the wyrm mark are bed-side recesses**, 0.45 mm deep, and print as bridged voids — which is *why* they are recesses: on a bed face, relief only goes inward. |
| `ember-back-shell.stl` | 1 | **back face DOWN**, open side up | **none** | Hexagonal button pads + living hinges print in the first ~8 layers; the pips point up into the cavity. Countersinks widen downward onto the bed. **The debossed cap faces are bed-side recesses** — a few layers bridge over each, no supports. |
| `ember-stand.stl` | 1 | **bottom face DOWN** | **none** | Chamber ceiling is a **17 mm bridge** and the cable channel a **16 mm bridge** — leave bridging on (slicer default) and they're fine. The two **finger scallops** in the rear slot wall open *upward*, so every wall is near-vertical and the pocket floor is solid: no bridge at all. |
| `ember-stand-base.stl` | 1 | flat | none | Closes the speaker chamber. Press fit. |

Outer sizes: slab (bezel + shell assembled) **55.9 × 91.9 × 17.4 mm**; stand **64 × 64 × 40 mm**.
Material use ≈ **124 cm³** total (~154 g in PLA), measured from the current STLs by
signed-tetrahedron volume — not an estimate. Per part: stand 95.9, back shell 17.5, bezel
7.5, base 3.2 cm³. The stand is three quarters of the print because it is a speaker cabinet,
and cabinets want mass.

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

**4 × M3 × 14 mm countersunk (flat-head) self-tapping**, driven **from the back**, so no
screw heads appear on the front face.

Load path: screw head countersunk in the back shell → 5.5 mm standoff → through the PCB's
⌀3.20 hole → **self-taps into a blind ⌀2.50 pilot in the bezel boss**.

- 14 mm is right: the tip lands 4.3 mm into the bezel boss with 1.9 mm of pilot spare, and
  1.5 mm of solid skin remains under the front face. **16 mm bottoms out — don't.**
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
2. **The grille is a hexagonal honeycomb** — 33 hexes, **6.50 mm across the flats** on a
   7.40 mm pitch (3.75 mm circumradius), 0.90 mm web. Open area **673.0 mm²**, solved
   *numerically* to match the slot array it replaces exactly, so the change is aesthetic
   rather than acoustic.

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

3. **0.60 mm flare on each slot mouth.** A sharp-edged slot sheds vortices and chuffs at
   level; the flare opens outward and is self-supporting in the print orientation.

**At assembly:**

- **Skip the wadding.** A sealed-back module brings its own rear volume, so there is no rear
  chamber to damp — stuffing the front cavity would just absorb output on its way out.
- **Seal every joint** — the wire pass-through and the base seam. Not to hold bass in a rear
  chamber, but to stop the *front* cavity venting anywhere except through the slots. A leak
  there lets the front wave escape and cancel, which costs level.
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
3. Lay the board **face down into the bezel**. The glass does **not** touch the bezel —
   there is a deliberate 0.40 mm gap. The four bosses land on the PCB's top face.
4. Drop the back shell on. Check the five 1.25 mm connectors and the microSD sit in the
   side channels before pulling anything tight.
5. Four M3 × 14 countersunk from the back. Snug, not hard — you are clamping a PCB.
6. ~~Press `ember-diffuser` into the ⌀16 seat around the rear glow window.~~
   **REMOVED.** There is no diffuser and no seat. The ⌀12 rear glow window and its ⌀16
   diffuser seat were both deleted when the back shell became a fine hex field: the LED's
   light now leaves through the apertures over it — 8 within r6, 23 within r10, 32 within
   r12 — plus straight through the wall if you print in white. Many small apertures in a
   translucent panel scatter; one large bore behind a printed disc just shows you the die.
7. Slide the slab into the stand slot; route the USB-C cable down the channel and out the back.
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
| `GRILLE_STYLE` | `"hex"` | `"ridge"` swaps the 33-hex field for lyra's raked dorsal-spine motif. **Both are solved to the same 673 mm² open area**, so this is aesthetic, not acoustic — the rake never did acoustic work, since these are straight-through bores raked *in the plane* of the wall, not louvered vanes angled through its thickness |
| `SCALLOP_D` / `SCALLOP_Z0` | 12.0 / 5.0 | the finger pockets over the button caps. Deeper reaches further behind the slab and eats the stand's rear wall — there is an assert holding 3 mm of wall at the rim. Raising `SCALLOP_Z0` keeps more of the lower rear grip and gives the finger less room |
| `BEZEL_DEBOSS` | 0.45 | how deep the honeycomb and wyrm cut into the front face. An assert holds ≥2.00 mm of bezel over the glass, so there is headroom — but this is the face you look at, and deeper is not automatically better on a 0.16 mm layer height |

---

## Why some numbers are what they are

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
  0.70 mm web), and the hearth-wyrm 27.00 × 11.25 mm in the brow — all 0.45 mm deep. This part
  prints front face down, so a raised logo would be the lowest feature and the bezel would land
  on it. **On a bed face, relief only goes inward** — that it bit both shell parts in the same
  session, on opposite faces, is the tell that it is a property of the process, not a mistake.
  The wyrm's *size* is set by the print floor rather than the space available: its verified
  minimum feature is 1.2333 mm at unit scale, and scaling it to fill the brow would take the
  thinnest part of the creature under the 0.90 mm floor.
- **Two of those cells used to sit on a screw boss, and it mattered for printing.** Nine chin
  cells per boss overlapped the fastener — four over the 2.50 mm pilot, five over the 5.40 mm
  pad — thinning the bezel roof over a self-tapper from 1.50 mm to **1.05 mm**. It was never a
  hole, which is why nothing flagged it. If you are checking a printed bezel against this
  sheet: the chin honeycomb should stop cleanly short of all four boss positions.
- **The hinges are sized by strain, not by feel — and the intuitive fix cracks them.** Bending
  strain in a flexure is `(t/2)·θ/L`, and **θ is not a free variable**: it is pip travel over
  the pip's distance from the hinge. The *smaller* cap therefore bends *further* — 5.56° on
  RESET against 3.50° on BOOT — because its pip sits on a shorter arm. At a shared 1.00 mm
  flexure that put RESET at **4.37%**, past PLA's ~2% yield and into its 4–6% break band. The
  natural remedy, thickening RESET's hinge so it presses firmer, takes it to **6.79%**: strain
  scales *with* thickness, so the obvious fix points the wrong way. Lengthening the flexure is
  what actually works. Shipped: **RESET 2.18% at L = 2.00, BOOT 2.29% at L = 1.20**, both under
  the 2.5% assert. The force ordering stays mildly inverted and that is the accepted trade — an
  easy RESET is an annoyance, a cracked RESET hinge is a dead part, and findability is already
  carried by cap size and deboss depth, which cost no strain at all.
  > **Every other check in this file would have passed all three variants happily.** The
  > geometry is valid, nothing collides, the pad stays attached, the solid is watertight, it
  > prints. It just breaks in your hand after a few dozen presses. Every assert here was about
  > *shape*; this is a property of the *material*. Worth asking of any parts library: which of
  > your invariants are about form, which are about matter, and is the second list empty?
- **The stand has finger scallops, and a taller cap would not have worked.** Docked, the stand
  swallows the first 16.56 mm of the slab, so BOOT's cap sat 3.81 mm *below* the rim and
  RESET's 6.23 — with 0.40 mm between the cap face and a solid wall. A finger does not fit in
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
