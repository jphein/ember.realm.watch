# Enclosure — board geometry, and why no case existed

Mechanical findings for the **LCDWIKI/QDtech ES3C28P**. Every dimension below is read
off the vendor's own outline drawing (`ES3C28P_ES2N28P_Specification_V1.0.pdf` §5.1,
Figure 5.1, rev V1.0, 2025-06-11), not calipered and not taken from a community table.

> **This is the survey, not the answer.** It records why nothing off the shelf fits. The case
> that came out of it lives in [`enclosure/`](../enclosure/) — four printable parts, with
> [`enclosure/PRINT-SHEET.md`](../enclosure/PRINT-SHEET.md) for orientations and assembly and
> [`print-sheet.html`](print-sheet.html) for the version you read at the printer.

For the electrical side — pinout, codec, display — see the comments in
[`esphome/ember-satellite.yaml`](../esphome/ember-satellite.yaml) and
[`audio-pop.md`](audio-pop.md).

---

## Headline: nothing on the model sites fits

**No printable case exists for this board, under any alias.** That is a
well-evidenced negative, not a failed search — see [§3](#3-evidence-for-the-negative).

Two things came out of the search that are worth more than a mediocre STL:

1. **LCDWIKI publishes an official STEP model of the board.**
   <https://www.lcdwiki.com/res/ES3C28P/ES3C28P_3D.zip> — 2.5 MB zip → 17.7 MB
   `ES3C28P_3D.step`. Verified genuine: an Altium→OpenCASCADE export dated 2025-06-10
   carrying `PRODUCT('PCB','PCB')`, with the real connectors modelled by part name
   (`MOLEX1.25-WS-2P`, `MOLEX1.25-WS-4P`, `MOLEX1.25-LS-2P`, `FPC0.5_2H-S-W-6P`,
   `C_0603`). **This makes designing beat adapting** — the board outline, corner radii,
   mounting holes, glass footprint, USB-C body, speaker header, SD mouth and rear LED all
   land correctly by construction, and the shells can be clearance-checked against the
   real solid by boolean intersection rather than against a transcribed table.

   **It does not give you everything, and the two it withholds are load-bearing.** The
   microphone port and the BOOT/RESET switch positions are *not* in this file — both had
   to be established another way. See the caveat below before trusting it for a feature.

   *Deliberately not committed here.* 17.7 MB of generated CAD does not belong in a
   firmware repo; fetch it from the vendor. Note lcdwiki.com serves an **expired TLS
   certificate**, so `curl -k` is required.

   > **⚠️ Standing caveat — the STEP is an OUTLINE model, and absence in it proves
   > nothing.**
   >
   > This export is trustworthy for **where things are** and silent about **what things
   > are**. Its 159 distinct `PRODUCT` names are passives by reference designator, the
   > microSD cage, the WS2812, and the Molex/FPC connectors by part number — and that is
   > close to all of it. Known omissions so far:
   >
   > - **No small holes. Not one via.** So it cannot show the microphone's acoustic
   >   port, which is a real front-facing hole on the real board.
   > - **No switches of any kind** — no `K1`, no `K2`, no switch body anywhere in the
   >   assembly. The two tact switches that are the device's only physical inputs are
   >   simply not in the file.
   > - **The microSD socket is authored as zero-thickness FACES**, so it has no solid to find.
  >   ⚠️ The plate that *was* taken for it — 11.15 × 14.15 mm, standing **0.50 mm** off the
  >   PCB — is the **LCD driver flex**: a microSD socket is 1.4–2.8 mm tall, so the height
  >   ruled it out and nobody checked the height. **Measure this file's faces, not only its
  >   solids**; a component authored as faces is invisible to a solid-only search and its
  >   absence looks like the component not being there.
   >
   > Both of the first two cost real time: the mic port was called "probably absent"
   > from the model's silence and settled in five seconds by looking at the board, and
   > the switch positions had to be measured off the PCB outline because the switches
   > themselves are not there to measure.
   >
   > **The rule, not the anecdotes:** measure *positives* from this file and never infer
   > *negatives* from it. If a feature matters and the STEP does not show it, that is a
   > statement about the export, not about the hardware — go and look at the board. A
   > boolean check against this solid can only tell you that two things collide, never
   > that a thing exists.

2. **The board is dimensionally drop-in with the "Cheap Yellow Display"**
   (ESP32-2432S028) — identical outline, identical hole pattern, identical edge inset,
   same standard 2.8" panel. So the large CYD case ecosystem is a legitimate
   adaptation base: **the shell fits, the cutouts don't.**

> ⚠️ **What every CYD-derived candidate gets wrong: the microphone.** On the ES3C28P
> the mic vents through the **front face**, in the bare bezel strip at the end
> opposite the USB-C. No CYD case has a port there, because the CYD has no mic at
> all. For a voice satellite that is the dealbreaker — and it is not a cutout you can
> add to a finished STL from the outside, because it has to go in the front bezel.

---

## 1 · Outline and mounting

| Feature | Value |
|---|---|
| PCB | **86.00 × 50.00 mm**, corner radius **R3.50** |
| Total thickness | **10.60 mm** |
| Mounting holes | **4 × ⌀3.20** (M3 clearance) |
| Hole pattern | **78.00 × 42.00 mm** centres — **4.00 mm in from every edge** |
| Pad / keepout per hole | **⌀5.60** — keep bosses ≤5.6 mm OD, or use nylon washers, so a metal screw head can't bridge the annular ring |
| Front stack (glass face → PCB back) | **5.90 mm** — see the discrepancy note below |
| Back component height | **4.70 mm** max |
| Touch glass | **50.00 × 69.20 × 1.00 mm** |
| LCD active area | 43.20 × 57.60 mm (visible 43.60 × 58.05 mm) |
| Glass inset from short edges | **8.22 mm** one end, **8.58 mm** the other |
| Weight | 111 g including packaging |

> **The vendor's own documents disagree by 0.30 mm** on the front stack: §3.4 "Module
> size" says 5.60 mm, while the side view sums to 5.90 mm
> (1.00 TP + 0.50 glue + 2.30 LCD + 0.50 glue + 1.60 PCB). **Design to 5.9.**

### ⚠️ You cannot clamp the long edges

**The touch glass is the full 50 mm PCB width, flush on both 86 mm sides.** There is
no side bezel to land a lip on. A front retaining lip can only bear on the two short-end
strips (8.22 mm and 8.58 mm) — which is also where all four screw holes are, so that
works out conveniently, but it is a hard constraint on any design that assumes a
continuous front rim.

## 2 · Where things are

Portrait, viewed from the front, **USB-C at the bottom** (confirmed against the
vendor's annotated board photo, §4.1 Figure 4.1):

- **Bottom short edge** — USB-C **dead centre at 25.0 mm**, with two tact switches
  flanking it across the 50 mm width, each **3.26 mm** in from the edge. The pairing is
  two switches at **x = 13.45 mm** and **x = 36.58 mm**. The pairing is **BOOT at x = 13.45**
  — the only readable switch — and **RESET at x = 36.58**, and it is now *derived* rather than
  typed: `ember_case.py` reads it off the microSD socket's side of the board.

  > ⚠️ **It used to be given the other way round, and the error is worth keeping.** The claim
  > rested on (a) the bare-board observation that the volume overlay comes up from the switch on
  > the **microSD side** — direct, and still true — plus (b) the microSD spanning x 33.68–44.83.
  > **(b) was wrong.** That extent came from an 11.15 × 14.15 mm plate standing **0.50 mm** off
  > the PCB in the vendor STEP; a microSD socket is 1.4–2.8 mm tall, so it was never one. It is
  > the LCD driver flex. The real socket is authored in the same file as **zero-thickness faces**
  > at **x 2.53–17.53** — the other long edge — so moving the anchor inverted the answer.
  >
  > **A correct observation, a correct inference, and a fictional anchor.** The durable form of
  > (a) needs no coordinate at all: *the readable switch is the one on the same long edge as the
  > microSD socket.* **A relative claim cannot be broken by mislabelling the thing it points at;
  > an absolute one can** — and converting this one to an x value is the only reason it could
  > break.

  > **Refer to these by coordinate or by constant, never by left/right.** Which side
  > each appears on flips with the view: a back three-quarter mirrors the board, and a
  > figure of the shell in print orientation (open side up) mirrors it back again. Get
  > it backwards and the big inviting thumb cap ends up over **RESET**.

  **They are not equivalent, and only one is an input.** BOOT is GPIO0 and is the
  entire hardware input budget for this board — short press summons the audio overlay
  (volume and mic gain) and steps it, long press opens the power menu. RESET is hardwired to `CHIP_PU`: it
  reboots the MCU *and* the LCD, and firmware **cannot read it at all**. The only other
  free broken-out pins are GPIO 2, 14 and 21, and reaching them means soldering.

  > **⚠️ Holding BOOT low across a reset enters ROM download mode**, which looks
  > exactly like a bricked device. Any enclosure that exposes both switches must
  > guarantee neither pusher can stick depressed and that one thumb cannot press both
  > at once.
- **Top front bezel strip** — the **microphone acoustic port**, **4.0 mm** from the
  short edge and **10.0 mm** from one long edge, sitting between the two mounting
  holes. The mic component is on the back; the port vents **forward** through the PCB.
- **One long edge** — SPEAKER (1.25 mm 2P), I²C (4P), Expand (4P).
- **The other long edge** — microSD slot (~15.97 mm wide, spanning ≈43.2–59.1 mm from
  one short edge), BAT (2P), UART (4P).
- **WS2812 RGB LED (GPIO42) is on the BACK, inboard, and fires backwards.** A closed
  back cover hides it completely.

Speaker header is rated **1.5 W / 8 Ω or 2 W / 4 Ω** and ships as an unpopulated
1.25 mm 2P connector with cable. Battery input is 3.7 V LiPo, charging at 290 mA
actual / 500 mA max.

**Verified vs inferred.** Every dimension is read off the drawing. The
**front-facing mic port is now CONFIRMED** — JP inspected the physical board and the
product photos: the microphone fires forward, through the front face, and the hole is
visible. It had been inferred from a PCB through-hole on the front view at the mic's
location, in a strip the glass deliberately doesn't cover, cross-checked against the
back-side photo — and the vendor STEP could never settle it, because that export
contains **no small holes at all, not one via**. So the model's silence was never
evidence of absence. Five seconds of looking closed what a 17 MB CAD file could not. The left/right handedness of the two long edges rests on a
drawing-convention assumption; what's solid is the **pairing** — speaker and microSD
are on **opposite** long edges, and the mic is at the end **opposite** the USB-C.

## 3 · Evidence for the negative

Aliases searched: `ES3C28P`, `ES3N28P`, `E32C28P`/`E32N28P`, `LCDWIKI`, `QDtech`,
`Hosyond 2.8 ESP32-S3`, `ESP32-S3 2.8 inch capacitive touch`, `Guition`,
`JC2432W328`, `JC3248W535`, `ESP32-2432S028`, `xiaozhi` + 外壳/2.8寸/3D打印, and the
`ILI9341 + FT6336 + ES8311` component combination.

- **20+ ES3C28P GitHub repos enumerated**, with the full file tree walked on the six
  most likely — including `sintak15/voice_assistant_es3c28p`, a voice-assistant build
  and therefore the most likely place for a case. **Zero `.stl/.step/.stp/.f3d/.3mf/.scad/.dxf`
  files in any of them.** `gh search code "es3c28p extension:stl"` → 0 results.
- The one Home Assistant community thread for this exact board was read in full,
  replies included: no model link anywhere, and no fitment discussion.
- Printables, MakerWorld, Thingiverse, Thangs, GrabCAD, yeggi, STLFinder, stlbase —
  nothing names this board under any alias.

**Tooling caveat, so the gap is known:** Printables and MakerWorld return **403** to
automated fetches from this host, so two candidates were judged from search snippets
only and their licences are recorded as unread rather than guessed.

## 4 · Why the CYD ecosystem is dimensionally compatible

| | **ES3C28P** (this board) | **ESP32-2432S028** (CYD) |
|---|---|---|
| PCB | 86.00 × 50.00 | 86 × 50 |
| Hole centres | 78.00 × 42.00 | 78.0 × 42.0 |
| Edge inset | 4.00 | 4.0 |
| Corner radius | R3.50 | R1.60 |
| Panel | 50.0 × 69.2 (2.8" 240×320) | same standard panel |

Our R3.50 corners are *more* rounded than the CYD's R1.60, so the board drops into a
CYD-shaped pocket with clearance to spare, and our 10.60 mm total is thinner (it may
rattle slightly).

**What differs and will bite:** RESET/BOOT positions, all four 1.25 mm JST positions,
the LED position, and the total absence of a mic port. USB-C (centred on the short
edge) and microSD (long edge, starting ≈43 mm in) happen to land in nearly the same
places on both boards — our SD slot is ~4 mm longer, so a CYD SD cutout is correctly
placed but slightly short.

**Confirmed NOT compatible**, despite keyword-matching:

- **Waveshare ESP32-S3-Touch-LCD-2.8** — **73.06 × 50.54 mm**, i.e. 13 mm too short.
  This is the trap: it matches on "ESP32-S3" and "2.8 inch" *and* it has the speaker
  grill everyone wants. It is the wrong outline. Don't order filament for it.
- **Guition JC2432W328** — ST7789 + CST820, different silicon entirely.

## 5 · Three design consequences worth acting on

1. **Put the mic port in the front bezel**, in the top strip — not the side, not the
   back. This is the requirement no existing case satisfies.
2. **Don't clamp the long edges** (§1). Land the front lip on the short-end strips.
3. **Give the rear LED somewhere to go.** Otherwise Ember loses its status glow
   entirely. *Since resolved:* this was first a ⌀12 mm window with a separate printed
   translucent disc seated in it, and is now a field of 113 hex apertures across the
   back — 3.2 mm across the flats on a 0.8 mm web, 56% open. Many small openings scatter;
   one large bore just shows you the die. That deleted a part, a seat and a second
   filament, and the case is printed in white, so the shell is translucent enough to
   glow between the holes as well as through them.

And one that isn't about the board: **size the speaker chamber to the driver, not to
the case.** A sealed enclosure behind a 28–40 mm driver, firing forward through a
grill, is the difference between a 2 W speaker and a project box.

## 6 · Vendor resources

| Resource | URL |
|---|---|
| Official 3D model (STEP) | <https://www.lcdwiki.com/res/ES3C28P/ES3C28P_3D.zip> |
| Touchless variant model | <https://www.lcdwiki.com/res/ES3C28P/ES3N28P_3D.zip> |
| Specification (§5 has the outline drawing) | <https://www.lcdwiki.com/res/ES3C28P/ES3C28P_ES2N28P_Specification_V1.0.pdf> |
| User manual | <https://www.lcdwiki.com/res/ES3C28P/2.8inch_IPS_ESP32-S3_ES3C28P_ES3N28P_User_Manual.pdf> |
| Altium footprint / 3D library | <https://www.lcdwiki.com/res/ES3C28P/2.8inch_IPS_ESP32-S3_Display_AD封装库.zip> |
| Product wiki | <https://www.lcdwiki.com/2.8inch_ESP32-S3_Display> |

> **Vendor-document sloppiness worth knowing.** The Specification's interface figure is
> captioned *"Figure 4.1 E32R28T product interface diagram"* — a different SKU —
> even though the photographed board's silkscreen clearly reads
> `2.8" LCD Display / ESP32-S3 240x320 / Capacitive Touch`. **Trust the drawings, not
> the captions.** This is the same class of error that puts the I²S data pins the wrong
> way round in every community pinout table.
