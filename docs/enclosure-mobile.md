# Mobile variant — battery Ember

The handheld build: the same board and the same front bezel, with a single 18650 and the
speaker moved into the case. Issue [#44](https://github.com/jphein/ember.realm.watch/issues/44).

Source of truth is [`enclosure/ember_mobile_case.py`](../enclosure/ember_mobile_case.py). It
imports every board and shell number from `ember_case.py` rather than re-typing any of them, so
this document is a reading of that model and not a second copy of it. **Where the two disagree,
the model is right.**

> ⚠️ **Status: verified in CAD, nothing completed, nothing wired.**
> Both parts pass every check the desk parts do, including 0.000 mm³ interference against the
> vendor board solid. That is a geometry result. No cell has been in a bay and no joint has been
> soldered. The numbers marked **soft** below are the ones to distrust first.
>
> *A cover print was started and **cancelled at 2 %** on 2026-08-01, when JP's re-measurement of
> the protection strip landed and the locator ribs turned out to be 1.5 mm too close together.
> Nothing has been printed to completion, but the bed is no longer untouched — and that cancel is
> the cheapest thing in this document.*

---

## Headline: it is a backpack, not a redesign

Three printed parts, **one of which is unchanged**.

| Part | Source | Layer | Prints on | Volume |
|---|---|---|---|---|
| `ember-front-bezel` | **reused bit-identical** from the desk case | 0.16 mm | front face down | 7.33 cm³ |
| `ember-mobile-midframe` | **`ember_case.back_shell("mobile")`** + additive features | 0.20 mm | back face down | 21.54 cm³ |
| `ember-mobile-back` | new | 0.20 mm | **outer** face down | 27.24 cm³ |

Neither new part needs supports. The desk stand and its base are simply not used.

**The shared shell is variant-aware now**, which is new and worth knowing before you read the
figures: `back_shell()` takes a variant, and it decides *which flank openings are cut and
therefore which connector labels are truthful*. The desk blocks `BAT`; the mobile blocks `BAT`
and `SPK`, because its speaker lives inside the cover's sealed cavity and its pigtail leaves
through the SPK relief rather than the flank. One shell, two honest back faces — and §10 records
the side effect nobody designed, which is that closing `SPK` moved the glow window.

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
| Envelope | **55.90 × 93.63 × 39.00 mm** | 55.90 × 91.90 × 17.40 mm |
| Thin section (y < 18.00) | 17.40 mm — unchanged | 17.40 mm |

Width **cannot** move: the bezel is untouched. Length grew **1.32 mm** — and §1 is about why that
number is not the one it used to be.

---

## 1 · Why 93.63, and why the reason is not the one anybody expected

The case is **1.32 mm longer than the desk one**, and the interesting part is what that
millimetre and a bit is paying for — because it is not what it was paying for a week ago.

```
BOOT cap + moat ends            16.40
  + finger clearance 1.60   ->  COVER_Y0   18.00   cover cannot start sooner
  + COV_WALL 2.20           ->  BAY_Y0     20.20   the cell's flat face bears here
  + BAY_L 66.75             ->  BAY_Y1     88.48   longest cell + leaf solid + margin
  + CELL_END_SETBACK 3.73   ->  MOB_OY1    90.68   (+2.95 outer wall = 93.63)
```

### The forcing term used to be the spring, and it isn't any more

The coil spring cost **3.50 mm** — solid height plus margin plus its tunnel — and that was the
whole of the overshoot. Replacing it with a **folded nickel leaf**, formed from the protection
strip's own B− tab, needs **0.50**. So the obvious conclusion was that the case could go back to
the desk profile exactly, `MOB_OY1 = OY1 = 88.95`, and the brow would simply vanish.

**It was built that way, and the gate refused it.** The cell-vs-cradle boolean came back at
**21.218 mm³**, at x −0.45..3.50, y 84.07..86.75 — the interior box's own **+Y corner fillet**.
The case's `OUT_R` = 6.45 corner curves inward over its last 6.45 mm, while the bore is already
only 0.10 inside the −X wall. **The bay cannot end where the case does, whatever the spring is.**
`CELL_END_SETBACK` is **3.73**, derived from that arc against `MIN_SOLID` rather than chosen.

> ⭐ **So the brow had two clients, and only one of them was ever named.** The coil (3.50) and the
> corner fillet (3.73) — and because 3.50 ≈ 3.73, **the coil had been paying the fillet's debt by
> accident, for the entire life of the design.** Nobody wrote the second client down because
> nothing ever asked it to: the feature that would have revealed it was being covered by the
> feature everyone knew about.
>
> Deleting the known client is what exposed the unknown one. **A feature can have a client nobody
> has named, and removing the obvious one is how you find out** — which is the same lesson as the
> `GLOW_WEB` half-fix in [`verification.md`](verification.md) §31, seen from the other side: there
> a coupling was hidden behind the coupling that fired; here a dependency was hidden behind the
> dependency everyone could see.

The brow therefore **shrank by 1.32 mm rather than vanishing**, and what remains of it is holding
the fillet off the cell, not the spring off the cell. *The brow did not outlive the coil by
accident — it outlived it because its last structural client was never the coil at all.*

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
| Cell contacts | **none to buy** — both ends are folded-excess **leaf springs** formed from the strip's own nickel tabs | Free height 3.60, closed 0.75. There is no coil spring and no `+` plate any more: the parts list got *shorter* as the design got harder. |
| Protection strip | **1S DW01-class + dual FET, tabs pre-welded** | ⚠️ **Required, not optional** — see §6. Body **21.50 × 4.50 × 2.50**, flat assembly **90.00**, tabs 34.25 each. **All JP-measured — no placeholders left.** It lies flat beside the cell; see §7. |
| Pigtail | JST 1.25 mm 2P | strip `P+`/`P−` → the board's `BAT` connector. |
| Cover screws | **2 × M3 × 0.5 × 22 ISO 4762** (cap head) | 2.5 mm hex key, 3.40 mm engaged in a 6.60 mm pilot. ⚠️ Briefly **M3×25** while the bay was 1.60 deeper (§7b); the growth was reverted and so was the screw. **Take the length from the build's own shopping line, not from a memory of this table.** |
| Bezel screws | 4 × M3 × 0.5 × 12 ISO 4762 | Unchanged from the desk build. |
| Driver | 40 × 27 × 10 mm sealed-back module | Carried over. Double-sided tape on its **back**. |

Retention is **two M3 × 22 screws driven straight down, and the cover's own box section**.

| | |
|---|---|
| Screws | a shared lane at **x 23.55** — chin **(23.55, 22.60)**, top **(23.55, 85.98)**. ⌀9.00 boss both ends, 6.60 pilot, **3.40 mm engaged** |
| Top screw placement | set by `SCREW_BOSS_D/2 + 0.20`, **not** by `SCREW_EDGE_MIN` — the boss is wider than the counterbore, and when it was placed by the counterbore rule it stood **0.30 proud** of the end face |
| The rest of the edge | carried by the cover's **21.60 mm closed box section**, not by fasteners |
| Worst unheld point | **43.19 mm, at (52.95, 54.34)** — mid-span of the **+X** long edge |

**Two screws is JP's cap, and the budget above is what that buys.** The lane sits 26.50 from the
−X edge and 29.40 from the +X, so pushing it inboard — which the protection strip forced —
*inverted which long edge is worse*. The +X edge is now the weaker one, and it is also the only
one that could ever take a third fastener: −X can never take one at any y, with the cell bore
below and `SCREW_EDGE_MIN` above.

> **A third screw is now possible, and is deliberately not proposed.** It was the protection
> strip that made a second top screw impossible, and the strip has since moved to the lower band,
> so the upper compartment is empty. One at roughly (46, 82) would halve the +X worst case. It is
> recorded here only so the constraint that used to forbid it is not re-derived from scratch by
> the next person — **the cap is JP's call, not an oversight.**

### This is the third retention scheme, and each was killed by a different kind of argument

| scheme | killed by |
|---|---|
| two undercut hooks | **printability** — a 0.60 mm lip bridging its own 0.80 mm slot |
| a dovetail rail | superseded when the whole retention approach was reconsidered |
| **two screws + box section** | *(built)* |

Worth keeping the shape of those failures rather than just the outcome. The hooks' fit was
asserted and their **printability was not** — the same distinction as the stand grille's webs
(#47), and the second time this project has paid for it. Every `HOOK_*` and every `DT_*` constant
is **deleted** rather than commented out, so no scheme can be reinstated from a note.

### Moving a screw is what found a real defect at the screw that did not move

The chin screw was investigated for relocation and **stayed at (23.55, 22.60)**. The investigation
was still worth it, because it exposed something at the *unmoved* position: the nearest surviving
hex cell left **0.80 mm of web** against a **1.60 mm floor** — at a **thread-forming** screw, which
expands material radially as it goes in. Thin web plus radial expansion is a split.

So the mobile now drops **two hex rows, not one**: the row whose cells at x 23.00 and 27.00 overlap
the chin pilot outright, and the row whose cell at x 25.00 left that 0.80. The desk keeps all 113
cells and stays byte-identical — this is a mobile-only subtraction. A new **`[collar]` probe**
asserts a full `MIN_SOLID` collar at both screws, and its **control in the open hex field reads
35 % and is correctly rejected**.

*The useful shape: a question asked about one feature ("can this screw move?") returned an answer
about a different one ("this screw is unsafe where it is"). Investigations are worth finishing even
when the answer is no.*

**Location lips were considered and are arithmetically impossible.** A lip needs
1.60 + 2 × 0.35 clearance + 2 × 1.60 skin = **5.50 mm of wall**. The cover has 2.20 and the
midframe's floor outboard of the board pocket has 2.60. **Short by 2.90** — not a tuning problem,
and the same shape as the −X dovetail elimination before it.

---

## 4 · Assembly order

The order matters, and the first two steps are the ones the geometry was arranged around:

1. **Lay the strip body flat in its channel beside the cell lane**, fold both tabs, and seat the
   leaf ends. The body goes in **before the cell**, and the cell **drops on top of it** — which is
   why the bay's growth was designed to land at the *bottom* when growth was still on the table.
   Nothing is threaded down beside a cylinder that already fills the bore.
2. **Solder the output wires on the body's +X side**, then thread them to the chin pass. That side
   sits past the cell's surface, so the joints live where their thickness is not a dimension anyone
   has to know. Everything is still open from above here — solder access is a property of *this
   ordering* and of nothing else.
3. **Tape the driver** to the midframe's back face, inside the locating groove (0.60 deep, 1.20
   wide, outline only — the tape does the work; a pocket would leave the bond bridging a step).
   That face is a printed **bed face**, the flattest plane in the project, so unlike the desk stand
   there is no proud pad.
4. **Route the driver's leads** through the SPK relief. ⛔ **Then seal that relief** — silicone, hot
   glue or putty. It opens into the sealed cavity, and it is asserted to lie *wholly inside* the rim
   rather than straddling its wall, because a straddled opening cannot be sealed at all.
   ⚠️ **And note what §7d says about that plug: it is half the seal, and it is the half the model
   cannot see.**
5. **Fit the board and bezel** exactly as the desk build.
6. **Drop the bare cell on top of the seated strip.** Both ends land on leaf springs. There is no
   plate to orient against any more, so read the debossed marks — and see §5 for why they are not
   mirror images of each other.
7. **Seat the cover and drive both M3 screws.**

## 5 · Cell bay

| | |
|---|---|
| Bore | ⌀**19.40** (⌀18.80 max cell + 0.30/side), axis at (x 8.95, z −19.40) |
| Bay | y **20.20 .. 89.80**, `BAY_L` **69.60** |
| Cradle | half-cylinder, concave, self-supporting — the cell self-centres |
| Spring bore | ⌀**9.00** for a ⌀8.00 spring, capped by a **53.13° gable** rising 6.00 over the 4.50 half-bore |
| Contacts | a **10 × 10 × 0.25** stamped plate in a **0.35 kerf** with a **0.15 detent** to hold it, 0.10 of play |
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
groove. **`+` sits at y 86.95** on the high-Y end wall; **`−` sits at y 19.10 — on the cover's
mating face, not the bay wall.** **That is weaker and the docs will not call it protection.**
Making reverse insertion *safe* is electrical, and it is unbuilt.

### ⚠️ The "−" mark was debossed correctly, and could not be seen

Both marks were cut to spec and both passed the deboss check — the one that bounds debossed volume
against ink area from *both* sides, which is a good check. **The `−` was 34 % visible**, because
the folded nickel leaf now sits in front of it. Nothing about the geometry was wrong: the mark was
there, at the right depth, in the right place, and a person putting a cell in could not read it.

**This is a different failure from an assertion that cannot fail.** This one *could* fail and did
not, because it was asking about **volume** when the thing that mattered was **sightline**. Check
15 gained a **visibility lens**, with the old geometry kept as its rejected control.

The fix is an asymmetry, and **the asymmetry is the finding**: `−` sits on the cover's mating face
at y 19.10 while `+` is on the +Y bulkhead's bay face at y 86.95. *A design that kept them
symmetric for tidiness would have kept one of them invisible.*

> ⚠️ **The original reason for that asymmetry has since expired, and the asymmetry has not.** It was
> justified by the two ends being unlike each other — a nickel leaf in front of one, a flat contact
> plate in front of the other. **Both ends are leaf seats now**; the `+` plate was retired when the
> strip's own tabs took over both contacts. So the positions are still what the model builds and
> still what the build reports, but the *stated reason* no longer distinguishes them.
>
> Recorded rather than papered over, because the tempting move is to invent a fresh justification
> for a position that is already correct — and a rationale reverse-engineered to fit an existing
> feature is indistinguishable from one that was designed. **If the low-Y mark is still the only
> obscured one, that is a measurement someone should take rather than a sentence someone should
> write.**

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
fits in neither orientation. Its phantom is kept in the file so the boolean reports **299 mm³ of
interference** on every run.

Restoring the pocket costs the **5.90 mm** that switching to bare cells saved — the same length
the protection strip now occupies. JP froze it on 2026-08-01: **the case stays as short as it is, in-case
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

## 7 · Where the protection strip lives — and the four days it took to find out

All three of its dimensions are **JP-measured** now: **21.50 × 4.50 × 2.50**, plus the flat
assembled length **90.00**. *There are no placeholders left in this section*, which is worth saying
explicitly because for most of this design's life the strip was the one part described entirely by
estimates.

| | |
|---|---|
| Home | **flat on the bay floor, beside the cell**, in the space the divider used to occupy |
| Footprint | x **16.15 .. 20.65**, mid-bay at y **42.83 .. 64.33**, channel z −29.10 .. −26.20 |
| Cell clearance | **0.46 mm** over the seated body |
| Tabs | **34.25 each** → **22.62 run + 11.63 fold** per end = **3.2 limbs**; *both* ends are folded-excess leaf springs |
| Solder joints | on the body's **+X half**, which sits past the cell's surface (18.35) entirely |

**Mid-bay is not a placement, it is the reason the arithmetic closes.** The tabs are a fixed
34.25 mm each and the case cannot grow, so the only way both ends reach their seats *with no added
nickel* is to start from the middle. Put the body at either end and one tab runs out.

### The solder problem was answered by placement, not by clearance

JP's own objection to a strip inside the bay was the joints: solder has thickness, nobody has
measured it, and a 0.15 mm tab plus a blob is exactly the kind of dimension that turns out to
matter after assembly. The answer is that the body's **+X half is past the cell's surface
altogether**, so the joints live where thickness never becomes a dimension anyone has to know.
*The good version of a tolerance problem is the one you arrange not to have.*

---

## 7b · Five constructions were measured dead before this one worked

This is the longest single argument in the design, and it is worth keeping in full because at two
separate points a **correct measurement pointed at the wrong conclusion**.

**First it was declared impossible.** The cell bore is inscribed in the bay *exactly* — measured,
not estimated:

```
-X extreme   -0.75  vs CELL_X0  -0.75     gap 0.00
+X extreme   18.65  vs CELL_X1  18.65     gap 0.00
bottom      -29.10  vs CAV_Z0  -29.10     gap 0.00
seated top  -10.30  vs BACK_Z   -9.70  -> 0.60 of headroom
```

Tangent on three sides. That is the X budget closing, not slack anyone forgot — and a strip needs
its thickness *somewhere*. So the strip was recorded as blocked and left in the chin band.

### ⭐ Then JP asked the question that broke it open

> **"the lid is flat teh battery is round isn't there space?"**

Yes. And the reason nobody had seen it is the most useful sentence of the round:

> **A correct measurement of the wrong feature reads exactly like a correct measurement.**

The extremes had been measured against the envelope and the bay called full. But **a round bore in
a square bay leaves four corner solids** — 4.53 mm of diagonal at the top pair, 4.11 at the bottom.
The measurement was right. The feature was wrong. Nothing about the number was suspicious, which is
precisely why it survived: *there is no tell.*

### And the corner still wasn't the answer

Building it there needed **BAY_EXTRA 1.60** of growth — less than the 2.50 first priced, because the
corner does four fifths of the work. That version was built, gated, and **rejected by JP on the one
line he had held all night: the case stays flush at 39.00.**

So the final answer went the other way — take the **divider** instead, since he had already granted
"or modify it". Every alternative was measured before that call, and **none closes at 39.00**:

| construction | why it fails |
|---|---|
| corner solid, axis-aligned | **−0.73 mm** — and no rotation satisfies both bounds |
| midframe straddle | **−0.21 mm** |
| upper compartment | fits, but puts the body **74.70 mm of tab-path** from the far seat: **52.08 mm of new nickel** against 23.25 of surplus |
| growing the case | works, and costs the flush envelope |

*Four of those are arithmetic and the fifth is a value judgement. Only the owner could make the
fifth one, and he did.*

---

## 7c · The divider is two stubs now, and the chamber is open to the bay

**Recorded as a decision, not an oversight**, because it is the largest deliberate compromise in
the design.

```
KEPT   y 20.20 .. 30.00   and   74.80 .. 88.48      (9.80 and 13.68)
GONE   y 30.00 .. 74.80                             (the chamber's span — the strip's home)
```

The divider was always **one wall doing two jobs**: the cell trough's inboard wall *and* the sealed
speaker chamber's −X wall. Deleting its middle means that **over y 30.00 .. 74.80 the chamber and
the cell bay are one volume.**

**The stubs are not decoration.** A rigid 65 mm cylinder located in +X at *both ends* cannot migrate
mid-span, so the cell keeps its lateral datum without the wall that used to provide it. They also
keep the screw lane's derivation subject — its counterbore still stops at the divider's base — and
give the internal labyrinth a root.

**What it costs, measured rather than asserted:** the opening is **584 mm²** against the grille's
**562.7 mm²** — so it is **a second mouth roughly the same size as the intended one, not a leak** —
and the front chamber goes **15438 → 19199 mm³, +24 %**, which the acoustic check still passes with
2.1 % to spare. Residual costs on the record: the strip's 0.15 mm tabs now sit in the driver's front
chamber, grille-borne dust can reach them, and the chamber is L-shaped in a way the box-mode
arithmetic does not model.

> **Check 7b now REPORTS two deliberately-open sides with their areas, instead of asserting walls
> that are deliberately gone.** That is the honest form for a check whose subject has been removed
> by choice: an assert would have to be deleted or weakened, and either reads as an oversight later.
> A report cannot rot into a false guarantee.

### The owner was told twice, and reaffirmed twice

> **"no strip and nickel lay besid ethe batteyr like i toild you"** ·
> **"you can delete that inner wall it's fine"** · **"or modify it"**

The sequence matters. The deletion was first granted on the premise that *the band would be empty*
with the strip in the bay. A tangency measurement then briefly falsified that premise — and the cut
was **held rather than run on a dead premise**. When the corner-solid pocket made the band genuinely
empty, the premise was true again and the cut went in. *A standing instruction was not treated as
standing authority while its reason was in doubt.*

## 7d · ⚠️ A retraction: the wall was never the boundary

Before that deletion was granted, it was argued *against* on the grounds that removing the
chamber's low-Y wall would "open the cavity into the interior the cell bay and board cavity share."
**JP challenged it. He was right, and the argument was wrong.**

A flood fill of the **assembled** stack settles it — subtract midframe and cover, screws modelled,
from a box past the case, and the solid modeller returns **one interior air component**: speaker
cavity, retention band, cell bay, upper compartment, board cavity **and the outside**, all
connected. Plug the grille and it is still one. Delete the wall and it is still one.

**The topology does not change, because the SPK relief already joins the cavity to the board
cavity** — and the design's answer to *that* has always been a hand-applied plug, applied on every
build.

> ⭐ **The mistake, stated so it is reusable: I read a wall as the boundary, when the boundary is a
> wall PLUS a manual step.** The model contains the wall. It does not contain the silicone. Any
> claim about sealing that is checked against geometry alone is checking half the seal — and the
> half it checks is the half that cannot be forgotten during assembly.

A second error was on its way and worth recording as well: the argument was heading toward
*cancellation* — two mouths interfering destructively. **That is wrong too.** Both mouths carry the
driver's **front** output, so they **sum**. Being wrong about the direction of an acoustic effect
while being wrong about the topology it depends on is two mistakes that would have looked like one
conclusion.

**What the wall actually bought was measurable all along**, and once measured the decision became
easy rather than contested: a 584 mm² second mouth, +24 % of front chamber volume, and three named
residual costs. *The disagreement was never about acoustics. It was about whether anybody had
measured the thing being argued over.*

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
| Front air, **box-mode** | **15437.8 mm³** | 15621.3 mm³ |
| Δ | **−1.2 %** | — |
| Cavity | 30.10 × 44.80 × 19.40 | 54.00 × 15.30 × 33.00 |
| Governing first mode | **3828 Hz** | 3176 Hz |
| Grille field | 946.6 mm² (identical by construction) | 946.6 mm² |
| Grille throat | **562.7 mm² in 31 openings** (59 % of field; lattice ceiling 63 %) | — |
| vs driver radiating area | **80 %** of ~700 mm² | — |
| Port length | 2.20 = the cover's own wall | 2.20, by thinning a 4.0 wall |

> ⚠️ **THE FRONT-AIR FIGURE IS NOW A BOX-MODE NUMBER AND NO LONGER DESCRIBES THE REAL CHAMBER.**
> Read it as a *comparison against the desk stand on identical arithmetic*, which is what it was
> always for — not as the volume of air actually in front of the diaphragm.
>
> The chamber's −X wall is deliberately gone over y 30.00 .. 74.80 (§7c), so the build now reports
> `[chamber] closed on 2 sides` — high-Y and the case wall. With the wall out, the real front volume
> is **≈19199 mm³, +24 %**, and the chamber is **L-shaped**, which the `c/2L` box modes above do not
> model at all. The check still passes with 2.1 % to spare, and passing is not the same as
> describing.
>
> **This is the honest state, not a gap waiting to be filled.** A closed-form mode figure for an
> L-shaped volume with two open sides is not something to invent; measuring it needs a different
> instrument than arithmetic. What the numbers above *do* still support is the comparison they were
> built for, so they stay — labelled as what they are.

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
| Window | **2 hex cells**, high-X wall, y **31.35 .. 42.64**, z **−6.60 .. −2.10** |
| Size | **4.50 mm across flats** (the Z extent), 5.196 across corners |
| Membrane | **0.80 = two passes of a 0.40 nozzle**, measured **100.0 % intact**; control inside the pocket 0.0 % |
| Cut from | the wall's **inner** face — the outside stays flat and unbroken, so the hexes are invisible until lit |

`GLOW_MEMBRANE` is **not a layer count**: this wall is vertical in the print, so the criterion is
extrusion width, not layer height.

**The site is solved, not typed** — and it has since moved on its own, which is the best evidence
that the solving is real. The LED's own Y lands inside a cable channel on *both* walls, so "put the
window at the LED" was never available. `_glow_site()` searches the solid spans between channels for
the nearest one that can hold the window, so if a connector moves the window follows instead of
quietly opening into a hole.

### The window relocated itself when an unrelated opening was blocked

JP ordered the `BAT` flank opening blocked on both variants, and the mobile **also** blocks its
`SPK` flank opening, because its speaker is internal and that opening had nothing left to serve.
The mobile therefore computes its own channel set — `side_channels("mobile")` — rather than reusing
the desk's, and blocking `SPK` merges what had been a channel at y 31.54..41.19 into the solid span
above it. The span grows from `(0.00, 31.54)` to `(0.00, 43.84)`, and the search relocates:

| | Before | After |
|---|---|---|
| Window centre | y 24.52 | **y 36.99** |
| Straight-line distance to the LED | 30.00 mm | **23.02 mm** |

**A 12.30 mm move, and a 23 % shorter light path, from a change made for wire routing.** That is a
free improvement — it can only help the brightness caveat below — but note carefully *how* it
arrived: `_glow_site()` returns a different answer and **nothing announces it.** The only assert on
that path fires when *no* span fits; a span that fits *differently* passes in silence. It is the
same shape as the `GLOW_R` regression below, with the sign reversed. The lesson is not "pin it" —
the search is doing exactly its job — it is that **a derived position needs its value printed, so
the next opening change cannot move it unnoticed.**

### ⚠️ Pinned, not shared — a cross-part regression, and it took two goes

`GLOW_R` was written as `HEX_R`, "the same cell as the grille". When the **desk stand's** grille was
re-parameterised 4.50 → 4.75 mm across flats for printable webs (#47), this window — **in a
different part** — silently inherited the change and stopped fitting its 5.50 mm cavity band. The
module-level assert fired at 4.75 against a 4.70 limit and the export gate refused to write the
STL.

**A window's size is set by the band it lives in, not by another part's lattice.** It is pinned at
exactly 4.50 now; the motif survives, 0.25 finer than the grille it used to match.

**And the first fix was half a fix.** `GLOW_R` was pinned while `GLOW_WEB` was left as `HEX_WEB` —
one line below, the same coupling, pointing the same way. So the web had silently gone 0.90 → 1.25
with the same #47 change, taking `GLOW_SPAN_Y` to 11.64 and quietly widening the span the site
search has to fit. No assert covered it because the web is not what the cavity band constrains.
`GLOW_WEB` is now pinned at **0.90** in its own right — the repo's print floor, this part's own
number — and the span is back to **11.29**. `HEX_WEB` stays 1.25 in the desk model, where it
belongs; the desk grille is unchanged.

*Two pins in one feature, from one upstream edit, found weeks apart. When a constant is shared
across parts, fixing the instance that fired is not the same as fixing the coupling.*

> ⚠️ **soft — brightness is filament-dependent, and in the specified charcoal this will be dim.**
> `PRINT-SHEET.md` records that white/natural PLA is translucent enough for the WS2812 to light the
> shell itself. Three options, each one constant: print the midframe in natural PLA; drop the
> membrane to 0.40 (one extrusion); or take it to 0 for true through-holes — which adds no ingress
> class this wall does not already have, since it still carries two open cable channels.

⚠️ **This feature is on the midframe, not the cover.** Any previously sliced midframe gcode is
stale.

---

## 9b · Cooling the chip, which is not the same as cooling the cell

New in this round, and it starts with a measurement rather than an assumption: **the ESP32-S3 was
located in the vendor solid, not guessed at.** It is the only 7.01 × 7.01 × 0.90 back-side solid in
the STEP — a QFN56 at x 20.51..27.52, y 61.11..68.12, z −2.50..−1.60.

The desk case vents that footprint through its hex field. **The mobile cannot**, and the reason is
exact rather than approximate: **the speaker's bond plateau refills precisely that footprint**, and
the sealed cavity sits behind it. Venting the back face would open the acoustic cavity. So
back-face cooling is not a trade-off here, it is **forbidden**.

That leaves one viable field — **bores through the +Y end face into the board cavity** — and it
comes with an orientation constraint the project has already paid for once: the cells are
**flat-top in Z** (60° shoulders, 2.74 crown), because vertex-up would put a 30° face on them,
which is issue #28's droop exactly.

A side-wall field was evaluated and **fails on 0.05 mm**: the cavity band `CAV_FLOOR..PCB_BOT` is
5.50, and a 4.75 AF cell under this file's own 0.80-margin rule needs ≤ 4.70. Recorded because
"we could put vents in the side wall" is the obvious next suggestion and the arithmetic has
already answered it.

> ⚠️ **This does not close the thermal item in §14, and should not be read as doing so.** It cools
> **the processor**. The cell bay's heat path is a separate problem with a separate answer, and
> blocking the flank openings made that one *tighter*, not looser.

---

## 9c · Light out the top — and a vent that could not be a hole

Three more openings landed with the strip work, and one of them is the most interesting geometry
argument in the file.

**The LED-side through field** — 5 real bores on the +X side of the boss, into the upper
compartment. This is JP's alternative to the glow window's dim membrane: take the light out of the
*top* instead. The compartment has been empty of electronics since the strip moved out of it, so the
chain is atmosphere → compartment → board cavity via the wire pass, and **no volume with a rule is
crossed.**

**A blind field on the battery side**, cells only, no bores. Its cell count carries a trap worth
naming: **`TOPMESH_N_MIN` exists because a field of one is a valid field.** A count assert that only
checks for "some" cells passes on a lattice that has collapsed to a single hole, which is the same
vacuity that has bitten this project's grille counter before.

### ⭐ The internal vent could not be a hole, and the angle is why

With the top field bored, the upper compartment is **open to the sky**. So a plain hex through the
divider would put outside air **one straight line** from a lithium bay. That is not hypothetical and
it was not argued — it was traced:

> a ray from a top cell at **x 30** to a divider hole at **x 20.65** leaves the top bore at
> **41°**, against a bore that only collimates to **65°**.

The ray gets out. So the internal vent is §8's labyrinth moved into the divider — 1.30 from each
face of the 2.00 wall, 0.60 band — and **check 19c proves the no-sightline on the artifact, with a
drilled-through control.**

⚠️ **And it is offset in Z, not Y**, which is a packaging consequence rather than a preference: the
divider's free Y window between the seal rim and the top boss is **5.08 mm — one cell wide, not
two.** It is **19.40 tall**. So the pair stacks vertically. *When a feature will not fit along the
axis you reach for, check whether the other axis is 19 mm deep.*

### The microphone bore is deleted — and its label went with it

On the desk case the back face is the exposed one and that bore is how the microphone hears. On the
mobile it is buried under the backpack, where it is just a **7.07 mm²** hole from the board cavity
into the upper compartment. So it is gone on this variant only.

**The label went in the same change, under one condition rather than two.** A back face reading
`MIC` over no bore is this project's founding hazard — *the same lie told in ink* — and the two are
now cut from one decision so they cannot drift apart.

It also corrected a claim made an hour earlier: the LED wire pass was **not** the first aperture
between those two volumes. *The mic bore had been there the whole time.* A new opening was described
as unprecedented by someone who had not looked for precedent.

## 10b · It did not dock, and the stand is what had to give

The backpack is meant to sit in the desk stand when it is at a desk. **It did not fit**, and
nothing had noticed, because **check 8i had never actually executed.** Its first real run
returned **121.784 mm³** of interference — cover against the stand's rear top edge.

Two things about that are worth more than the fix.

**It was pre-existing on `main`, and worse there.** This is not a regression the retention work
introduced; it is a collision that had been true for as long as there had been a backpack, sitting
behind a check that reported nothing because it was not running. A check that has never fired and a
check that passes are indistinguishable from the outside — see
[`verification.md`](verification.md) §28, which is the same shape one step further along.

**The cover could not yield, so the stand did.** The interference is **mid-height on the cover's
chin end face and full width** — cover y 18.00..20.06, z −26.44..−17.37 — not a corner nick that a
bevel could take off. The cover's bottom wall there is 2.20 with the leaf's 0.35 kerf behind it, so
it can give up **0.60 and no more**. There is no cover-only fix, and no fix at all that leaves the
stand untouched.

So the stand gets a relief: **`DOCK_RELIEF` 13.00 × 4.40** on its rear top edge, **sized by
bisection against the real docked stack** rather than guessed —

| relief | interference |
|---|---|
| 6.00 × 2.00 | 96.6 mm³ |
| 9.00 × 3.00 | 28.8 mm³ |
| 10.00 × 3.50 | 7.8 mm³ |
| **13.00 × 4.40** | **0.000 mm³** |

— and check 8i is now a **hard zero** assert rather than a threshold. That is 250 mm³ removed from
a part of over 100 cm³: **a quarter of a percent of the stand, to admit a device that did not exist
when its slot was drawn.**

> ⭐ **The part that had to give was the one whose assumption was oldest.** The stand's slot was cut
> for a slab — the desk case, 17.40 mm thick — and it was cut before the backpack existed to be
> docked. Every later part inherited that opening as though it were a fact about the world. It was
> a fact about a decision, and the decision predated the requirement. When two parts cannot both be
> right, *the one to change is not the newest one, it is the one carrying the stalest premise.*

⚠️ The stand is therefore at **r5** and needs reprinting for anyone who docks a backpack. A desk-only
build is unaffected by the geometry but will still show the rev bump.

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
| Envelope | **55.90 × 93.63 × 39.00** (desk 55.90 × 91.90 × 17.40) — **flush, and it held** |
| Volumes | midframe **20.96 cm³**, cover **23.43 cm³** |
| Mesh | midframe **24 510** tris, cover **6 390** — both **0 boundary, 0 non-manifold, watertight** |
| Board interference | midframe **0.000**, cover **0.000**, cell phantom **0.000** mm³ |
| Interference controls | cover +22 mm → 1261.0 · midframe +2 mm → 199.1 · cell +12 mm → 1884.8 mm³ |
| Dock | mobile stack vs the stand **0.000 mm³ CLEAR**; control sunk 2 mm → 1332.9 mm³ |
| **Strip** | 1S PCB **21.50 × 4.50 × 2.50 — all JP-measured**, plus the 90.0 flat assembly. **No placeholders left** |
| **Tabs** | **34.25 per side.** −Y: 22.62 run + 11.63 fold · +Y: 22.62 + 11.62 — **3.2 limbs each end** |
| Cell + leaf | bay **66.75** on a folded leaf: shortest 64.9 → fold at 1.85 (preload **1.75**), longest 65.5 → 1.25 (**0.50 off closed**). Both fit |
| **Chamber** | **closed on 2 sides** (high-Y and the case wall) — *reported, not asserted*; control inside the cavity 0.0 % |
| Seal rim | 100.00 % solid; control on the open vent field 37.21 % |
| Front air (box-mode) | 15621.3 → **15437.8 mm³ (−1.2 %)** — ⚠️ see the caveat in §9; the real chamber is L-shaped and ≈19199 mm³ |
| Grille | **31 openings, 562.7 mm² throat** over a 946.6 field (59 %, ceiling 63 %); 80 % of driver area |
| Retention | 2 × **M3×22**, lane x 23.55, y 22.60 and 85.98 (**63.38 baseline**); both bosses on solid floor |
| Screw | under-head at both sites; head z −28.30, **3.40 mm engaged in a 6.60 mm pilot** |
| Counterbores | chin annulus 1.60, seat 100.0 %, control outside the boss 48.3 % · top 1.60, 100.0 %, control 38.2 % |
| Collar | both pilots have a full **1.60 mm collar**; control in the open hex field **35 %, rejected** |
| **Ease** | battery edge **R 3.00** — 1.76 across the bed face, 3.00 up the side, **1.87 mm of wall at the diagonal** (floor 1.60, ceiling R 3.65) |
| **LED wire pass** | one 4.75 hex at (32.0, 80.5) through the midframe floor, **100 % open** (control on solid floor 0 %), 0.60 edge break at the cavity mouth |
| **Top mesh (blind)** | **5 blind cells**, 0.60 deep in the +Y end face over x 5.10..17.45, z −27.90..−10.90; **100.0 % membrane behind it** (1.60 mm) |
| **Top vent (through)** | **5 real bores** on the LED side of the boss, x 29.65..44.90 — the LED's window as much as a vent |
| **Internal vent** | cell bay ↔ LED compartment, 1.30 from each face of the 2.00 divider, 0.60 band; **notches at z −22.50 and −16.55, both at y 79.00** — stacked in Z, not Y |
| Cell-bay vent | 4 units, **16.56 mm² throat vs 9.42 assumed (1.76×)**; band 0.60 × 6.90, skin 0.80 each face |
| Min feature | floor 1.60, 10 sections; control — #47's failed 0.90 web — **rejected** |
| ⚠️ Exempt | **1.25 lattice web — UNVALIDATED, deliberately shared with the stand's grille** · 0.80 glow membrane · 0.80 vent skin · 0.15 detent (meant to deform) |
| Print frame | as-printed = model frame (pure Z lift); end-vent shoulder **60.0°**, control (#28's vertex-up) **30.0° rejected** |
| Marks | `+` on the +Y bulkhead's bay face (y 86.95); `−` on the cover's **mating face** (y 19.10) |
| Glow | 2 cells, hi wall, `GLOW_CY` 36.99 (y 31.35..42.64), `GLOW_DIST` 23.02 |
| BAT lead pass | open (0.0000 mm³ blocked); control on solid floor blocks 51.5 mm³ |
| Bed contact | cover **3178.1 mm²**, midframe **4057.6 mm²** |

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

   ⚠️ **And it just got tighter.** Blocking the `BAT` and `SPK` flank openings removes side
   channels from the *last leg* of exactly that path. The blocks are right for wire routing and
   for ingress, and neither reason is thermal — so this item is now carrying a cost it did not
   carry when it was written, and the cell-bay vent (§8) is doing correspondingly more of the work.
2. **Protection is unbuilt electrically.** The pocket exists and the schematic proves the need.
   No strip has been fitted, no firmware cutoff written.
3. **Reverse insertion is unprotected** — markings only (§5).
4. ✅ **Closed: the strip is fully measured.** All three body dimensions plus the flat assembly are
   JP-calipered (21.50 × 4.50 × 2.50, flat 90.00). This was the longest-standing soft number in the
   design and it is gone — see §7b for the four days it took, and for the two correct measurements
   that pointed at wrong conclusions on the way.
5. **The 1.76× vent ratio** inherits an assumption about the cell's own port area (§8).
6. **The front-gap redistribution** is a declared belief (§9).
7. **Glow brightness in charcoal** (§10) — though the window's relocation shortened the light path
   by 23 %, which can only help.
8. **~0.30 mm of cell slop**, unmeasured because there is no cell in hand (§5).
9. **No graceful shutdown** without a boost (§6).
10. **Nothing has been printed to completion and nothing wired.** Both parts show
    `printed_at: null`; one cover print was cancelled at 2 % (see the banner at the top).

### ✅ Closed since the first draft

- **Cover top-edge gap.** The old hook scheme anchored only the bottom edge, so the top ~70 mm
  leaned on the cover's own wall stiffness and the divider, and nothing but a test print could
  settle it. It is closed now for a different reason than the one that first closed it: retention
  reaches **y 85.98** at the top, and the edge between the two screws is carried by the cover's
  **21.60 mm closed box section** rather than by fasteners. The worst unheld point moved to the
  **+X long edge** — 43.19 mm at (52.95, 54.34) — so the question did not disappear, *it moved to
  a different edge and got smaller.* Reopen it there, not at the top, if a print gaps. *Recorded as closed rather than
  deleted, because the reason it closed is the interesting part: it was retired by a change made
  for printability, not by anyone attacking the gap.*

---

## See also

- [`enclosure.md`](enclosure.md) — verified board geometry and the case survey. Everything there
  about the board applies unchanged.
- [`verification.md`](verification.md) — the running log of claims that outran their evidence.
- [`vendor/README.md`](vendor/README.md) — the schematic and what it settles.
- [`../enclosure/PRINT-SHEET.md`](../enclosure/PRINT-SHEET.md) — desk parts only; see §11.
