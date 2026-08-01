# Mobile variant — battery Ember

The handheld build: the same board and the same front bezel, with a single 18650 and the
speaker moved into the case. Issue [#44](https://github.com/jphein/ember.realm.watch/issues/44).

Source of truth is [`enclosure/ember_mobile_case.py`](../enclosure/ember_mobile_case.py). It
imports every board and shell number from `ember_case.py` rather than re-typing any of them, so
this document is a reading of that model and not a second copy of it. **Where the two disagree,
the model is right.**

> ⚠️ **Status: verified in CAD, never printed, nothing wired.**
> Both parts pass every check the desk parts do, including 0.000 mm³ interference against the
> vendor board solid. That is a geometry result. No part has been on a bed, no cell has been in
> a bay, and no joint has been soldered. The numbers marked **soft** below are the ones to
> distrust first.
>
> ⏳ **AND THE COVER RETENTION IS MID-REDESIGN.** The undercut hooks were rejected on
> printability and dovetail slides are in flight on `feat/dovetail-retention`, so **both mobile
> STLs will change again.** Until that lands and this document is regenerated against it, treat
> every cover-dependent figure and every §12 row that touches the cover as **provisional** —
> including the two shaded renders, which still depict the hook scheme. The cell bay, the vent,
> the acoustics, the glow window and the protection pocket are not implicated, but their *numbers*
> come from the same build and must be re-read from it rather than assumed to have held.

---

## Headline: it is a backpack, not a redesign

Three printed parts, **one of which is unchanged**.

| Part | Source | Layer | Prints on | Volume |
|---|---|---|---|---|
| `ember-front-bezel` | **reused bit-identical** from the desk case | 0.16 mm | front face down | 7.33 cm³ |
| `ember-mobile-midframe` | `ember_case.back_shell()` + additive features only | 0.20 mm | back face down | 21.31 cm³ |
| `ember-mobile-back` | new | 0.20 mm | **outer** face down | 27.71 cm³ |

Neither new part needs supports. The desk stand and its base are simply not used.

The board is clamped by **the same joint at the same plane** — the midframe's back face is held
at `BACK_Z = −9.70`, so bezel↔board↔midframe is the desk assembly, with the same four
M3 × 0.5 × 12 and the same 5.34 mm of thread engagement. That is the whole reason a deeper
back shell was rejected instead: `SCREW_LEN` is an under-head length, an M3×14 already bottoms
out against the pilot's end, and deepening the shell moves the counterbore 21.80 mm further from
the pilot — invalidating the derivation while still looking like it works.

**Removing the cover does not disturb the board.** The cover carries no board load, which is what
makes one-screw cell access real rather than nominal.

| | Mobile | Desk |
|---|---|---|
| Envelope | **55.90 × 94.95 × 39.00 mm** | 55.90 × 91.90 × 17.40 mm |
| Thin section (y < 18.00) | 17.40 mm — unchanged | 17.40 mm |

Width **cannot** move: the bezel is untouched. Length grew **3.05 mm**.

---

## 1 · Why 94.95 is forced

Not chosen — derived, link by link, and no lane avoids it:

```
BOOT cap + moat ends            16.40
  + finger clearance 1.60   ->  COVER_Y0   18.00   cover cannot start sooner
  + COV_WALL 2.20           ->  BAY_Y0     20.20   cell's flat face bears here
  + BAY_L 69.60             ->  BAY_Y1     89.80   dimensioned to the LONGEST cell
  + COV_WALL 2.20           ->  MOB_OY1    92.00   (+2.95 outer wall = 94.95)
```

The cover **deliberately stops short of the chin** so it cannot bury the two rear buttons or the
USB-C socket. That is a *reachability* constraint — the class of fault no clearance check sees,
and the same one filed as #31 when the desk buttons turned out to be completely buried inside
the stand. It is asserted anyway, with a vacuity control, plus a check that the cover clears the
USB-C plug at z −4.85..−1.60.

Rotating the cell to avoid the growth does not work: the widest gap between the two button caps
is 8.70 mm against a 19.40 mm bore, and along X the cell's 65.20 mm exceeds the 50.70 mm
interior outright.

## 2 · The X budget closes exactly

```
interior 51.50 = cell bore 19.40 + shared divider 2.00 + rim span 30.10
```

The divider is **one wall doing two jobs** — the cell trough's inboard wall *is* the seal rim's
inboard wall. Two walls do not fit. The driver's 28.20 mm tape footprint in a 30.10 mm rim leaves
1.90 mm total, 0.95 per side (assert floor 0.50).

`COV_WALL = 2.20` rather than the family's `WALL = 2.60`, for two converging reasons: at 2.60 the
budget does not close, and the cover's outer wall **is** the grille baffle, so `COV_WALL ==
BAFFLE_T` makes the acoustic port length identical to the stand's by construction. It is
asserted. *Do not "fix" a failure there by editing `BAFFLE_T`.*

---

## 3 · Bill of materials

| Item | Spec | Notes |
|---|---|---|
| Cell | **1 × bare flat-top 18650**, ⌀18.80 max incl. wrap | **Bare only.** Protected/button-top cells are out of scope — see §5. 3400 mAh assumed for the charge figure. |
| Spring | compression, **7.00 mm free / 2.50 mm solid**, ⌀9.00 seat | Generic AA/18650 holder spring. 4.50 mm travel against 0.60 mm of cell-length spread. |
| Protection strip | **1S DW01-class + dual FET, pre-welded nickel tabs** | ⚠️ **Required, not optional** — see §6. Pocket sized 20.0 × 6.50 × 2.50, all three **soft**. |
| Pigtail | JST 1.25 mm 2P | strip `P+`/`P−` → the board's `BAT` connector. |
| Cover screw | **1 × M3 × 0.5 × 22 ISO 4762** (cap head) | 2.5 mm hex key. 3.40 mm engaged in a 6.60 mm pilot. |
| Bezel screws | 4 × M3 × 0.5 × 12 ISO 4762 | Unchanged from the desk build. |
| Driver | 40 × 27 × 10 mm sealed-back module | Carried over. Double-sided tape on its **back**. |

Retention is **dovetail slides + that one screw**.

> ⚠️ **The slide geometry is in flight and no dimensions for it are quoted anywhere in this
> document.** It replaces an undercut-hook scheme that JP rejected on printability: the hook's
> 0.60 mm lip had to bridge its own 0.80 mm slot, which is the same failure family as the stand
> grille's webs (#47) — a feature whose *fit* was asserted and whose *printability* was not.
>
> What carries over unchanged is the **constraint set**, because it never came from the hooks:
> the retention features can only live where the button-cap keepout, the seal footprint, the vent
> field ("a lip made of honeycomb is not a lip") and the cover's own material at the mating plane
> all allow — and whatever replaces the hooks still has to be asserted on **reach as well as
> fit**, since a feature that fits engaged but cannot *reach* engaged is the same fault class as
> a buried button. That assert is the one to check survived the redesign.

---

## 4 · Assembly order

The order matters, and two steps are irreversible-ish:

1. **Seat the protection strip** in its pocket in the cover and solder its tabs. The whole
   compartment is open from above until the midframe goes on, so every joint is reachable with an
   iron *now* and not later. Solder access is a property of this ordering, and it is measured
   rather than asserted in prose.
2. **Tape the driver** to the midframe's back face, inside the locating groove (0.60 deep, 1.20
   wide, outline only — the tape does the work; a pocket would leave the bond bridging a step).
   That face is a 3678 mm² printed **bed face**, the flattest plane in the project, so unlike the
   desk stand there is no proud pad.
3. **Route the driver's leads** through the SPK relief. ⛔ **Then seal that relief** — silicone,
   hot glue or putty. It opens into the sealed cavity and it is asserted to lie *wholly inside*
   the rim rather than straddling the rim wall, because a straddled opening cannot be sealed at
   all.
4. **Run the cell leads** down the divider's groove (1.00 deep × 5.40 — widened from 3.20 so a
   flat 5 mm nickel tab lies in it instead of a round wire) and through the lead pass to `BAT`.
5. **Fit the board and bezel** exactly as the desk build.
6. **Drop the cell in** — `+` toward low Y — engage the cover's retention and drive the single M3.

## 5 · Cell bay

| | |
|---|---|
| Bore | ⌀**19.40** (⌀18.80 max cell + 0.30/side), axis at (x 8.95, z −19.40) |
| Bay | y **20.20 .. 89.80**, `BAY_L` **69.60** |
| Cradle | half-cylinder, concave, self-supporting — the cell self-centres |
| Contacts | printed pockets: ⌀9.00 × 1.00 spring seat one end, 10 × 10 flush plate the other |
| Spring | shortest cell 64.90 → 4.10 occupied, 2.90 compressed (still preloaded); longest 65.50 → 3.50, 1.00 clear of coil-bound |

### ⚠️ There is no mechanical reverse-insertion protection, and there cannot be

The previous revision had a real one: a ⌀7.00 aperture that a protected cell's **raised** positive
button passes and a flat can-face does not (blocked a reversed cell by 144.6 mm³, passed a correct
one at 0.00). It was **deleted**, because JP uses bare cells only — *"no protected tops"* — and on
a bare flat-top **both ends are geometrically identical**. Any aperture that stops a reversed cell
stops a correct one. This is not a matter of finding a cleverer profile: *the information is not
present in the geometry.* Left in, the feature would have rejected the only cells its owner owns.

It was removed rather than commented out, so nobody reinstates it from a note.

What replaces it is **markings only**: `+` and `−` debossed 0.60 mm deep, 2.80 mm tall, 0.90 mm
groove, into the two bay end walls and **facing into the bore**, so they are read as the cell goes
in. **That is weaker and the docs will not call it protection.** Making reverse insertion *safe*
is electrical, and it is unbuilt.

*(The check on those glyphs is worth knowing about: the repo's stroke-gap probe returns `inf` for
both — `+` because its strokes cross, `−` because it is a single stroke — so a `gap ≥ width`
assert passes on any glyph of that shape, sound or broken. It is asserted to stay vacuous, and the
real test bounds the debossed volume against ink area from **both** sides.)*

**soft:** a ⌀18.80 cell in a ⌀19.40 cradle has ~0.30 mm of radial slop, held endwise by the
spring rather than radially. A foam shim or a printed rib removes it. Neither is built, because
there is no cell in hand to measure the rattle.

---

## 6 · Charging and power

**The board charges the cell itself. The default build needs no charging hardware.**

| | |
|---|---|
| Charger | **TP4054** (U2), PROG `R12` = 3.3 kΩ → **~290 mA** |
| Charge time | **15.8 h** for 3400 mAh (`3400 × 1.35 / 290`; the ×1.35 is the vendor doc's own implied CC/CV factor) |
| Power path | SL2305 P-FET + B5819W Schottky — plugged in, the system runs from VBUS and **the full charge current still goes to the cell** |
| Level sense | 200 kΩ / 200 kΩ divider → `BAT_ADC` |

Overnight, and stated up front so nobody files it as a fault later.

### ⛔ There is no protection IC on the board. `BAT` goes straight to the cell.

Confirmed against the [vendor schematic](vendor/ES3C28P_Schematic.pdf), after searching the docs,
the model and the firmware for `DW01`, `FS312`, `8205`, BMS, over-discharge and low-voltage and
finding nothing. The battery area of the sheet is exactly two blocks: charge management and level
detection. That is all.

**"It browns out first" is the wrong reading.** With a bare cell the only over-discharge floor is
the ME6217 LDO's dropout: the device stops working around 3.4 V and **then keeps draining** —
roughly **9 µA** through that divider alone (3.7 V / 400 kΩ) plus quiescent draw. A cell left flat
in a drawer goes to zero, and a Li-ion cell taken to zero does not come back. Hence the strip is
**required equipment**.

Also from the sheet, for the record: amp SC8002B, codec ES8311, mic LMA2718B381, 2 × ME6217C33.

### The TP4056 trade, frozen

A ~1 A TP4056 module would charge in 4.6 h. **It does not fit, and the model proves it rather than
claiming it** — the free compartment is 30.10 × 13.40 and the module's short axis is 17.00, so it
fits in neither orientation. Its phantom is kept in the file so the boolean reports **228 mm³ of
interference** on every run.

Restoring the pocket costs the **5.90 mm** that switching to bare cells saved — the same length
the protection strip now occupies. JP froze it on 2026-08-01: **the case stays at 94.95, in-case
fast charging is out**, because with bare cells the missing protection is the sharper gap and
removable cells can be fast-charged in an external bay charger. This **reversed** an earlier call
to keep the TP4056 pocket; recorded rather than quietly absorbed.

⚠️ **And a hazard the CAD deliberately does not decide:** two chargers on one cell — the board's
and a TP4056 — means plugging in both ports puts two CC/CV controllers on the same cell, fighting
each other. Moot as built. It returns the moment anyone buys the pocket back.

⚠️ **No boost, so no graceful shutdown.** On battery the `+5` rail is the raw cell; the device
browns out rather than shutting down. Single-sourced. Firmware's problem, not the case's — though
the device already publishes battery voltage, so the hook for a low-voltage cutoff exists.

---

## 7 · Protection strip pocket

| | |
|---|---|
| Pocket | centred x **35.70**, y **78.50 .. 85.00**, floor at `CAV_Z0` |
| Sized for | **20.00 × 6.50 × 2.50** — see the warning |
| Clearances | 0.40 around, **1.00 over the component face** (the FETs are the tall parts) |
| Locating | three ribs, 1.60 wide × 1.20 high, **outside** the PCB footprint |
| Tab slots | 5.40 × 0.40 — these tabs are ~5 mm × 0.15 flat conductors, so shallow slots, excess trimmed |

> ⚠️ **soft — all three dimensions.** `PROT_L = 20.0` is JP's eyeball estimate ("20 mm about"),
> carrying **±2**; `PROT_W` and `PROT_T` are **unmeasured class placeholders**. The build prints
> `⚠️ UNMEASURED — awaiting JP's calipers` on every run. The *class* is certain from a photograph;
> the figures are not. When calipers land, those three constants are the whole edit.

The floor **under** the PCB is left flat — a rib under a PCB is a rock under a board — and the
ribs sit on floor that was already empty.

**The briefed class length, 31.00 mm, does not fit.** The compartment seats **29.30** flat, short
by 1.70, and it fits no other way: not rotated (13.40 of Y), not on edge (against 19.40 of depth),
not diagonally (a 31 × 6.5 rectangle needs 30.96 of X at its best angle). The compartment cannot
grow — the cell bore pins one side, the case wall the other, and the driver's 41.20 mm tape pad
sets the Y.

### The tabs do not go where the packaging suggests

These strips are *sold* to be spot-welded to a cell under its wrap, and **that is emphatically not
what happens here.** The strip is fixed in the case; the cell stays bare and removable.
**Nothing attaches to the cell.**

```
bay spring (−) --tab--> B−
+ contact plate --tab--> B+
P+ / P−  --> JST 1.25 2P pigtail --> BAT
```

---

## 8 · Cell-bay failure vent

A lithium cell in a sealed plastic box is the one thing in this design that can hurt someone, and
"the compartment isn't sealed to the board cavity" was too weak an answer.

| | |
|---|---|
| Geometry | **4 labyrinth units** through the cell lane's low-X wall, y **30.00 .. 55.60**, pitch 6.80 |
| Per unit | 2.00 slot in Y, cut 1.40 from **each** face at Ys offset by a 1.20 rib, 1.60 between units |
| Band | **0.60 × 6.90** — and 0.60 is `SLOT_W`, this repo's proven void at a 0.40 nozzle with gap-closing at 0. Not a number picked for the vent. |
| Skin | **0.80 standing at each face** — gas turns twice; a straight line finds 0.80 of material |
| Throat | **16.56 mm²** measured |
| vs cell ports | **1.76×** an assumed 9.42 mm² |
| Line of sight | worst outer slot **36 % obstructed** (assert > 25 %); control on a deliberately drilled wall **0.0 %** |
| Acoustics | untouched — seal rim still **100.00 % on all four legs** |

The requirement is only that **the enclosure is never the restriction**, which is why the assert is
`throat ≥ cell ports` and not a ratio target.

**Every cut runs its long axis along model Z, which is the print Z with the cover on its bed
face** — vertical slots, self-supporting, no bridge anywhere. *That is why the vent is in a side
wall and not the floor.*

> ⚠️ **soft — the target is an assumption, and it sets the number.** An 18650's positive cap
> carries 3–4 vent ports; 3 × ⌀2.0 mm = 9.42 mm² was taken. That is general cell construction, not
> a datasheet anyone here holds. The unit count is the knob if real figures turn up.

### The check was wrong first, in the most dangerous possible way

The throat probe originally spanned half a millimetre *outside* the part and half a millimetre of
bay interior either side of a 2.20 wall, and read **52.80 mm²** — 3× the analytic figure. Worse:
**with the band deleted entirely it would still have read 36.00 and passed.** An assert that cannot
fail, inside the check written to retire the design's single biggest risk. It surfaced only because
the measured number beat the calculated one by 3×, which is a defect signal and not a win.

Standing rule that came out of it, and out of two other over-reaching probes in the same file:
**a probe's extent is the feature's extent. A margin "to be safe" is not safe.**

---

## 9 · Acoustics

The driver is a **sealed-back module**, not a bare driver — it brings its own rear cavity, so
there is no sealed-vs-ported decision to make and what matters is the **front**.

| | Mobile | Desk stand |
|---|---|---|
| Net sealed front air | **15437.8 mm³** | 15621.3 mm³ |
| Δ | **−1.2 %** | — |
| Cavity | 30.10 × 44.80 × 19.40 | 54.00 × 15.30 × 33.00 |
| Governing first mode | **3828 Hz** | 3176 Hz |
| Grille field | 946.6 mm² (identical by construction) | 946.6 mm² |
| Grille throat | **562.7 mm² in 31 openings** (59 % of field; lattice ceiling 63 %) | — |
| vs driver radiating area | **80 %** of ~700 mm² | — |
| Port length | 2.20 = the cover's own wall | 2.20, by thinning a 4.0 wall |

Front air is **measured by boolean on the finished solid**, not by the arithmetic above it. The
mode figures use the same `c/2L` on both so the comparison is honest, and the assert requires the
mobile's governing mode not to go *down*.

**No grille flare here.** Issue #28's droop is a property of horizontal bores in a vertical wall;
in the cover the hexes are vertical prisms in a bed face, zero unsupported span — so the mouth web
stays the full `HEX_WEB` and the stand's flared-web trap cannot arise at all. Clipped cells are
filtered on **width** (≥ 1.20), not area: an 8 mm² hex is 3.0 mm across and fine, a 10 × 0.5
crescent is 5 mm² and unprintable. Filtering on area would keep exactly the wrong ones.

> ⚠️ **soft — a declared departure.** The gap in front of the diaphragm goes **2.50 → 9.40 mm**,
> because the cell bore sets the cover's depth and the driver has to sit somewhere in it. The
> repo's stated reason for keeping that gap small is about *total* front air, and total front air
> went **down** while the governing mode went **up 21 %** — so moving air from lateral to axial is
> believed neutral-to-better. **It is a belief, flagged rather than buried.** One constant if JP
> wants it otherwise.

---

## 10 · WS2812 glow window

Any closed back hides the LED, which fires backwards — `enclosure.md` said as much for *any* cover
before this variant existed. Here the occlusion is proved, not argued: the LED at (29.0, 45.6) lies
**inside the driver's footprint**, and the driver cannot be moved off it, because a 40 mm driver
cannot clear it inside a 44.80 mm cavity that must also contain the wire's only exit.

A light pipe was costed and **rejected on bend count**: the only bore starting at the LED runs into
the sealed cavity and hits the driver 2.60 mm later; escaping takes three hard corners against a
rule of two.

**Light does not need line of sight — only a lit pocket with a wall in it.** The board cavity
already reaches both side walls (proof needed no new measurement: the side channels are cut at
exactly the cavity's own Z band, which could not be true otherwise). Path: LED → cavity → a thinned
patch of side wall. One bounce, no pipe, no extra parts.

| | |
|---|---|
| Window | **2 hex cells**, high-X wall, y **18.70 .. 30.34**, z **−6.60 .. −2.10** |
| Size | **4.50 mm across flats** (the Z extent), 5.196 across corners |
| Membrane | **0.80 = two passes of a 0.40 nozzle**, measured **100.0 % intact**; control inside the pocket 0.0 % |
| Cut from | the wall's **inner** face — the outside stays flat and unbroken, so the hexes are invisible until lit |

`GLOW_MEMBRANE` is **not a layer count**: this wall is vertical in the print, so the criterion is
extrusion width, not layer height.

**The site is solved, not typed.** The LED's own Y lands inside a cable channel on *both* walls, so
"put the window at the LED" was never available. `_glow_site()` searches the solid spans between
channels for the nearest that can hold the window — so if a connector moves, the window follows
instead of quietly opening into a hole. It asserts with a named fallback if no span fits.

### ⚠️ Pinned, not shared — a cross-part regression

`GLOW_R` was written as `HEX_R`, "the same cell as the grille". When the **desk stand's** grille was
re-parameterised 4.50 → 4.75 mm across flats for printable webs (#47), this window — **in a
different part** — silently inherited the change and stopped fitting its 5.50 mm cavity band. The
module-level assert fired at 4.75 against a 4.70 limit and the export gate refused to write the
STL.

**A window's size is set by the band it lives in, not by another part's lattice.** It is pinned at
exactly 4.50 now; the motif survives, 0.25 finer than the grille it used to match.

> ⚠️ **soft — brightness is filament-dependent, and in the specified charcoal this will be dim.**
> `PRINT-SHEET.md` records that white/natural PLA is translucent enough for the WS2812 to light the
> shell itself. Three options, each one constant: print the midframe in natural PLA; drop the
> membrane to 0.40 (one extrusion); or take it to 0 for true through-holes — which adds no ingress
> class this wall does not already have, since it already carries three open cable channels.

⚠️ **This feature is on the midframe, not the cover.** Any previously sliced midframe gcode is
stale.

---

## 11 · Print notes

Everything in `PRINT-SHEET.md`'s shell column applies: 0.20 mm layers, 3 perimeters, 15 % gyroid,
no supports, bridging on. Matte charcoal PLA (PETG only if it will sit in direct sun).

⛔ **Set gap-closing radius / hole horizontal expansion to 0 before slicing.** A slicer default
welds the printed-in-place buttons and the 0.90 mm labels shut — and `VENT_BAND` is 0.60, the same
proven void, so the labyrinth depends on that setting too.

- Every depth in the file is asserted to be a whole multiple of 0.20, with three controls that must
  read misaligned. Cover depth is 21.60 = 108 layers exactly; the cell bore 19.40 = 97.
- **Bed contact is measured on both parts** — cover 3340.9 mm², midframe 3779.9 mm², floor 600 —
  because balancing a part on a proud feature is a defect this repo has had on both shell parts in
  one session.
- Both parts are modelled entirely below z = 0 and lifted on export, with the lift asserted,
  because a slicer silently drops a part onto the bed and the mistake never surfaces as an error.
- Export goes through a `.stl.partial` → `os.replace` gate that is self-tested in both directions;
  on failure nothing is committed and the STLs on disk are the previous good set.

⚠️ **`PRINT-SHEET.md` does not list the mobile parts.** There is no mobile print sheet, no mobile
supports statement of its own, and no mobile filament call. The figures above are the shell spec
inherited by layer height.

---

## 12 · Verification — what the build actually measures

Printed by `ember_mobile_case.py` on every run. Regenerate with the command in §13; do not
transcribe these by hand.

| Check | Result |
|---|---|
| Envelope | 55.90 × 94.95 × 39.00 (desk 55.90 × 91.90 × 17.40) |
| Mesh | midframe 30 640 tris, cover 4 718 — both **0 boundary, 0 non-manifold, watertight** |
| Board interference | midframe **0.000**, cover **0.000**, cell phantom **0.000** mm³ |
| Interference controls | cover +22 mm → 2248.8 · midframe +2 mm → 184.4 · cell +12 mm → 1919.7 mm³ |
| X budget | interior 51.50 = 19.40 + 2.00 + 30.10; driver slack 1.90 |
| Reachability | BOOT top 16.40 vs cover start 18.00; USB-C clear |
| Cell + spring | bay 69.60; 64.9 → 4.10, 65.5 → 3.50; travel 4.50 vs 0.60 needed |
| Seal rim | **100.00 % on all four legs**; control on the open vent field 93.11 % |
| Fasteners vs rim | 3 fasteners, all clear of the rim footprint |
| Front air | 15621.3 → **15437.8 mm³ (−1.2 %)** |
| Cavity mode | 3176 → **3828 Hz** |
| Grille | **31 openings, 562.7 mm² throat** over 946.6 field (59 %, ceiling 63 %); 80 % of driver area |
| Cover retention | ⏳ **pending the dovetail redesign** — the hook figures this row carried (travel 2.90 / 3.60, pocket 1.40 in a 2.60 floor) describe a scheme that was rejected on printability, so they are removed rather than left to read as current |
| Cover screw | M3×22, head at z −28.30, **3.40 mm engaged in a 6.60 mm pilot** |
| Counterbore | 4.60 mm to the cover edge (needs 4.20); annulus 1.60 (min 1.00); seat 100.0 % solid |
| Strip pocket | 20.00 × 6.50 × 2.50 fits (0.00 mm³ foul); max that seats flat 29.30 |
| TP4056 | **228 mm³ interference — does not fit** |
| Charge | 290 mA → **15.8 h** |
| Vent | 4 units, **16.56 mm² throat vs 9.42 assumed (1.76×)**; worst slot 36 % obstructed, drilled control 0.0 % |
| Glow | 2 cells, y 18.70..30.34, z −6.60..−2.10; membrane **100.0 % intact**, control 0.0 % |
| Bed contact | cover 3340.9 mm², midframe 3779.9 mm² |

The file carries **17 numbered checks plus 3 module-level asserts and 98 assertions**, and a large
share of them are **controls** — probes that must *fail* on deliberately broken input. That is the
lesson `verification.md` exists for: on this project the first version of a check has been wrong
more often than the geometry it checked.

---

## 13 · Regenerating

```bash
cd enclosure
./cadenv/bin/python ember_mobile_case.py        # model + all checks + both STLs
./cadenv/bin/python tools/make_mobile_renders.py # the site figures, into site/renders/
cd ../site && python3 build.py                   # docs/index.html
```

`ember_mobile_case.py` writes nothing unless every check passes. `make_mobile_renders.py` slices
and projects the same model, so **no figure carries hand-drawn geometry and every dimension label
is measured off the outline it sits under** — a number typed into a figure is a rumour about the
part.

⚠️ Both need the 17.7 MB vendor STEP, which is deliberately not committed and will never be in a
`git archive`/`clone` extract. See [`../enclosure/README.md`](../enclosure/README.md).

⚠️ `ember_mobile_case.py` does **not** refresh the print queue — only `ember_case.py` does. The
mobile queue entries are only as current as the last `ember_case.py` run.

---

## 14 · Open items, in rough order of how much they should worry you

1. **Thermal path out of the cell bay** — the largest unresolved risk, and it is not mechanical.
   Most of the rear vent field is refilled by the speaker bond plateau, and what survives vents
   into a **closed** compartment: compartment → remaining hexes → board cavity → side channels →
   outside. The desk case vents straight to the room. Deliberately *not* "fixed" with invented
   vent geometry.
2. **Protection is unbuilt electrically.** The pocket exists and the schematic proves the need.
   No strip has been fitted, no firmware cutoff written.
3. **Reverse insertion is unprotected** — markings only (§5).
4. **The strip's three dimensions** are an estimate and two placeholders (§7).
5. **Cover retention is being redesigned as this is written.** The undercut hooks were rejected
   on printability — a 0.60 mm lip bridging its own slot — and dovetail slides are in flight on
   `feat/dovetail-retention`. Two consequences: the **top-edge gap** question is still open (the
   old scheme anchored only the bottom, so the top ~70 mm leaned on wall stiffness and the
   divider, and only a test print settles it either way), and **every figure and every measured
   number in §12 that touches the cover must be regenerated against the new geometry** before
   this document is trusted.
6. **The 1.76× vent ratio** inherits an assumption about the cell's own port area (§8).
7. **The front-gap redistribution** is a declared belief (§9).
8. **Glow brightness in charcoal** (§10).
9. **~0.30 mm of cell slop**, unmeasured because there is no cell in hand (§5).
10. **No graceful shutdown** without a boost (§6).
11. **Nothing has been printed and nothing wired.** Both parts show `printed_at: null`.

---

## See also

- [`enclosure.md`](enclosure.md) — verified board geometry and the case survey. Everything there
  about the board applies unchanged.
- [`verification.md`](verification.md) — the running log of claims that outran their evidence.
- [`vendor/README.md`](vendor/README.md) — the schematic and what it settles.
- [`../enclosure/PRINT-SHEET.md`](../enclosure/PRINT-SHEET.md) — desk parts only; see §11.
