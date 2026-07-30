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

## Speaker

Cut for a **rectangular 40 × 27 mm driver with rounded corners**, adhesive-mounted
(8 Ω; the board's amp does 1.5 W/8 Ω or 2 W/4 Ω). Sealed chamber ≈ **30 cm³** in the
stand, firing forward through a **37 × 24 mm slotted grille**.

> **Revised from a ⌀28 mm round driver.** The first cut assumed a round, flanged
> driver seated in a ⌀29 × 2.2 mm recess. JP's actual speaker is a 40 × 27 rectangle
> held on with **adhesive tape**, which inverts two requirements: the grille field had
> to become rectangular, and the recess had to go. Tape needs a **flat, continuous
> surface** to bond to — a pocket deep enough to seat a flange leaves the adhesive
> bridging a step, which is where the bond fails first.

- The front wall's inner face is **flat** where the speaker lands. Only a **0.60 mm
  deep, 1.20 mm wide locating lip** is cut around the driver's outline: enough to stop
  it sliding while the adhesive grabs, too shallow to interrupt the bonded area.
- Chamber ceiling was raised **34 → 37 mm** for the taller driver. At 34 the chamber was
  30 mm tall and a 27 mm driver left 1.5 mm a side. The sealed volume went 27.5 → 30 cm³,
  which helps the low end.
- **Wire pass-through: a 6 × 5 mm channel** from inside the chamber (y=19) back to y=30,
  meeting the board's cable route. From there the wire follows the same path up to the
  slot. ⚠️ **Seal it after wiring** — silicone, hot glue or putty. An unsealed hole turns
  the sealed box into a leaky one and costs exactly the low end the chamber exists to
  produce. It is sized for a bead of sealant rather than a press fit, because a hole
  tight enough to grip the wire abrades the insulation.
- The ES3C28P **speaker header is unpopulated** — you need a 1.25 mm 2P pigtail.
- Changing driver: edit `DRIVER_W`, `DRIVER_H`, `DRIVER_R` in `ember_case.py` and re-run.
  `GRILLE_INSET` (1.5 mm) keeps the slots inside the radiating area so the grille never
  opens onto the frame — an open slot over the flange is a dust path into the chamber and
  vents the enclosure.

⚠️ **Keep the driver magnet away from the top 8 mm of the board's back face** —
`ANT = (17.57, 32.21, 80.04, 85.70)` is the PCB Wi-Fi antenna. The stand geometry already
puts the magnet ~70 mm away, so this only matters if you relocate the speaker into the slab.

---

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
