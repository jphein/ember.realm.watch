# Ember satellite case — print sheet

Board: **LCDWIKI/QDtech ES3C28P** (Hosyond 2.8" ESP32-S3).
Source of truth: `ember_case.py` (build123d). The STLs are output, not the artifact.

Rebuild with:
```
cd scratch/hosyond-s3/ember-case && ../cadenv/bin/python ember_case.py
```

---

## Parts

| File | Qty | Print orientation | Supports | Notes |
|---|---|---|---|---|
| `ember-front-bezel.stl` | 1 | **front face DOWN** on the bed | **none** | The visible face is the bed face — use a smooth PEI sheet. Mic flare + window are all bed-side chamfers, so they self-support. |
| `ember-back-shell.stl` | 1 | **back face DOWN**, open side up | **none** | Button pads + living hinges print in the first ~8 layers; the pips point up into the cavity. Countersinks widen downward onto the bed. |
| `ember-stand.stl` | 1 | **bottom face DOWN** | **none** | Chamber ceiling is a **17 mm bridge** and the cable channel a **16 mm bridge** — leave bridging on (slicer default) and they're fine. |
| `ember-stand-base.stl` | 1 | flat | none | Closes the speaker chamber. Press fit. |
| `ember-diffuser.stl` | 1 | flat | none | Print in **translucent / natural / ember-orange** filament — this is the WS2812 glow window. |

Outer sizes: slab (bezel + shell assembled) **55.9 × 91.9 × 17.4 mm**; stand **64 × 64 × 40 mm**.
Material use ≈ 122 cm³ total (~150 g).

---

## Slicer settings

| | Bezel | Shell | Stand | Base / diffuser |
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
Diffuser in translucent or ember-orange so the glow reads warm.

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

There is a **USB-C well** under the slot — 22 × 22 mm, full height from the stand floor to
the slot floor, opening into the rear cable route. Deliberately generous: a moulded plug's
strain relief is wider than the connector, and a cable forced into a tight well takes the
bend at the plug rather than in the lead, which is how USB-C cables die.

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
2. **The slots are lyra-artist's hearth-wyrm dorsal ridge, re-derived for this field.**
   Nine slots **raked 24° back**, tapering **3.20 → 2.50 mm** thick-to-thin toward the
   tail, capsule ends. Open area **673 mm²** — identical to the plain array it replaces,
   and above the driver's ~700 mm² effective radiating area. Minimum web 0.91 mm, and the
   rake leans the self-supporting direction for FDM.

   Her motif *as delivered* was 11 spines in a 50 × 15 field at 190 mm² open, sized for the
   round ⌀28 driver the design used to have. Applied unchanged it would have cost **72% of
   the open area**. The re-derivation keeps the rake and the thick-to-thin gradient — both
   read at this scale — and drops the **length** taper, which is the literal ridge shape and
   also precisely what removes open area.
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
6. Optional: press `ember-diffuser` into the ⌀16 seat around the rear glow window.
7. Slide the slab into the stand slot; route the USB-C cable down the channel and out the back.

---

## Tunables (edit + re-run)

| Parameter | Default | Change it when |
|---|---|---|
| `FIT` | 0.35 | board is tight/loose in the pocket |
| `HINGE_T` | 0.90 | **buttons feel stiff → try 0.70.** The pad must flex ~0.40 mm total (0.15 mm air gap + ~0.25 mm switch travel). 0.90 mm of PLA over a 9.5 mm cantilever is at the stiff end of workable — this is the parameter most likely to need a second print. |
| `GLASS_GAP` | 0.40 | never reduce below 0.25 — see below |
| `SLOT_CLR` | 0.40 | slab loose/tight in the stand |
| `TILT` | 15° | viewing angle |
| `GRILLE_SLOT_W` / `GRILLE_PITCH` / `GRILLE_FIELD` | 2.2 / 3.4 / 30 | the grille is a clean parameter block, ready for a motif to replace it |

---

## Why some numbers are what they are

- **`GLASS_GAP = 0.40` — the bezel never touches the capacitive glass.** The vendor tolerances
  the LCD at 2.3 ±0.1 and the touch panel at 1.0 ±0.1, so the glass front face can sit up to
  0.2 mm high. A rigid printed bezel bearing on glass is how you crack a display. The entire
  clamping load runs bezel → bosses → PCB → standoffs → shell; the glass is never in the load
  path. This was a bug in the first iteration, caught before export.
- **Button pads extend in +Y only.** The switches sit just 3.26 mm from the board edge, so a
  centred pad cut straight through the shell's bottom wall. Caught by rendering and looking.
- **Side channels are deliberately generous.** See the open question below.
- **Shrinkage:** PLA ≈0.3 % over 86 mm = 0.13 mm/side, PETG ≈0.5 % = 0.22 mm/side — both
  inside the 0.35 mm pocket fit, so **no scaling compensation is needed**.

---

## Two things to check on the physical board

**1. Which way does the mic fire?** — 20 seconds with the board in hand.

Look at the **front** face, in the bare strip at the end **away from the USB-C**, about
**10 mm in from one long edge and ~4.5 mm from the short edge** (just inboard of the
top-right mounting hole). Is there a tiny hole, ~0.5–1 mm, through the PCB?

- **Hole present** → the mic fires forward. The bezel's ⌀2.40 port and its collar are doing
  the work, exactly as designed.
- **No hole** → the mic fires rearward, and the ⌀3.00 relief through the back shell behind
  the mic is what's carrying it.

**The case provides both paths**, so it works either way — but knowing which one lets you
tune it (and tells you which opening not to obstruct when mounting).

Why it's still open: the vendor STEP contains **no small holes at all** — not one via — so
Altium clearly suppressed them on export. Absence of a port hole in the model is therefore
not evidence of absence on the board. The front-view outline drawing *does* show a circle at
the mic location, which is why I lean front-firing.

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
