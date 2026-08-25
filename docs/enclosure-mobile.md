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
| Envelope | **55.90 × 91.90 × 39.00 mm** | 55.90 × 91.90 × 17.40 mm |
| Thin section (y < 18.00) | 17.40 mm — unchanged | 17.40 mm |

Width **cannot** move: the bezel is untouched. **And length no longer grows at all** — §1 is about
how that closed after three revisions of it not closing.

---

## 1 · There is no lip. The envelope is the desk case's, to the hundredth.

```
55.90 × 91.90 × 39.00        mobile
55.90 × 91.90 × 17.40        desk
```

**Y is identical.** `MOB_OY1 == OY1 == 88.95`, asserted exactly — the backpack is the desk slab's
footprint with depth behind it and nothing else. Width never could move, because the bezel never
moved. Length now doesn't either.

> **JP: "no litle lip in backpack figure it out pls."**

That instruction arrived after three rounds in which the case was 3.05, then 1.32, then 1.73 mm
longer than the desk profile, each time for a reason that was correct at the time — the coil
spring, then the corner fillet the coil had been paying for by accident, then the strip's own
housing.

### How it closed: the conflict was MOVED, not reshaped around

Every earlier attempt had tried to *fit* something into the contested corner. This one moved the
contest instead:

| | |
|---|---|
| `CELL_WALL_X` | **3.678**, given its own name — it had been two separate jobs of `COV_WALL` |
| `NOLIP_ROLL` | **0.30** on the void's plan corner |
| Divider | **1.60** |
| Driver | **+1.078** to `DRV_CX` 36.778 — which lands it *centred* in its usable span |

⭐ **And one of those numbers is a derivation beating an estimate.** `NOLIP_ROLL` is 0.30 because
that is `CELL_BORE_CLR` — the **seat guarantee**: at any radius above 0.30, a cell with no roll of
its own cannot seat. JP's suggestion was *"~0.5mm"*, a visual estimate from the render. **The bound
wins, and it wins by being a bound rather than a preference.** His eye had been right four times
this week about *where* to look; this is the case where the arithmetic was right about *how far*.

### The assert that makes the lip's return audible

The plan-view bound that killed every earlier shape now reads closed, and it is asserted **both
ways** — cut-available ≥ bezel-need, *and* `MOB_OY1 == OY1` exactly.

> **If either fires, the failure message says "the lip is back" in those words.**

That is the right shape for an assert guarding an *aesthetic* requirement the owner stated in
plain language. A numeric tolerance failure would be true and unreadable; this one fails in the
vocabulary the requirement was given in.

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
3. **Route the driver's leads** through the SPK relief. ⛔ **Then seal that relief** — silicone, hot
   glue or putty. It opens into the sealed cavity, and it is asserted to lie *wholly inside* the rim
   rather than straddling its wall, because a straddled opening cannot be sealed at all.
   ⚠️ **And note what §7d says about that plug: it is half the seal, and it is the half the model
   cannot see.**
4. **Fit the board and bezel** exactly as the desk build.
5. **Drop the bare cell on top of the seated strip.** Both ends land on leaf springs. There is no
   plate to orient against any more, so read the debossed marks — and see §5 for why they are not
   mirror images of each other.
6. **Seat the cover and drive both M3 screws.**

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

## 7c · The wall came back — and it took six positions to get there

The divider is whole again, plus a **separator wall JP designed himself**, and this section has been
rewritten more times than any other in the file. That is the record, not churn:

| | the wall was | why |
|---|---|---|
| 1 | present | one wall doing two jobs — cell trough and chamber |
| 2 | deletion granted | "the band is empty with the strip in the bay" |
| 3 | **held** | a tangency measurement falsified that premise; the cut was *not run on a dead premise* |
| 4 | deleted | the corner pocket made the band genuinely empty again |
| 5 | middle removed, two stubs | the strip needed the span, and flush would not close any other way |
| 6 | **whole, plus a double separator** | JP's own construction, once he saw room for it |

**Every one of those six has a stated reason and a measurement behind it.** A design that moves six
times under measurement is not indecisive — it is one where nobody was allowed to guess.

### ⚠️ A correction to what this document said at position 5

The previous version of this section reported **one** opening, 584 mm², and called it *"a second
mouth roughly the size of the intended one."* **That was incomplete, and the reason is worth more
than the correction.**

Check 7b was printing the divider's **cross-section** — 2.00 × 19.40 = 39 mm² — as the opening the
wall left behind. But the opening is the face the wall **vacated**: its Y span by its height,
**869 mm²**. *Off by 22×, in the one number the owner judges the acoustic trade by.*

> ⭐ **A wrong area is worse than no area, because it gets trusted.**

With the right figure the trade read differently: **869 against the grille's 562.7 — half again the
chamber's intended mouth — on top of the low-Y wall's 584.** The intended mouth was the *minority*
of the aperture, and the cell and the BMS were inside the acoustic volume. **That is a materially
different decision from the one this document described**, and it described it in good faith from
the number the build printed.

*It is corrected here rather than quietly overwritten, because a document that silently starts
saying something else is the same hazard one layer up from the check that misreported.*

### The separator wall, and the thinnest solid in the family

The −X opening now measures **0.000**. JP's construction is a **double wall**: a partial wall, plus
a stepped full wall at **0.90** that thins to **0.50** in the band beside the strip.

**Both are below the 1.60 minimum-solid floor and both are recorded as experimental**, with the
distinction stated rather than blurred:

- **0.90 (2.25 extrusions)** — under the floor, but a **vertical wall supported along its whole
  44.80 mm bottom edge** is a different class from #47, whose collapsed 0.90 was an *unsupported web
  spanning a bore*.
- **0.50 (1.25 extrusions)** — **the thinnest solid in this family**, thinner than an already-flagged
  label groove is *wide*. ⭐ **Its thickness is set by the strip, not chosen:** 0.50 is the entire
  lane between the strip's +X drift and the driver's locating groove. There was no number to pick.

> **Cost of failure, stated because it is what makes the experiment acceptable:** a floppy or absent
> wall, trimmable with scissors. **Nothing structural depends on it.** That is the difference between
> an experiment and a gamble — and *the print is the verdict*, exactly as the 1.25 web was.

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
| Front air, **box-mode** | **13718.5 mm³** | 15426.1 mm³ |
| Δ | **−11.1 %** | — |
| Cavity | 30.10 × 44.80 × 19.40 | 54.00 × 15.30 × 33.00 |
| Governing first mode | **3828 Hz** | 3176 Hz |
| Grille field | 946.6 mm² (identical by construction) | 946.6 mm² |
| Grille throat | **562.7 mm² in 31 openings** (59 % of field; lattice ceiling 63 %) | — |
| vs driver radiating area | **80 %** of ~700 mm² | — |
| Port length | 2.20 = the cover's own wall | 2.20, by thinning a 4.0 wall |

> ⚠️ **The chamber is closed again, so this figure describes a real box once more — but it moved a
> long way, and the movement is the news.** It was −1.2 % for three revisions. It is now **−11.1 %**,
> because the separator wall and the driver's re-measured 27.5 width both take volume out of the
> front chamber.
>
> **That is a real acoustic cost, not a bookkeeping change**, and it is worth separating from the
> period when this number was merely *wrong*: at position 5 the wall was gone, the chamber was
> L-shaped and open on two sides, and the box-mode arithmetic did not describe it at all. Now the
> box exists, the arithmetic applies, and the answer is simply worse than it used to be.
>
> The check still passes — its tolerance is ±25 % — and **passing is not the same as unchanged.** An
> 11 % loss inside a 25 % band is exactly the kind of drift a threshold hides, which is why the
> figure is quoted rather than the verdict.

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

## 10c · ⛔ The near-miss that outranks everything else in this project

A "Z-tail" was ranked first among the no-lip options and briefed as five verified edits needing only
a new home for the internal vent. **It needed no new home. It was dead, and the already-exported
part said so.**

`_lip_ytop()` took the void's −X extreme to be the *bore's* at every height, symmetric in dz.
Slicing the **shipped** STL says otherwise:

```
z −25.70   wall 3.121   void x  1.58   ┐
z −23.30   wall 2.074   void x  0.07   ├ retreats going DOWN, as modelled
z −21.30   wall 1.563   void x −0.56   ┘
z −19.40   wall 1.405   void x −0.75     the cell axis
z −11.00   wall 1.404   void x −0.75   ┐ DOES NOT retreat going UP
z −10.30   wall 1.404   void x −0.75   ┘ flat to the mating plane
```

**The bore is a cradle, not a tube.** An 18650 loads straight down, so the lane stays full bore
width from the axis to the mating plane. Had the tail been cut, the profile would have left

> ### 0.296 mm of shell over a lithium cell.

⭐ **And the only thing that stopped it was an assert aimed at something else entirely** — the vent's
module-level check, which fires *before any solid exists*. **No check in this file was ever going to
see it.** The geometry that would have shipped was caught by accident, by a guard for a different
feature, at a stage where the part it would have ruined had not been built yet.

*Every other defect in this document was found by a check doing its job. This one was found by a
check doing someone else's.*

### Two real defects in the shipping part, found on the way

**The vent assert measured across the FLATS of a shape presenting its CORNERS.** The notch is drawn
flats-on-Z deliberately — it is a horizontal bore, and vertex-up is issue #28 — so it is the
**vertices** that lead in Y: `2 × LAT_R` = **5.485**, not `LAT_AF` = 4.75. At y 79.00 the notch ran
76.258..81.742 against a 76.40 rim line and **broke 0.142 into the sealed chamber's rim wall**,
thinning a 1.60 seal wall to 1.458.

> ⭐ **An invariant insensitive to its own failure.** It was not silent because nobody looked. It was
> silent because it was measuring the wrong extent of the right feature — and the number it returned
> was correct for the extent it measured. *This is the flats-and-corners twin of the corner-solids
> lesson: same shape, opposite direction.*

**And the same assert bounded a cylinder by its bounding box** — a d9.00 column on a lane nowhere
near the divider, reported as adjacent because a box is not a circle.

The fix is the lens rather than the number: **check 7d now sweeps nine planes instead of one**, the
worst plane is cross-checked against the solid, and the control fails if the sweep cannot tell the
cradle's open bottom from its full-width top. In morpheus's own words — **that is the lens that was
missing.**

### The same round: a typed constant quietly degraded a safety property

`IVENT_D` was typed as *"1.30 from each face of the 2.00 divider."* **The divider became 1.60.** The
band silently grew to 1.00 and **the no-sightline figure fell to 19 %** against a 25 % floor — on the
labyrinth whose entire purpose is that outside air has no straight path to a lithium bay.

It is derived now — `(DIVIDER_W + 0.60)/2` — so the proven 0.60 band holds by construction. Two
siblings were converted with it: `TOPMESH_D` (typed 0.60, assumed a wall band the contact kerf had
since bounded; derived to **0.40**) and its membrane probe, re-anchored to the *feature* rather than
the coordinate.

> ⭐ morpheus-final's parting line, and this round is its proof:
> **"a threshold you typed is a guess wearing an assert's clothes."**
>
> Its companion belongs beside §7d: **"constants describe intent; booleans describe the part."** The
> constant said *wall*. The boolean said *one volume, including the outside*. The constant said
> *1.30 of each face*. The solid said *19 %*.

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

## 11b · Seven exemptions, and they are not one class

The minimum-solid floor is 1.60 and seven features sit below it. **Lumping them together would be
the single easiest way to lose the safety content of this file**, so the reasons are kept separate:

| thickness | feature | why it is exempt |
|---|---|---|
| **1.25** | top fields, horizontal bores | clear of #47's *measured* 0.90 collapse — but see the note below |
| **1.25** | LED wire pass · internal labyrinth | **functional apertures**, sized to pass a 3-wire pigtail and to collimate — not decorative fields |
| **0.90** | separator wall, full section | a **vertical wall supported along its whole 44.80 bottom edge** — a different class from an unsupported web spanning a bore. **Experimental** |
| **0.80** | blind deboss web | the back grille's own, and **that field printed on JP's r1** — but proven only for *vertical prisms in a bed face*; exempt here because a 0.60 surface relief **has no rib to lose** |
| **0.80** | glow window membrane | a face **backed by wall on all four edges** — not a standing rib |
| **1.54** | vent labyrinth skin | same class as the membrane |
| **0.50** | separator wall, thinned band | **the thinnest solid in the family.** Set by the strip, not chosen. **Experimental** |
| **0.15** | contact detent bar | it is *meant* to deform past the plate |

**Three different justifications are doing work there** — *proven by print*, *structurally a different
class*, and *not load-bearing at all* — and only the first is evidence. Writing "the thin features are
exempt" would erase that.

### ✅ Resolved: the 1.25 validation transfers, and the argument is span-monotonicity

The build's report briefly said two things about one constant — that the 1.25 web was *"still
UNVALIDATED at this cell size"* and, four lines later, that it was *"validated on r10."* **Both
cannot be the operative reading of a safety exemption**, so here is the single one, with the
reasoning attached rather than asserted:

> **Web collapse is governed by the unsupported SPAN each web bridges.** The web is the *printed
> feature*; the cell size sets the *span*. JP's r10 bench verdict — **"clean — webs crisp"** —
> validated 1.25 webs at **4.75 AF spans**. Every current field runs **the same web at shorter
> spans**: 3.20 on the top fields, 4.00 on the dock. A shorter span is **strictly easier**.
>
> So: **1.25 is validated at 4.75 spans, and every field at ≤ 4.75 is covered *a fortiori*.**
> `UNVALIDATED` now applies only to a hypothetical future field with spans **above** 4.75.

**This is the same span-monotonicity argument this file already used for droop in #28**, applied in
the favourable direction rather than the punishing one — which is the point: an argument that only
ever gets used to reject is not being used, it is being deployed.

Two things worth keeping about how this resolved:

- ⭐ **It is the shared-constant decision paying off a second time.** Had `HEX_WEB` been pinned
  per-part after #47, r10's print would have validated *one obsolete cover* and nothing else.
  Because the web was deliberately shared, one bench observation covers every field in the family —
  including fields that did not exist when the part was printed. *Sharing is correct when the shared
  constant is the hypothesis.*
- **The transfer had to be argued, not assumed.** "The web is the same, so it's fine" is the right
  answer reached by the wrong route — it would have been equally confident had the spans gone *up*.
  The monotonicity is what makes the conclusion safe, and it is the part worth writing down.

*(The build's contradictory wording is a one-line source fix, queued for a gate window rather than
spending a full gate on a comment. This document carries the resolved reading in the meantime.)*

## 12 · Verification — what the build actually measures

Printed by `ember_mobile_case.py` on every run. Regenerate with the command in §13; do not
transcribe these by hand.

| Check | Result |
|---|---|
| Envelope | **55.90 × 91.90 × 39.00** — **Y identical to the desk case**, asserted exactly |
| Volumes | midframe **19.69 cm³**, cover **24.82 cm³** |
| Mesh | midframe **33 352** tris, cover **8 020** — both **0 boundary, 0 non-manifold, watertight** |
| Board interference | midframe **0.000**, cover **0.000**, cell phantom **0.000** mm³ |
| Interference controls | cover +22 mm → 1843.9 · midframe +2 mm → 205.4 · cell +12 mm → 1858.6 mm³ |
| Dock | mobile stack vs the stand **0.000 mm³ CLEAR**; control sunk 2 mm → 1332.9 mm³ |
| X budget | interior 51.50 = bore 19.40 + **divider 1.60** + rim 29.22; driver slack **0.92** |
| Cell + leaf | bay **66.55**: shortest 64.9 → fold 1.65 (**preload 1.95**), longest 65.5 → 1.05 (**0.30 off closed**) |
| Strip | 21.50 × 4.50 × 2.50 + the 90.0 flat — **all JP-measured, no placeholders** |
| Tabs | **34.25 per side**; each end 22.52 run + 11.73 fold = **3.3 limbs** |
| Chamber | **closed on 2 sides** (high-Y, case wall); **−X opening 0.000** with the separator in |
| Front air (box-mode) | 15426.1 → **13718.5 mm³ (−11.1 %)** — a real cost; see §9 |
| Grille | **31 openings, 569.8 mm² throat** over a 965.6 field (59 %, ceiling 63 %); **81 %** of driver area |
| **Driver outline** | witness ring **151.3 mm², cut 100 %, 0.40 deep on a 96 % solid baffle** (floor 83 %); control over the open field 32 %, rejected |
| **Side labels** | 3 on the flanks, h 3.90 / stroke 0.80 / depth 0.80, band z −0.80..3.90 |
| **Deboss depths** | **every depth derived** (JP: *as deep as we can*). Quantum is layer height 0.20 on horizontal faces, **extrusion width 0.40 on vertical walls** — *layer height does not govern a vertical wall* |
| Retention | 2 × M3×22, lane **x 24.63**, y 22.60 and 84.25 (**61.65 baseline**) |
| Screw | head z −28.30, **3.40 mm engaged in a 6.60 mm pilot** |
| Counterbores | chin annulus 1.60, seat 100.0 %, control 45.7 % · top 1.60, 100.0 %, control 38.2 % |
| Collar | full 1.60 mm collar at both pilots; control in the open field **53 %, rejected** |
| Ease | battery edge **R 3.00** — 1.76 across the bed face, 3.00 up the side, **1.87 mm of wall at the diagonal** |
| Top mesh (blind) | **7 blind cells** (100 % of the field), **0.40 deep** — derived, not typed — x 5.10..18.53; **99.5 % membrane** behind it (1.80 mm) |
| Top vent (through) | **7 real bores** on the LED side, x 30.73..44.90 |
| Internal vent | **1.10 from each face of a 1.60 divider**, 0.60 band; notches at z −22.50 and −16.55, both at y **79.47** |
| Cell-bay vent | 4 units, **16.56 mm² vs 9.42 assumed (1.76×)**; band 0.60 × 6.90, **skin 1.54** each face |
| LED wire pass | one 4.75 hex at (32.0, 80.5), **100 % open**; control on solid floor 0 % |
| Marks | `+` at y 86.50 (bay face); `−` at y **18.98** on the cover's mating face |
| Glow | 2 cells, hi wall, `GLOW_CY` 36.99, `GLOW_DIST` 23.02 |
| Bed contact | cover **3078.4 mm²**, midframe **3932.1 mm²** |
| Seal rim | 100.00 % solid; control on the open vent field 36.77 % |
| Min feature | floor 1.60; control — #47's failed 0.90 web — **rejected** |
| Exemptions | **seven**, and they are **not one class** — three different justifications, only one of which is evidence (§11b). The 1.25 web reads **validated at ≤4.75 spans**, *a fortiori* from r10 |

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

> ⚠️ **BYTE-IDENTITY PROVES THE FIGURE DID NOT CHANGE. IT DOES NOT PROVE THE PART DID NOT.**
>
> This release taught the distinction the hard way. The desk stand genuinely changed — `DRIVER_H`
> 27.0 → 27.5 measured off the physical driver, `DRIVER_CLR` 0.60 → 0.40 bench-corroborated — and it
> was *predicted* that all three stand-bearing figures would move. Two did. **`case-docked-rear.svg`
> came back byte-identical.**
>
> The reason is sound: that view looks at the stand from behind, the driver-derived changes are the
> chamber interior, the tape pad and the grille field, and hidden-line projection emits only *visible*
> edges. **Nothing the figure can see changed.** The front three-quarter hero and the flat print
> layout both moved, because they can see it.
>
> But it means an identical figure carries two possible meanings — *the part is unaffected*, or *the
> part changed somewhere this view cannot look* — and they are not the same claim. Byte-identity is
> still a good control for detecting **spurious** movement. It is **not** evidence that geometry is
> untouched. *Use it to catch the figures that shouldn't have moved, never to conclude the model
> didn't.*

⚠️ Both need the 17.7 MB vendor STEP, which is deliberately not committed and will never be in a
`git archive`/`clone` extract. See [`../enclosure/README.md`](../enclosure/README.md).

⚠️ `ember_mobile_case.py` does **not** refresh the print queue — only `ember_case.py` does. The
mobile queue entries are only as current as the last `ember_case.py` run.

---

## 13b · ⏳ Two experiments awaiting a bench verdict

Both are printed or printing. **Neither has a result yet, and neither is written as though it does.**

| experiment | what a verdict would settle | status |
|---|---|---|
| **The separator wall, 0.90 / 0.50** | whether a *supported vertical* wall survives below the 1.60 floor — and specifically whether 0.50, the thinnest solid in the family, prints as a wall or as a suggestion | ⏳ back r15 printing overnight |
| **The flank labels, the SD label and the driver witness outline** | whether debosses driven to *"as deep as we can"* read at arm's length, whether the below-floor SD groove forms at all, and whether the witness ring actually delivers tolerance-at-a-glance | ⏳ midframe r10 printed tonight; **inspection pending JP's morning** |

**Placeholders on purpose.** The temptation with a printed part sitting on the bench is to write the
result you expect — and the 1.25 web is the reason not to: that trial's outcome arrived as *"clean —
webs crisp"* from the owner's own eye, and it could as easily have gone the other way. **A predicted
verdict in a document reads exactly like a recorded one**, which is the whole failure family this
file catalogues.

⚠️ **The SD label is the one to watch.** It is deliberately *below* the printable floor —
authorised as an experiment — so "it did not form" is a **valid and expected outcome**, not a defect.
If it comes out illegible, the label is what fails, not the part.

## 14 · Open items, in rough order of how much they should worry you

1. **Thermal path out of the cell bay** — still the largest unresolved risk, and still not mechanical.
   The flank blocks tightened it; the top fields and the internal labyrinth now give the compartment
   a route to atmosphere, which helps the *chip* rather than the bay. The bay's own answer remains its
   failure vent.
2. **Two experiments below the minimum-solid floor** await bench verdicts — §13b. The 0.50 band is
   the thinnest solid in the family.
3. **Protection is fitted at board level — in-case fit is still unproven.** When this item was
   written it read *"no strip has been fitted"*; that retired on **2026-08-09**, when JP fitted 1S
   strips to both battery boards (`f240fe6` — the observation, dated per the §32 rule, which also
   scrubbed a live alarm message that would have announced the old fact as current). What this item
   still holds open is narrower and real: **the strip has never sat in this case's channel.** The
   channel, the leaf seats and the tab folds are dimensioned from JP's measurements but nothing has
   been printed to completion — the 2026-08-01 rib-spacing cancel is the only contact between this
   geometry and the physical strip. No firmware cutoff is written, and per the repo's standing rule
   none may ever be *called* the protection — the strip is.
4. **Reverse insertion is unprotected** — markings only, and §5 records that the *rationale* for their
   asymmetry expired when both ends became leaf seats. A measurement order is open on it.
5. **The 1.76× vent ratio** still inherits an assumption about the cell's own port area.
6. **Front air is −11.1 %** now, a real acoustic cost inside a ±25 % check band. Passing is not
   unchanged.
7. **~0.30 mm of cell slop**, unmeasured — there is still no cell in hand to measure the rattle.
8. **No graceful shutdown** without a boost.
9. **`LEAF_FREE` 3.60 is JP-tunable** — the one number in the design still set by feel rather than
    derived, and the only survivor of a long list.

### ✅ Closed since the first draft

- **The 1.25 web's exemption is resolved.** It read two ways in the build's own report; it now reads
  one, *a fortiori* from JP's r10 bench verdict by span-monotonicity (§11b). Closed by an argument
  rather than by a new measurement — the measurement already existed and was being under-used.

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

## 15 · Decision register — what the `needs decision` label is actually waiting on

*Added 2026-08-25.* Issue [#44](https://github.com/jphein/ember.realm.watch/issues/44) carries the
label; this section is the list it points at. Everything here already exists somewhere above — the
register's only job is to collect the calls **only JP can make**, each with its options and the
observation that would unblock it, so the label can be retired decision-by-decision instead of by
fatigue. Where a default is stated, it is what the model currently builds, not a recommendation.

### 15a · The issue's six electrical questions, reconciled

The issue body's ⚠️ block predates most of §6 and §7. Current status, so nobody re-opens a closed
one or trusts a closed-looking open one:

| # | question (as asked) | status | where |
|---|---|---|---|
| Q1 | Can `BAT` charge a cell at all? | ✅ **answered** — TP4054 on-board, with a power path | §6 |
| Q2 | At what current / correct CC/CV? | ✅ **answered** — ~290 mA (R12 3.3 kΩ), 15.8 h for 3400 mAh; in-case fast charge frozen **out** 2026-08-01, external bay charger instead | §6 |
| Q3 | Does the board protect the cell? | ✅ **answered** — no protection IC (schematic fact); 1S strips **fitted to both battery boards 2026-08-09**. In-*case* strip fit still unproven — §14.3 | §6, §7 |
| Q4 | Run while charging / brown-out on transition? | ◐ **half-answered** — the SL2305 + B5819W power path runs the system from VBUS while the cell charges, per the schematic. **The unplug transition is unmeasured** — a bench observation, one plug-pull with the device mid-response | §6 |
| Q5 | Venting / thermal path | ◐ **redesigned, not closed** — the cell-bay *failure* vent is built and measured (§8); the *steady-state* heat path is still open item №1 → **D1** | §8, §9b, §14.1 |
| Q6 | Reverse insertion | ◐ **moved, not closed** — mechanical keying is provably impossible on bare cells (§5); the live question is now **electrical, about the strip** → **D2** | §5 |

The issue body is also stale on five headline facts the register should not let anyone re-derive
from it: envelope (101.45 → **91.90**, the lip is gone, §1), cell policy (protected-cell bay →
**bare only**, §5), the TP4056 pocket (reserved → **frozen out**, §6), retention (hooks + one screw
→ **two screws + box section**, §3), and the rear LED (occluded, unsolved → **glow window built**,
§10). *The body should be updated from this document or explicitly superseded by it — reading it
as current is now a way to be wrong five times.*

### 15b · The decisions, in worry order

| | decision | options and their stated costs | what unblocks it |
|---|---|---|---|
| **D1** | **Print gate: does the cell-bay thermal path need a measurement before a full print?** The issue called this the biggest unresolved risk "needing a call before a print", and §14.1 still ranks it first. | (a) **accept for a first print** — charge is capped at ~290 mA (≤ 0.09 C on the assumed 3400 mAh, so self-heat is small by arithmetic, not by measurement), the failure case is §8's vent, and the first full in-case charge is bench-supervised with a thermometer in the bay. (b) **require a measurement first** — no print until a heat path is demonstrated or modelled. | JP's call. If (a): one supervised charge cycle with a probe in the bay converts the arithmetic into an observation. |
| **D2** | **Does the fitted DW01-class strip block a reversed cell?** Q6's remainder. The keying is gone for a proved reason; the marks are informational; the strip is now the only thing standing between a backwards cell and the board. | (a) strip datasheet states reverse-polarity behaviour → cite it. (b) bench test — reversed cell through the strip on a current-limited supply, nothing downstream connected. (c) accept marks-only and rely on the operator. | A datasheet or one bench test. Until one exists, §5's "making reverse insertion *safe* is electrical, and it is unbuilt" stays true *with the strip fitted*. |
| **D3** | **Vent sizing premise** (§8 soft, §14.5): the 1.76× margin is measured against an *assumed* 9.42 mm² of cell port area. | (a) name the actual cell SKU and take its real vent figure — the unit count is the stated knob if it moves. (b) accept the general-construction assumption. | Naming the cell. This also settles §5's slop (real ⌀/length) and the leaf preload figures in §12. |
| **D4** | **Bench verdicts JP already owes himself** (§13b): the 0.90/0.50 separator wall, and the deboss/SD-label/witness-ring legibility set. Not design decisions — *observations* — but two exemption classes in §11b are experimental until his eye rules. | Look at the printed parts. The SD label is allowed to fail; the 0.50 wall is allowed to be trimmed to nothing. | Parts are printed or printing; the verdicts are a morning's inspection. |
| **D5** | **Acoustic acceptance** (§9): front air is −11.1 % (real cost, hidden inside a ±25 % band) and the diaphragm gap went 2.50 → 9.40 on a stated *belief* that axial air trades neutral against lateral. | (a) accept and let the first print's listening test rule. (b) A/B against the desk stand before accepting. (c) reject — it is one constant, but reclaiming volume re-opens the §7b packing argument. | A listening test on the first assembled unit — the only instrument this repo has for it. |
| **D6** | **Glow in charcoal** (§10 soft): the window will be dim in the specified filament. | (a) accept dim. (b) natural-PLA midframe — fights the charcoal finish spec. (c) membrane 0.80 → 0.40. (d) through-holes (adds no ingress class the wall doesn't already have). Each is one constant. | Aesthetic call; (a) can be judged on the first print and revisited — the options don't expire. |
| **D7** | **Third cover screw at ~(46, 82)** (§3): would halve the +X worst unheld span (43.19 mm). Two screws is JP's stated cap; the constraint that used to forbid a third has moved. | (a) hold the cap. (b) lift it — one boss, one pilot, one more M3×22. | JP's call outright; or let the first print's gap (if any) decide — §14's closed item says *reopen at the +X edge, not the top*. |
| **D8** | **Cell radial slop ~0.30 mm** (§5 soft): shim, printed rib, or accept. | Foam shim (no CAD), rib (one feature + reprint), accept. | A cell in hand and a shake — explicitly blocked on D3's cell naming. |
| **D9** | **Low-battery behaviour** (§6, §14.8): no boost, so the device browns out at ~3.4 V rather than shutting down. The strip (fitted) is the safety floor; this is UX, not protection — and per the standing rule nothing in firmware may be *called* protection. | (a) accept brown-out; candle + ladder + battery_watch already warn. (b) add a firmware graceful *shutdown/announcement* — permissible as UX under that rule, never as the answer to Q3. | JP's call; the voltage sensor and the announce chain both already exist, so (b) is HA/firmware work with no case impact. |
| **D10** | **`LEAF_FREE` 3.60** (§14.9): the one number still set by feel. | Leave it, or let the first assembly's preload feel adjust it. | First assembly. Recorded so it isn't mistaken for a derived value. |
| **D11** | **Stand r5 reprint** (§10b): docking a backpack requires the relieved stand. | Reprint now, or defer until a backpack exists to dock. | Scheduling only; a desk-only setup is unaffected. |
| **D12** | **Mobile print sheet** (§11): `PRINT-SHEET.md` has no mobile column — the parts print on inherited shell spec plus this file's ⛔ slicer note. | (a) add the column before a print campaign. (b) keep inheriting and rely on §11. | A doc task, not a measurement — but the gap is the kind that bites the *next* person, not this one. |
| **D13** | **The issue body itself** (§15a): stale on five headline facts. | (a) rewrite the body from this document. (b) replace it with a pointer here and keep only the decision label. | One edit; (b) is the one-name-one-thing shape. |

**What is *not* on this list, deliberately:** everything the model already answers with an assert
and a control. The register holds only items where the missing input is an owner's judgement, a
bench observation, or a datasheet — the three things `ember_mobile_case.py` cannot generate.

---

## See also

- [`enclosure.md`](enclosure.md) — verified board geometry and the case survey. Everything there
  about the board applies unchanged.
- [`verification.md`](verification.md) — the running log of claims that outran their evidence.
- [`vendor/README.md`](vendor/README.md) — the schematic and what it settles.
- [`../enclosure/PRINT-SHEET.md`](../enclosure/PRINT-SHEET.md) — desk parts only; see §11.
