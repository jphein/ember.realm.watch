"""
Ember voice-satellite enclosure  --  LCDWIKI/QDtech ES3C28P (Hosyond 2.8" ESP32-S3)
====================================================================================
Parametric source.  Run:  ../cadenv/bin/python ember_case.py
Outputs STLs + runs a boolean clearance check against the VENDOR STEP.

COORDINATE SYSTEM = the board's own frame, taken from ES3C28P_3D.step:
    X  0 .. 50      board width
    Y  0 .. 86      board length   (Y=0 is the USB-C / button end, Y=86 the mic end)
    Z               glass front face = +4.30 | PCB top = 0 | PCB bottom = -1.60
                    deepest back component = -6.30
Every board number below was MEASURED from the vendor STEP solid, not transcribed
from a datasheet table.  See VERIFIED{} for the provenance of each.
"""
from build123d import *
import os, sys, math

# PATH-INDEPENDENT IMPORTS. This file used a bare `import wyrm_spans`, which only resolved
# when cwd happened to be enclosure/tools/ — so `./cadenv/bin/python ember_case.py` from the
# enclosure directory died with ModuleNotFoundError, and the README's own build command did
# not work. "Buildable from a fresh clone" was a claim, not a fact. Resolve relative to THIS
# FILE instead of the working directory, so it runs from anywhere.
_HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.join(_HERE, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(_HERE, "tools"))
import wyrm_spans as _W

# ============================================================================
# 1. BOARD FACTS  -- all measured from ES3C28P_3D.step
# ============================================================================
BW, BL          = 50.00, 86.00      # PCB outline
PCB_TOP, PCB_BOT= 0.00, -1.60
GLASS_Z         = 4.30              # front face of the capacitive glass
BACK_MAX        = -6.30             # deepest back-side component
CORNER_R        = 3.50
HOLES           = [(4.0,4.0),(46.0,4.0),(4.0,82.0),(46.0,82.0)]   # d3.20, pad d5.60
GLASS_Y         = (8.40, 77.60)     # glass spans full 50mm width
VA              = (3.20, 46.80, 16.81, 74.86)   # visible area x0,x1,y0,y1
MIC             = (40.00, 81.50)    # mic package centre, in the top bare strip
MIC_HOLE_D      = 3.00              # back relief bore; the MIC label's keepout reads it
# ---- THE ONE ABSOLUTE BIT.  EVERYTHING ELSE ABOUT X IN THIS FILE IS RELATIVE. ----
#
# ⚠️ READ THIS BEFORE ADDING ANY "IS THE BOARD MIRRORED?" CHECK, because the obvious ones cannot
# work.  The alignment assert compares the board's bounding box to X 0..50 — and a mirrored
# board has the IDENTICAL bounding box, so that check is structurally incapable of failing.
# Less obviously, so is every RELATIVE claim: "BOOT shares its long edge with the microSD" is
# true in the mirrored world too, because mirroring moves both.  A relative predicate is
# mirror-invariant BY CONSTRUCTION.  You cannot detect a reflection from the model alone.
#
# So exactly one fact here is anchored to a PHYSICAL OBSERVATION and nothing else, and every
# relative assert in _check_geometry() hangs off it.  The relative ones then earn their place by
# catching a PARTIAL mirror — one feature moved without the others — which is the failure that
# actually happened (the switches were swapped relative to the socket).
#
# PROVENANCE: set from JP's physical board and the printed parts, 2026-07-30 — NOT from the
# vendor STEP and NOT from the outline drawing, both of which were read the wrong way round at
# least once each that day.  Corroborated afterwards by the STEP's own mic face at
# X 39.21..40.81, Y 80.15..82.85 -> centre (40.01, 81.50), which agrees to 0.01mm.
#
# ⚠️ Added after a mirror was SUSPECTED AND RULED OUT.  Nobody should later read this block as
# evidence that a reflection ever occurred — it did not.  It is here because the hole existed.
# If this constant is ever re-measured and comes back the other way, EVERY x in section 1
# mirrors, not just this line.
MIC_ON_HIGH_X   = True
USB_X           = (20.53, 29.47)    # USB-C body, centred on 25.00
USB_Z           = (-4.85, -1.60)
# ---- microSD SOCKET.  MEASURED FROM THE STEP'S *FACES*, NOT ITS SOLIDS. ----
#
# ⚠️ WHAT USED TO BE HERE WAS NOT THE SOCKET.  `SD_PLATE = (33.68,44.83,15.84,29.99)` was taken
# from the largest back-side SOLID in the vendor STEP: an 11.15 x 14.15mm plate standing 0.50mm
# off the PCB.  A microSD socket is 1.4-2.8mm tall, so 0.50mm was never a socket — it is a
# footprint placeholder, and JP, holding the board, identified it as the LCD driver flex.
#
# The real socket IS in the same STEP, authored as a stack of ZERO-THICKNESS FACES.  That is why
# a census of `.solids()` could not find it: it has no solid, no volume, and no height to filter
# on.  ⚠️ A SEARCH FOR THE WRONG KIND OF OBJECT RETURNS A CONFIDENT ABSENCE.  Searching
# `.faces()` instead gives four stacked rectangles:
#
#     X 2.53..17.53   Y 43.70..58.36   Z -1.60..-3.45      15.00 x 14.66 x 1.85mm
#
# 1.85mm tall — a real socket.  Corroborated independently by the vendor outline drawing, whose
# bottom dimension chain 11.82 + 15.97 + 35.03 closes exactly on Y=86 and puts the socket
# centreline at Y 50.955; the STEP faces give 51.03.  Two unrelated instruments, 0.3mm apart.
#
# The mouth faces the X=0 edge (the body stops 2.53mm short of it), so THE CARD TRAVELS
# PARALLEL TO THE PCB AND EXITS THROUGH THE SIDE.  The opening is therefore a side-wall slit,
# like the connector channels — not a hole in the back face.
#
# >>> THIS IS THE LANDMARK THE BUTTON ASSIGNMENT IS DERIVED FROM.  Do not edit it without
#     reading the block below. <<<
SD_SOCKET       = (2.53, 17.53, 43.70, 58.36)   # x0,x1,y0,y1
SD_SOCKET_Z     = (-3.45, -1.60)
SD_CARD_W       = 11.00              # microSD card width, across the direction of travel

# Rear-facing tact switches. WHICH IS WHICH — DERIVED FROM THE SOCKET, NOT TYPED, and the
# reason is the entire bug this block used to contain.  The vendor STEP carries designators for
# plenty of parts (C10, SD_CARD1, MOLEX1.25-…, the WS2812 library part) but contains NO K1/K2
# and no switch part at all — the same export suppression that hid the mic hole and the socket.
#
# JP's bench test, on the bare board: "volume button is on sd card side."  That observation was
# always correct.  ⚠️ WHAT WAS WRONG WAS THE LANDMARK IT WAS DECODED THROUGH.  The old comment
# reasoned "SD_PLATE spans x 33.68..44.83, i.e. high-x, so x = 36.58 -> BOOT" — and SD_PLATE was
# the LCD driver flex.  A correct physical fact, a correct inference, and a fictional anchor;
# the answer came out mirrored.  Read against the real socket at x 2.53..17.53 the same bench
# test gives the OPPOSITE assignment, which is what JP saw on the printed part.
#
# So it is COMPUTED now.  A comment has to be re-decoded by a human every time it is trusted,
# and this one was re-decoded wrongly.  Code is decoded once.
_SD_CX          = (SD_SOCKET[0] + SD_SOCKET[1]) / 2.0
_BTN_XS         = sorted(x for (x, _y) in [(13.45,3.26),(36.58,3.26)])
BTN             = [(13.45,3.26),(36.58,3.26)]
# the volume switch shares its long edge with the socket; the other switch is RESET.
BTN_BOOT_X      = _BTN_XS[0]  if _SD_CX < BW/2 else _BTN_XS[-1]   # big cap, the only readable switch
BTN_RESET_X     = _BTN_XS[-1] if _SD_CX < BW/2 else _BTN_XS[0]    # small cap
#
#   BOOT  = K2 / GPIO0  -- the ONLY readable input. Short press = volume overlay + step,
#           long press = power menu. Gets the BIG hex cap.
#   RESET = K1          -- hardwired to CHIP_PU, unreadable by firmware, reboots the MCU
#           *and* the LCD. Gets the SMALL hex cap.
#
# ⚠️ Holding BOOT low ACROSS a reset enters ROM download mode, which looks like a brick.
# With two pressable caps that is reachable by accident, so neither cap may be able to
# stick depressed, and one thumb must not span both.
#
# ⚠️ THE COST OF GETTING THIS BACKWARDS IS ASYMMETRIC, which is why it is derived and asserted
# rather than trusted: the generous thumb-sized cap over HARDWARE RESET is a device that reboots
# when you reach for the volume.  An easy RESET is an annoyance; a RESET you cannot avoid is not.
#
# >>> NEVER SPECIFY THESE AS "LEFT" OR "RIGHT". USE THE COORDINATES. <<<
#
# The apparent side flips between three figures of this same part:
#   case-back.svg          eye behind the part -> board +X appears on the viewer's LEFT
#                          (confirmed from the render: the mic at (40, 81.5) lands
#                          upper-left and the x=46 countersinks are the left-hand pair)
#   case-print-layout.svg  shell open-side-up -> mirrored back again, +X on the RIGHT
#   case-hero.png          a front view entirely
#   the VENDOR OUTLINE DRAWING (spec p.14) — the fourth figure, and the dangerous one,
#                          because it is the document someone checking this work will reach
#                          for first. It reads the OPPOSITE way to the bench test. An agent
#                          re-derived the assignment from it in good faith and got BOOT and
#                          RESET swapped, via a chain that was sound except for the handedness
#                          of a -90deg-rotated, 180deg-flipped figure — which cannot be
#                          established from the drawing itself. ⚠️ THE VENDOR DRAWING IS NOT
#                          USABLE TO RE-DERIVE THIS. The bench test wins because it anchors a
#                          physical observation to a model coordinate: JP pressed both, and
#                          the volume one is on the microSD side, and SD_PLATE is at x
#                          33.68..44.83 in the STEP. That is a landmark, not an orientation.
#
# So "big cap on the left" is true in one figure, false in another and meaningless in the
# third. Spec from the wrong one and the generous thumb-sized cap lands over the HARDWARE
# RESET — a device that reboots when you reach for the volume. Same discipline as the
# hostname rule in CLAUDE.md: the literal is the thing that silently goes stale, and a
# coordinate cannot be mirrored by a camera.
BTN_TIP_Z       = -4.10             # plunger tip (2.50mm below PCB back face)
PIP_D           = 3.00              # pip that reaches the plunger. WAS 4.00, and shrinking it
                                    # is what makes the offset island placeable: the island hex
                                    # narrows toward its bottom flat, exactly where the pip
                                    # sits, so a 4.00mm pip left only a 0.40mm window of legal
                                    # island X. 3.00mm more than doubles it to 0.98mm, and a
                                    # tact switch plunger is 1.5-3.5mm so 3.00 still covers it.
                                    # A 0.40mm placement window on a printed part with a 3.5mm
                                    # pip offset is not a tolerance, it is a hope.
LED             = (29.00, 45.60)    # WS2812B 5x5, on the BACK, fires rearward
ANT             = (17.57, 32.21, 80.04, 85.70)  # PCB antenna -- KEEPOUT, no metal
CONN_R         = [(32.54,40.19),(44.84,54.99),(62.69,72.84)]  # X=50 edge connectors
# X extent of the X=50 edge connectors, MEASURED off the STEP solids. Stored because the
# speaker relief (#33) needs it and nothing else in this file knew how far inboard they reach.
CONN_R_X       = (45.29, 49.49)
# >>> THE SPEAKER CONNECTOR IS TOP-ENTRY, AND IT IS THE ONLY ONE. <<<  (issue #33)
#
# JP, board and shell in hand: the speaker plug and its wires leave the board UPWARD into the
# shell, not sideways like every other connector, so the side-channel treatment is the wrong
# shape for it and the shell bears on the plug instead of closing.
#
# ⚠️ THAT OBSERVATION INDEPENDENTLY CONFIRMS THE #27 MAPPING, which is worth more than the
# relief it asks for. Measured out of the STEP, the five connectors are:
#
#     CONN_R[0]  z -6.30..-1.60  H 4.70   0.80mm to CAV_FLOOR   <- SPK, per the silkscreen
#     CONN_R[1]  z -5.00..-1.60  H 3.40   2.10mm
#     CONN_R[2]  z -5.00..-1.60  H 3.40   2.10mm
#     CONN_L[0]  z -5.00..-1.60  H 3.40   2.10mm
#     CONN_L[1]  z -5.00..-1.60  H 3.40   2.10mm
#
# EXACTLY ONE connector is taller than the others, it is 1.30mm taller, it reaches the board's
# own minimum Z, and it is the one the vendor silkscreen chain names SPEAKER. A physical
# observation ("the speaker one is different") and a documentary one (the drawing) agreeing on
# the same solid is the standard this file holds for handedness — see BTN_TIP_Z, where the
# bench test beat the drawing. There is an assert in __main__ that keeps them agreeing.
SPK_CONN_I     = 0                 # index into CONN_R. Derived-and-asserted, not chosen.
# ---- and the relief it needs. A THROUGH-OPENING, and the reasoning is a bound, not a guess ----
#
# The plug's height is the one number nobody has: it is JP's speaker's own pigtail and it is
# not in the STEP. So the choice was made on which failure is available rather than on a
# dimension I would have had to invent.
#
#   headroom today                                    0.80mm
#   a blind pocket, leaving 0.40mm of printable floor 0.80 + 2.20 = 3.00mm    <- BOUNDED
#   a through-opening                                 unbounded              <- cannot be short
#
# A 2-pin 1.25mm plug protrudes ~1.5-2.5mm past its header and its wires then need to turn.
# 3.00mm might do and might not, and "might" fails an acceptance test that reads "the shell
# closes fully". A through-opening cannot be too shallow, which is the whole argument.
#
# ⚠️ IT MUST REACH THE SIDE WALL, and that is the part a footprint-shaped hole would miss. The
# connector already fills the cavity to within 0.80mm, so the lead cannot travel over the top
# of it to the side channel — a 1mm wire in 0.80mm of gap is the pinched-wire hazard the stand's
# wire saddle exists to prevent, reintroduced 40mm away. Taking the opening outboard to OX1
# merges it with the existing side channel over the same Y span, so the plug drops in and the
# lead leaves sideways through a route that already exists.
SPK_RELIEF_CLR = 0.75              # per side, plug housing vs connector body
SPK_RELIEF_Y   = (CONN_R[SPK_CONN_I][0] - SPK_RELIEF_CLR,
                  CONN_R[SPK_CONN_I][1] + SPK_RELIEF_CLR)
SPK_RELIEF_X0  = CONN_R_X[0] - SPK_RELIEF_CLR
CONN_L         = [(21.07,25.32),(29.91,40.06)]                # X=0  edge connectors
CONN_R_EDGE_X  = BW      # the long edge CONN_R sits on
CONN_L_EDGE_X  = 0.0     # the long edge CONN_L sits on
# ⚠️ NOT THE MICROSD.  This is the 0.50mm-tall placeholder the old `SD_PLATE` name was attached
# to — the LCD driver flex, per JP.  It is kept ONLY as a keepout: it is the thing the phantom
# opening was exposing, so anything that cuts the X=BW wall must be checked against it.  The
# real socket is `SD_SOCKET`, 30mm away across the board and 28mm along it.
LCD_FLEX       = (33.68,44.83,15.84,29.99)

# ============================================================================
# 2. CASE PARAMETERS  -- tune these
# ============================================================================
FIT        = 0.35    # clearance per side, board edge -> pocket wall
WALL       = 2.60    # shell wall thickness
BEZEL_T    = 3.00    # bezel thickness over the glass
CAV_CLR    = 0.80    # clearance under the deepest back component
WIN_MARGIN = 0.40    # bezel window oversize beyond the visible area
BOSS_D     = 5.40    # <= 5.60 pad diameter, per the vendor keepout
PILOT_D    = 2.50    # M3 self-tapper pilot
SCREW_D    = 3.30    # M3 shank clearance through the shell
# ---- COUNTERBORE, SIZED TO A MEASURED HEAD ----
#
# JP's screws are SOCKET CAP with a hex recess, so the head is a CYLINDER. This is a
# flat-bottomed counterbore, not a cone.
#
# HISTORY, in one line, because it explains why this used to be forty: it was a 90deg conical
# countersink with a long derivation about included angles, DIN 965 versus ISO 10642 heads, and
# why fixing the angle without also fixing the mouth diameter still leaves the head bearing on
# its rim. All of it solved for a conical seat this fastener does not have. It is DELETED rather
# than adapted — a comment explaining a 90deg cone sitting next to a counterbore is precisely the
# stale-rationale failure this repo keeps logging.
#
# A counterbore is also the more forgiving feature, which is worth knowing before anyone
# "improves" it back: a flat floor seats a cylindrical head on its FULL ANNULAR UNDERSIDE
# regardless of small diameter errors, where a cone punishes any angle mismatch by concentrating
# the load on a line. And a flat floor at a layer boundary is exactly what an FDM printer makes
# well, so the staircase-of-annular-steps problem the cone had disappears.
#
# ⚠️ EVERY NUMBER IN THE FASTENER CHAIN IS MEASURED. Calipered by JP on the actual screws,
# 2026-07-30. The ISO 4762 table agrees with both figures, but the table is not the source — this
# is the only part of this design where no input is nominal, and that is worth preserving. If a
# screw ever does not fit, no assumption is hiding in here.
SCREW_SPEC      = "M3 x 0.5 x 12 ISO 4762 socket cap, hex recess"
SCREW_HEAD_D    = 5.50   # MEASURED, JP, 2026-07-30
SCREW_HEAD_H    = 3.00   # MEASURED, JP, 2026-07-30
SCREW_LEN       = 12.00  # UNDER-HEAD length, which is how ISO 4762 is dimensioned. ⚠️ A
                         # countersunk screw's stated length INCLUDES its head; a socket cap's
                         # does not. That difference is why a 12mm cap out-performs the 14mm
                         # countersunk this used to specify.
# ============================================================================
# LAYER HEIGHT IS PER-PART.  IT IS NOT ONE NUMBER, AND TREATING IT AS ONE WAS ISSUE #26.
# ============================================================================
#
# ⚠️ THIS WAS A SINGLE `LAYER_H = 0.16` COMMENTED "PRINT-SHEET's layer height for the shell
# parts", AND THAT COMMENT WAS FALSE. PRINT-SHEET's settings table is FOUR COLUMNS —
# bezel / shell / stand / base — and reads 0.16 for the BEZEL and 0.20 for the other three. The
# 0.16 was the bezel's value, borrowed by the shell and relabelled as the shell's on the way.
#
# It was load-bearing in both directions at once, which is why it survived: `BEZEL_DEBOSS`
# consumed it and was CORRECT, while `CBORE_DEPTH` and `LABEL_DEBOSS` consumed the same constant
# and were wrong for a shell sliced at 0.20 — 15.2 and 2.4 layers, both mid-layer floors. The
# claims "19 layers exactly" and "3 layers at 0.16" were true of the number and false of the part.
#
# ⚠️ AND THE ISSUE UNDERSTATED IT. Auditing every Z depth against BOTH candidates found three more
# mid-layer floors, and unlike the two above these are misaligned at EVERY layer height in play:
#
#     DEBOSS_BIG    0.90   5.625 layers @0.16   4.5 layers @0.20
#     DEBOSS_SMALL  0.50   3.125               2.5
#     HINGE_T       0.90   5.625               4.5
#
# So the real defect was never "one constant borrowed the wrong value". It was that Z depths were
# never checked against ANY layer height, and two of them happened to divide 0.16 — which is what
# made the other three invisible. `HINGE_T` is the serious one: it is the strain-critical
# dimension (`strain = (t/2)*theta/L`), computed to three significant figures throughout this
# file, and the slicer was picking its actual value.
LAYER_H_BEZEL   = 0.16   # PRINT-SHEET: the bezel alone. Its front face is the one you look at and
                         # its mic bore is only d2.40, which starts to close up at 0.20.
LAYER_H_SHELL   = 0.20   # PRINT-SHEET: shell, stand and base. ⚠️ The bezel's reasons DO NOT apply
                         # here — the shell's fine features (the 0.60 button moat, the 0.80 hex
                         # webs, the 0.90 label grooves) are all VERTICAL walls, and layer height
                         # does not govern the width of a vertical wall.
CBORE_CLR       = 0.30   # diametral clearance, 0.15 a side
CBORE_D         = SCREW_HEAD_D + CBORE_CLR              # 5.80
# DEPTH IS A WHOLE NUMBER OF LAYERS, AND AT 0.20 IT IS EXACTLY FLUSH.
# The measured head is 3.00 and 3.00 / 0.20 = 15 exactly, so the head sits DEAD FLUSH with no
# rounding at all. ⚠️ This retires a compromise rather than adding one: at the borrowed 0.16 the
# head was 18.75 layers, 18 left it 0.12 PROUD (which stops the part sitting flat and stops the
# screw clamping) and 19 sank it 0.04 to avoid that. The fudge existed only because the shell was
# being sliced at the bezel's layer height. Correcting #26 deletes it.
CBORE_DEPTH     = 15 * LAYER_H_SHELL                    # 3.00 — exactly the head height
# ---- BOSS FLARE.  THIS EXISTS BECAUSE THE HEAD IS 3.00mm TALL.  DO NOT REMOVE IT. ----
#
# A flush 3.04mm pocket floors at z -6.66, which is 0.44mm PAST CAV_FLOOR — out of the solid back
# slab and into the cavity, where the only material is the screw boss. At BOSS_D = 5.40 the
# CBORE_D = 5.80 bore is WIDER THAN THE THING IT IS CUTTING, so it removes the boss root and
# leaves the head nothing to bear on. ⚠️ A POCKET DEEPER THAN THE SLAB IT IS CUT INTO STOPS BEING
# A POCKET. Nothing else in this file could have caught that: every other check compares the PART
# to the BOARD, and this is the part disagreeing with itself.
#
# ⚠️ THE PERMISSION FOR THE FLARE IS A DISTINCTION, NOT A LICENCE: the vendor's d5.60 pad keepout
# applies AT THE PCB FACE, not below it. So the boss stays 5.40 where it touches the board and
# widens only underneath, in free space. Anyone "restoring" it to a uniform 5.40 to match the
# keepout comment will silently delete the head's seat.
#
# Bounded above by the button slots, not by taste. The slots pass within 9.49mm (RESET) and
# 12.38mm (BOOT) of a boss centre — the hex has NARROWED by the time it reaches the boss's y, so
# the naive x-extent overstates the conflict. 8.40 clears the tighter one by 1.09mm.
BOSS_FLARE_D    = 8.40   # boss diameter at CAV_FLOOR, tapering to BOSS_D at the PCB face
BOSS_MIN_ANN    = 1.00   # minimum annular bearing width under the head, at the bore floor
# ⚠️ AND THE BINDING CONSTRAINT IS NO LONGER THE ONE EVERYONE REACHES FOR. The wall from a screw
# hole to the outer corner arc was 2.533mm with the old d6.42 cone mouth and is 2.843mm with this
# d5.80 bore — the counterbore is LESS binding there, because a socket cap head (5.50) is smaller
# than the countersunk head (6.00) whose 90deg cone needed a 6.42 mouth. The arc was the right
# worry for the cone and is the wrong worry for this. Depth against the 2.60mm wall is what bites.
# ---- HEXAGONAL BUTTON CAPS ----
# The pads were rectangles. JP: "i wanted the buttons to be hexagons not squares" — and
# they should be, since every other aperture on this case is a hex cell.
#
# FLAT-TOP, NOT POINTY-TOP, AND THIS IS STRUCTURAL RATHER THAN AESTHETIC. The rest of the
# case uses `RegularPolygon(R, 6, rotation=30)` (pointy-top) because that is the honeycomb
# pitch. A button cannot: the pad is a living hinge, so it must stay attached along its +Y
# edge, and a pointy-top hex has a VERTEX at +Y. Hinging on a point gives a hinge of zero
# width, which is not a hinge — it is a tear. Flat-top puts a full edge of length R at +Y.
# So the caps are the one place in the case where the hexes are rotated 30 degrees from the
# lattice, and the reason is that a hinge needs a hem.
#
# The envelope is not free: the island's bottom edge cannot go below y=0.80 (the shell's
# bottom wall is just outside the board edge and the switches sit only 3.26mm in), and the
# slot's OUTER boundary must clear the fine hex field at HEX_FIELD_Y0 (19.00; this comment
# said 11.0, the value before the field yielded to the thumb-sized caps). A flat-top hex of
# circumradius R spans R*sqrt(3) in Y, so R is pinned by those two facts, not chosen.
# THUMB-SIZED, AND IT IS A STRENGTH FIX AS WELL AS JP'S REQUEST. JP asked for "big
# thumbsized hexagons" and 9.01mm across flats is not one — a thumb pad is 15-20mm. But the
# decisive argument is strain: at the old 9.01mm cap the hinge sat 6.55mm from the pip, giving
# 3.50deg and 2.29% at L=1.20 — over PLA's ~2% YIELD, safe only against fracture. A bigger hex
# puts the hinge further from the pip, so theta falls and strain falls with it. At 15mm the pip
# arm is 12.54mm, theta 1.83deg, strain 1.20%. The cap that JP wanted is also the cap that
# stops the hinge creeping, which is the rare case where the ergonomic and the mechanical
# answer are the same number.
BTN_R_BIG   = 8.6603  # BOOT/volume. 17.32 across corners, 15.00 across flats.
BTN_R_SMALL = 5.7735  # RESET. "it can be smaller hexagon" — 11.55 corners, 10.00 flats.
# ISLAND CENTRES ARE OFFSET FROM THE SWITCHES, and the screw heads force it. The M3 heads at
# (4,4) and (46,4) open to HEAD_MOUTH_D at the outer face. A 17.32mm-wide island centred on the
# switch at 36.58 would span 27.92..45.24 and eat into the high-x one. Shifting the ISLAND
# inboard is free because the hinge line runs across X and the PIP stays on the switch — only
# the decorative hex moves.
#
# ⚠️ THESE WERE TWO HAND-TYPED NUMBERS WHOSE JUSTIFICATION THE FILE DID NOT COMPUTE, and that
# made them a trap in two directions at once. The switches swapped sides (see the BTN block) and
# the screw recess changed shape — either alone silently invalidates a literal, and nothing here
# would have objected. So they are SOLVED from the clearance that motivated them:
#
#   * the binding dimension is the SLOT's outer edge, not the island's: the ring cut reaches
#     R + SLOT_W, and that is what can break into the head recess.
#   * ISLAND_SLOT_CLR reproduces the shipped BOOT island to 0.01mm (33.04 solved vs 33.05
#     typed), which is the case the original comment names as the forcing one. The shipped RESET
#     island was 0.44mm more generous than the rule; it was never the binding side.
SLOT_W          = 0.60   # printed-in-place slot around the button pads. Declared HERE because
                         # the island solve below needs it — it used to sit 70 lines further on.
PAD_Y0          = 0.80   # island bottom edge. Any lower cuts the shell's bottom wall. Declared
                         # HERE because _island_cx() needs it — it used to sit below the islands.
def _cap_cy(R):
    """Island/cap centre y for a cap of circumradius R. THE single derivation.

    ⚠️ Extracted because two places now need it and this file has already been bitten once by
    exactly that: HEX_FIELD_Y0 exists because _hex_panel() moved to 19.00 while the assert
    checking it still read a hardcoded 11.0, so the assert fired against a boundary the part no
    longer had. cap_geometry() and _island_cx() must not each carry their own copy of this."""
    return PAD_Y0 + R*math.sqrt(3)/2
ISLAND_SLOT_CLR = 0.49   # wall between the slot and the d5.80 counterbore bore
FLARE_SLOT_CLR  = 0.80   # wall between the slot and the d8.40 boss flare. Larger because this
                         # one is a load path — the boss carries the screw — where the bore wall
                         # is only cosmetic. Two extrusions at a 0.4 nozzle.
def _island_cx(cx, R):
    """Island centre for a cap of circumradius R whose switch is at x=cx.

    Returns cx unchanged when nothing is in the way, otherwise the nearest position that clears
    BOTH obstructions near each screw hole. Leaving it concentric is always preferred: the pip
    stays on the switch while only the decorative hex moves, and the hex narrows toward its bottom
    flat exactly where the pip sits, so the legal offset window is under 1mm wide.

    ⚠️ THE TWO OBSTRUCTIONS ARE DIFFERENT SHAPES AT DIFFERENT DEPTHS AND A SINGLE max() IS WRONG.
    The slot is cut from BACK_Z-1 up to CAV_FLOOR+1, so it passes BOTH:

      * the d5.80 counterbore bore, deep in the back slab, at the slot's full circumradius;
      * the d8.40 boss flare, up in the cavity — WIDER, but the slot has NARROWED by the time it
        reaches the boss's y, because a flat-top hex loses 1/sqrt(3) of half-width per unit of y
        away from its own centre. The boss sits at y=4.0 and the big cap's hex centres at y=8.30,
        so 4.30mm of narrowing turns a 9.26 half-width into 6.78.

    Taking max(bore, flare) against the naive x-extent — my first attempt — pushed the big island
    to 17.95, an offset of 4.50 from its switch, which is outside that sub-millimetre pip window:
    it would have moved the pip off the island entirely to dodge a collision that the narrowing
    means does not happen. AN OVER-CONSERVATIVE CONSTRAINT IS STILL A WRONG ONE."""
    reach = R + SLOT_W                                    # slot circumradius (its widest)
    cyh   = _cap_cy(R)
    narrow = max(0.0, reach - abs(HOLES[0][1] - cyh)/math.sqrt(3))   # half-width at the boss's y
    _b = []
    for hx in (HOLES[0][0], HOLES[1][0]):
        _b.append((hx, CBORE_D/2      + ISLAND_SLOT_CLR + reach))
        _b.append((hx, BOSS_FLARE_D/2 + FLARE_SLOT_CLR  + narrow))
    lo = max(hx + k for (hx, k) in _b if hx < BW/2)
    hi = min(hx - k for (hx, k) in _b if hx > BW/2)
    # ⚠️ ROUND AWAY FROM THE RECESS, NOT TO NEAREST. This line was `round(..., 2)` and the
    # assert in _check_geometry() 0g caught it on the first build: the solve wanted 16.9603 and
    # round-to-nearest tidied it to 16.96, SPENDING 0.0003mm of the clearance it had just
    # computed. The number was wrong by three ten-thousandths of a millimetre and it was still a
    # real violation, because a value sitting ON a constraint boundary has no slack to round
    # into. Whenever a rounded number IS a clearance, the direction of the rounding is part of
    # the constraint. Kept at 2dp because these are read by humans in renders and sheets.
    if cx < lo: return math.ceil(lo * 100) / 100
    if cx > hi: return math.floor(hi * 100) / 100
    return cx
CAP_CX_BOOT  = _island_cx(BTN_BOOT_X,  BTN_R_BIG)    # island centre; switch at BTN_BOOT_X
CAP_CX_RESET = _island_cx(BTN_RESET_X, BTN_R_SMALL)  # island centre; switch at BTN_RESET_X
# PAD_Y0 moved UP to the island-solve block -- _island_cx() needs it. A second
# definition here would shadow it and the two cy derivations would silently diverge.
# The back hex field's lower boundary, NAMED because two places need it and they disagreed:
# _hex_panel() was moved to 19.00 for the thumb-sized caps while the assert that checks the
# caps clear the field still read a hardcoded 11.0 — so the assert fired against a boundary
# the part no longer had. Exactly the dead-GRILLE_SLOT_W hazard one screenful up, and the
# reason a shared number gets a name.
HEX_FIELD_Y0 = 19.00
# X0/X1/Y1 hoisted out of the _hex_panel() call below at the same time the back-face labels
# went in. They were literals with ONE consumer, which was fine; the labels make them literals
# with TWO, which is exactly the shape that produced the dead SD_PLATE and the dead
# GRILLE_SLOT_W. Naming them is cheaper than re-learning it a third time.
HEX_FIELD_X0 = 9.00
HEX_FIELD_X1 = 41.00
HEX_FIELD_Y1 = 75.00
# DEBOSSED, NOT RAISED — and the print orientation decides this, not taste.
#
# The first version of these caps stood 1.20mm PROUD of the back face, because JP asked for
# "big beautiful tactile buttons you can feel" and a boss is the obvious reading of that.
# It cannot work: PRINT-SHEET.md prints this part BACK FACE DOWN with no supports, so a
# proud cap is the LOWEST feature on the part. A 55 x 92mm shell would balance on two
# hexagons totalling ~74mm2 with the whole back face 1.20mm in the air. The bbox even
# confirmed it — the part grew from 14.40 to 15.60mm deep, exactly the cap height, which is
# how the boss was caught. Raised features on a bed face are self-defeating; recessed ones
# are free, because a few layers bridge over an 8mm void and nothing else changes. It is the
# same reason the front bezel's debossed hexes print in ITS bed-face orientation.
#
# A debossed hexagon with a crisp rim, plus the 0.60mm slot moat around the island, is
# genuinely findable — a fingertip resolves steps two orders of magnitude smaller than this.
# It also matches the debossed hexagons JP asked for on the bezel, so the two faces speak
# the same language rather than one embossing and the other engraving.
#
# AND IT REMOVES A HAZARD RATHER THAN MITIGATING ONE. Holding BOOT low across a reset enters
# ROM download mode, which presents as a brick. Proud caps make that reachable by anything
# resting on the case; recessed ones cannot be pressed by a flat object at all. The unequal
# DEPTHS still give a thumb two independent discriminators in the dark — size and depth — on
# a case that carries no lettering.
# ⚠️ WERE 0.90 / 0.50, AND NEITHER WAS A WHOLE NUMBER OF LAYERS AT ANY LAYER HEIGHT THIS PROJECT
# USES — 5.625 / 3.125 at 0.16 and 4.5 / 2.5 at 0.20. Both recess floors landed mid-layer, on the
# visible back face, and issue #26 did not name either of them: it named the two constants that
# happened to divide 0.16. These are now 4 and 2 layers of the SHELL's own height.
# THE DIFFERENTIAL IS WHAT MATTERS AND IT IS PRESERVED EXACTLY. 0.90-0.50 and 0.80-0.40 are both
# 0.40mm, so the "two independent discriminators in the dark — size and depth" property is
# untouched; only the absolute depths moved, and both got shallower by the same amount.
DEBOSS_BIG   = 4 * LAYER_H_SHELL   # 0.80  BOOT/volume, the one you reach for
DEBOSS_SMALL = 2 * LAYER_H_SHELL   # 0.40  RESET, deliberately shyer under the finger
CAP_INSET  = 1.00    # cap circumradius is R - this, leaving a shoulder inside the island
                     # edge so the raised cap can never bridge the slot and weld shut.
# ⚠️ WAS 0.90, WHICH IS 5.625 LAYERS AT 0.16 AND 4.5 AT 0.20 — MID-LAYER AT BOTH. This is the
# STRAIN-CRITICAL dimension: `strain = (t/2)*theta/L` is computed to three significant figures
# throughout this file and asserted at <=2.0%, and t was whatever the slicer rounded 0.90 to. A
# precise calculation on a dimension nobody controlled. 0.90 -> 1.00 would have raised strain 11%
# against an assert that never knew.
# 0.80 IS CHOSEN OVER 1.00 FOR TWO REASONS. It is 4 layers at 0.20 AND 5 layers at 0.16, so it
# stays aligned whichever way the PRINT-SHEET table lands — the only value in this block that is
# robust to that decision. And it moves strain DOWN ~11% (t scales it linearly), which is the safe
# direction on a flexure whose failure mode is cracking. ⚠️ It also softens the press slightly;
# 1.00 would firm it up at +11% strain, still inside the 2.0% limit. That is a FEEL choice and
# therefore JP's — see the report on issue #26.
HINGE_T    = 4 * LAYER_H_SHELL   # 0.80  living-hinge thickness
# FLEXURE LENGTH IS PER-BUTTON, AND IT IS A STRENGTH FIX, NOT A FEEL ONE.
#
# The hinge rotation is not a free variable: theta = pip travel / the pip's distance from the
# hinge. The SMALLER cap has the LARGER angle, because its pip sits on a shorter arm — 5.6deg
# on RESET against 3.5deg on BOOT. Bending strain is (t/2)*theta/L, so at a shared 1.0mm
# flexure the small button was the one being over-strained:
#
#   BOOT   t=0.90  L=1.0  ->  2.75%
#   RESET  t=0.90  L=1.0  ->  4.37%   past PLA's ~2% yield, into its 4-6% break band
#
# A teammate, reasoning about FEEL rather than strength, proposed thickening RESET's hinge to
# 1.40mm — correctly observing that with equal thickness the smaller hex always presses
# lighter, which is backwards from "deliberately shyer under the finger". But strain scales
# with t, so that fix takes RESET to 6.79% and cracks the hinge on the bench. The feel defect
# is real and the proposed cure destroys the part.
#
# Lengthening the flexure fixes what actually breaks and costs nothing. ⚠️ THE SHIPPED PAIR IS
# 2.29% (BOOT) AND 2.18% (RESET) — an earlier version of this comment said "2.18% and 1.37%",
# and 1.37% is BOOT at L = 2.00, a flexure length BOOT does not have. Both figures were real
# and one of them described a configuration that was never built. Same discipline the firmware
# side arrived at independently: state which configuration you RAN, not which conclusion you
# reached. Both pass the 2.0% assert (`_strain <= 0.020`; this line said 2.5%), so nothing was
# broken — which is exactly why it survived.
# The
# force ordering stays mildly inverted, and that is the right trade — an easy RESET is an
# annoyance, a cracked RESET hinge is a dead part, and RESET is the recoverable button anyway.
# Findability is already differentiated by size and deboss depth, which cost no strain at all.
HINGE_L_BOOT  = 1.20
HINGE_L_RESET = 2.00
# SLOT_W moved UP to the island-solve block — `_island_cx()` needs it. A second definition here
# would shadow it and the islands would silently solve against a stale width.
# LED_WIN_D / DIFF_D deleted with the rear glow window and the diffuser disc. The fine
# hex field on the back now carries the WS2812's light, and JP is printing in WHITE — a
# translucent shell, so the glow leaves through the wall as well as the holes. Many small
# apertures in a translucent panel scatter; one 12mm bore behind a printed disc just shows
# you the die.

GLASS_GAP  = 0.40    # bezel NEVER touches the glass: LCD 2.3+/-0.1 & TP 1.0+/-0.1
                     # stack up to +0.2, so 0.40 keeps 0.2 clear worst-case.
SEAM_Z     = GLASS_Z + GLASS_GAP             # +4.70  shell wall top = bezel underside
CAV_FLOOR  = BACK_MAX - CAV_CLR              # -7.10
FRONT_Z    = SEAM_Z + BEZEL_T                # +7.70
BACK_Z     = CAV_FLOOR - WALL                # -9.70
OX0, OX1   = -(FIT+WALL), BW+FIT+WALL        # -2.95 .. 52.95   (55.90 wide)
OY0, OY1   = -(FIT+WALL), BL+FIT+WALL        # -2.95 .. 88.95   (91.90 tall)
OUT_R      = CORNER_R + FIT + WALL           # 6.45
PK0, PK1   = -FIT, BW+FIT
PY0, PY1   = -FIT, BL+FIT
POCK_R     = CORNER_R + FIT

# ============================================================================
# 3. helpers
# ============================================================================
def bx(x0,x1,y0,y1,z0,z1):
    return Pos(x0,y0,z0) * Box(x1-x0, y1-y0, z1-z0,
                               align=(Align.MIN,Align.MIN,Align.MIN))

def rbox(x0,x1,y0,y1,z0,z1,r):
    sk = RectangleRounded(x1-x0, y1-y0, r)
    return Pos((x0+x1)/2,(y0+y1)/2,z0) * extrude(sk, z1-z0)

def rrect_y(cx, cz, w, h, r, y0, depth):
    """Rounded rectangle in the XZ plane, extruded along +Y.

    Same trick as the Cylinder seat it replaces: build the profile in XY, extrude in
    +Z, then Rot(-90,0,0) maps +Z onto +Y so the prism drives through the front wall.
    """
    sk = RectangleRounded(w, h, r)
    return Pos(cx, y0, cz) * (Rot(-90,0,0) * extrude(sk, depth))


def chamfer_outline(part, z, size, what):
    """45deg chamfer on the EXTERIOR PERIMETER edges lying in the plane z.  Issue #35.

    Generic on purpose: the bezel is owned by another agent right now, and when its front
    perimeter wants the same treatment it should be one call with the same constant rather
    than a second implementation that drifts from this one.

    >>> THE SELECTOR IS "IN THE PLANE **AND** TOUCHING THE PART'S OWN SILHOUETTE". <<<
    The back face at z=BACK_Z also carries nine label grooves, 113 hex apertures, four
    counterbores, the SD slit and the speaker relief — every one of them has edges in that
    plane, and chamfering the lot would be a catastrophe dressed as a one-liner. An edge
    qualifies only if it ALSO reaches an extreme of the part's own bounding box, which the
    outline does by definition and no interior feature does.

    45deg chamfer, not a roundover, and that is an FDM decision rather than a style one: a
    roundover's lower quadrant is an overhang into the bed and prints ragged on a face-down
    part, while a chamfer is self-supporting in every orientation this project uses.
    """
    bb = part.bounding_box()
    sel = []
    for e in part.edges():
        eb = e.bounding_box()
        if abs(eb.min.Z - z) > 1e-6 or abs(eb.max.Z - z) > 1e-6:
            continue
        if (eb.max.X > bb.max.X - 1e-6 or eb.min.X < bb.min.X + 1e-6
                or eb.max.Y > bb.max.Y - 1e-6 or eb.min.Y < bb.min.Y + 1e-6):
            sel.append(e)
    assert sel, (
        f"{what}: no perimeter edge found in the plane z={z:.3f}. The selector has drifted, "
        f"and a chamfer that selects nothing is SILENTLY ABSENT — which is exactly how #38's "
        f"gable hid through three builds")
    return chamfer(sel, length=size)


def cyl(x,y,z0,z1,d):
    return Pos(x,y,z0) * Cylinder(d/2, z1-z0,
                                  align=(Align.CENTER,Align.CENTER,Align.MIN))

# ---- BEZEL FACE: debossed honeycomb + the hearth-wyrm mark ----
# JP: "we should debossed hexagons on the front of the front bezel with the ember logo on the
# top left", then, on seeing the hero render: "the case hero i just was shown doesn't have the
# debossed hexagons on the front bezel — or the logo". Correct, and the figure was being
# honest: this was designed, discussed at length, and never wired into front_bezel(). A
# decision recorded only in conversation is not in the part.
#
# EVERYTHING HERE IS A RECESS, AND THAT IS FORCED. The bezel prints FRONT FACE DOWN on the
# bed, so any raised feature on this face becomes the lowest point of the part and the bezel
# lands on its own logo. Same trap that killed the raised button caps on the back shell, in
# the same session, on the opposite face — which is the tell that it is a property of the
# process rather than a one-off mistake: on a bed face, relief only goes inward.
BEZEL_DEBOSS = 5 * LAYER_H_BEZEL  # every debossed feature on the front face. EXACTLY 5 layers at
                      # 0.16mm PRINT-SHEET specifies for this part. It was 0.45, which is
                      # 2.8125 layers — the recess floor landed mid-layer and the comment
                      # claimed "3 layers at 0.15", a layer height this part does not use. Two
                      # reviewers flagged it independently. The slicer would have rounded it
                      # harmlessly, but a depth that is an exact multiple means the floor is a
                      # real layer boundary rather than wherever the rounding fell.
                      # ⚠️ 3 LAYERS (0.48) DID NOT READ. JP printed that bezel and asked for the
                      # wyrm, the side hexes and the bottom hex field all deeper (#34) — size
                      # unchanged, `BEZ_AFLAT` 2.60 stays, and the issue's own title said
                      # "bigger bottom hexes" before the body retracted it. Depth only, and
                      # global, because every region moved together.
                      # THE FLOOR THIS LEAVES IS MEASURED, NOT ASSUMED. Ray-cast on a 0.4mm grid
                      # over the exported bezel at 0.48: 3899 of 3901 debossed sample points sat
                      # on exactly 2.520mm of web = a full 3.00 slab minus the deboss, with NO
                      # back-side thinning anywhere. The four screw pilots DO reach up into the
                      # slab (to SEAM_Z+1.5, leaving only 1.50mm there) but every debossed region
                      # is held off them — the hex field by a BOSS_D/2 + BEZ_MARGIN + R keepout,
                      # the wyrm by starting at x = 4.0 + BOSS_D/2 + MARK_MARGIN. So the binding
                      # number really is the nominal one: 5 layers leaves 2.20mm, clearing the
                      # 2.00 assert below by 0.20. The shell already runs DEBOSS_BIG = 0.80 on a
                      # 2.60 wall and keeps far less than this.
BEZ_AFLAT    = 2.60   # hex across flats. Finer than the back's 3.20 — this face is read
                      # from arm's length, and the brow is only 13.69mm tall.
BEZ_WEB      = 0.70   # material between cells. ⚠️ NOT "two extrusion widths at a 0.4mm
                      # nozzle", which this comment claimed: two 0.40mm extrusions is 0.80, so
                      # 0.70 is 1.75 of them. It prints as ONE wide extrusion rather than two
                      # lines — solid, but the edges round over and the cells read slightly
                      # larger than drawn. Kept at 0.70 because that is acceptable on a
                      # decorative face and raising it would shrink the cell counts the region
                      # asserts are calibrated against; 0.85-0.90 if you ever want two genuine
                      # lines. The comment is fixed rather than the number precisely because a
                      # stated-as-fact justification is what licenses a wrong edit later.
                      # (HEX_WEB = 0.90 on the back face IS 2.25 widths, so that one is two
                      # lines and its comment is right.)
MARK_MARGIN  = 1.00   # the MARK's keepout, deliberately tighter than the cells' BEZ_MARGIN.
                      # Not a fudge to make it fit — the constraint is different. A hex cell
                      # can land anywhere, including beside the r6.45 corner fillets, so it
                      # needs the conservative figure. The mark's ink sits at x 7.700..33.351
                      # (measured on the solid, not transcribed — it read 7.90..34.90), where
                      # the outer silhouette is a STRAIGHT edge (fillet influence ends by
                      # x=3.5) and the lower bound is the screen window. 1.00mm of face
                      # material beside a 0.48mm-deep cosmetic recess, with 2.52mm of bezel
                      # still under it, is structurally uninteresting.
                      #
                      # It exists because the assert below caught the mark occupying 11.25 of
                      # 11.29mm of usable brow — 0.04mm of slack, which is a coincidence
                      # wearing a fit's clothing. The honest options were a tighter margin with
                      # a stated reason or a smaller mark, and the mark cannot shrink: its
                      # scale is pinned by the 0.90mm print floor.
BEZ_MARGIN   = 1.20   # keepout from the outer edge, the screen window, the mic flare AND the
                      # four screw bosses. ⚠️ An earlier version of this comment named three
                      # keepouts and the code implemented one and a half: the window was tested
                      # only on its BOTTOM edge and only in the chin, the mic flare was never
                      # tested anywhere (it held solely because the brow is excluded), and the
                      # screw bosses were not considered at all — so 4 chin cells overlapped a
                      # 2.50mm pilot and 5 more the 5.40mm pad, thinning the roof over a
                      # fastener from 1.50 to 1.05mm, and the mark overlapped the (4,82) boss
                      # pad by 1.18mm. The rails' clearance from the window's vertical edges
                      # was 1.575mm BY LUCK. A comment that lists the keepouts is not a test
                      # that applies them, and this one was read as if it were for hours.

def _inside_rrect(px, py, x0, x1, y0, y1, r, m=0.0):
    """Is (px,py) inside a rounded rectangle, inset by m? Standard rounded-rect distance.

    This exists because the bezel's outline is a RectangleRounded with a 6.45mm corner, and a
    naive x/y range test lets cells sit in the corner voids where there is no material — a
    hex tiling that pokes out of the part's own silhouette. At x=1.0 the top edge is at 88.45,
    not 88.95, purely because of the corner arc.
    """
    dx = max(x0 + r - px, px - (x1 - r), 0.0)
    dy = max(y0 + r - py, py - (y1 - r), 0.0)
    return math.hypot(dx, dy) <= r - m

def _bezel_cells():
    """Pointy-top hex cells on the bezel face. Returns (solid, {region: count}).

    TWO REGIONS, GENERATED SEPARATELY, AND COUNTED SEPARATELY. The first version filtered one
    global staggered grid and produced 75 cells — all of them in the CHIN, none on the rails,
    because the nearest grid column missed the rail's 0.75mm-wide usable band by 0.05mm. That
    is the worst possible outcome: the stand covers 86% of the chin and 0% of the rails, so
    the entire motif landed on the one surface you cannot see while docked.
    ⚠️ AND THE ASSERT PASSED. It read `_n >= 60`, and 75 >= 60 is true. A TOTAL ABSORBED A
    COMPLETE REGIONAL ABSENCE — the same shape as every other proxy failure recorded in
    docs/verification.md: the number was real, it just wasn't the property. Hence a dict of
    per-region counts and a non-empty assert on each, which no single total can satisfy
    vacuously. If you add a region, add its count and its assert.

    The rails get an explicit CHAIN rather than a filtered tiling, because a 3.35mm usable
    width admits exactly one column and whether that column exists should not depend on where
    a global grid's phase happens to fall.

    POINTY-TOP here (rotation=30), unlike the button caps: this is decorative lattice with no
    hinge to hem, so it follows the honeycomb pitch the rest of the case uses.

    The brow is deliberately EXCLUDED. It carries the wyrm mark, and a mark reads better
    against a calm field than against texture — also the mic flare and the top corner arcs
    turn the brow into a fragmented strip where whole cells barely fit.
    """
    R = BEZ_AFLAT / math.sqrt(3)          # circumradius: pointy-top spans R*sqrt(3) across
    px, py = BEZ_AFLAT + BEZ_WEB, 1.5 * R + BEZ_WEB * math.sqrt(3) / 2
    win = (VA[0]-WIN_MARGIN, VA[1]+WIN_MARGIN, VA[2]-WIN_MARGIN, VA[3]+WIN_MARGIN)
    out = None
    cnt = {"chin": 0, "rails": 0}

    def _fits(x, y):
        # inside the part's rounded outline...
        if not all(_inside_rrect(x + R*math.cos(math.radians(a+30)),
                                 y + R*math.sin(math.radians(a+30)),
                                 OX0, OX1, OY0, OY1, OUT_R, BEZ_MARGIN)
                   for a in range(0, 360, 60)):
            return False
        # ...clear of the mic flare (2.30 radius)...
        if math.hypot(x-MIC[0], y-MIC[1]) < 2.30 + BEZ_MARGIN + R:
            return False
        # ...clear of all four screw bosses, on the PAD diameter not the pilot. The pad is
        # what must stay solid: a cell over the 2.50 pilot is a hole into a fastener, and a
        # cell over the 5.40 pad thins the roof over it to 1.05mm.
        for (hx, hy) in HOLES:
            if math.hypot(x-hx, y-hy) < BOSS_D/2 + BEZ_MARGIN + R:
                return False
        # ...and clear of the screen window on ALL FOUR edges, not just the bottom one.
        if not (x + R < win[0]-BEZ_MARGIN or x - R > win[1]+BEZ_MARGIN
                or y + R < win[2]-BEZ_MARGIN or y - R > win[3]+BEZ_MARGIN):
            return False
        return True

    def _cell(x, y):
        return Pos(x, y, FRONT_Z - BEZEL_DEBOSS) * extrude(
                   RegularPolygon(R, 6, rotation=30), BEZEL_DEBOSS + 1)

    # --- CHIN: a proper staggered honeycomb, full width, below the window ---
    j, y = 0, OY0
    while y <= win[2]:
        x = OX0 + (px/2 if j % 2 else 0.0)
        while x <= OX1:
            if _fits(x, y):
                out = _cell(x, y) if out is None else out + _cell(x, y)
                cnt["chin"] += 1
            x += px
        y += py
        j += 1

    # --- RAILS: one explicit chain up each side of the window ---
    # Pitch is 2R + BEZ_WEB, so the vertical gap between cells matches the web thickness used
    # everywhere else. That consistency reads more strongly at arm's length than sharing the
    # chin's row rhythm would, and a lone column of a staggered tiling (pitch 3R) would look
    # like a dotted line rather than a chain.
    for rc in ((OX0 + win[0]) / 2.0, (win[1] + OX1) / 2.0):
        y = win[2] + R
        while y <= win[3] - R:
            if _fits(rc, y):
                out = _cell(rc, y) if out is None else out + _cell(rc, y)
                cnt["rails"] += 1
            y += 2*R + BEZ_WEB
    return out, cnt

def _bezel_mark():
    """The hearth-wyrm, debossed into the brow. Returns (solid, w, h, min_feat).

    ⚠️ "AT TOP-LEFT" WAS IN THIS LINE UNTIL IT WAS MEASURED, and the file knew better 27 lines
    down, where the comment on mirroring already names "the 'not top-left' cost" as something
    JP accepted. Measured on the solid: ink x 7.700..33.351, y 76.240..87.530, 11.250mm tall.
    So: top, and left of centre, but not in the corner.

    >>> TWO CENTRES LIVE IN THIS AREA AND THEY ARE DIFFERENT QUANTITIES. NAME WHICH ONE. <<<

        the MARK's ink centre         20.525    ->  4.475mm LEFT of the x=25.0 centreline
        the MARK + PORT group centre  25.000    ->  dead on it, and asserted below

    The composition is the PAIR regarding each other — a hearth-wyrm attending the port sound
    enters through — so the thing that is centred is the group, from the mark's left ink edge
    to the port's right edge: `(_mx0 + (MIC[0] + 2.30)) / 2 == 25.000`, exactly. The mark alone
    being off-centre is not a defect, it is what centring the group requires.

    Both sentences are here because they were briefly taken for contradictions of each other,
    and a corrected number sitting next to an uncorrected one WITHOUT ITS SUBJECT NAMED is how
    a reader concludes one of them must be wrong. State the subject, not just the value.

    ONE CREATURE, NOW RENDERED FOUR WAYS — the device draws it as RLE spans, the website
    traces it to SVG, the stand's grille is cut from it, and this debosses it. All four read
    esphome/art/dragon.py, so re-posing the wyrm moves all four.

    ⚠️ AND "THE SCALE IS SET BY THE PRINT FLOOR" IS BACKWARDS. This paragraph used to end
    "the mark is as large as the floor allows rather than as large as the brow allows", and the
    direction is wrong: SCALING UP MULTIPLIES EVERY FEATURE SIZE BY s, so a larger mark is
    strictly safer to print. The print floor bounds the scale from BELOW. It cannot cap the
    mark's size and never could.

    The magnitude was wrong too. `WYRM_MIN_FEATURE` is 4*px of the source canvas — a
    conservative BOUND, not a measurement of the creature (see tools/minfeature.py, now the
    fourth metric, not the third). Measured threshold-free as the smallest ridge value of the
    distance transform, the silhouette's thinnest feature is 2.4667mm, so at s = 0.90/1.2333
    the mark's real thinnest feature is 1.800mm — TWICE the 0.90mm floor, not on it.

    So the floor would permit this mark at half its current scale, and permits any larger scale
    without limit. Whatever should set the size, it is not printability: the candidates are the
    brow's usable height and MARK_MARGIN's keepout, and neither has been measured against the
    mark as built. NOT RESCALED HERE — JP has a printed bezel in hand and this geometry is
    byte-identical across that correction. Recorded so the next person sizing it does not
    inherit the inverted reason.
    """
    s = 0.90 / _W.WYRM_MIN_FEATURE
    h = _W.WYRM_H * s

    # MIRRORED, AND THAT IS THE WHOLE COMPOSITION. dragon.py line 48: "Faces LEFT." Unmirrored,
    # the creature's TAIL points at the mic port and its gesture exits off the face — so the
    # port became the end of a sentence with nothing leading to it, and the 12mm before it read
    # as dead air rather than as spacing. Mirrored, the head faces the flare and the same
    # emptiness becomes direction: the port is where sound enters, so a hearth-wyrm attending it
    # is the device's function drawn on its own face.
    #
    # ⚠️ THE COST, ON THE RECORD: this hands the creature. Three other renderings (the device's
    # RLE spans, the website's SVG, the stand's grille) share one handedness and this one does
    # not, so "one creature, four renderings" is now "…one of them mirrored". JP was shown that
    # cost and the "not top-left" cost and chose this anyway.
    #
    # READ IT AS A FRIEZE, NOT A LOGO. The ink fills the canvas height completely
    # (y 0.0000..15.4166 of 15.4167) and the scale is floored by printability, so it CANNOT be
    # given a ground — and a frieze fills its band by definition. That reframing is what makes
    # the full-height fit correct rather than cramped, and the port sharing the register
    # natural. It is also why this is not the coiled-ember mark: it is character art in a band.
    _ix0 = min(r[0] for r in _W.WYRM)
    _ix1 = max(r[0] + r[2] for r in _W.WYRM)

    # x0 IS DERIVED TWICE OVER, NOT CHOSEN.
    #
    # First by the screw boss: the mark once started at x=1.00, which put it 1.18mm INSIDE the
    # (4,82) boss's 5.40mm pad, thinning the bezel roof over a driven self-tapper from 1.50 to
    # 1.05mm. Invisible to the clearance check because the pilot stops at SEAM_Z+1.5 and the
    # front face is 1.5mm above it — an absence cannot collide.
    #
    # Second, and this is the part worth checking rather than trusting: the constraint is on the
    # INK, not on the canvas. Mirrored, the leftmost ink sits 0.900mm inside the canvas origin,
    # so a canvas origin of 6.80 puts the first ink at exactly 7.70 = boss pad + MARK_MARGIN.
    # The reviewer's 6.80 and my 7.70 looked like a disagreement and were the same number
    # measured from different edges.
    #
    # The payoff is not spacing, it is centring: ink 7.70..33.35 plus the flare's right edge at
    # 42.30 gives a creature-and-port group centred on 25.00 — the face's exact centreline. The
    # 4.35mm gap reads as attention (2.0 crowds, 5.0 drifts, both rendered), and the leftover
    # 9.45mm becomes plain left margin, which is invisible.
    _inset_l = (_W.WYRM_W - _ix1) * s          # mirroring swaps which inset leads
    x0 = (4.0 + BOSS_D/2 + MARK_MARGIN) - _inset_l
    y0 = (VA[3] + WIN_MARGIN) + MARK_MARGIN
    # ⚠️ EVERY SPAN IS INFLATED BY EPS, AND THE STL IS NON-MANIFOLD WITHOUT IT.
    #
    # The mark is 104 row-runs stacked into a staircase. Wherever one row's run ENDS at exactly
    # the x where the next row's run BEGINS, the two boxes touch along a single vertical edge —
    # and edge-only contact between solids is non-manifold by definition, not a rounding
    # artefact. It produced 9 non-manifold edges and 22 mis-oriented directed edges in
    # ember-front-bezel.stl, all of them at z = 7.700 and 7.220: the front face and the deboss
    # floor, inside the wyrm's footprint. The other three parts were clean.
    #
    # Inflating each span by EPS in BOTH x and y turns every such corner kiss into a genuine
    # 2*EPS square prism of overlap, which unions cleanly. It must be both axes: y alone leaves
    # the contact zero-width in x and still an edge. At 1.5um the silhouette grows 3um overall —
    # three orders of magnitude below the 0.90mm print floor and below the resolution of any
    # instrument here — and it only ever makes features THICKER, so no printability claim
    # weakens.
    #
    # THE REASON THIS SURVIVED SO LONG IS WORTH MORE THAN THE FIX. The repo asserted "all parts
    # watertight, 0 non-manifold edges" on the strength of a check that imported each STL and
    # counted boundary edges — but build123d's import_stl returns a single Face with ZERO edges
    # and zero volume, so the count was 0 because there was nothing to count. A perfect result
    # about nothing. The real test is arithmetic on the triangles: every undirected edge shared
    # by exactly two, every directed edge appearing exactly once.
    # EPS MUST EXCEED THE MESHER'S TOLERANCE, NOT MERELY EXCEED ZERO. At 1.5um the overlap was
    # real in the BRep and vanished in the triangulation — the tessellator collapsed a 3um-wide
    # prism back to a single edge, so the solid was manifold and the exported mesh was not. That
    # took 9 non-manifold edges to 3 and stopped, which is the tell: a fix that helps but does
    # not finish is usually the right idea at the wrong magnitude. 20um is above any linear
    # deflection used here and still 45x below the 0.90mm print floor.
    EPS = 0.020
    out = None
    for (rx, ry, rw, rh) in _W.WYRM:
        mx = _W.WYRM_W - (rx + rw)             # mirror in X about the canvas centre
        b = bx(x0 + mx*s - EPS, x0 + (mx + rw)*s + EPS,
               y0 + ry*s - EPS, y0 + (ry+rh)*s + EPS,
               FRONT_Z - BEZEL_DEBOSS, FRONT_Z + 1)
        out = b if out is None else out + b
    # return the INK extents, not the canvas: every assert downstream is about where the
    # creature actually is, and the canvas carries up to 0.9mm of nothing on either side.
    ink0 = x0 + (_W.WYRM_W - _ix1) * s
    ink1 = x0 + (_W.WYRM_W - _ix0) * s
    return out, ink0, ink1 - ink0, h, _W.WYRM_MIN_FEATURE * s

def cap_hex_pts(cx, cy, R):
    """The six corners of a FLAT-top hexagon, in mm, counter-clockwise from +X.

    ONE SOURCE FOR THE CAP OUTLINE. This exists because the outline was previously typed
    twice — once as a solid here and once as a hand-written polygon in
    `tools/make_renders.py` — and the two copies were free to disagree forever with nothing
    to notice. They did: the solid and the figure were both rectangles, JP asked for
    hexagons, and only the figure was ever looked at. A second hand-drawn copy of geometry
    is not documentation of the geometry, it is a rumour about it.

    Flat-top means a vertex at +/-X and a flat edge at +/-Y: 2R across corners, R*sqrt(3)
    across flats. The +Y flat is the hinge, which is the whole reason for this orientation.
    """
    return [(cx + R*math.cos(math.radians(a)), cy + R*math.sin(math.radians(a)))
            for a in range(0, 360, 60)]

def cap_hex_top_y(cy, R):
    """Y of the flat-top hexagon's +Y edge — where the hinge lives."""
    return cy + R*math.sqrt(3)/2

def cap_hinge_len(cx):
    """Thinned-flexure length for the cap at board x=cx. Keyed on the coordinate, like
    cap_geometry, and for the same reason: sides flip between figures, coordinates do not."""
    return HINGE_L_BOOT if cx == BTN_BOOT_X else HINGE_L_RESET

def cap_center_x(cx):
    """Island centre X for the cap actuating the switch at board x=cx — NOT the switch's x.

    Added as a separate function rather than a fourth element of cap_geometry()'s tuple
    deliberately: that tuple has six call sites and two of them are inside a block another
    agent is editing right now. Widening a shared signature mid-flight breaks their work with a
    stack trace that looks like their bug. A new function breaks nothing.
    """
    return CAP_CX_BOOT if cx == BTN_BOOT_X else CAP_CX_RESET

def cap_geometry(cx):
    """(cy, R, deboss_depth) for the cap at board x=cx. THE single derivation.

    Keyed on the coordinate rather than an index or a side, per the never-say-left-or-right
    rule above: the apparent side flips between three figures of this same part, so a caller
    that asks for "the big one" by position is correct in one figure and silently wrong in
    the others. Asking by x cannot be mirrored by a camera.
    """
    big = (cx == BTN_BOOT_X)
    R = BTN_R_BIG if big else BTN_R_SMALL
    return (_cap_cy(R), R,
            DEBOSS_BIG if big else DEBOSS_SMALL)

def hexp(cx, cy, R, z0, z1):
    """Flat-top hexagonal prism. Deliberately NOT rotation=30 — see BTN_R_BIG."""
    return Pos(cx, cy, z0) * extrude(RegularPolygon(R, 6), z1 - z0)

def cone(x,y,z0,z1,d0,d1):
    return Pos(x,y,z0) * Cone(d0/2, d1/2, z1-z0,
                              align=(Align.CENTER,Align.CENTER,Align.MIN))

# ============================================================================
# 4. FRONT BEZEL   -- the part that unblocks printing
# ============================================================================
def front_bezel():
    p  = rbox(OX0,OX1,OY0,OY1, SEAM_Z, FRONT_Z, OUT_R)
    # screen window
    w  = (VA[0]-WIN_MARGIN, VA[1]+WIN_MARGIN, VA[2]-WIN_MARGIN, VA[3]+WIN_MARGIN)
    sk = RectangleRounded(w[1]-w[0], w[3]-w[2], 1.5)
    p -= Pos((w[0]+w[1])/2,(w[2]+w[3])/2, SEAM_Z-1) * extrude(sk, BEZEL_T+2)
    # mounting bosses: PCB top face up into the bezel body
    for (hx,hy) in HOLES:
        p += cyl(hx,hy, PCB_TOP, SEAM_Z, BOSS_D)
        p -= cyl(hx,hy, PCB_TOP-0.01, SEAM_Z+1.5, PILOT_D)
    # ---- MIC: defined acoustic port + collar down to just above the PCB ----
    mx,my = MIC
    p += cyl(mx,my, PCB_TOP+0.30, SEAM_Z, 5.0)          # collar (tube wall)
    p -= cyl(mx,my, PCB_TOP+0.20, FRONT_Z+1, 2.40)       # the port bore
    p -= cone(mx,my, FRONT_Z-0.90, FRONT_Z+0.01, 2.40, 4.60)  # outside flare
    # ---- debossed honeycomb + the hearth-wyrm mark, both cut INTO the front face ----
    _cells, _cnt = _bezel_cells()
    if _cells is not None:
        p -= _cells
    _mark, _mx0, _mw, _mh, _mf = _bezel_mark()
    p -= _mark
    # A DEBOSS THAT BREAKS THROUGH IS A HOLE. The bezel is BEZEL_T over the glass and this
    # face is the only thing between a finger and the LCD, so assert the remaining thickness
    # rather than trusting that 0.45 "looks shallow".
    assert BEZEL_T - BEZEL_DEBOSS >= 2.00, (
        f"a {BEZEL_DEBOSS}mm deboss leaves only {BEZEL_T-BEZEL_DEBOSS:.2f}mm of bezel over "
        f"the glass")
    # PER-REGION, never a total: see _bezel_cells() for the run where 75 >= 60 passed with
    # the rails completely empty.
    # THRESHOLDS, AND WHY THEY MOVED. The chin was 75 cells and is now 57: adding the screw
    # boss keepout removed 9 cells per boss and two of the four bosses are in the chin, so the
    # 18-cell drop is accounted for rather than tolerated. The floors below are set to catch a
    # region COLLAPSING — which is the failure this assert exists for, after 75 cells all
    # landed in the chin and the rails got none — not to track the exact count. Do not simply
    # lower a floor to make a build pass; work out where the cells went first.
    for _rg, _min in (("chin", 50), ("rails", 20)):
        assert _cnt[_rg] >= _min, (
            f"only {_cnt[_rg]} hex cells landed on the bezel {_rg} (need >={_min}) — "
            f"a keepout or the grid phase has eaten the region. Counts: {_cnt}")
    assert _mf >= 0.90, f"wyrm mark min feature {_mf:.2f}mm is under the 0.90mm print floor"

    # ⚠️ THE MARK MUST BE ONE PIECE, AND NO MINIMUM-FEATURE TEST CAN CHECK THIS.
    #
    # The shipped mark was TWO components: a body, and the head floating 1.215mm above the
    # shoulders with no neck. Two upstream bugs — head_mask() returns the sprite unposed at
    # dragon-local (0,0) while the device translates it, and dragon.py's neck_spans() is drawn
    # by the device and omitted from body|head entirely.
    #
    # A GAP IS NOT A THIN FEATURE. Morphological opening measures the narrowest place material
    # EXISTS; it is structurally blind to material that is absent. So 1.23mm minimum feature
    # and 0.19% opening loss were both true, both green, and both silent about a logo that had
    # come apart. The generator now exports the component count precisely so this cannot
    # recur quietly.
    assert _W.WYRM_COMPONENTS == 1, (
        f"the wyrm mark is {_W.WYRM_COMPONENTS} disconnected pieces (largest gap "
        f"{getattr(_W, 'WYRM_GAP', float('nan')):.3f}mm at generator scale) — it will print as "
        f"a creature with a detached head. Regenerate with body|neck|posed-head.")

    # THE GAP TO THE FLARE IS THE COMPOSITION, so assert the gap rather than a keepout.
    # 2.0mm crowds and 5.0mm drifts — both were rendered and looked at — and 3.5..4.5 reads as
    # attention. Below the floor it stops being a creature regarding a port and becomes a
    # creature bumping into a hole.
    _gap = (MIC[0] - 2.30) - (_mx0 + _mw)
    assert 3.00 <= _gap <= 5.50, (
        f"wyrm head sits {_gap:.2f}mm from the mic flare — outside the 3.00..5.50 band where "
        f"it reads as attention rather than as collision or as dead air")
    # AND THE PROPERTY THE COMPOSITION ACTUALLY RESTS ON: the creature-and-port group is
    # centred on the face. This is the one thing that makes the arrangement deliberate rather
    # than merely spaced — ink 7.70..33.35 plus the flare's right edge at 42.30 centres on
    # 25.000, the exact face centreline, which turns 9.45mm of leftover into plain margin.
    # Nothing else here would notice if it drifted: every other assert is a clearance, and a
    # clearance is satisfied by any amount of slack in the wrong place.
    _centre = (_mx0 + (MIC[0] + 2.30)) / 2.0
    assert abs(_centre - BW/2) <= 0.40, (
        f"the wyrm-and-port group centres on x={_centre:.3f}, {abs(_centre-BW/2):.3f}mm off the "
        f"face centreline {BW/2:.3f} — the frieze reads as centred or it reads as an accident")
    # ...and must fit the brow with margin rather than by coincidence. It previously occupied
    # 11.28 of 11.29mm of usable height and sat 1.21mm from an outer silhouette whose keepout
    # is 1.20mm: both true, both luck, and neither would survive the mark changing size.
    # NOTE a bounding-box check cannot substitute for the outer one — the mark's bbox corner
    # sits INSIDE the r6.45 fillet while the geometry itself does not.
    _brow = OY1 - (VA[3] + WIN_MARGIN) - 2*MARK_MARGIN
    assert _mh <= _brow - 0.30, (
        f"wyrm mark is {_mh:.2f}mm in {_brow:.2f}mm of usable brow — under 0.30mm of slack "
        f"is a coincidence, not a fit")
    front_bezel.report = (_cnt, _mw, _mh, _mf)
    return p

# ============================================================================
# 5. BACK SHELL
# ============================================================================
# ============================================================================
# SIDE-WALL OPENINGS — DERIVED FROM THE COMPONENTS THEY EXIST TO CLEAR
# ============================================================================
#
# ⚠️ THIS IS THE FIX FOR THE FAILURE THAT CAUSED THE REPRINT, and it is structural rather than
# numeric. The channels used to be two hand-typed literals:
#
#     [(14.0,40.5),(44.0,56.0),(62.0,75.0)]     and     [(14.0,26.0),(29.0,42.0)]
#
# and the constant that NAMED the feature they served — the old `SD_PLATE` — had NO CONSUMERS.
# `grep` found it in its own definition and two comments, nothing else. So the coordinate and
# the opening were never connected by anything except a human reading both.
#
# ⚠️ A CONSTANT WITH NO CONSUMER CANNOT BE WRONG IN A WAY ANYTHING DETECTS. Nothing recomputes
# when it changes, no assert compares it to the geometry, and its only reader is a person who
# has to re-derive the link every time. That is why a 26.50mm opening with 18.54mm of nothing
# behind it survived every check in this file: the checks all compare the PART to the BOARD, and
# an opening over a component that isn't there is agreement, not conflict.
#
# Now the spans are computed from CONN_R / CONN_L / SD_SOCKET. A wrong coordinate MOVES an
# opening, and `_check_geometry()` asserts the converse — every span must have a component
# behind it. The dead-`GRILLE_SLOT_W` hazard this file already logs, one screenful above
# CAP_CX_BOOT, is the same shape; it recurred anyway, so this time the link is code.
CHAN_PAD      = 1.00   # lead-in each side of a connector footprint. The shipped non-phantom
                       # channels had 0.84 / 0.69 / 0.91, so 1.00 is not a tightening.
CHAN_RIB      = 1.20   # thinnest wall allowed between two openings; under this they MERGE
                       # rather than leaving a stringy fin. Three extrusions at a 0.4 nozzle.
SD_SLIT_INSET = 0.50   # slit is the socket span less this, so it cannot undercut the socket's
                       # own side walls while still clearing SD_CARD_W plus a finger.

def _merge_spans(spans, min_rib):
    """Sort, then merge any pair separated by less than min_rib.

    A rib thinner than a few extrusion widths is not a wall, it is a defect that happens to
    have a dimension — the same reasoning desk_stand() applies to its finger pockets."""
    out = []
    for a, b in sorted(spans):
        if out and a - out[-1][1] < min_rib:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]

def side_channels():
    """(spans on the x=BW edge, spans on the x=0 edge), derived from the component tables.

    The microSD slit goes on WHICHEVER EDGE THE SOCKET IS ON — read from SD_SOCKET, not typed.
    That is deliberate: the last time this was decided by a human reading a coordinate, the
    coordinate was a placeholder and the opening landed on the far side of the board."""
    hi = [(y0 - CHAN_PAD, y1 + CHAN_PAD) for (y0, y1) in CONN_R]
    lo = [(y0 - CHAN_PAD, y1 + CHAN_PAD) for (y0, y1) in CONN_L]
    slit = (SD_SOCKET[2] + SD_SLIT_INSET, SD_SOCKET[3] - SD_SLIT_INSET)
    (lo if _SD_CX < BW/2 else hi).append(slit)
    return _merge_spans(hi, CHAN_RIB), _merge_spans(lo, CHAN_RIB)

# ============================================================================
# 5a-bis. BACK-FACE LABELS  --  SD, VOL, a power symbol, MIC
# ============================================================================
#
# DEBOSSED, and for the same reason the button caps are: this face prints against the bed, so
# a raised feature becomes the lowest thing on the part and the shell balances on it. The
# depth is a whole number of the SHELL's layers -- see LABEL_DEBOSS for why it is 2 and not 3.
#
# ⚠️ MIRRORED IN X, AND THIS IS THE ONE THAT SHIPS BACKWARDS IF NOBODY WRITES IT DOWN.
# The back face is seen from -Z. For a viewer there with +Y up, their right-hand direction is
# forward x up = (0,0,1) x (0,1,0) = (-1,0,0) -- so model +X runs to their LEFT. Every glyph
# is therefore authored in READING space (u to the right as read) and mirrored on placement by
# _back_label(). The wyrm mark on the FRONT bezel is also mirrored, but for art-direction
# reasons, so it is not precedent for this and copying its sign would prove nothing.
#
# TWO SIZES, NOT ONE, and the split is forced rather than stylistic. The big cap is 13.27mm
# across flats, which caps a three-letter label at h=3.80. The flat back has room for h=5.50,
# and SD NEEDS it: at h=5.10 the S's upper counter pinches to 0.843mm against the 0.90 floor.
# Using the cap size everywhere would have put an unprintable S on the part; using the flat
# size everywhere would not fit on the cap.
import strokefont as _SF

LABEL_W      = 0.90            # groove width == this repo's nozzle floor, the same 0.90 the
                               # wyrm mark asserts. It is an ARGUMENT to the stroke font, not
                               # a consequence of a typeface -- see tools/strokefont.py.
LABEL_GAP    = 1.90            # centreline gap between glyphs -> exactly 1.00mm of material.
                               # 1.80 was tried and lands the gap ON 0.90, i.e. zero margin.
# ⚠️ WAS `3 * LAYER_H` = 0.48, i.e. three layers of the BEZEL's height applied to a SHELL feature
# — 2.4 layers at the shell's own 0.20. TWO layers, not three, and the reason is the pad assert
# below rather than taste: at 3 shell layers (0.60) the big cap keeps
# WALL - DEBOSS_BIG - LABEL_DEBOSS = 2.60 - 0.80 - 0.60 = 1.20, exactly ON the 1.20 floor, and a
# value sitting on a constraint boundary has no slack. 2 layers leaves 1.40.
LABEL_DEBOSS = 2 * LAYER_H_SHELL   # 0.40
LABEL_H_CAP  = 3.80            # centreline cap height on a button face (ink 4.70)
LABEL_H_FLAT = 5.50            # centreline cap height on the flat back  (ink 6.40)
LABEL_MARGIN = 0.80            # keepout from any edge or neighbouring feature
# ---- and two constants that exist only because a slice of the finished mesh was looked at ----
#
# >>> THE FIRST CUT OF THE CONNECTOR LABELS READ `SPKI2C` AND `BATUARTSD`. <<<
#
# Every assert passed. Each label cleared its 0.90mm floor, each sat on its own port, and no
# two ink boxes came within LABEL_MARGIN. And the result was unreadable, because LABEL_MARGIN
# is 0.80 while the material BETWEEN TWO GLYPHS of one word is LABEL_GAP - LABEL_W = 1.00 —
# so the space between two labels was SMALLER than the space inside one, and the eye correctly
# read them as a single word. A keepout is not a word space; nothing had ever needed the
# difference before because no two labels had ever been neighbours.
LABEL_WORD_GAP = 2 * (LABEL_GAP - LABEL_W)   # 2.00 — twice the material inside a word.
# 3x was tried first and does not fit: at 3.00 the UART label is forced down until its ink
# reaches into BAT's own channel, which trades a legibility defect for a naming one. 2.00 is
# the largest word space the left strip can carry with all three labels still over their own
# features, and it is double the 1.00mm that reads as a letter space.
# ⚠️ AND SHRINKING THE LABELS TO AFFORD IT IS NOT AVAILABLE, WHICH IS WORTH RECORDING BECAUSE
# IT WAS THE OBVIOUS MOVE AND IT FAILED ON THE FIRST BUILD. A 4.50 connector height was tried;
# `S` immediately went under the floor at 0.638mm, because the glyph is normalised and the
# 0.90 stroke is not, so every counter scales with h while the stroke does not:
#
#     S's material at h  =  (0.98 + 0.90) * h/5.50 - 0.90   ->  S needs h >= 5.27
#
# `SPK` contains an S, so the connector set cannot go below ~5.27 at all. Everything therefore
# stays at LABEL_H_FLAT, and the room for the word space is found in the PLACEMENT RULE
# instead — see _pack_labels and the ledger below.
PWR_R        = 2.70            # power-symbol ring, centreline radius (ink dia 6.30)
PWR_STEP_DEG = 12.0            # ring subdivision. Sagitta = r*(1-cos(6deg)) =
                               # 0.015mm, invisible at a 0.4mm nozzle, and the
                               # CHECK reads the same polyline the cut does.
PWR_GAP_DEG  = 84.0            # DERIVED, not styled: the material between a ring end and the
                               # bar is PWR_R*sin(gap/2) - LABEL_W, so clearing 0.90 needs
                               # gap >= 83.6 deg. A conventional 60-deg break measures 0.45mm
                               # and prints as a closed ring with a smudge in it.

_pwr_web = PWR_R * math.sin(math.radians(PWR_GAP_DEG / 2)) - LABEL_W
assert _pwr_web >= LABEL_W, (
    f"the power symbol's break leaves {_pwr_web:.3f}mm between the ring end and the bar, "
    f"under the {LABEL_W}mm floor. Widen PWR_GAP_DEG or grow PWR_R.")


def _label_sketch(paths, w):
    """Reading-space centrelines -> one 2D sketch of round-capped strokes.

    2D rather than 3D on purpose: ~130 segments across the four labels, and fusing that many
    SOLIDS in OCC is minutes where fusing faces is seconds. One extrude at the end.

    ⚠️ BULK-FUSED, NOT ACCUMULATED. `sk = sk + piece` in a loop is quadratic in OCC -- it
    rebuilds the whole result every iteration -- and it took this model from 3s to over four
    minutes. `Sketch() + [pieces]` fuses in one pass: measured 0.30s vs 5.01s on 120 discs,
    and the gap widens with count. One round cap per unique VERTEX rather than two per
    segment halves the face count again."""
    pieces, seen = [], set()
    for poly in paths:
        for i, (vx, vy) in enumerate(poly):
            key = (round(vx, 6), round(vy, 6))
            if key not in seen:                 # one cap per vertex, not two per segment
                seen.add(key)
                pieces.append(Pos(vx, vy) * Circle(w / 2))
            if i + 1 < len(poly):
                (bx_, by_) = poly[i + 1]
                L = math.hypot(bx_ - vx, by_ - vy)
                if L > 1e-9:
                    pieces.append(Pos((vx + bx_) / 2, (vy + by_) / 2)
                                  * Rot(0, 0, math.degrees(math.atan2(by_ - vy, bx_ - vx)))
                                  * Rectangle(L, w))
    return Sketch() + pieces


def _back_label(paths, cx, cy, z0, z1, rot90=False):
    """Cut-solid for a label centred on the back face at board (cx, cy). See the mirror note."""
    if rot90:                                  # reads bottom-to-top, for a label beside a slit
        paths = [[(-v, u) for (u, v) in poly] for poly in paths]
    paths = [[(-u, v) for (u, v) in poly] for poly in paths]        # <-- THE MIRROR
    return Pos(cx, cy, z0) * extrude(_label_sketch(paths, LABEL_W), z1 - z0)


def _label_ok(paths, what):
    """Every label proves its own material clearance before it is allowed onto the part."""
    d, who, n = _SF.min_gap(paths, LABEL_W)
    assert n > 0, (
        f"label {what!r}: min_gap measured ZERO pairs, which reads as a pass and is not one — "
        f"it means every counter has fused into ink. See strokefont.min_gap's RETURNS note.")
    assert d >= LABEL_W, (
        f"label {what!r} leaves {d:.3f}mm of material at its tightest point, under the "
        f"{LABEL_W}mm floor — it will print as a smudge. Worst pair: {who}")
    return d


def _hex_holds(w, h, R, margin, what):
    """Does an ink box of w x h fit inside a FLAT-TOP hexagon of circumradius R, inset by
    `margin`? Flat-top means the binding constraint is the slanted edge, not the width:
    a point is inside iff |y| <= sqrt(3)R/2 AND sqrt(3)|x| + |y| <= sqrt(3)R."""
    Ri = R - 2 * margin / math.sqrt(3)          # inset perpendicular to every edge
    x, y = w / 2.0, h / 2.0
    slack = math.sqrt(3) * Ri - (math.sqrt(3) * x + y)
    assert y <= math.sqrt(3) * Ri / 2 and slack >= 0, (
        f"{what}: a {w:.2f}x{h:.2f}mm label does not fit a hexagon of R={R:.3f} with "
        f"{margin}mm of margin (slack {slack:+.3f}mm). Shrink LABEL_H_CAP.")
    return slack / math.sqrt(3)                 # spare margin, perpendicular to the slant


def _hex_holds_circle(d, R, margin, what):
    """Same question for a ROUND mark. A circle is not its bounding box and using the box
    test on the power symbol failed it by 1.94mm on a hexagon it clears by 0.98 — the box's
    corners overhang the circle by 41%, and a hexagon is exactly where that bites."""
    apothem = math.sqrt(3) * R / 2.0
    slack = apothem - d / 2.0 - margin
    assert slack >= 0, (
        f"{what}: a {d:.2f}mm round mark does not fit a hexagon of R={R:.3f} with {margin}mm "
        f"of margin (slack {slack:+.3f}mm). Shrink PWR_R.")
    return slack


# ---- WHERE EACH LABEL GOES. Every coordinate DERIVED from the feature it names. ------------
#
# This file has been bitten twice by a coordinate that named a feature and was linked to it
# only by a human reading both (the dead SD_PLATE, the dead GRILLE_SLOT_W). A label is the
# purest form of that hazard -- it is a coordinate whose ENTIRE JOB is to point at something
# else -- so none of these are typed. Move the mic and its label follows; move the hex field
# and the SD label re-centres in whatever margin is left.
_LBL = {}
_LBL["VOL"] = _SF.text_paths("VOL", LABEL_H_CAP,  LABEL_W, LABEL_GAP)
_LBL["PWR"] = _SF.power_paths(PWR_R, LABEL_W, PWR_GAP_DEG, PWR_STEP_DEG)
_LBL["SD"]  = _SF.text_paths("SD",  LABEL_H_FLAT, LABEL_W, LABEL_GAP)
_LBL["MIC"] = _SF.text_paths("MIC", LABEL_H_FLAT, LABEL_W, LABEL_GAP)
for _t in ("UART", "I2C", "SPK", "BAT", "IO"):          # the connector set, issue #27
    _LBL[_t] = _SF.text_paths(_t, LABEL_H_FLAT, LABEL_W, LABEL_GAP)
for _k in _LBL:
    _label_ok(_LBL[_k], _k)

_SD_W,  _SD_H  = _SF.ink_size("SD",  LABEL_H_FLAT, LABEL_W, LABEL_GAP)
_MIC_W, _MIC_H = _SF.ink_size("MIC", LABEL_H_FLAT, LABEL_W, LABEL_GAP)
_VOL_W, _VOL_H = _SF.ink_size("VOL", LABEL_H_CAP,  LABEL_W, LABEL_GAP)

# SD: centred in the free margin strip between the board edge and the hex field, and centred
# on the SLIT so the two read as one thing. Rotated, so its INK HEIGHT is what spends the
# strip's width.
LBL_SD_X = HEX_FIELD_X0 / 2.0
LBL_SD_Y = (SD_SOCKET[2] + SD_SOCKET[3]) / 2.0
assert LBL_SD_X - _SD_H / 2 >= LABEL_MARGIN and LBL_SD_X + _SD_H / 2 <= HEX_FIELD_X0 - LABEL_MARGIN, (
    f"the SD label is {_SD_H:.2f}mm across and the margin strip is only {HEX_FIELD_X0}mm "
    f"wide; it would foul the board edge or the hex field. Shrink LABEL_H_FLAT.")
assert (LBL_SD_Y - _SD_W / 2 >= SD_SOCKET[2] - 2.0
        and LBL_SD_Y + _SD_W / 2 <= SD_SOCKET[3] + 2.0), (
    "the SD label has drifted off the slit it names")

# MIC: butted up to the mic hole's keepout on the side away from the corner boss, and centred
# on the hole's own Y so the label sits beside it rather than under it.
LBL_MIC_X = MIC[0] - MIC_HOLE_D / 2 - LABEL_MARGIN - _MIC_W / 2
LBL_MIC_Y = MIC[1]
assert LBL_MIC_Y - _MIC_H / 2 >= HEX_FIELD_Y1 + LABEL_MARGIN, (
    f"the MIC label reaches y={LBL_MIC_Y - _MIC_H/2:.2f} and the hex field ends at "
    f"{HEX_FIELD_Y1} — it would cut into the vent cells.")
assert LBL_MIC_X - _MIC_W / 2 >= HOLES[2][0] + CBORE_D / 2 + LABEL_MARGIN, (
    "the MIC label runs into the upper-left screw counterbore")
assert LBL_MIC_X + _MIC_W / 2 <= MIC[0] - MIC_HOLE_D / 2 - LABEL_MARGIN + 1e-9, (
    "the MIC label runs into the mic hole")

# ============================================================================
# CONNECTOR LABELS -- issue #27.  UART / I2C / SPK / BAT / IO.
# ============================================================================
#
# >>> THE MAPPING IS THE ENTIRE RISK IN THIS FEATURE, AND IT IS NOT DERIVABLE. <<<
#
# `CONN_R` and `CONN_L` are ANONYMOUS Y-SPANS lifted out of the vendor STEP. Nothing in this
# file knows which of them is the battery and which is the UART, and a label is a coordinate
# whose entire job is to point at something else — so getting it wrong produces exactly the
# fault the opening/component ledger at check 0d exists for, except permanent, in plastic, and
# on the port a person is about to plug a LiPo into. The block at BTN_TIP_Z is the precedent:
# BOOT and RESET were swapped by re-deriving an assignment from a drawing IN GOOD FAITH.
#
# So the names come from the vendor silkscreen (Figure 5-1, ES3C28P outline drawing), and the
# ORDER along each edge is pinned by that drawing's own dimension chains — which are asserted
# below against this file's `CONN_*`, because a chain that closes is evidence and a chain
# nobody checked is a chain someone read backwards.
#
#   silkscreen, X=0 edge (2 connectors)   BAT (2-pin, "- +")   UART (4-pin, RXD TXD GND 5V)
#   silkscreen, X=50 edge (3 connectors)  SPEAKER (2-pin)      I2C (3.3V GND SCL SDA)   IO
#
# ⚠️ WHICH EDGE IS WHICH IS **NOT** TAKEN FROM THE DRAWING. That is the handedness question the
# drawing cannot answer (see BTN_TIP_Z). It is taken from the five-way STEP solid fit that also
# fixed CONN_R/CONN_L, corroborated here by the microSD: the chain puts the socket centre at
# BL-35.03 and `SD_SOCKET` independently centres 0.06mm away, on the low-x edge. The drawing is
# used only for the ORDER ALONG an edge, and Y is not the disputed axis.
_DRAW_CHAIN_R = (13.55, 17.85, 18.25)   # CONN_R[0] -> [1] -> [2] -> board end
_DRAW_CHAIN_L = (11.82, 15.97, 35.03)   # CONN_L[0] -> [1] -> microSD centre -> board end
CONN_LBL_R = ("SPK", "I2C", "IO")       # X=50 edge, in increasing Y
CONN_LBL_L = ("BAT", "UART")            # X=0  edge, in increasing Y


def _chain_centres(chain):
    """Feature centres implied by a drawing dimension chain that closes on the board end."""
    out, y = [], float(BL)
    for d in reversed(chain):
        y -= d
        out.append(y)
    return list(reversed(out))


# ⚠️ AND THE CONTROL IS THE REVERSED READING, because that is the mistake available here. A
# chain is a list of gaps; reading it from the wrong end is a mirror in Y and produces a
# perfectly self-consistent set of centres that lands on the wrong connectors. It has to MISS.
for _chain, _spans, _what in ((_DRAW_CHAIN_R, CONN_R, "CONN_R"), (_DRAW_CHAIN_L, CONN_L, "CONN_L")):
    _want = [(a + b) / 2 for (a, b) in _spans]
    _got = _chain_centres(_chain)[:len(_want)]
    assert all(abs(g - w) <= 0.05 for g, w in zip(_got, _want)), (
        f"the vendor drawing's {_what} chain {_chain} implies centres "
        f"{[round(g,2) for g in _got]} but the STEP gives {[round(w,2) for w in _want]} — the "
        f"chain no longer closes, so the silkscreen ORDER it establishes is unsupported and "
        f"the labels below may be naming the wrong ports. Do not adjust the tolerance")
    _rev = [sum(_chain[:i + 1]) for i in range(len(_want))]
    assert not all(abs(r - w) <= 0.05 for r, w in zip(_rev, _want)), (
        f"[self-test] reading the {_what} chain from the OTHER end also closes, so the chain "
        f"cannot tell which way round the edge runs and it is not evidence of the order")
assert abs(_chain_centres(_DRAW_CHAIN_L)[2] - (SD_SOCKET[2] + SD_SOCKET[3]) / 2) <= 0.10, (
    "the drawing's chain and SD_SOCKET disagree about the microSD centre — that closure is "
    "what ties the drawing's bottom edge to this file's LOW-X edge, and without it the "
    "BAT/UART pair could belong to either long edge")

# ---- placement ----
# One strip per edge, mirroring the SD rule (centred between the board edge and the hex field),
# and one label per connector, ROTATED so the ink HEIGHT is what spends the strip's width.
LBL_CONN_X_L = HEX_FIELD_X0 / 2.0                 # 4.50, the same strip SD uses
LBL_CONN_X_R = (HEX_FIELD_X1 + BW) / 2.0          # 45.50
# The Y window is set by the corner counterbores, which sit dead centre of BOTH strips.
_LBL_Y_LO = HOLES[0][1] + CBORE_D / 2 + LABEL_MARGIN          #  7.70
_LBL_Y_HI = HOLES[2][1] - CBORE_D / 2 - LABEL_MARGIN          # 78.30


def _pack_labels(items, y_lo, y_hi, what):
    """Centres for a column of labels: on their own feature where possible, else separated.

    ⚠️ CENTRING EACH LABEL ON ITS OWN CONNECTOR DOES NOT FIT AND CANNOT BE MADE TO. BAT and
    UART are 11.78mm apart and their ink is 13.28 and 18.04 long, so the two would overlap by
    3.9mm; shrinking to fit needs h <= 2.93, which is far under the stroke floor. So the rule
    is: nominal = the connector's own centre, then push apart to LABEL_MARGIN in increasing Y,
    then slide the whole column down if it has run out the top. ORDER IS PRESERVED BY
    CONSTRUCTION, which is the property that keeps each label next to its own port.
    """
    c = [n for (_, n, _) in items]
    ln = [l for (_, _, l) in items]
    for i in range(1, len(c)):
        c[i] = max(c[i], c[i - 1] + (ln[i - 1] + ln[i]) / 2 + LABEL_WORD_GAP)
    _over = (c[-1] + ln[-1] / 2) - y_hi
    if _over > 0:
        c = [v - _over for v in c]
    assert c[0] - ln[0] / 2 >= y_lo - 1e-9, (
        f"the {what} label column needs "
        f"{sum(ln) + LABEL_WORD_GAP*(len(ln)-1):.2f}mm and the strip has "
        f"{y_hi - y_lo:.2f}mm between the corner counterbores. Shorten a label or LABEL_H_FLAT")
    return c


_FACE_OPENING = {"SPK": SPK_RELIEF_Y}   # ports whose relief pierces the back face
_CH_HI, _CH_LO = side_channels()                  # x=BW edge, x=0 edge
_conn_place = {}                                  # name -> (x, y, own channel span)
for _names, _spans, _x, _yhi, _what in (
        # ⚠️ the LEFT column stops at the SD label, not at the counterbore: SD is already on
        # this strip and is not moving for us. The right strip is empty, so it gets the lot.
        (CONN_LBL_L, _CH_LO, LBL_CONN_X_L, LBL_SD_Y - _SD_W / 2 - LABEL_WORD_GAP, "x=0"),
        (CONN_LBL_R, _CH_HI, LBL_CONN_X_R, _LBL_Y_HI, "x=%g" % BW)):
    # ⚠️ A PORT WITH A HOLE IN THE FACE CANNOT HAVE ITS LABEL ON TOP OF IT (#33). SPK's relief
    # is a through-opening across y 31.79..40.94, which is exactly where SPK's ink wanted to
    # be, so its nominal moves to just clear of the opening instead of onto its port. That is
    # not a downgrade in association: a label beside a visible hole points harder than a label
    # over an invisible connector. The `nearest label wins` ledger below is what checks it.
    _items = []
    for _i, _n in enumerate(_names):
        _len = _SF.ink_size(_n, LABEL_H_FLAT, LABEL_W, LABEL_GAP)[0]
        _nom = (_spans[_i][0] + _spans[_i][1]) / 2
        if _n in _FACE_OPENING:
            _nom = min(_nom, _FACE_OPENING[_n][0] - LABEL_WORD_GAP - _len / 2)
        _items.append((_n, _nom, _len))
    for _n, _cy in zip(_names, _pack_labels(_items, _LBL_Y_LO, _yhi, _what)):
        _conn_place[_n] = (_x, _cy, _spans[list(_names).index(_n)])

# ---- and the ledger: every label must name the connector it sits on ----
#
# This is check 0d's question asked of labels instead of openings, and it is the one thing
# here a render cannot answer: a label 6mm off its port looks perfectly deliberate.
for _n, (_x, _cy, _own) in _conn_place.items():
    _w, _h = _SF.ink_size(_n, LABEL_H_FLAT, LABEL_W, LABEL_GAP)
    # THE ASSOCIATION RULE IS "THE INK SPANS THE PORT'S CENTRELINE", not "the label's centre
    # sits in the channel", and the weaker-looking rule is the better one for two reasons.
    # It is what a reader actually does — look across from the port into the strip and read
    # whatever is level with it — and the stricter rule is unsatisfiable here: BAT and UART
    # are 11.78mm apart carrying 13.28 and 18.04mm of ink, so pinning both centres inside
    # their channels leaves 16.88mm for a 15.66mm + word-space column. The strict rule would
    # have forced the word space back down to 1.22mm, i.e. back to labels that merge.
    _port = (_own[0] + _own[1]) / 2
    # >>> THE RULE IS "EVERY PORT'S NEAREST LABEL IS ITS OWN". <<<
    #
    # It was "the ink spans the port's centreline", which is the stronger and nicer property
    # and four of the five still satisfy it exactly. SPK cannot: #33 put a through-opening
    # over its port, so no ink can be level with it. Weakening to nearest-wins is not giving
    # up — it is the property that was actually meant. "This label names that port" IS a
    # nearest-neighbour claim, and stating it that way covers the case where the port's own
    # relief is the thing the label points at.
    _dist = lambda cy, w: max(0.0, abs(_port - cy) - w / 2)
    _mine = _dist(_cy, _w)
    for _o, (_ox, _ocy, _) in _conn_place.items():
        if _o == _n or (_ox < BW / 2) != (_x < BW / 2):
            continue
        _ow = _SF.ink_size(_o, LABEL_H_FLAT, LABEL_W, LABEL_GAP)[0]
        assert _dist(_ocy, _ow) > _mine, (
            f"the {_o} label is nearer to {_n}'s port at y={_port:.2f} "
            f"({_dist(_ocy, _ow):.2f}mm) than {_n}'s own is ({_mine:.2f}mm) — the two labels "
            f"have swapped ports, or one has been packed past the other")
    assert _mine <= LABEL_WORD_GAP + (_own[1] - _own[0]) / 2, (
        f"the {_n} label's ink is {_mine:.2f}mm from its port at y={_port:.2f} — near enough "
        f"to win the nearest-label test only because nothing else is close, which is not the "
        f"same as labelling it")
    _s0, _s1 = (0.0, float(HEX_FIELD_X0)) if _x < BW / 2 else (float(HEX_FIELD_X1), float(BW))
    assert _s0 + LABEL_MARGIN <= _x - _h / 2 and _x + _h / 2 <= _s1 - LABEL_MARGIN, (
        f"the {_n} label is {_h:.2f}mm across and its margin strip is x {_s0:g}..{_s1:g} — it "
        f"would foul the board edge or the hex field. Shrink LABEL_H_FLAT")
    for _o, (_ox, _ocy, _oown) in _conn_place.items():
        if _o == _n or (_ox < BW / 2) != (_x < BW / 2):
            continue                              # different edge: no possible confusion
        assert _cy + _w / 2 < _oown[0] or _cy - _w / 2 > _oown[1], (
            f"the {_n} label's ink reaches into {_o}'s channel ({_oown[0]:.2f}..{_oown[1]:.2f}) "
            f"— two ports and one label between them is worse than no label")
        _ow = _SF.ink_size(_o, LABEL_H_FLAT, LABEL_W, LABEL_GAP)[0]
        assert abs(_cy - _ocy) >= (_w + _ow) / 2 + LABEL_WORD_GAP - 1e-9, (
            f"the {_n} and {_o} labels are {abs(_cy-_ocy)-(_w+_ow)/2:.2f}mm apart, under the "
            f"{LABEL_WORD_GAP}mm word space — at {LABEL_GAP - LABEL_W}mm they read as ONE WORD, "
            f"which is what `SPKI2C` and `BATUARTSD` were")
# and nothing may collide with the label that was already on the left strip
# ⚠️ A WORD SPACE, NOT A KEEPOUT. SD is the third label on this strip and it merges with UART
# exactly as UART merged with BAT — the first cut read `BATUARTSD` as one string. LABEL_MARGIN
# would satisfy a clearance check and still print an unreadable column.
_uart_top = _conn_place["UART"][1] + _SF.ink_size("UART", LABEL_H_FLAT, LABEL_W, LABEL_GAP)[0] / 2
assert _uart_top <= LBL_SD_Y - _SD_W / 2 - LABEL_WORD_GAP + 1e-9, (
    f"the UART label ends at y={_uart_top:.2f} and the SD label's ink starts at "
    f"{LBL_SD_Y - _SD_W/2:.2f} — under a {LABEL_WORD_GAP}mm word space they read as one word")
# ⚠️ STATED RATHER THAN ASSERTED, because it is true and unavoidable: UART's ink DOES overlap
# the microSD channel's Y span by ~1.8mm. The microSD is not one of the five ports being
# labelled, it already carries its own label 0.8mm further on, and the alternative is a UART
# label that no longer covers the UART. The foreign-channel assert above is therefore scoped
# to the CONNECTORS, which is the confusion that actually matters.

# CAP LABELS. The remaining cap thickness is the thing to watch, and it was worth a number
# rather than a shrug: the big cap goes 1.70 -> 1.22mm under its label. As a cantilever plate
# (b~13, L~7, E~3500MPa) a 2N press bows it 0.033mm, against 0.012mm before the label and a
# ~0.25mm switch travel. So the label costs ~8% of travel in bow. Negligible — but it is
# negligible because it was computed, not because 1.22 > 0.90 sounded comfortable.
for _cx in BTN:
    _cy, _R, _deb = cap_geometry(_cx[0])
    _big = (_cx[0] == BTN_BOOT_X)
    _rem = WALL - _deb - LABEL_DEBOSS
    assert _rem >= 1.20, (
        f"a label on the cap at x={_cx[0]} leaves {_rem:.2f}mm of cap. Too floppy to drive "
        f"the pip; either shallow the label or shallow the cap deboss.")
    if _big:
        _slack = _hex_holds(_VOL_W, _VOL_H, _R - CAP_INSET, LABEL_MARGIN, "VOL on the big cap")
    else:
        _pw = 2 * (PWR_R + LABEL_W / 2)
        _slack = _hex_holds_circle(_pw, _R - CAP_INSET, LABEL_MARGIN,
                                   "power symbol on the small cap")


def back_shell():
    p  = rbox(OX0,OX1,OY0,OY1, BACK_Z, SEAM_Z, OUT_R)
    # board + glass pocket, and the back-component cavity, in one cut
    p -= rbox(PK0,PK1,PY0,PY1, CAV_FLOOR, SEAM_Z+1, POCK_R)
    # ---- BACK-FACE LABELS, cut EARLY and on purpose. ----
    # Boolean cost in OCC depends on how many faces the operand already has, so the same four
    # cuts are cheap here and expensive after the ~110-cell hex field lands. The RESULT is
    # order-independent (p-A-B == p-B-A); only the bill changes. Cutting the cap labels here
    # also means they do not depend on the cap recess existing yet -- both are just cuts.
    #
    # Which label goes on which cap is keyed on the SWITCH x, never on "the big one": the
    # apparent side flips between figures of this same part, and reading a side off a picture
    # is what put the caps on backwards the first time.
    for (_cx, _cy) in BTN:
        _cyh, _R, _deb = cap_geometry(_cx)
        p -= _back_label(_LBL["VOL"] if _cx == BTN_BOOT_X else _LBL["PWR"],
                         cap_center_x(_cx), _cyh,
                         BACK_Z - 1.0, BACK_Z + _deb + LABEL_DEBOSS)
    # SD reads bottom-to-top, beside the slit it names; MIC sits beside the mic bore.
    p -= _back_label(_LBL["SD"],  LBL_SD_X,  LBL_SD_Y,
                     BACK_Z - 1.0, BACK_Z + LABEL_DEBOSS, rot90=True)
    p -= _back_label(_LBL["MIC"], LBL_MIC_X, LBL_MIC_Y,
                     BACK_Z - 1.0, BACK_Z + LABEL_DEBOSS)
    # CONNECTOR LABELS (#27). All rotated, like SD: they live in the 9mm margin strips beside
    # the side channels they name, so the ink's HEIGHT is what has to fit the strip's width.
    # Placement and the port mapping are derived and asserted at _conn_place — see the block
    # there, and do not move one of these without re-reading it.
    for _t, (_lx, _ly, _) in _conn_place.items():
        p -= _back_label(_LBL[_t], _lx, _ly,
                         BACK_Z - 1.0, BACK_Z + LABEL_DEBOSS, rot90=True)
    # screw standoffs up to the PCB back face
    for (hx,hy) in HOLES:
        # FLARED boss: BOSS_D at the PCB face (the vendor keepout applies THERE), widening to
        # BOSS_FLARE_D underneath so the counterbore has something to floor on. See BOSS_FLARE_D.
        p += cone(hx,hy, CAV_FLOOR, PCB_BOT, BOSS_FLARE_D, BOSS_D)
        p -= cyl(hx,hy, BACK_Z-0.01, PCB_BOT+0.01, SCREW_D)
        # COUNTERBORE for a cylindrical head. Flat floor, CBORE_DEPTH deep = 19 layers.
        p -= cyl(hx,hy, BACK_Z-0.01, BACK_Z+CBORE_DEPTH, CBORE_D)
    # ---- USB-C opening + cable relief (bottom short edge) ----
    p -= bx(18.0,32.0, OY0-1, PY0+0.5, -6.60,-0.60)
    p -= bx(15.5,34.5, OY0-1, OY0+1.6, -8.20, 0.40)      # outside relief for overmould
    # ---- side channels: connectors + the microSD slit.  DERIVED — see side_channels(). ----
    _hi, _lo = side_channels()
    for (a,b) in _hi:
        p -= bx(BW+FIT-0.01, OX1+1, a,b, CAV_FLOOR, PCB_BOT)
    for (a,b) in _lo:
        p -= bx(OX0-1, PK0+0.01, a,b, CAV_FLOOR, PCB_BOT)
    # ---- SPEAKER PLUG RELIEF (#33). The one TOP-ENTRY connector; see SPK_CONN_I. ----
    #
    # Through the back slab, and outboard only as far as PK1 — the CAVITY wall, not the shell's
    # outer edge. ⚠️ THE FIRST CUT RAN TO OX1 AND BIT A NOTCH OUT OF THE SHELL'S OUTLINE, which
    # a slice of the mesh showed and no assert would have. It is not needed: the lead only has
    # to get OUTBOARD OF THE CONNECTOR (x > 49.49) before it can rise into the cavity, which is
    # clear there, and leave through the side channel that already serves this Y span. Stopping
    # at PK1 = 50.35 leaves the outer wall whole and the outboard face flush with the cavity's
    # own wall, so there is no sliver between them.
    p -= bx(SPK_RELIEF_X0, PK1 + 0.01, SPK_RELIEF_Y[0], SPK_RELIEF_Y[1],
            BACK_Z - 1.0, CAV_FLOOR + 0.01)
    assert PK1 > CONN_R_X[1], (
        f"the relief stops at x={PK1:.2f} but the speaker connector reaches {CONN_R_X[1]:.2f} — "
        f"the lead would still be trapped under the connector with nowhere to rise")
    # ---- mic BACK relief: works whichever way the port faces ----
    p -= cyl(MIC[0],MIC[1], BACK_Z-1, CAV_FLOOR+0.01, MIC_HOLE_D)
    # ---- #35: exterior chamfer on the back face, the one you hold ----
    # Applied LAST so it runs on the finished silhouette. The selector takes only edges that
    # reach the part's own bounding box, so the nine labels, 113 hex apertures, four
    # counterbores, the SD slit and the speaker relief are untouched — see the helper.
    p = chamfer_outline(p, BACK_Z, CHAMFER, "shell back face")
    # ---- NO LED WINDOW, NO DIFFUSER ----
    # There used to be a 12mm bore over the WS2812 plus a 16mm seat for a printed
    # translucent disc. Both are gone: the fine hex field below passes straight over the
    # LED, so its light leaves through ~30 small holes instead of one big one. That is a
    # better diffuser than the diffuser was — many small apertures scatter, one large one
    # just shows you the die — and it deletes a part, a seat, and a second filament.
    # ---- printed-in-place HEXAGONAL button pushers ----
    for (cx, cy) in BTN:
        cyh, R, deb = cap_geometry(cx)
        icx = cap_center_x(cx)          # island centre; cx remains the SWITCH
        ytop = cap_hex_top_y(cyh, R)
        # A HEX RING, THEN THE HINGE PUT BACK. The old pad was three box cuts forming a U,
        # which only works because a rectangle's sides are axis-aligned. A hexagon's are
        # not, so the slot is the difference of two concentric hexes and the hinge is what
        # you decline to cut. Wrapping the tab SLOT_W past each end of the +Y flat carries
        # the hinge a little around both upper shoulders: cutting exactly to the corners
        # would leave the hinge meeting the slot at a knife edge, which prints as a
        # stress riser in the one feature here designed to flex.
        ring = (hexp(icx, cyh, R + SLOT_W, BACK_Z-1, CAV_FLOOR+1)
                - hexp(icx, cyh, R,        BACK_Z-1, CAV_FLOOR+1))
        ring -= bx(icx - R/2 - SLOT_W, icx + R/2 + SLOT_W,
                   cyh, ytop + SLOT_W + 1, BACK_Z-1, CAV_FLOOR+1)
        p -= ring
        # thin the hinge from the inside
        _hl = cap_hinge_len(cx)
        p -= bx(icx - R/2 - SLOT_W, icx + R/2 + SLOT_W, ytop - _hl/2, ytop + _hl/2,
                BACK_Z+HINGE_T, CAV_FLOOR+1)
        # pip that reaches the switch plunger
        p += cyl(cx,cy, CAV_FLOOR, BTN_TIP_Z-0.15, PIP_D)   # on the SWITCH, not the island
        # DEBOSSED CAP FACE. Cut after the ring, inset CAP_INSET from the island edge so
        # the recess never breaks into the slot and never undercuts the hinge — at
        # R - CAP_INSET it stops 0.87mm short of the hinge line.
        p -= hexp(icx, cyh, R - CAP_INSET, BACK_Z - 1.0, BACK_Z + deb)
    # ---- FINE HEX BACK. Replaces two arrays of slot vents. ----
    #
    # The patch is bounded by what is already in the back face, not by taste:
    #   x 9..41  clears the screw bosses. Holes sit on 78x42 centres 4mm in from every
    #            edge, so at x=4 a BOSS_D boss spans 1.3..6.7 and at x=46, 43.3..48.7.
    #   y 11..75 clears the printed-in-place button pads at y~3.3, the USB-C relief below
    #            them, the mic relief at (40, 81.5), and the PCB antenna keepout
    #            ANT y 80.04..85.70. The old slot vents dodged the same features.
    #
    # 3.2mm across the flats on a 0.8mm web — fine enough to read as a texture rather
    # than as holes, and 0.8mm is two extrusion widths at a 0.4mm nozzle. Every hex is
    # kept WHOLLY inside the patch: a clipped hex at the boundary leaves a sliver of
    # material that prints as stringing.
    # y0 11.0 -> 19.00, DERIVED not chosen: the hinge cut reaches ytop + HINGE_L/2 = 16.30, a
    # 3.2mm pointy-top cell has half-height 3.2/sqrt(3) = 1.85, and 0.80mm of clearance between
    # them gives 16.30 + 0.80 + 1.85 = 18.95. An earlier estimate of 18.5 omitted the cell's
    # half-height; an earlier one of 34 was measured against a different cap architecture
    # entirely. The field yields 8mm so the caps can be thumb-sized — JP authorised that trade.
    p -= _hex_panel(HEX_FIELD_X0, HEX_FIELD_X1, HEX_FIELD_Y0, HEX_FIELD_Y1,
                BACK_Z-1, CAV_FLOOR+1, 3.2, 0.8)
    return p

# diffuser() deleted along with the LED window it seated into — see back_shell().


# ============================================================================
# 5b. DESK STAND  -- cradle wedge; also the SPEAKER ENCLOSURE.
#     Own coordinate frame: X 0..64 width, Y 0..64 depth (Y=0 = front),
#     Z 0..40 up.  The assembled slab drops into an angled slot.
# ============================================================================
SLAB_W   = OX1-OX0                 # 55.90
SLAB_T   = FRONT_Z-BACK_Z          # 17.40  (bezel front .. shell back)
TILT     = 15.0                    # degrees back from vertical, seated viewer
# ---- #35: ONE CHAMFER WIDTH ACROSS THE FAMILY, DERIVED FROM THE TIGHTEST WALL ----
#
# A chamfer is the most cross-cutting change in this file: every part, every silhouette, every
# feature placed today. The failure mode is not the chamfer being the wrong size — it is what
# the chamfer EATS, and no assert on the chamfer itself can see that. So the ceiling is
# MEASURED, per feature, from the outline inward:
#
#   speaker relief (#33) to the outline    2.60mm   <- BINDING
#   counterbore to the corner arc          2.84
#   counterbore to a flat side             4.05
#   every connector label's ink            4.25
#   stand: slot side wall to the outline   3.65     chamber shaft to the outline  4.00
#
# Holding 1.20mm of remaining wall (three extrusions at a 0.40 nozzle) puts the ceiling at
# 2.60 - 1.20 = 1.40. CHAMFER is 0.80: 0.60mm of margin on the binding feature, 1.80mm of
# actual wall, and comfortably more than the 0.2-0.4mm elephant's foot it exists to absorb —
# which is the functional half of this issue and the reason the STAND BASE gets one too.
CHAMFER = 0.80
_CHAMFER_MAX = 2.60 - 1.20
assert CHAMFER <= _CHAMFER_MAX, (
    f"CHAMFER={CHAMFER} exceeds {_CHAMFER_MAX:.2f} — at that size it cuts into the wall "
    f"between the speaker relief and the shell's outer face, the tightest thing the chamfer "
    f"can reach. Re-measure the clearances above before raising it")
SLOT_CLR = 0.40
ST_W, ST_D, ST_H = 64.0, 64.0, 40.0
# CORNER RADIUS OF THE STAND'S PLAN PROFILE. Hoisted out of desk_stand()'s rbox() call, where
# it was a literal 10.0, because a second feature now has to know about it: the rear face is
# only flat for x <= ST_W - ST_R, and a cut placed outboard of that is measuring its depth
# against a surface that is not there. See WIRE_X. A literal that two features depend on is
# exactly the duplicate-constant trap this file keeps being bitten by.
ST_R     = 10.0
ST_WALL  = 4.0
# DRIVER — JP's actual speaker is a RECTANGLE with rounded corners, 40 x 27 mm,
# not the round 28mm driver this was first cut for. Rectangular drivers are the norm
# in this size class (phone/tablet speakers), so this is the likely case rather than
# the exception, and both the seat and the grille field derive from these numbers.
DRIVER_W = 40.0                    # across the front wall (X)
DRIVER_H = 27.0                    # up the front wall (Z)
DRIVER_R = 3.0                     # corner radius of the driver body
DRIVER_CLR = 0.60                  # locating clearance per side, print tolerance
# MOUNTING: JP's speaker is held on with ADHESIVE TAPE, not a flange in a pocket.
# That inverts the requirement. A 2.2mm recessed seat was right for a flanged driver
# and is wrong here for two reasons: tape needs a FLAT, continuous surface to bond to,
# and a pocket deep enough to seat a flange leaves the tape bridging a step — which is
# where an adhesive bond fails first. So the wall face stays flat and only a shallow
# LOCATING LIP is cut: deep enough to stop the speaker sliding while the adhesive
# grabs, too shallow to interrupt the bonded area.
# >>> THE TAPE IS ON THE SPEAKER'S BACK — its NON-radiating face. <<<
# That is the third revision of this mount and it inverts it again. A baffle-mounted
# driver needs adhesive on the face that meets the baffle; this one has it on the
# opposite side. So the surface it bonds to cannot be the front wall — it has to be a
# flat pad BEHIND the driver, with the diaphragm facing forward at the grille.
#
# Consequence: the chamber's REAR wall becomes the mounting surface, and the driver's
# thickness sets how close its diaphragm sits to the baffle. A large air gap in front of
# a diaphragm is a resonant cavity, so that distance wants to be small and deliberate.
DRIVER_T   = 10.00                 # MEASURED (JP). It is a SEALED-BACK MODULE, not a
                                   # bare driver: a plastic box carrying its own rear
                                   # cavity, with the diaphragm on one face and a
                                   # JST-1.25 pigtail. That is why the stand's chamber
                                   # volume barely matters acoustically — the module
                                   # brings its own. What matters is the FRONT: keep the
                                   # cavity between diaphragm and grille small, and stop
                                   # it leaking anywhere except through the slots.
FRONT_GAP  = 2.50                  # diaphragm -> baffle. Small on purpose.
PAD_PROUD  = 0.80                  # pad stands off the wall so nothing else fouls the tape
LIP_DEPTH  = 0.60                  # alignment only; the tape does the work
LIP_WIDTH  = 1.20                  # the groove is a thin outline, not a pocket
# ---- SEALED CHAMBER BOUNDS, AT MODULE SCOPE BECAUSE A SECOND PART DEPENDS ON THEM ----
#
# >>> stand_base() USED TO CARRY ITS OWN COPY OF THESE AND THE COPY WENT STALE. <<<
#
# The base plate read `bx(ST_WALL+1.3, ST_W-ST_WALL-1.3, ST_WALL+0.3, 20.7, 0.4, ST_WALL)`.
# That 20.7 is 21.00 - 0.30: the chamber's rear wall WAS 21.0, and the 0.30 is the plate's
# clearance. The rear wall then went 21.0 -> 22.0 -> DERIVED to 19.30 (baffle + front gap +
# driver body + tape pad), and the plate never followed. Measured by boolean: the plate
# overlapped the stand's own floor by 269.136 mm3 over y 19.30..20.70 — 1.40 mm too deep to
# seat at all. THE SEALED CHAMBER COULD NOT BE CLOSED.
#
# Nothing could have caught it. Every clearance check in this file compares a part to the
# BOARD, and the base plate never goes near the board; the mesh checks look at one STL at a
# time; and a part that is too big to fit intersects nothing that anybody was measuring.
# It is the two-parts-must-agree case, and it now has an assert in _check_geometry().
CHAM_X0, CHAM_X1 = ST_WALL + 1, ST_W - ST_WALL - 1
CHAM_Y0 = ST_WALL
CHAM_Y1 = ST_WALL + FRONT_GAP + DRIVER_T + PAD_PROUD + 2.0      # 19.30, derived not chosen
BASE_CLR = 0.30                    # base plate clearance per side, all four edges
SLOT_CY  = 34.0                    # slot centreline Y at the floor
# SLOT_FLOOR 10.0 -> 24.0. Two faults, one cause: the slab sat too deep.
#
#   At 10.0 the stand rose 30mm above the slab's bottom edge, which is 31.1mm ALONG the
#   slab once tilt is accounted for (30 / cos 15deg). The visible area starts only
#   19.76mm up from that edge, so the stand covered 11.3mm of screen — 19.5% of a
#   58.05mm-tall display, hidden behind the box. JP spotted it in the render.
#
#   The same depth left only 6.0mm between the slab's bottom edge and the stand floor,
#   and a straight USB-C plug body needs ~18-20mm. There was nowhere for the power lead
#   to go, which nobody had noticed because no figure showed a cable.
#
# At 24.0: engagement 16.6mm along the slab (a captive slot constraining both faces, so
# ample), the visible area is entirely clear of the stand, and 20.0mm remains below for
# the plug. See the VA_CLEAR assert below — this must not silently regress.
SLOT_FLOOR = 24.0
# ============================================================================
# THE PLINTH — #29 / #30.  A 40mm RIGID CABLE DOES NOT FIT UNDER A 40mm STAND.
# ============================================================================
#
# >>> THE CRADLE KEEPS ITS OWN Z ORIGIN. THE PLINTH GROWS DOWNWARD FROM IT. <<<
#
# This is the whole reason the change is small. `SLOT_FLOOR`, `ST_H`, the slot, the well, the
# chamber, the grille, the scallops and the wire route all still evaluate in the CRADLE frame,
# where the cradle's own floor is z=0 and its rim is z=ST_H=40. The plinth occupies
# z = -PLINTH_H .. 0, so the DESK is at z = -PLINTH_H, and the exported STL is lifted by
# PLINTH_H at export time (see PRINT_LIFT) so the printed part rests on z=0.
#
# ⚠️ EVERY HEIGHT IN THIS FILE IS THEREFORE A CRADLE-FRAME HEIGHT, AND THE SAME FEATURE HAS
# TWO LIVE NUMBERS. The #31 rim notch is z=27.62 here and z=43.62 in the exported STL; both
# literals were circulating in the same conversation and each is wrong in the other frame.
# That is why NOTCH_Z below is a formula and not a number, and why nothing here is measured
# off the exported mesh without adding PLINTH_H first.
#
# ---- WHY 56. THE SIGN IS SETTLED AND BOTH RIVAL FIGURES ARE RECONCILED. ----
#
# JP measured the cable: 40mm from the plug tip to where it can first bend. The plug leaves
# the port along the slab's own axis, 15deg off vertical, so the corridor it needs is
# STRAIGHT and it is 40mm long. Recessing the slot floor cannot buy that — the deficit is
# larger than the entire floor thickness. The port has to sit higher above the desk.
#
#     port_z (cradle) = SLOT_FLOOR - pc*sin(TILT) + z_face*cos(TILT)
#     requirement     = port_z + PLINTH_H  >=  CABLE_RIGID*cos(TILT) + CABLE_OD/2
#
# ---- 1. THE SIGN OF pc. SETTLED, by two routes that agree. ----
#
# `pc` is the port axis's offset from the slab's mid-plane, and 2*pc*sin(TILT) = 1.152mm of
# stand height rides on it. It was disputed; it is not any more.
#
#     slab spans board z   BACK_Z -9.700 .. FRONT_Z +7.700   ->  mid-plane -1.000
#     USB-C body           USB_Z  -4.850 .. -1.600           ->  axis      -3.225
#     offset = axis - mid  = -2.225   ->  2.225mm toward the BACK SHELL
#
# Two constants and a subtraction, and it agrees with the physical picture: the USB-C shell
# hangs BELOW the PCB bottom (-1.600) down to -4.850, into the back cavity, so the axis must
# be on the shell side of centre. Independently, check 3b's cap probe fixes the frame mapping
# — a back-shell feature sits at slot-local +SLAB_T/2, so local +y is REARWARD and
# local_y = -(board_z - mid_z) = +2.225.
#
# ⚠️ AND THE BACK OF A BACKWARD-LEANING SLAB IS THE **LOW** SIDE, WHICH IS WHERE THIS GETS
# READ BACKWARDS. The file already says so at the USB-C well: rotating the slot by TILT sends
# "the front-bottom corner up to z ~= 26.4 while the rear-bottom corner drops to ~= 21.6".
# So a port on the back side sits LOWER in the stand frame — port_z = 25.918, not 27.070 —
# and the settled sign is therefore the one that demands the **TALLER** stand, not the
# shorter one. Any pairing of "the port sits below the mid-plane" with the smaller of two
# candidate heights has the implication inverted.
#
# ---- 2. THE TWO RIVAL FIGURES. Not unreconciled: both are this derivation + CABLE_OD/2. ----
#
# 53.82 and 54.97 were both quoted for the required total. Neither is arbitrary and neither
# is a competing model — they are the same arithmetic with the tail's end held half a cable
# THICKNESS above the desk instead of merely touching it, which is the right requirement:
# what has to clear the desk plane is the cable's CENTRELINE, not its lowest surface.
#
#     tip merely reaches the desk        back side 52.719   front side 51.567
#     + CABLE_OD/2 = 2.25                back side 54.969   front side 53.817
#                                        ^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^
#                                        = the quoted 54.97 and 53.82, to 2 d.p.
#
# Two independent matches to three decimal places is not a coincidence, so the requirement
# below carries the CABLE_OD/2 term and **54.97 is now derived rather than asserted as a
# magic floor**. Note which one it pairs with: 54.97 goes with the SETTLED sign.
#
# The build clears it by 1.031mm, which is build tolerance and cable-OD uncertainty rather
# than slack absorbing an unknown. A future trim has a defined floor of 54.97 — and if
# CABLE_OD is ever measured, that floor moves by half of whatever the change is.
CABLE_RIGID   = 40.0    # MEASURED (JP): plug tip -> the first point the cable can bend.
                        # Not "effectively stiff" and not apportionable into overmold + radius:
                        # an earlier 22mm-overmold + R18 split was WITHDRAWN as more optimistic
                        # than what JP actually said. The whole 40 is straight.
CABLE_OD      = 4.5     # ⚠️ ASSUMED, not measured — a chunky USB-C lead. JP measured the rigid
                        # LENGTH, not the diameter. It buys the tail's centreline CABLE_OD/2 of
                        # clearance over the desk, so the sensitivity is exactly half: every mm
                        # of OD is 0.5mm of stand height. Measure it and this tightens.
STAND_TOTAL_H = 56.0    # the decision. Everything else here derives from it.
PLINTH_H      = STAND_TOTAL_H - ST_H          # 16.00 — never typed, so the two cannot drift
# ---- THE EGRESS: the plinth IS the cable exit, which is what makes 56 work instead of ~75 ----
#
# A stand tall enough for the cable to complete its BEND inside the plinth is a different
# part. The turn from the tail's heading (75deg below horizontal) to flat needs 1.2588*R of
# descent below the end of the rigid run — 22.7mm at the R18 a 4.5mm cable wants — which is
# a ~75mm stand. 56mm instead accommodates the RIGID run and lets the cable bend in open air,
# and that is only true if there is a channel at desk level for it to reach open air through.
#
# >>> THE CHANNEL RUNS FORWARD, AND THAT IS NOT A PREFERENCE. <<<
#
# The design brief for this change said "rearward". It cannot be: the tail leaves the port
# heading DOWN AND FORWARD and ends at y=26.465, z=-12.719 — 3.281mm above the desk, still
# travelling forward. It meets the desk 0.9mm later at y=25.586. Turning that to rearward is
# a 105deg turn with 3.281mm of vertical budget: R <= 2.6mm, against a minimum of ~18. There
# is no channel width that fixes it either — a horizontal U-turn at R18 needs 40mm of x.
# A rear channel would be 626mm2 of bearing area spent on a path the cable cannot take.
# So the run-out goes forward, under the grille, and the user leads it off to either side.
EGRESS_W  = 14.0        # x. Cable ~4.5mm, strain-relief boot ~8mm; 14 is the boot plus room
                        # to lie over rather than fight the channel wall.
EGRESS_H  = 10.0        # above the desk. Sets where the tail corridor stops (see TAIL_Y) —
                        # a shorter channel pushes that corridor deeper, and the corridor
                        # drifts FORWARD as it descends, into the chamber shaft.
EGRESS_R  = 4.0         # rounds the channel's top corners, so the widest flat span the
                        # slicer has to bridge over the mouth is 14 - 2*4 = 6.0mm, not 14.
# ---- THE REAR CORD TUCK (#46). NOT a second cable path — a place for the cord to lie. ----
#
# JP, with the r2 dock printed: "Power lead should leave toward the back of the desk."
#
# ⚠️ READ THE BLOCK ABOVE FIRST. The cable CANNOT be routed rearward: it leaves the port
# heading down-and-forward, is rigid for its first 40mm, and reaches the desk plane still
# travelling forward with 3.281mm of vertical budget — a rearward exit needs a horizontal
# U-turn wanting ~40mm of lateral room against a 14mm channel. That analysis is unchanged and
# this does not challenge it.
#
# What this is instead: the FLEXIBLE section, having left the front mouth and turned around in
# OPEN AIR out front where it has unlimited radius, tucks under the plinth and runs out the
# back. The stand stops being something the cord has to go around.
#
# RETENTION IS THE DESK, and that is why there is no lip. The obvious move is a dovetail or a
# 0.2-0.4mm undercut at the mouth to grip the cord — it is unnecessary here and would be the
# worse part. This groove faces DOWN. Once the stand is set on the desk the cord is captive
# between the desk surface and the groove ceiling with nowhere to fall; a constriction would
# only make it hard to press in. An undercut that fights the user to solve a problem gravity
# already solved is decoration with a failure mode.
TUCK_W = CABLE_OD + 2.5   # 7.00. Same reasoning as EGRESS_W: cable plus room to LIE in
                          # rather than fight the wall. No boot here — the strain-relief
                          # stays out front, so this is the bare cord and needs far less
                          # than the 14mm the mouth does.
TUCK_D = CABLE_OD + 0.5   # 5.00. Must EXCEED the cord, not merely admit it: a groove
                          # shallower than the cord leaves the stand resting ON the cord,
                          # which is a rocking dock and a crushed cable.
EGRESS_Y1 = SLOT_CY     # rear bound. Derived: the corridor's rear face at the channel
                        # ceiling is at y=30.10, so the channel has to reach past that and
                        # nothing is bought by going further. Asserted in desk_stand().
# ---- and the corridor that gets the cable from the well into that channel ----
# The well above (22 x 12) stops at the cradle's inner floor and is sized for the plug HEAD.
# Below it only the lead and its boot descend, so the corridor is narrower — and it has to be,
# because it drifts forward by tan(TILT) per mm and the speaker chamber's access shaft is
# straight ahead of it at y = CHAM_Y1.
TAIL_W = 18.0           # x. Generous: any moulded USB-C body is under 14mm across.
TAIL_Y = 8.0            # along the slab thickness. THIS IS THE CONSTRAINED ONE — at 10.0 it
                        # leaves 0.95mm of wall to the chamber shaft, which prints as a fin.
                        # Asserted in desk_stand(), overlap-or-clear, not merely "thin".
# ---- stability ----
SLAB_L     = OY1 - OY0                                    # 91.90, the slab's own length
SLAB_COM_Y = SLOT_CY + (SLAB_L/2)*math.sin(math.radians(TILT))   # 45.89
# Treats the docked slab as uniform along its length, which is a proxy, and the proxy errs in
# the UNSAFE direction: the display glass is top-heavy, so the real CoM sits higher up the slab
# and therefore further REARWARD than 45.89. Stated rather than hidden — the check below is
# "bearing material must reach well behind SLAB_COM_Y", and it has 18.11mm of stand depth
# behind this figure to absorb the error. If the slab ever gains a battery, re-derive it.
# Finger scallops in the rear slot wall — see the block in desk_stand() for why they exist
# and why a taller cap could not have worked. Module scope because _check_geometry() asserts
# against them too, and a second hand-typed 12.00 in the assert is exactly the kind of
# duplicate constant this file has been bitten by: the check would keep passing against a
# depth the part no longer has.
SCALLOP_Z0 = 5.00    # local, from the slab's bottom edge: keeps the lower rear grip intact
SCALLOP_D  = 12.00   # out from the slot's rear face, leaving ~7mm of wall behind it
SCALLOP_R  = 3.00    # corner radius IN THE RIM PROFILE — see desk_stand() for both reasons
SCALLOP_CLR = 1.80   # clearance per side beyond the cap's across-corners width. ONE value
                     # for both caps, so the width rule is visible in the result.
SCALLOP_MIN_RIB = 3.00  # if two caps' openings would leave a rib thinner than this, they
                     # MERGE into one scoop. A rib here is a full-height wall segment 12mm
                     # deep carrying the slab's bearing load; under ~3mm it is a fin, not a
                     # wall. The rule decides, so a cap change cannot leave a sliver standing.
SCALLOP_CHAMFER = 0.90  # on the pocket MOUTH, where the rim plane cuts the prism. RETIRED by
                     # the #31 notch — see desk_stand(). Kept as the record of what it was for.
# ---- #31: THE REAR RIM IS TOO TALL TO REACH THE CAPS PAST, AND HEIGHT IS THE DIMENSION ----
#
# The scallops are not the problem and neither is their depth. `SCALLOP_Z0 = 5.00` puts the
# pocket floor BELOW both caps' bottom edge already, so the caps are largely exposed. What is
# missing is an APPROACH: you reach 12mm down a 36mm-wide slot to a cap you cannot see.
#
# The relation is exact, and >>> IT MUST BE TYPED AS THIS FORMULA, NEVER AS ITS VALUE <<<:
# it evaluates to 27.62 in the cradle frame and 43.62 in the exported/desk frame, and both
# numbers were live in the same conversation. A literal here is wrong half the time.
#
#   board y | what sits there        | rim z  | engagement left there
#     15.80 | BOOT cap top edge      | 42.11  | 18.75
#     13.61 | the rim before this    | 40.00  | 16.56
#      0.80 | BOTH caps' bottom edge | 27.62  |  3.75   <- taken
#
# `PAD_Y0` IS the caps' bottom edge and is not a coincidence: the caps are flat-top hexagons
# centred at `_cap_cy(R) = PAD_Y0 + R*sqrt(3)/2`, so their lower flat lands on PAD_Y0 for
# EVERY R. Both caps, one number, derived — a cap resize cannot leave this behind.
#
# ⚠️ THE NOTCH REMOVES APPROACH, NOT RETENTION. It spans only the cap opening (stand x
# 13.20..50.23); the slot's two x-extremes keep the full 16.56mm of engagement, so the lean is
# still contained by 19.67mm of full-height rear rim out of 56.70. Lowering the WHOLE wall to
# the same height would leave 3.75mm everywhere and let the slab flop back ~6deg. That is the
# difference between this and the change it looks like.
NOTCH_Z = SLOT_FLOOR + (PAD_Y0 - OY0)*math.cos(math.radians(TILT))   # 27.6222, cradle frame
NOTCH_R = SCALLOP_R  # rounds the notch's floor-to-sidewall corners, in the XZ profile, for
                     # both of SCALLOP_R's reasons at once — the inside corner of a cut in the
                     # bearing wall is a crack starter, and here (unlike SCALLOP_R, which is
                     # buried 11.5mm down) it is also the edge a fingertip drags over on the
                     # way to the cap. That is the job SCALLOP_CHAMFER used to do.
# --- grille: lyra-artist's hearth-wyrm dorsal ridge, RE-DERIVED for this field.
#
# An earlier comment here deferred the motif and gave the wrong reason ("changing open
# area while validating fit would confound two variables"). Fit is validated by the bezel
# and shell against the board; the stand's grille pattern is independent of it. The real
# obstacle was arithmetic:
#
#   lyra's motif as delivered:  11 spines, 50 x 15 field, 190 mm2 open
#   this grille needs:          38 x 25 field, ~673 mm2 open
#
# It was sized for the geometry that existed when she drew it — a round 28mm driver behind
# a circular 30mm grille. The driver then turned out to be a 40 x 27 sealed-back module and
# the grille was re-tuned for acoustics. The motif was obsolete before it was ever applied,
# through nobody's fault: it correctly answered the previous question. Applied as-is it
# would have cost 72% of the open area and undone the baffle work.
#
# WHAT SURVIVES THE RE-DERIVATION, and what does not:
#   - the RAKE (24.0deg back, measured off her SVG) — the strongest ridge cue at this
#     scale, and it leans the self-supporting direction for FDM, which she noted.
#   - the THICK-TO-THIN gradient — a dorsal ridge tapers toward the tail.
#   - capsule ends (radius = half width), as she drew them.
#   - DROPPED: the length taper. Spines of falling LENGTH are the literal ridge, and are
#     also precisely what removes open area. Moving the taper from length into WIDTH keeps
#     both cues that read at grille scale and costs no acoustics.
#
# Solved for 673 mm2 — identical to the plain array it replaces. See the assert below.
# GRILLE STYLE. "hex" or "ridge". Both are solved to the SAME 673 mm2 open area, so the
# choice is aesthetic, not acoustic — which is only true because the rake was never doing
# acoustic work. These are straight-through bores raked IN THE PLANE of the wall, not
# louvered vanes angled through its thickness: nothing about the angle steers sound.
#
# Hex is the better engineering answer at equal open area, for two reasons:
#   - it is the optimal packing for a given web thickness, so it reaches the target with
#     more material left between holes than parallel slots do;
#   - it is ISOTROPIC. A slot array is slightly stiffer across the bars than along them;
#     a hex field has no preferred direction.
# Solved numerically (not from the closed form) for 673.0 mm2: R=3.75mm circumradius,
# 6.50mm across the flats, 7.40mm pitch, 33 hexes.
#
# RE-DERIVED AGAINST THE GEOMETRY THAT IS ACTUALLY THERE, because the 673 solve assumed
# separate un-flared cells. Rastered in the X-Z plane at 0.01mm — the bores run in Y, so
# that plane IS the aperture. Re-run it with `tools/grille_area.py`:
#
#   THROAT, un-flared cells & field    607.8 mm2 in 37 openings   <- the restriction
#   MOUTH,  flared cells & field       715.9 mm2 in 37 openings   <- the visible face
#   field itself (38 x 25, r2.0)       946.6 mm2
#
# ⚠️ THESE FIGURES WERE STALE FOR THREE RELEASES AND SAID SOMETHING QUALITATIVELY FALSE.
# They were measured at GRILLE_INSET 1.5, HEX_R 3.75 and GRILLE_FLARE 0.60 and then left
# alone while all three moved (1.0, 4.50/sqrt(3), 0.25). What they used to say:
#
#   throat 678.0 in 27 openings · mouth 886.1 in ONE · field (37 x 24, r1.5) 886.1
#
# The old mouth claim was the dangerous one. At flare 0.60 the flared cells DID cover the
# field completely, so the face really was one 37 x 24 opening with the honeycomb behind
# it, and that sentence was repeated in five other files. At the live flare of 0.25
# GRILLE_MOUTH_WEB is 0.4670mm — POSITIVE, so GRILLE_MOUTH_MERGED is False and the cells
# stand apart. The face is now 53 discrete flared holes. Not a drifted decimal: the
# opposite description of what the part looks like.
#
# THE THROAT NO LONGER CLEARS THE SOLVE, and this is the real acoustic news. 607.8 against
# the stated 673.0 is -9.7% (it was +0.7%), and against the driver's ~700mm2 radiating area
# it is 86.8% matched, not 97%. 4.9 of those points are #47's fatter web, bought knowingly. That is the predicted cost of the finer lattice, written
# down at GRILLE_INSET below: HEX_WEB is a print floor that does not scale with the cells,
# so AF 6.4952 -> 4.50 drops the open fraction 0.7714 -> 0.6944, and growing the field
# 37x24 -> 38x25 pays back only part of it. The arithmetic there predicted this; nobody
# had re-measured to confirm it. NOT corrected by moving geometry — that is a real design
# decision about level, and this commit only fixes the numbers that describe it.
#
# 37 cells produce 37 openings. `len(_cells.solids()) >= 30` counts the CUTTING TOOLS, not
# the resulting apertures — right for the question it asks (have the cells fused) and not a
# count of holes in the part. It consumes none of these areas, so nothing asserted moved.
#
# ⚠️ AND THE SLIVERS ARE BACK. The old note ended "the smallest surviving opening is
# 12.85mm2, so no clipped slivers" — true then, false now: the smallest is 1.12mm2, clipped
# by the field's rounded corners. They are open holes, not
# unprintable webs, so this is a cosmetic and dust-ingress note rather than a build failure.
# (The raster also finds 8 ONE-PIXEL specks where a hex edge grazes a field corner; those
# are artifacts of the ruler, 0.0008mm2 in total, and grille_area.py discards them by an
# explicit threshold and reports the count rather than quietly rounding them away.)
GRILLE_STYLE  = "hex"
# ⚠️ WAS 3.75 (AF 6.4952) AND THE GRILLE DROOPED. Issue #28, and the diagnosis moved twice.
#
# JP first: "the hex holes on the front grill are too big." Then, decisively: "sagging/messy but
# holes are open." THE APERTURES FORMED. So this is DROOP, not collapse — and that inverts which
# lever is primary. Droop scales with unsupported SPAN LENGTH, so a bigger aperture droops more
# even when it never fails to bridge. JP's original instinct was right and two of us reasoned
# them out of it: the analysis everyone ran (mine included) was a COLLAPSE analysis, which asks
# where a span fails to form at all. A span can form and still sag.
#
# AF 4.50 rather than the back face's 3.20: JP released the match-the-back-face constraint
# ("they don't have to be exactly the same size ... but they do need to be smaller"), and 4.50
# holds GRILLE_INSET at a comfortable 1.0 where 3.20 would need ~0.2.
#
# 2.5981 = 4.50/sqrt(3), so the ACROSS-FLATS is exactly 4.50. Cells go 33 -> 59.
# ⚠️ r2 PRINTED AND THE WEBS TORE OUT. #47. AF 4.50 / web 0.90 collapsed in patches: webs
# gone, cells merged, heavy fuzz. THE MECHANISM IS THE WEB, NOT A BRIDGE, and that is settled
# by evidence rather than argument — the cells are pointy-up in the print frame (an STL scan
# walked one opening and found it tapering 3.70 -> 0.92mm, a PEAK, so every cell ceiling is
# self-supporting). What failed is the 0.90mm wall itself: at a 0.40 nozzle that is 2.25
# extrusion lines, laid as dozens of tiny per-layer segments around a hex. A weak start tears
# free, its neighbour loses half its anchorage, and the failure propagates — which is exactly
# the "in patches" JP reported and not what a global span problem looks like.
#
# So the lattice is re-parameterised for WEB ROBUSTNESS, and the acoustics re-measured rather
# than assumed. `tools/grille_area.py` rasters each candidate from these very constants:
#
#     AF    web   lines  holes   throat   % of driver ~700mm2
#     4.50  0.90  2.25     53    640.8    91.5%   <- r2, the part that failed
#     4.50  1.25  3.12     49    584.9    83.6%
#     4.75  1.25  3.12     37    607.8    86.8%   <- CHOSEN
#     5.00  1.25  3.12     33    623.2    89.0%
#     5.25  1.25  3.12     33    634.5    90.6%
#     5.50  1.25  3.12     33    638.0    91.1%
#
# EVERY ROW IS RASTERED, INCLUDING THE HOLE COUNTS. An earlier draft of this table carried
# `cells_placed` in the holes column for the rows it had not measured and read 37 all the way
# down. That is the cutting-tool count, not the apertures — the same conflation the 2b ledger
# note warns about — and it made 5.00 look denser than it is. It is 33.
#
# THE TWO CONSTRAINTS PULL OPPOSITE WAYS. Coarser cells buy back open area, because HEX_WEB
# is a print floor that does not scale: open fraction is (a/(a+w))^2, so a fatter web costs
# proportionally more in a finer field. But JP rejected AF 6.4952 in #28 as "too big" (27
# holes), and did not complain about r2's look at 53 — so the aesthetic pressure is toward
# fine and the acoustic pressure toward coarse.
#
# THE RULE USED, so the choice is reproducible rather than a taste: take the FINEST lattice
# whose throat stays within ~5% of the part that actually failed. 4.75 is -5.1% (607.8 vs
# 640.8); 4.50 would be -8.7% and stack a second big regression on a throat this file already
# flags as under-matched, while 5.00+ drops to 33 holes, only six more than the count JP
# rejected. 4.75 keeps 37 holes and is 27% finer across the flats than 6.4952.
#
# Reversible in one constant, and JP judges the look on the print: if r3 reads too coarse,
# 4.50 is one edit (at 83.6%); if it reads fine and sounds thin, 5.00-5.50 is one edit.
#
# Not fixed by going finer, and worth stating because it is the intuitive move: smaller cells
# make this WORSE. The web is a print floor, so a finer field has more web per unit area and
# more per-layer segments to start badly, which is the failure mode.
HEX_R         = 4.75/math.sqrt(3)   # circumradius; ACROSS-FLATS = 4.75 exactly
HEX_WEB       = 1.25     # material between hexes; the print floor. 3.12 lines at a 0.40
                         # nozzle — see the #47 block above for why 0.90 (2.25) tore out.
WYRM_ON       = False    # solid wyrm island in the grille field
GRILLE_RAKE   = 24.0     # degrees back from vertical, from lyra's motif
GRILLE_N      = 9
GRILLE_W0     = 3.20     # widest slot, at the head
GRILLE_TAPER  = 0.78     # narrowest / widest, toward the tail
# GRILLE_SLOT_W / GRILLE_SLOT_W2 / GRILLE_PITCH DELETED — all three were DEAD. Only GRILLE_N,
# GRILLE_W0 and GRILLE_TAPER are read, by the GRILLE_STYLE == "ridge" branch.
#
# The comment that stood here read "was written twice, identically, back to back … both values
# agreed, the second silently wins". ⚠️ THAT WAS TRUE WHEN IT WAS WRITTEN — the file really did
# carry `GRILLE_SLOT_W = 2.20` on two consecutive lines. One was then deleted and the comment
# kept, so by HEAD it described a duplication that no longer existed. I first wrote it up here
# as a comment that had been WRONG, which is a different and worse accusation than the truth:
# it was STALE, and stale-versus-wrong is the whole distinction this file exists to make. A
# fix that leaves its own explanation behind creates the next stale comment.
#
# THE HONEST FIX WAS NEVER A COMMENT. Two dead constants that disagreed (2.20 and 2.60) and a
# third nobody read do not need a hazard note about which one silently wins — none of them won,
# because none of them was referenced. Deleting them removes the hazard instead of documenting
# it, and a hazard comment on a risk that no longer exists is worse than no comment: it points
# somewhere harmless AND certifies that somebody looked.
# Slots are clipped to the driver's RADIATING AREA, inset 1.0mm from its outline so
# the grille never opens onto the frame — an open slot over the flange is a dust path
# into the chamber and vents the enclosure it is meant to seal.
# 1.5 -> 1.0, AND THE REASON IS THE OPPOSITE OF THE INTUITION. A finer lattice is LESS open per
# unit of field, not more, because HEX_WEB is a print floor that does not scale with the cells:
#
#     open fraction = (a/(a+w))^2      w = HEX_WEB = 0.90 always
#     AF 6.4952 -> (6.4952/7.3952)^2 = 0.7714
#     AF 4.5000 -> (4.5000/5.4000)^2 = 0.6944      -10 percentage points
#
# So shrinking the cells spends open area, and the field has to grow to pay for it. 1.0 keeps the
# throat near the 673 mm2 the baffle was solved for; the build's own aperture measurement is the
# authority, not this arithmetic, because the field rect clips edge cells.
GRILLE_INSET  = 1.0
# ── ACOUSTIC TUNING ────────────────────────────────────────────────────────────
# The bottleneck was never the box volume, it was the BAFFLE. A slot behaves like a
# short duct: its impedance scales with length/width, and 2.20mm slots through a 4.00mm
# wall is an aspect ratio of 1.82:1 — the sound has to squeeze through slits nearly
# twice as deep as they are wide. Recessing the OUTER face of the wall in the grille
# region takes the slot depth to 2.20mm (1.00:1) and roughly halves the impedance.
# That is a bigger effect than anything available from volume here.
BAFFLE_T      = 2.20    # wall thickness in the grille region only (was ST_WALL=4.0)
GRILLE_RECESS = ST_WALL - BAFFLE_T
# Slots widened 2.20 -> 2.60 at the same pitch: open area over the field goes 65% -> 76%,
# which puts it above the driver's effective radiating area (~700mm2) rather than below.
# The remaining material still spans only 0.80mm between slots, so it stays printable.
GRILLE_SLOT_W2 = 2.60
# Outer chamfer on each slot. A sharp-edged slot mouth sheds vortices and chuffs at
# level; a flare is the standard fix and costs nothing to print because it opens
# downward-outward, i.e. it is self-supporting in the stand's print orientation.
#
# >>> THE FLARE AND HEX_WEB ARE COUPLED, AND THE COUPLING IS INVISIBLE AT BOTH CALL SITES. <<<
#
# `_hex_field(flare=f)` grows each cell's circumradius by f, so its ACROSS-FLATS grows by
# sqrt(3)*f, while the lattice pitch does not move. The web at the flared MOUTH is therefore
#
#     GRILLE_MOUTH_WEB = HEX_WEB - sqrt(3)*GRILLE_FLARE
#
# and the flared cells MERGE at flare = HEX_WEB/sqrt(3) = 0.5196. At 0.60 they interpenetrate
# by 0.1392mm, so the outer 0.40mm of the 2.20mm baffle is ONE aperture and the 33-cell pattern
# only begins 0.40mm inside the recess floor. Measured in the STL: the webs exist only over
# y 2.20..4.00, exactly as that arithmetic predicts.
#
# THAT IS A CHOICE AND IT IS KEPT ON PURPOSE, but it had to be found by measurement, because
# `assert len(_cells.solids()) >= 30` — the check that exists precisely to catch merged cells —
# is computed on the UN-flared term and is structurally incapable of seeing it. An assert on
# the wrong object reads as coverage. Fixed below.
#
# There is no value that gives relief AND keeps HEX_WEB's 0.90 floor: any flare at all thins
# the mouth. The three coherent settings are flare 0 (0.900 web, no relief), flare <= 0.2598
# (0.450 web, printable but under the part's own floor), and >= 0.5196 (merged on purpose).
# 0.45 is the trap: it leaves 0.1206mm, which passes a solids count and does not print — too
# thin to be a web, too thick to be a merge. The assert below rejects exactly that band, so
# this constant can be changed freely but not into a sliver.
# ⚠️ WAS 0.60 (MERGED ON PURPOSE) UNTIL THE PART CAME OFF THE BED WITH NO GRILLE. Issue #28.
#
# JP: "the hex holes on the front grill are too big" and then "they didn't print because of too
# far bridging." The apertures DID NOT FORM. Everything above this line is correct and none of it
# is about printing: the merge was chosen for acoustics, measured, asserted against the sliver
# band, and documented. What nobody asked is what the merge does to the UNSUPPORTED SPAN.
#
# MEASURED on the shipped ember-stand.stl — downward-facing near-horizontal facets, which are by
# definition bridge undersides, with their X-coverage resolved into contiguous runs:
#
#     z ~ 32.5   35.283 mm   ONE run, no gaps
#     z ~ 34.5   37.078 mm   ONE run, no gaps      <- 37mm of unsupported bridge
#
# ⚠️ ZERO WEBS IN A 37MM RUN. FDM bridges reliably to ~10-20mm. The merge is not merely visible
# at the mouth — it DELETES THE WEBS THAT WOULD HAVE ANCHORED EACH BRIDGE, welding the truncated
# top row of cells and the field rectangle's top edge into one continuous span.
#
# ⚠️ AND THE OBVIOUS LEVER IS THE WRONG ONE. The issue asks for smaller hexes; smaller hexes do
# NOT fix this. The merge threshold is HEX_WEB/sqrt(3) = 0.5196 and HEX_WEB stays 0.90 at every
# lattice scale, so a finer field with this flare merges exactly as completely and still will not
# print. Finer cells arguably make it worse: more cells per row means more truncation.
#
# 0.25 gives a 0.4670mm mouth web -- above the 0.45 floor the assert below names, with margin
# rather than sitting on it. It keeps 42% of the original relief.
#
# THE ACOUSTIC OBJECTION TO CUTTING THE FLARE HAS COLLAPSED, and it is worth saying why rather
# than just doing it: the flare exists because a sharp-edged mouth sheds vortices and chuffs at
# level. That is a real effect. But AN ACOUSTIC BENEFIT THAT DOES NOT PRINT IS NOT A BENEFIT --
# the shipped geometry had no apertures at all, so it had no relief either. 42% of a feature that
# exists beats 100% of one that does not.
GRILLE_FLARE  = 0.25
GRILLE_MOUTH_WEB = HEX_WEB - math.sqrt(3) * GRILLE_FLARE       # 0.4670 at 0.25
GRILLE_MOUTH_MERGED = GRILLE_MOUTH_WEB <= 0.0
assert GRILLE_MOUTH_WEB >= 0.45 or GRILLE_MOUTH_MERGED, (
    f"the grille's flared mouth web is {GRILLE_MOUTH_WEB:.4f}mm — a fin: too thin to print and "
    f"too thick to be a deliberate merge. Either GRILLE_FLARE <= "
    f"{(HEX_WEB-0.45)/math.sqrt(3):.4f} for a printable 0.45mm mouth web, or >= "
    f"{HEX_WEB/math.sqrt(3):.4f} to merge on purpose. This is the SCALLOP_MIN_RIB rule: a wall "
    f"or no wall, never a fin")

def _hex_panel(x0, x1, y0, y1, z0, z1, aflat, web):
    """Fine hex lattice filling a rectangular patch, extruded through Z.

    >>> rotation=30 IS LOAD-BEARING. Without it this field is a single hole. <<<

    `RegularPolygon(R, 6)` is FLAT-top: two vertices share the maximum Y, so the cell
    measures 2R across-corners in X and R*sqrt(3) across-flats in Y. Both lattices here
    space columns at `dx = aflat + web` — POINTY-top spacing, where across-flats is the X
    extent. Drawn flat-top, the cell is 2R wide against a 2R*sqrt(3)/2 + web pitch, so the
    cells OVERLAP and the web is negative.

    Found by luna-bezel while building the bezel face. As built, the stand grille returned
    ONE solid instead of 33, and flood-filling the field showed the remaining material as
    44 disconnected pieces — 43 loose prisms of 2.53-5.38mm2 spanning the full wall. It
    would have printed as a single 37x24 opening with 43 loose triangles rattling around,
    and the back panel's stated 0.80mm web measured 0.305mm. rotation=30 gives one
    connected web at the stated figures.

    Used on the back shell. Same lattice maths as the speaker grille, different
    granularity — coarse there because open area is the goal, fine here because the
    back is a surface you look at and the holes are venting plus the LED's light path.
    """
    R = aflat / math.sqrt(3)
    dx = aflat + web
    dy = 1.5 * R + web * math.sqrt(3) / 2
    cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
    out = None
    ny = int((y1 - y0) / dy) + 2
    nx = int((x1 - x0) / dx) + 2
    for j in range(-ny, ny + 1):
        for i in range(-nx, nx + 1):
            hx = cx0 + i * dx + (dx / 2 if j % 2 else 0)
            hy = cy0 + j * dy
            # keep every hex wholly inside the patch — a clipped hex leaves a sliver
            if not (x0 + R <= hx <= x1 - R and y0 + R <= hy <= y1 - R):
                continue
            h = Pos(hx, hy, z0) * extrude(RegularPolygon(R, 6, rotation=30), z1 - z0)
            out = h if out is None else out + h
    return out


def _hex_field(dz, flare=0.0, depth=None):
    """Pointy-top hex lattice covering the grille field, extruded through the wall."""
    R = HEX_R + flare
    aflat = math.sqrt(3) * HEX_R
    dx = aflat + HEX_WEB
    dy = 1.5 * HEX_R + HEX_WEB * math.sqrt(3) / 2
    fw, fh = DRIVER_W - 2*GRILLE_INSET, DRIVER_H - 2*GRILLE_INSET
    d = depth if depth is not None else ST_WALL + 4.0
    out = None
    for j in range(-int(fh/dy)-3, int(fh/dy)+4):
        for i in range(-int(fw/dx)-3, int(fw/dx)+4):
            cx = i*dx + (dx/2 if j % 2 else 0)
            cy = j*dy
            if abs(cx) > fw/2 + aflat or abs(cy) > fh/2 + HEX_R:
                continue
            h = Pos(ST_W/2 + cx, -2.0, dz + cy) * (Rot(-90,0,0) *
                    extrude(RegularPolygon(R, 6, rotation=30), d))
            out = h if out is None else out + h
    return out


def desk_stand():
    # Deliberately NOT chamfered.  A first attempt shaved the top-front at 38deg;
    # the render showed it eating into the driver seat and the grille field, which
    # both live on the front wall.  Generous R10 corners + the leaning slab give
    # the form; the front wall stays solid and predictable from z=0 to z=ST_H.
    # ONE shell for cradle AND plinth — the plinth is not a second part bolted under a first,
    # it is the same extrusion carried down to z = -PLINTH_H. Modelled SOLID on purpose: a
    # hollow plinth would need the cradle floor to bridge ~56mm at z=0, while a solid one is
    # sliced with ordinary infill and prints with no bridge at all across the transition.
    p = rbox(0,ST_W, 0,ST_D, -PLINTH_H,ST_H, ST_R)
    # slab slot, leaning back by TILT
    slot = Box(SLAB_W+2*SLOT_CLR, SLAB_T+2*SLOT_CLR, 70,
               align=(Align.CENTER,Align.CENTER,Align.MIN))
    p -= Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) * slot)
    # ---- FINGER SCALLOPS: the buttons were unreachable while docked ----
    #
    # JP, looking at the render: "are those new hexagon buttons tall enough? seems like there
    # should be a tab to bring them taller to be more accessible when in the stand." The
    # instinct was right and the cause was worse than height. The stand swallows the first
    # 16.56mm of the slab, so the rim crosses the slab at board y=13.61, and with 0.40mm of
    # SLOT_CLR between the cap face and a solid wall a finger reaches nothing:
    # THE OBSTRUCTION IS BESIDE THE CAP, NOT ABOVE IT. Adding material cannot fix a problem
    # caused by surrounding material; the wall has to go.
    #
    # ⚠️ RE-MEASURED AFTER THE CAPS GREW, BECAUSE THIS PARAGRAPH'S OWN PREMISE EXPIRED. It
    # used to read "BOTH caps are entirely inside the slot — the BOOT cap's top edge is 3.81mm
    # BELOW the rim, the RESET cap's 6.23mm below". At 15.00/10.00mm across flats that is no
    # longer true of BOOT:
    #     RESET  top edge y=10.80  ->  2.81mm BELOW the rim   (still buried)
    #     BOOT   top edge y=15.80  ->  2.19mm ABOVE the rim   (now breaks the rim line)
    # The scoop is still required, for two reasons that survive the change: RESET is still
    # wholly buried, and 2.19mm of proud cap with a wall 0.40mm behind it is something you can
    # see but not get a fingertip onto — the obstruction was always lateral, and it still is.
    # But "both caps are entirely inside the slot" was the justification for this whole
    # feature, so it is worth saying plainly that it is now half true rather than leaving a
    # stale premise propping up a correct conclusion.
    #
    # WHY NOT THE TAB, since that was the actual suggestion. A lever hinged at the pad's
    # BOTTOM with a thumb tab reaching above the stand is mechanically sound in principle and
    # unbuildable here. The hinge angle is not a free variable: it is pip travel over the
    # pip's distance from the hinge, 0.40 / 2.46 = 9.3deg, and it does not improve by making
    # the lever longer (a longer lever buys tip travel, not a gentler bend). Holding PLA under
    # ~2% strain through 9.3deg needs about 4mm of thinned flexure; there is 2.46mm between
    # the shell's bottom wall and the switch. The hinge would craze in service. The existing
    # top-hinged pad only works because its pip is 7.07mm from the hinge, which is 3.2deg.
    #
    # WHY A SCALLOP RATHER THAN A WINDOW. The rear wall is ~19mm thick at this height, so a
    # through-window is a tunnel, not an access port. Opening the pocket UPWARD instead means
    # the finger comes down the back of the slab from above — and it prints with no bridge at
    # all, since the pocket floor is solid and every wall is near-vertical.
    #
    # THE SLAB LEANS BACK, SO THIS REAR RIM IS THE LOADED SURFACE — the scallops are sized to
    # leave three well-spaced bearing zones rather than one continuous line. THE ZONES ARE
    # IN BOARD X (0..50): x < 8.4, 18.5..29.6, and > 43.6. The slab is 55.9mm wide because
    # it spans board x -2.95..52.95, so quoting zones in one frame and the width in the
    # other invites exactly the arithmetic error this file keeps warning about. On a ~100g slab the raised contact pressure is
    # irrelevant; losing the bearing line entirely would not be.
    # WIDTHS ARE DERIVED, NOT TYPED. They were 14.0 and 10.0, which are +1.80 and +1.20 per
    # side of their caps' across-corners width. Two different widths for two different caps is
    # logical, but because the two margins DISAGREED the pair read as arbitrary — the rule was
    # not visible in the result. One clearance for both makes it legible: BOOT stays 14.00 and
    # RESET goes 10.00 -> 11.20. Bearing zones become 7.85 / 10.53 / 6.42 = 24.80mm of 50.0
    # (50%), against 26.0 before, so the whole change costs 1.2mm of bearing line.
    #
    # RESET AT 11.20mm IS NAIL ACCESS, NOT FINGER ACCESS, AND THAT IS THE DECISION. A
    # fingertip pad is ~15-19mm wide, so BOOT at 14.00 is a snug finger and RESET is a nail or
    # a tool. That is the right way round rather than a consequence of the cap being smaller:
    # RESET is hardwired to CHIP_PU and reboots the MCU *and* the LCD, and holding BOOT low
    # across it enters ROM download mode, which looks like a brick. The awkward one should be
    # the destructive one.
    #
    # TWO RADII, IN TWO DIFFERENT PLACES, FOR TWO DIFFERENT REASONS. Do not conflate them —
    # I did, and the render caught it.
    #
    # SCALLOP_R = 3.00 rounds the pocket FLOOR, via rrect_y's X-Z profile. That is the
    # STRUCTURAL fix only. Under the leaning slab the rim is the bearing surface and a crack
    # would start at the floor's inside corner, so the corner a Box left there was a stress
    # riser. It is also COMPLETELY INVISIBLE: the floor sits at local Z=5.00 and the rim
    # crosses at ~16.56, so the radius is buried 11.5mm down. A first version of this comment
    # claimed the profile radius was "the plane you actually see" and the rear elevation
    # showed the silhouette unchanged — the notch was still square.
    #
    # SCALLOP_CHAMFER = 0.90 breaks the mouth's arris — the edge a fingertip drags over on the
    # way in, and the one that prints as a sharp lip. It has to be an EDGE chamfer because of
    # what forms the notch: the mouth is the RIM PLANE CUTTING A STRAIGHT-WALLED PRISM, so its
    # corners are a 90deg dihedral between wall and top face, and no radius anywhere in the
    # prism's own profile can reach it.
    #
    # >>> IT DOES NOT MAKE THE SILHOUETTE STOP READING AS CASTELLATION, AND IT WAS RENDERED
    # BEFORE THAT WAS WRITTEN DOWN. <<< 0.90mm of chamfer on an 11-14mm notch is a lip detail;
    # the rear elevation still shows two square bites. The notch is rectangular BY FUNCTION —
    # the cap sits 3.81mm below the rim so the pocket has to be deep, and the cap sets its
    # width — so it will read as a service opening rather than as decoration. That is
    # acceptable for a rear-facing feature, and the honest lever if it ever needs to look
    # deliberate rather than merely soft is SYMMETRY, not softness: both scallops at 14.00
    # would cost 4mm more bearing line (22.0mm, 44%) and buy a matched pair, which reads far
    # more intentional than a derived-but-unequal one. Not taken; recorded so it is a choice.
    #
    # The mouth edges are selected by BOTH ENDPOINTS lying inside the pocket's own x span,
    # not by midpoint: the slot's rear top edge is split into segments by these pockets and
    # one of those segments has its midpoint inside the BOOT span. Selecting on the midpoint
    # would have chamfered a 10.5mm stretch of the bearing rim by accident.
    # >>> CENTRED ON THE CAP, NOT THE SWITCH. <<< The first version of this block used the
    # switch x, and once the caps gained their offset islands that was a real defect rather
    # than a style point: a 20.92mm pocket centred on BTN_BOOT_X=36.58 spans 26.12..47.04
    # while the island spans 24.39..41.71, so 1.73mm of the cap would have sat behind solid
    # wall while the pocket wasted 5.33mm on empty rim. A finger reaches the CAP. There is an
    # assert below, because that failure is invisible in a render from the wrong angle.
    #
    # AND THE MERGE IS DERIVED, NOT TYPED. Each cap gets a span; if the rib the two would
    # leave between them is too thin to be a wall, they become ONE scoop. At the current caps
    # (15.00 / 10.00 across flats) the rib is 0.51mm, which is not a wall, it is a defect that
    # prints as a fin — so this resolves to a single opening. At the previous 9.01/6.58 caps
    # the same rule left a 10.53mm rib and gave two pockets, which is also right. The rule
    # decides, so a future cap change cannot silently leave a sliver standing.
    # One scoop also reads better, for the same reason two notches read as castellation: one
    # deliberate opening beats two bites with a splinter between them.
    _spans = []
    for (cx, cy) in BTN:
        _cyh, _R, _ = cap_geometry(cx)
        _icx = cap_center_x(cx)
        _w = 2*_R + 2*SCALLOP_CLR          # cap across CORNERS + clearance per side
        _spans.append((_icx - _w/2, _icx + _w/2))
    _spans.sort()
    _rib = _spans[1][0] - _spans[0][1]
    if _rib < SCALLOP_MIN_RIB:
        _spans = [(_spans[0][0], _spans[-1][1])]
    for (_x0, _x1) in _spans:
        p -= Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) * rrect_y(
                 (_x0 + _x1)/2 - BW/2, SCALLOP_Z0 + 35.0, _x1 - _x0, 70.0, SCALLOP_R,
                 SLAB_T/2 + SLOT_CLR, SCALLOP_D))
    # every cap must be WHOLLY inside an opening — this is the assert the switch-vs-island
    # bug above would have tripped, and it costs nothing to keep.
    for (cx, cy) in BTN:
        _cyh, _R, _ = cap_geometry(cx)
        _icx = cap_center_x(cx)
        assert any(_a <= _icx - _R and _icx + _R <= _b for (_a, _b) in _spans), (
            f"the cap at island x={_icx} spans {_icx-_R:.2f}..{_icx+_R:.2f} and no scallop "
            f"opening {[(round(a,2), round(b,2)) for a, b in _spans]} contains it — part of "
            f"the cap you are meant to press is behind solid wall")
    # ---- #31: NOTCH THE REAR RIM ACROSS THE SAME SPAN ----
    #
    # >>> THIS RETIRES THE MOUTH CHAMFER, AND THE REASON IS WORTH STATING. <<<
    #
    # There used to be a `chamfer(_mouth, SCALLOP_CHAMFER)` here, selecting the three edges per
    # opening that lie at z = ST_H — the pocket's two side walls and its back wall where the rim
    # plane cuts them. Every one of those edges is inside the region this notch removes
    # (x within the span, y >= 43.76, z >= 40 > NOTCH_Z). Running it would have been 0.9mm of
    # chamfer applied to geometry deleted four lines later: not wrong, just spent. The edge a
    # fingertip now drags over is the notch floor's, and NOTCH_R rounds it BY CONSTRUCTION —
    # the cut's own XZ profile — rather than by an edge query that has to be asserted against
    # drift. A radius you build into the tool cannot select the wrong edge.
    #
    # The pocket itself SURVIVES and is not redundant: its floor tilts with the slab, from
    # z=26.53 at the slot face down to z=23.42 twelve millimetres out, so it dips BELOW the
    # notch and keeps giving the finger depth under the cap's bottom edge.
    #
    # Cut from y = SLOT_CY rearward: at every height the notch spans (27.62..40) the slot's
    # FRONT face is at y=26.18..29.50, so the front wall is never touched, and everything
    # between the centreline and the rear face at those heights is either slot void or the rim
    # this is removing. The x bounds are the scallop spans, so the notch cannot drift off the
    # caps — one derivation, two features.
    for (_x0, _x1) in _spans:
        _a, _b = ST_W/2 + (_x0 - BW/2), ST_W/2 + (_x1 - BW/2)
        p -= rrect_y((_a + _b)/2, (NOTCH_Z + ST_H + 2*NOTCH_R)/2, _b - _a,
                     (ST_H + 2*NOTCH_R) - NOTCH_Z, NOTCH_R, SLOT_CY, ST_D + 1 - SLOT_CY)
    # sealed speaker chamber, open at the bottom (closed by the base plate)
    cx0,cx1 = CHAM_X0, CHAM_X1
    # Rear wall pushed 21.0 -> 22.0. That is as far as it safely goes: the slab slot's
    # front face at the floor sits at y = SLOT_CY - (SLAB_T/2 + SLOT_CLR) ~= 24.9, so
    # 22.0 leaves ~2.9mm of wall at the tightest point and more above, since the slot
    # leans back at TILT. Volume 30.3 -> 32.1cm3. Modest, and free — the sealed volume
    # only sets the low-frequency corner, and on a driver with Fs ~650Hz the box is not
    # what is limiting output. The baffle was.
    # Rear wall now DERIVED, not chosen: baffle + front gap + driver body + the pad it
    # tapes to. Previously 22.0 was "as deep as the slab slot allows", which maximised
    # sealed volume — the right goal for a baffle-mounted driver and the wrong one here.
    # With the driver taped to the rear wall, extra depth is not extra enclosure, it is
    # extra AIR IN FRONT OF THE DIAPHRAGM, i.e. a cavity resonance.
    cy0, cy1 = CHAM_Y0, CHAM_Y1
    assert cy1 <= 24.0, f"chamber rear {cy1} would foul the slab slot at ~24.9"

    # Ceiling raised 34.0 -> 37.0 for the rectangular driver. At 34 the chamber was
    # 30mm tall and a 27mm driver left 1.5mm a side — no room for a seat lip. At 37 it
    # is 33mm tall, the seat clears by ~2.5mm, and the sealed volume goes 27.5 -> 30cm3,
    # which helps the low end rather than hurting it. Still 3mm of wall above (ST_H=40),
    # and no conflict with the slab slot: that sits at y~34 while the chamber ends at 21.
    p -= bx(cx0,cx1, cy0,cy1, ST_WALL, 37.0)   # ceiling = 17mm bridge, no supports
    # BOTTOM ACCESS — now a SHAFT, because the plinth is underneath it. The driver goes up
    # this way and the base plate closes the chamber at the top of it (z 0.4..4, unmoved), so
    # it has to stay open all the way to the desk. That is 826mm2 of the plinth's underside
    # and it is the single largest intentional opening in the part; it is in the bearing
    # ledger at check 2b, not a surprise found later.
    p -= bx(cx0,cx1, cy0,cy1, -PLINTH_H - 1.0, ST_WALL)
    # driver seat on the INSIDE of the front wall + grille through it
    # Centred in the taller chamber: (ST_WALL + 37.0) / 2
    dz = 20.5
    # TAPE PAD on the chamber's rear wall, standing PAD_PROUD off it so the adhesive
    # meets one continuous flat plane and nothing — no fillet, no print artefact at the
    # wall/floor junction — interrupts the bond. Added, not subtracted: this is the one
    # feature in the stand that is material rather than a void.
    #
    # ⚠️ THAT CLAIM WAS FALSE OF THE PART FOR AS LONG AS THIS COMMENT HAS EXISTED, and it is
    # worth correcting rather than deleting, because the comment is how it survived. The
    # speaker-wire pass is cut through this pad 129 lines below, and it used to start 0.50mm
    # BEHIND the pad's inner face — so 6.0 x 4.6mm of the "continuous flat plane" was a
    # 0.474mm membrane with a hole behind it. Worse than the fillet the sentence rules out,
    # and the sentence is what stopped anyone looking. There is now an aperture assert at that
    # cut; the bond loses a 6 x 5mm notch, 30 of ~1150mm2 (2.6%), at the pad's bottom edge
    # where the driver's own JST pigtail leaves anyway.
    #
    # A COMMENT THAT GUARANTEES A PROPERTY IS A LIABILITY UNLESS SOMETHING CHECKS IT. This one
    # promised an uninterrupted bond surface and outlived the geometry that made it true.
    pad = rrect_y(ST_W/2, dz,
                  DRIVER_W + 2*DRIVER_CLR, DRIVER_H + 2*DRIVER_CLR,
                  DRIVER_R + DRIVER_CLR,
                  cy1 - PAD_PROUD, PAD_PROUD)
    p += pad
    # The baffle's inner face is now deliberately LEFT ALONE — no lip, no recess. The
    # driver never touches it, and anything cut there would only add a cavity edge in
    # front of the diaphragm.
    field = rrect_y(ST_W/2, dz,
                    DRIVER_W - 2*GRILLE_INSET, DRIVER_H - 2*GRILLE_INSET,
                    max(DRIVER_R - GRILLE_INSET, 0.8),
                    -1.0, ST_WALL + 3)
    # BAFFLE RECESS. Cut from the OUTSIDE, so the inside face the speaker tapes to stays
    # flat and unbroken — the recess must not touch the bonded area. Slightly larger than
    # the grille field so the thin region fully contains the slots.
    p -= rrect_y(ST_W/2, dz,
                 DRIVER_W + 2*DRIVER_CLR, DRIVER_H + 2*DRIVER_CLR,
                 DRIVER_R + DRIVER_CLR,
                 -0.5, GRILLE_RECESS + 0.5)

    if GRILLE_STYLE == "hex":
        _cells = _hex_field(dz)
        # THE CELLS MUST BE SEPARATE, and no area check can tell you they are.
        #
        # Drawn flat-top on pointy-top spacing they overlapped and fused into ONE solid,
        # while the open area still measured ~673mm2 — the number was right and the part
        # was ruined. Counting solids is the property that actually matters: 33 cells with
        # a connected web between them, not one hole with loose prisms in it.
        _n = len(_cells.solids())
        assert _n >= 30, (
            f"hex grille collapsed to {_n} solid(s) — the cells have merged, so the web is "
            f"negative and the part would print as one opening with loose prisms")
        _flared = _hex_field(dz, flare=GRILLE_FLARE, depth=GRILLE_RECESS + 2.4)
        # >>> AND THE SAME CHECK ON THE FLARED TERM, WHICH IS THE ONE THAT CAN MERGE. <<<
        #
        # The assert above is aimed at `_cells`, whose web is HEX_WEB by construction and does
        # not depend on the flare at all — so it has never been able to fail for the reason it
        # names, and it passed throughout the whole period the flared mouth WAS merged. That is
        # this file's own recurring fault, in one of its own guards: an invariant whose success
        # condition is insensitive to the failure mode it appears to cover.
        #
        # Only asserted when the design CLAIMS separate flared cells. At GRILLE_FLARE >= 0.5196
        # the merge is deliberate (see the constant), and a merged mouth must not be a build
        # failure — but it must not be an accident either, which is what GRILLE_MOUTH_WEB and
        # its assert make impossible.
        if not GRILLE_MOUTH_MERGED:
            _nf = len(_flared.solids())
            assert _nf >= 30, (
                f"the FLARED grille cells collapsed to {_nf} solid(s) at GRILLE_FLARE="
                f"{GRILLE_FLARE} — mouth web {GRILLE_MOUTH_WEB:.4f}mm. `_cells` is unaffected "
                f"by the flare, so the assert above cannot see this")
        bars = _cells + _flared
    else:
        bars = None
        _fw = DRIVER_W - 2*GRILLE_INSET
        _pitch = _fw / GRILLE_N
        _widths = []
        for i in range(GRILLE_N):
            w = GRILLE_W0 * (1 - (1-GRILLE_TAPER)*i/(GRILLE_N-1))
            _widths.append(w)
            cx = ST_W/2 - _fw/2 + _pitch*(i+0.5)
            sk = RectangleRounded(w, 46.0, w/2 - 0.01)
            b  = Pos(cx, -2.0, dz) * (Rot(0, GRILLE_RAKE, 0) *
                                      (Rot(-90,0,0) * extrude(sk, ST_WALL + 4)))
            skf = RectangleRounded(w + 2*GRILLE_FLARE, 46.0,
                                   (w + 2*GRILLE_FLARE)/2 - 0.01)
            fl  = Pos(cx, -2.0, dz) * (Rot(0, GRILLE_RAKE, 0) *
                                       (Rot(-90,0,0) * extrude(skf, GRILLE_RECESS + 2.4)))
            bars = (b+fl) if bars is None else bars+(b+fl)
        _web = _pitch - max(_widths)
        assert _web >= 0.85, f"grille web {_web:.2f}mm is too thin to print"

    # THE WYRM IS A SOLID ISLAND IN THE SLOT FIELD.
    #
    # Not a hole shaped like a dragon — material shaped like one, with the slots cut
    # everywhere except inside it. It therefore reads as a figure standing in the grille,
    # the same way the creature sits in the fire on the screen.
    #
    # Traced from esphome/art/dragon.py by tools/make_wyrm_spans.py, so it is the SAME
    # curves the device renders and the website traces — one creature, three renderings.
    # Re-pose the wyrm there and this follows.
    #
    # THE COST, stated because it is real: the silhouette is 204.9mm2 and blocks ~156mm2
    # of slot, taking open area 673 -> ~517mm2. That is 77% of the plain array and 74% of
    # the driver's ~700mm2 effective radiating area. A dragon on the case costs about a
    # quarter of the grille. Setting WYRM_ON = False restores the plain array exactly.
    if WYRM_ON:
        _fx = ST_W/2 - (DRIVER_W - 2*GRILLE_INSET)/2
        _fz = dz - (DRIVER_H - 2*GRILLE_INSET)/2 + ((DRIVER_H - 2*GRILLE_INSET) - _W.WYRM_H)/2
        wyrm = None
        for (rx, ry, rw, rh) in _W.WYRM:
            b = bx(_fx+rx, _fx+rx+rw, -3.0, ST_WALL+4.0, _fz+ry, _fz+ry+rh)
            wyrm = b if wyrm is None else wyrm + b
        p -= ((field & bars) - wyrm)
    else:
        p -= (field & bars)
    # USB-C WELL. The plug enters the board's bottom short edge and points down-and-
    # forward along the slab's own axis, so it needs a cavity UNDER the slot rather than
    # behind it. Spans the full height between the stand floor and the new slot floor.
    # Generous on purpose: a moulded plug's strain relief is wider than the connector,
    # and a cable forced into a tight well takes the bend at the plug rather than in the
    # lead, which is how USB-C cables die.
    # >>> THE WELL MUST FOLLOW THE SLAB'S AXIS, NOT A HORIZONTAL PLANE. <<<
    #
    # First cut was a flat box down to z = SLOT_FLOOR. That is wrong, and the reason is
    # worth stating because it is invisible on the centreline: the slot is a box rotated
    # by TILT with align=MIN, so its BOTTOM FACE tilts too. The front-bottom corner rises
    # to z ~= 26.4 while the rear-bottom corner drops to ~21.6. A flat well to z = 24
    # therefore leaves a wedge of material between itself and the real slot bottom —
    # exactly where the plug emerges. Point-sampling the centreline said "20mm clear",
    # because the centreline is the one place the discrepancy vanishes.
    #
    # The plug travels DOWN THE TILT, so its clearance volume has to be tilted with it.
    #
    # 16mm in Y, not 22: the well drifts forward as it descends (sin 15deg per mm), and at
    # full depth a wider one would breach the sealed speaker chamber at y = 22.0. The
    # assert below is what makes that a build failure rather than a leak discovered by ear.
    # 12.0, solved rather than guessed: the well drifts forward sin(TILT) per mm of depth,
    # so at full reach its front face sits at SLOT_CY - sin(15)*20.7 - _wellY/2. At 16.0 that
    # is y=20.6, inside the sealed chamber whose rear wall is at 22.0 — the assert in
    # _check_geometry caught it, which is the whole point of having it. 12.0 lands at 22.6.
    _wellY = 12.0
    # DEPTH IS DERIVED, not 30.0. At 30 the well ran 30mm down the tilted axis and its far
    # end reached z = -4.98 — straight THROUGH the 4mm floor, leaving a 273mm2 hole in the
    # underside and a bearing footprint of only 2911 of 4010mm2. The stand was standing on a
    # ring. Nothing detected it: the boolean check compares parts to the BOARD, and a hole in
    # the floor intersects nothing at all.
    #
    # ⚠️ THIS SAID "1099mm2 HOLE", WHICH IS THE WRONG NUMBER FOR THE RIGHT FAULT. 1099 is
    # 4010 - 2911, the TOTAL open plan — the chamber shaft, the egress channel and the chamfer
    # included. The WELL's own opening was 273mm2. Attributing all of it to the well overstates
    # this feature by 4x and would misprice any future decision to deepen it. Both figures come
    # from the 2026-07-30 battery study (scratch/hosyond-s3/battery.md), and both were
    # re-measured here: the old 30.0 box cuts 273.3mm2 at z~0, the derived depth cuts 0.0.
    #
    # CLOSED, and measurably so: at 20.71 the well's lowest corner sits at z = +2.447 — the end
    # face centres on the inner floor at z = ST_WALL = 4.0 and the tilt drops one corner 1.55
    # below that, still 2.4mm of material above the outside. That is why the 2b ledger carries
    # no well term: there is no opening left to account for.
    #
    # The plug never needed it. Measured clearance was "past 20.7mm" for every plug size, and
    # 20.7 IS the floor — (SLOT_FLOOR - ST_WALL)/cos(TILT). So ending the well exactly at the
    # inner floor surface costs nothing and closes the hole for free.
    _wellDepth = (SLOT_FLOOR - ST_WALL) / math.cos(math.radians(TILT))
    p -= Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) *
             Box(22.0, _wellY, _wellDepth, align=(Align.CENTER, Align.CENTER, Align.MAX)))
    # ---- TAIL CORRIDOR + EGRESS CHANNEL: the rest of the 40mm rigid run (#29/#30) ----
    #
    # The well above ends at the cradle's inner floor, which is where the paragraph above says
    # the plug stops needing room. It is where the CABLE starts needing it. 22.69mm of the
    # rigid run is inside the well; the remaining 17.31mm goes through the floor and into the
    # plinth, and it is still straight, so it still needs a straight corridor.
    #
    # The corridor stops at the egress channel's ceiling rather than at the desk, and that is
    # not thrift — it is the chamber. THE CORRIDOR DRIFTS FORWARD AS IT DESCENDS, tan(TILT)
    # per mm, straight at the speaker chamber's access shaft. The exact y of a corridor wall
    # at local offset a, at height z, is
    #
    #     y = SLOT_CY + tan(TILT)*(z - SLOT_FLOOR) -/+ a/cos(TILT)
    #
    # — NOT the `SLOT_CY - sin(TILT)*reach -/+ a` that check 2a uses, which offsets the axis
    # in GLOBAL y and so understates the drift by (1/cos - 1)*a. 2a is conservative and left
    # alone; this one is exact because it is the tight one.
    # ⚠️ THE OVERRUN IS WHY r2 PRINTED A MEMBRANE ACROSS THE BORE. #47, and JP carved it out
    # by hand. Without it the corridor stops at exactly the channel's ceiling plane — but the
    # corridor's end face is PERPENDICULAR TO THE TILTED AXIS, so it is a sloped face, and its
    # high side sits (TAIL_Y/2)*sin(TILT) = 1.29mm ABOVE that plane. What is left between the
    # sloped face and the arched roof is a lens of material lying across the open bore with
    # nothing under it, and the slicer prints it: one partial layer, straight through the
    # cable's path.
    #
    # MEASURED, not inferred. Sectioning the r2 solid inside the bore's own plan footprint
    # every 0.4mm walks the material up to a LOCAL MAXIMUM exactly at the roof plane and back
    # down again — 63.50mm2 at z=-6.40, 85.07 at z=-6.00, 76.66 at z=-5.60, then 30.92 steady
    # above. A local maximum is the signature: ~21.6mm2 appears at one layer with void beneath
    # it. Anything monotonic there is supported; a bump is a membrane.
    #
    # The fix is to let the bore run PAST the ceiling by exactly that overhang, so the two
    # voids merge and no roof plane crosses the bore at all. Derived from the geometry that
    # causes it — (TAIL_Y/2)*tan(TILT) of extra travel along the axis lowers the face's high
    # side by (TAIL_Y/2)*sin(TILT) — so it tracks TAIL_Y and TILT automatically and cannot go
    # stale the way a typed 1.3 would. It costs no bearing area: the extra void lives at
    # z -7.3..-6, ten millimetres above the desk.
    _tailOverrun = (TAIL_Y/2) * math.tan(math.radians(TILT))
    _tailDepth = ((SLOT_FLOOR + PLINTH_H - EGRESS_H) / math.cos(math.radians(TILT))
                  + _tailOverrun)
    p -= Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) *
             Box(TAIL_W, TAIL_Y, _tailDepth, align=(Align.CENTER, Align.CENTER, Align.MAX)))
    def _tail_y(a, z):
        return (SLOT_CY + math.tan(math.radians(TILT))*(z - SLOT_FLOOR)
                + a/math.cos(math.radians(TILT)))
    _cz = -PLINTH_H + EGRESS_H
    # ⚠️ OVERLAP-OR-CLEAR, not merely "thick enough" — the SCALLOP_MIN_RIB idiom applied to a
    # third pair of features. What separates the corridor from the chamber shaft is a wedge of
    # plinth that exists only over z -6..4; below that the egress channel opens and the two
    # voids are one, which is HARMLESS (both are outside the seal — the chamber's seal is the
    # base plate at z 0.4..4, and everything under it is atmosphere). The failure is the
    # in-between case: a wall that tapers to nothing prints as a fin. 2.52mm at TAIL_Y=8.0;
    # 0.95mm at 10.0, which is what set the constant.
    _wall = _tail_y(-TAIL_Y/2, _cz) - CHAM_Y1
    assert _wall <= 0.0 or _wall >= 2.0, (
        f"the tail corridor's front wall reaches y={_tail_y(-TAIL_Y/2, _cz):.2f} at the egress "
        f"ceiling (z={_cz:.2f}) and the chamber shaft's rear wall is at y={CHAM_Y1:.2f} — "
        f"{_wall:.2f}mm between them. Either clear it by 2mm or let them merge; a wedge "
        f"thinner than that is a fin standing on the channel ceiling. Lower TAIL_Y or raise "
        f"EGRESS_H — both move it, and EGRESS_H also shortens the fin")
    # and it must not breach the SEALED chamber, which begins at the cradle's inner floor
    assert _tail_y(-TAIL_Y/2, ST_WALL) >= CHAM_Y1 + 3.0, (
        f"the tail corridor reaches y={_tail_y(-TAIL_Y/2, ST_WALL):.2f} where the sealed "
        f"chamber's rear wall is at {CHAM_Y1:.2f} — that is the wall of a SEALED box")
    # EGRESS CHANNEL — the run-out, at desk level, opening through the FRONT face.
    # Built as a rounded profile rather than a box so the mouth's flat bridge is
    # EGRESS_W - 2*EGRESS_R = 6.0mm instead of 14.0, and so a 64mm-wide face gains a detail
    # rather than a rectangular bite. The profile is centred ON the desk plane and half of it
    # is therefore outside the part: what remains is a EGRESS_H-tall arch.
    p -= rrect_y(ST_W/2, -PLINTH_H, EGRESS_W, 2*EGRESS_H, EGRESS_R,
                 -1.0, EGRESS_Y1 + 1.0)
    assert _tail_y(+TAIL_Y/2, _cz) <= EGRESS_Y1, (
        f"the corridor's rear face is at y={_tail_y(TAIL_Y/2, _cz):.2f} at the channel ceiling "
        f"but the channel stops at y={EGRESS_Y1:.2f} — the cable would arrive onto a ledge")
    assert TAIL_W <= 22.0 and EGRESS_W <= TAIL_W, (
        f"the corridor ({TAIL_W}) must stay inside the well above it (22.0) so it removes no "
        f"new material there, and the channel ({EGRESS_W}) must stay inside the corridor so "
        f"the step at z=0 faces UP (supported) rather than down (an overhang)")
    # REAR CORD TUCK (#46) — straight run, front channel's end to the rear face.
    #
    # Starts where the egress channel stops (EGRESS_Y1 + 1) so the two read as one system and
    # no rib is left between them, and runs past ST_D so the mouth is a clean opening in the
    # rear face rather than a blind pocket. Straight is available: the speaker chamber's access
    # shaft ends at y=CHAM_Y1=19.3, far in front of where this starts, so nothing is in the way
    # and no route-around is needed.
    #
    # THIS CUTS THE BEARING SURFACE ON PURPOSE. 7.00 x 29.00 = 203.0mm2, carried as its own
    # line in the 2b ledger with the floor re-derived — never nudged to fit.
    p -= bx(ST_W/2 - TUCK_W/2, ST_W/2 + TUCK_W/2,
            EGRESS_Y1 + 1.0, ST_D + 1.0, -PLINTH_H, -PLINTH_H + TUCK_D)
    # IT MUST NOT MEET THE SPEAKER-WIRE ROUTE, which crosses the same y-span. Proven, not
    # assumed: that cut lives at z ST_WALL..13.0 and this one at -PLINTH_H..-PLINTH_H+TUCK_D.
    assert -PLINTH_H + TUCK_D < ST_WALL, (
        f"the rear cord tuck reaches z={-PLINTH_H + TUCK_D:.2f} and the speaker-wire route "
        f"starts at z={ST_WALL:.2f} — they would merge into one opening through the plinth "
        f"and the rear face would lose the material between them")
    # AND IT MUST NOT UNDERCUT THE #35 CHAMFER at the rear face. The chamfer takes 0.80 off
    # the bottom edge all the way round; the tuck's ceiling has to stay above it, or the
    # groove mouth opens into the chamfer and the rear edge becomes a knife.
    assert TUCK_D > CHAMFER + 1.0, (
        f"the tuck is {TUCK_D:.2f} deep against a {CHAMFER:.2f} perimeter chamfer — under "
        f"1mm of material between the groove ceiling and the chamfered edge")

    # SPEAKER-WIRE ROUTE: slot floor -> out the back.  ⚠️ THIS IS NO LONGER THE USB CABLE'S
    # ROUTE. It was cut for the power lead, the power lead never fitted through it (#29), and
    # the lead now leaves through the plinth instead. What still uses it is the driver's own
    # pigtail, which arrives from the chamber pass-through at y=30 — so the cut stays, with
    # the right name on it. It is the reason that pass-through has somewhere to go.
    p -= bx(ST_W/2-8, ST_W/2+8, 29.0, ST_D+1, ST_WALL, 13.0)
    # SPEAKER WIRE PASS-THROUGH. Caught by JP: the chamber had no exit at all. Its only
    # opening was the bottom, closed by the base plate — which is correct for a SEALED
    # enclosure and leaves the driver's own wires with nowhere to go. The board's
    # speaker header is on a long edge, so the wire has to reach the slab slot.
    #
    # This channel runs from inside the chamber rearward to y=30, meeting the board cable
    # route that starts at 29. From there the wire follows the same path up to the slot.
    # 6 x 5mm: enough for a 2-core lead, small enough to seal.
    #
    # >>> IT MUST START INSIDE THE TAPE PAD, NOT BEHIND IT. THIS CUT WAS 92% BLOCKED. <<<
    #
    # It read `19.0`, which was `cy1` when cy1 was 21.0 and is 0.50mm BEHIND the pad's inner
    # face now that the pad exists. `p += pad` (above) fills y cy1-PAD_PROUD .. cy1 across
    # x 11.40..52.60, so a cut starting at cy1 leaves the pad's full PAD_PROUD standing across
    # the whole mouth of this channel:
    #
    #     a 0.474mm membrane at x 29.00..35.00, z 6.40..11.00 — 12.4mm3 over 23 layers,
    #     a rock-steady 2.69mm2 per layer, THE THINNEST FEATURE IN THE PART
    #     clear aperture into the chamber: 2.37 of 30mm2 (7.9%) — one 5.92 x 0.40mm slit
    #     at z 6.00..6.40, under the pad's bottom edge
    #
    # A 2-core speaker lead is 1.2-2.0mm. It does not fit. So the sealed chamber had no usable
    # exit again — which is JP's own catch ("the chamber had no exit at all") reintroduced by a
    # feature added 129 lines away, in the same file, months of reasoning apart.
    #
    # THE TWO LESSONS, because the fix is one line and they are not:
    #   1. A CUT AND THE FEATURE IT PASSES THROUGH MUST SHARE A CONSTANT. `19.0` was correct
    #      against the geometry of the day and became wrong silently, from a distance, without
    #      anything in either place changing. Keyed to PAD_PROUD it cannot drift again.
    #   2. NOTHING COULD HAVE CAUGHT IT. Every check here compares parts to the BOARD, and a
    #      blocked hole intersects nothing — an absence cannot collide, and neither can an
    #      absence that failed to happen. The assert below therefore measures the APERTURE,
    #      not the constants: it intersects the finished solid with the pad's own plane over
    #      the channel's footprint and requires it EMPTY. That is the property. Asserting
    #      `_passY0 <= cy1 - PAD_PROUD` would only restate the line above it.
    #
    # >>> IT MUST BE SEALED AFTER WIRING — a dab of silicone, hot glue or putty. <<<
    # An unsealed hole turns the sealed box into a leaky one and costs exactly the low
    # end the chamber exists to produce. Sizing it for a bead of sealant rather than
    # trying to make it wire-tight is deliberate: a press-fit hole that has to be forced
    # abrades the insulation.
    _passY0 = cy1 - PAD_PROUD - 0.01
    p -= bx(ST_W/2-3, ST_W/2+3, _passY0, 30.0, 6.0, 11.0)
    _probe = bx(ST_W/2-3, ST_W/2+3, cy1 - PAD_PROUD, cy1, 6.0, 11.0)
    _blocked = (p & _probe).volume
    assert _blocked < 0.01, (
        f"{_blocked:.3f}mm3 of material still blocks the speaker-wire pass in the tape pad's "
        f"own plane (y {cy1-PAD_PROUD:.2f}..{cy1:.2f}) — the chamber has no usable wire exit. "
        f"The pass must start at or inside y={cy1-PAD_PROUD:.2f}, not behind the pad")
    # ---- SPEAKER WIRE: A RIM SADDLE AND A GROOVE DOWN THE BACK ----
    #
    # THE SADDLE IS NOT COSMETIC — it removes a hazard that would have been misdiagnosed.
    #
    # The shell's side channel releases the speaker lead at board y=14, which lands at stand
    # z = SLOT_FLOOR + (14 + 2.95)*cos(TILT) = 40.37 — and the rim is at ST_H = 40.00. The wire
    # therefore emerges 0.37mm ABOVE the rim: level with it, for practical purposes. Any
    # variation in how far the slab is pushed down puts the lead BELOW the rim, where the gap
    # between the slab's back face and the slot's rear wall is SLOT_CLR = 0.40mm. A 1.2mm lead
    # in 0.40mm of slot is crushed, and repeated docking can cut through the insulation.
    #
    # ⚠️ It would present as INTERMITTENT AUDIO — which is a firmware-shaped symptom. Someone
    # would go looking at the amp gating, the codec mute, or the media player, because that is
    # where intermittent audio lives in this system, and the actual fault is a pinched wire
    # inside a slot nobody can see into. The cost of the wrong diagnosis is far higher than the
    # cost of this cut, and a 0.37mm margin is not a design — it is a coincidence.
    #
    # So the rim is lowered locally to give the lead a defined crossing, and a shallow groove
    # carries it down the back face to the existing cable route. Neither cut roofs anything, so
    # neither adds a bridge; both are open to the outside and print unsupported.
    WIRE_W   = 5.0     # saddle width
    WIRE_D   = 2.5     # saddle depth below the rim
    GROOVE_W = 3.0
    GROOVE_D = 2.0
    # >>> WIRE_X IS DERIVED FROM THE CORNER, NOT FROM WHERE THE WIRE COMES OUT. <<<
    #
    # It was 57.0, commented "stand x where the shell's side channel exits (board x=50)".
    # That is a true fact about the WIRE and the wrong constraint on the CUT, and the two were
    # conflated: x=57 lies inside the rear R10 corner, whose arc is centred (ST_W-ST_R,
    # ST_D-ST_R) = (54, 54). So the rear face there is NOT at y=64 —
    #
    #     x = 55.50 -> 63.887      x = 59.00 -> 62.660
    #     x = 57.00 -> 63.539      x = 59.50 -> 62.352
    #     x = 58.50 -> 62.930      x = 60.00 -> 62.000
    #
    # — and a groove cut to y = ST_D - 2.0 = 62.0 therefore left only 0.930mm of wall behind
    # its floor instead of 2.0, plus a wedge outboard of its own wall tapering 0.768mm (at
    # y=62.5) to ZERO at y=62.93. Measured in the STL: a 0.671mm feature over z 11.80..37.40,
    # 128 layers, median 0.05mm2 per layer. A 25.6mm-tall knife edge on the part that carries
    # the leaning slab, on a face you can see, and the slicer drops everything under 0.4mm of
    # it — so it prints ragged as well as thin.
    #
    # Nothing measured the wall thickness BEHIND a groove, and nothing would have: the boolean
    # checks compare parts to the BOARD, and a groove cut too deep into a rounded corner
    # collides with nothing at all. Same absence-cannot-collide blindness as the well through
    # the floor.
    #
    # So the groove's OUTBOARD edge is pinned to the corner's tangent point and WIRE_X follows
    # from it. The wire then crosses the rim 4.5mm inboard of where the shell releases it and
    # runs laterally along the top of the rear rim to get there — which is open air above the
    # slot's rear wall, where nothing obstructs it and nothing can pinch it.
    WIRE_X   = ST_W - ST_R - GROOVE_W/2                 # 52.50
    assert WIRE_X + GROOVE_W/2 <= ST_W - ST_R + 1e-9, (
        f"the groove's outboard edge at x={WIRE_X + GROOVE_W/2:.2f} is past the rear face's "
        f"flat region (x <= {ST_W - ST_R:.2f}), so its {GROOVE_D}mm depth is measured against "
        f"the R{ST_R:g} corner arc and leaves a knife edge outboard of it")
    # AND THE SADDLE MUST NOT LEAVE A FIN AGAINST THE SCALLOP — the SCALLOP_MIN_RIB rule, which
    # only ever governed the two scallops against each other, applied to the cut that comes
    # after them. The merged scallop's right edge is at stand x = 50.51 and the saddle is 5mm
    # wide, so inside the 3.49mm of flat face there is no position that both clears the scallop
    # and stays off the corner: the saddle therefore MERGES with the scallop, deliberately.
    #
    # That is the better outcome and not merely the available one. At the old WIRE_X=57 the
    # saddle sat at x 54.5..59.5 and left a 0.85mm-wide, 2.5mm-tall fin standing between it and
    # the slot's side wall at x=60.35 — ON THE REAR RIM, which is the bearing surface under the
    # leaning slab. Merging removes that fin and the rim's bearing line goes 15.13 -> 15.64mm.
    _scallop_x1 = ST_W/2 + (_spans[-1][1] - BW/2)
    _rib_to_scallop = (WIRE_X - WIRE_W/2) - _scallop_x1
    assert _rib_to_scallop <= 0.0 or _rib_to_scallop >= SCALLOP_MIN_RIB, (
        f"the saddle leaves a {_rib_to_scallop:.2f}mm rib between itself and the scallop at "
        f"x={_scallop_x1:.2f} — under {SCALLOP_MIN_RIB}mm that is a fin on the bearing rim, "
        f"not a wall. Either overlap the scallop or clear it by {SCALLOP_MIN_RIB}mm")
    assert WIRE_X + WIRE_W/2 <= ST_W/2 + SLAB_W/2 + SLOT_CLR - SCALLOP_MIN_RIB, (
        f"the saddle's outboard edge at x={WIRE_X + WIRE_W/2:.2f} leaves under "
        f"{SCALLOP_MIN_RIB}mm of rim before the slot's side wall at "
        f"x={ST_W/2 + SLAB_W/2 + SLOT_CLR:.2f} — that is the 0.85mm fin the old WIRE_X=57 left")
    p -= bx(WIRE_X-WIRE_W/2, WIRE_X+WIRE_W/2, 44.0, ST_D+1, ST_H-WIRE_D, ST_H+1)
    p -= bx(WIRE_X-GROOVE_W/2, WIRE_X+GROOVE_W/2, ST_D-GROOVE_D, ST_D+1,
            12.0, ST_H-WIRE_D+0.01)
    p -= bx(ST_W/2-8, WIRE_X+GROOVE_W/2, ST_D-GROOVE_D, ST_D+1, 12.0, 15.0)
    # ---- #35: exterior chamfer, base and rim ----
    # The BASE one is functional as well as cosmetic: it is the bearing face, and elephant's
    # foot on a bearing face is what makes a stand rock. It costs bearing area, and check 2b's
    # ledger is re-derived to account for it rather than having its floor quietly nudged.
    p = chamfer_outline(p, -PLINTH_H, CHAMFER, "stand base")
    p = chamfer_outline(p, ST_H, CHAMFER, "stand rim")
    return p

def stand_base():
    """The plate that closes the sealed speaker chamber. EVERY EDGE DERIVED FROM THE CHAMBER.

    The y extent was the literal 20.7 and that is how it broke — see CHAM_Y1. Reading the
    chamber's own bounds means the plate cannot be left behind by a change to the driver, the
    front gap or the tape pad, all three of which feed CHAM_Y1.
    """
    _b = bx(CHAM_X0 + BASE_CLR, CHAM_X1 - BASE_CLR,
            CHAM_Y0 + BASE_CLR, CHAM_Y1 - BASE_CLR, 0.4, ST_WALL)
    # #35: only the EXPOSED edge. The other five faces mate — four sides into the chamber
    # shaft at BASE_CLR, the top against the chamber floor — and chamfering a mating face
    # changes a fit rather than an appearance.
    return chamfer_outline(_b, 0.4, CHAMFER, "base plate")

def _check_manifold(path):
    """Parse a binary STL and test the mesh itself. Returns (tris, boundary, nonmanifold, dup).

    ⚠️ THIS REPLACES A CHECK THAT COULD NOT FAIL. The repo asserted "all parts watertight, 0
    non-manifold edges" on the strength of importing each STL with build123d and counting
    boundary edges — but `import_stl` returns a single Face with ZERO edges and zero volume, so
    the count was 0 because there was nothing to count. It reported a perfect result about an
    empty object, for as long as anyone had been looking at it. `docs/verification.md` §6 is
    about exactly this and it did not stop me writing another one.

    The real test is arithmetic on the triangles and needs no CAD kernel at all:
      * WATERTIGHT  — every undirected edge is shared by exactly two triangles
      * ORIENTABLE  — every directed edge appears exactly once
    Vertices are quantised to 1e-4mm so exporter float noise cannot split a shared vertex.
    """
    import struct as _st, collections as _co
    with open(path, "rb") as f:
        f.read(80)
        n, = _st.unpack("<I", f.read(4))
        tris = []
        for _ in range(n):
            d = _st.unpack("<12fH", f.read(50))
            tris.append([tuple(round(d[i+j]*1e4) for j in range(3)) for i in (3, 6, 9)])
    und, dir_ = _co.Counter(), _co.Counter()
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            dir_[(u, v)] += 1
            und[tuple(sorted((u, v)))] += 1
    return (n,
            sum(1 for v in und.values() if v == 1),
            sum(1 for v in und.values() if v > 2),
            sum(1 for v in dir_.values() if v > 1))

# Known, measured, and deliberately not asserted away. ember-front-bezel carries 3 edges shared
# by more than two triangles, all at one spot inside the wyrm recess (x 26.149, y 82.11..82.79,
# at the front face and the deboss floor). Everything that could be established says the SOLID
# is fine: `is_valid` is True, it is one solid of 326 faces, the boundary-edge count is 0, and
# the figure is 3 whether the union is built in 2D or 3D, at tessellation tolerances from 0.1
# to 0.001, before or after clean(). It is a mesher artefact at coplanar face seams in a valid
# solid, and every slicer repairs this class silently.
#
# It is recorded as a NUMBER rather than hidden behind a threshold, because the whole reason it
# went unnoticed is that the previous check reported zero without measuring anything. A known
# defect with a stated cause is honest; a green light over an unmeasured one is not.
KNOWN_NONMANIFOLD = {"ember-front-bezel": 3}

# ============================================================================
# 6. build + verify
# ============================================================================
# ============================================================================
# PRINT ORIENTATION IS APPLIED AT EXPORT, NOT IN THE MODEL (issue #25)
# ============================================================================
#
# The parts were exported in raw model coordinates, and for the BEZEL that is an unprintable
# orientation. Measured off the shipped mesh:
#
#     at MIN z:  coplanar area   71.9 mm2   (x 1.30..48.70, y 1.30..84.70)
#     at MAX z:  coplanar area 1847.9 mm2   (the full -2.95..52.95 outline)
#
# 71.9 mm2 is exactly the four annular boss tips — 4 * (pi/4)(5.40^2 - 2.50^2) = 71.96 — so the
# file as shipped stands the part on four ⌀5.40 pillars with the whole 1847.9 mm2 slab 4.70mm in
# the air. ⚠️ THAT IS THE SAME FAILURE THIS FILE ALREADY REJECTED ON THE OTHER FACE: the proud
# button caps would have balanced the shell "on two hexagons totalling ~74mm2". 71.9 against 74 —
# the same defect, the same magnitude, arrived at from the opposite direction, and PRINT-SHEET has
# said "front face DOWN" the whole time. It only ever worked because a human flipped it in the
# slicer.
#
# ⚠️ A RIGID ROTATION IS NOT A GEOMETRY CHANGE, so this is NOT a reprint: JP's printed bezel was
# flipped in the slicer and is dimensionally identical to what this now exports. The STL bytes move;
# the part does not.
#
# ROTATE ABOUT X, NOT Y, AND THE CHOICE IS DELIBERATE. Both are 180deg proper rotations
# (det = +1, so neither mirrors — which matters more in this file than in most). But about X maps
# (x,y,z) -> (x,-y,-z) and PRESERVES THE X COORDINATE, and X is the axis this project has been
# read backwards on repeatedly — the mic at x=40, the switch pair, the microSD edge. About Y would
# send the mic to x=10 in the exported file and hand the next person a fresh handedness puzzle for
# no benefit.
#
# Only the bezel needs it. The other three already export print-face-down: the shell's bed face is
# its back at min z (3678.3 mm2 coplanar), the stand's is its base (3183.8), and the base plate is
# a flat slab that is symmetric in Z.
PRINT_FLIP = {"ember-front-bezel"}
# AND ONE PART IS MODELLED BELOW ITS OWN BED. The stand's plinth grows DOWNWARD from the
# cradle's z origin so that every cradle formula in this file keeps evaluating in the cradle
# frame (see the PLINTH block) — which leaves the modelled part spanning z -16..40. A rigid
# lift at export, like the bezel's rotation, and for the same reason: the print orientation is
# a fact about the STL, not about the model.
#
# ⚠️ THIS IS THE FRAME SEAM. Above it, z=0 is the cradle floor; below it, z=0 is the desk. Any
# height quoted from the exported mesh is PLINTH_H larger than the same height in this file.
PRINT_LIFT = {"ember-stand": PLINTH_H}

def _print_oriented(name, part):
    """The part as it should sit in the exported STL: bed face at min Z, resting on z=0."""
    if name in PRINT_LIFT:
        return Pos(0.0, 0.0, PRINT_LIFT[name]) * part
    if name not in PRINT_FLIP:
        return part
    q  = Rot(180, 0, 0) * part
    bb = q.bounding_box()
    return Pos(0.0, -bb.min.Y, -bb.min.Z) * q


def _find_step():
    """Locate the 17.7MB vendor STEP used by the clearance check.

    It is UNTRACKED ON PURPOSE (too big for the repo), so a git worktree never gets a copy and
    `import_step` raised here. That was survivable only because the STLs had ALREADY been
    written by the time it blew up — an agent in a worktree got usable output and read the
    traceback as cosmetic. Gating export behind the checks flips that same line from a soft
    failure into a hard one: a worktree build would now produce nothing at all. The bug did not
    move; the write moved to the other side of it. So resolve the asset from the MAIN worktree
    as well, which makes the clearance check actually RUN in a worktree instead of merely not
    killing it — the check was never running there, and nobody noticed because the STLs
    appeared anyway.
    """
    rel = os.path.join("ES3C28P_3D", "ES3C28P_3D.step")
    cands = [os.path.join(_HERE, "..", rel), os.path.join(_HERE, rel)]
    # A worktree's .git is a FILE holding "gitdir: /main/.git/worktrees/<name>"; the main
    # checkout is three dirnames up from that.
    for _probe in (os.path.join(_HERE, ".git"), os.path.join(_HERE, "..", ".git")):
        if os.path.isfile(_probe):
            with open(_probe) as fh:
                line = fh.read().strip()
            if line.startswith("gitdir:"):
                gd = line.split(":", 1)[1].strip()
                root = os.path.dirname(os.path.dirname(os.path.dirname(gd)))
                cands += [os.path.join(root, "enclosure", rel), os.path.join(root, rel)]
    for c in cands:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(
        "the ES3C28P STEP is missing from every candidate path, so the clearance check cannot "
        "run and NO STL will be committed. Tried:\n  " + "\n  ".join(cands))


STL_TMP = ".stl.partial"   # exports land here; renamed to .stl only once every check passes


def _discard_partials(out, names):
    for n in names:
        try:
            os.remove(os.path.join(out, n + STL_TMP))
        except FileNotFoundError:
            pass


def _selftest_export_gate():
    """Prove the gate in BOTH directions, on scratch files, on every build.

    ⚠️ A PASSING BUILD CANNOT DEMONSTRATE THIS. A passing build commits, so it cannot tell
    "the checks now gate the export" apart from "the checks still run last and happened to
    pass". The one-off manual control that established this gate was the right instrument and
    it ran once; this is the same experiment wired into every run, for ~1ms.

    BOTH directions, because the failure modes are opposite and both are silent:
      * failing  -> the previous good STLs must be untouched and no debris left behind
      * clean    -> they must actually update. A gate that never commits looks exactly like
                    a healthy repo — same bytes on disk, no error — until someone prints from
                    a month-old file. That is the direction a one-way check cannot see.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        names = ["part-a", "part-b"]
        for n in names:
            with open(os.path.join(d, n + ".stl"), "w") as f:
                f.write("PREVIOUS GOOD SET")
        try:                                              # --- failing path ---
            for n in names:
                with open(os.path.join(d, n + STL_TMP), "w") as f:
                    f.write("NEW BYTES")
            raise AssertionError("simulated check failure")
        except AssertionError:
            _discard_partials(d, names)
        for n in names:
            with open(os.path.join(d, n + ".stl")) as f:
                assert f.read() == "PREVIOUS GOOD SET", (
                    "[self-test] a failed build overwrote the previous good STL — the export "
                    "gate does not hold and a bad part can still reach a printer")
            assert not os.path.exists(os.path.join(d, n + STL_TMP)), (
                "[self-test] a failed build left .partial debris behind")
        for n in names:                                   # --- clean path ---
            with open(os.path.join(d, n + STL_TMP), "w") as f:
                f.write("NEW BYTES")
        for n in names:
            os.replace(os.path.join(d, n + STL_TMP), os.path.join(d, n + ".stl"))
        for n in names:
            with open(os.path.join(d, n + ".stl")) as f:
                assert f.read() == "NEW BYTES", (
                    "[self-test] a clean build did NOT commit — the gate has become a brick "
                    "wall, and a repo that never updates its STLs looks perfectly healthy")
    return True


if __name__ == "__main__":
    assert _selftest_export_gate()
    out = os.path.dirname(os.path.abspath(__file__))
    _committed = False
    parts = {"ember-front-bezel": front_bezel(),
             "ember-back-shell":  back_shell(),
             }
    # ⚠️ THIS USED TO SWALLOW THE FAILURE AND CARRY ON — printing "!! stand failed" and then
    # exporting the two parts that DID build, over the top of a good set, while the stand's
    # previous STL stayed behind pretending to belong with them. Same defect class as the
    # ungated export: a build that did not fully succeed must publish nothing.
    parts["ember-stand"] = desk_stand()
    parts["ember-stand-base"] = stand_base()
    # ⚠️ atexit, NOT try/finally: the run spans two __main__ blocks with module-level
    # definitions between them, so a try in the first cannot reach a finally in the second.
    # atexit fires on normal exit and on an unhandled exception, which is every way an assert
    # here ends. Without this a failed build leaves four .partial files that the next reader
    # has to know to distrust — and "left behind as diagnostics" is how stale artifacts start.
    import atexit
    atexit.register(lambda: None if _committed else (
        _discard_partials(out, parts),
        print("\n!! BUILD DID NOT PASS — nothing committed, no debris. The .stl files on "
              "disk are the previous good set, untouched.")))
    for n,p in parts.items():
        p = _print_oriented(n, p)
        bb = p.bounding_box()
        # A LIFTED PART THAT DID NOT LAND IS THE WHOLE RISK OF MODELLING BELOW z=0: the STL
        # would open in the slicer floating or sunk, and a slicer silently drops it onto the
        # bed, so the mistake never surfaces as an error — only as a part whose Z is off by
        # PLINTH_H everywhere a measurement is taken from the mesh.
        if n in PRINT_LIFT:
            assert abs(bb.min.Z) < 1e-6, (
                f"{n} exports with min Z = {bb.min.Z:.4f}, not 0 — PRINT_LIFT "
                f"({PRINT_LIFT[n]}) does not match how far below z=0 the part is modelled")
        print(f"{n:20s} vol={p.volume/1000:7.2f} cm^3   "
              f"bbox {bb.size.X:6.2f} x {bb.size.Y:6.2f} x {bb.size.Z:6.2f}")
        # WRITE TO A TEMP NAME. The final rename happens only after EVERY check passes —
        # see the commit step at the bottom of this file. Until 2026-07-31 this wrote
        # straight to n+".stl", 660 lines before _check_geometry() ran, so a failing
        # assert left a finished-looking STL on disk AND had already overwritten the
        # previous good one. That is how a part violating its own bearing floor
        # reached a slicer. "The STL is on disk" never meant "the checks passed".
        export_stl(p, os.path.join(out, n+STL_TMP))

    print("\n--- MESH CHECK (the STL itself, not the solid) ---")
    _mesh_bad = []
    for n in parts:
        _t, _b, _nm, _dd = _check_manifold(os.path.join(out, n+STL_TMP))
        _expect = KNOWN_NONMANIFOLD.get(n, 0)
        _ok = (_b == 0 and _nm <= _expect)
        print(f"  {n:20s} {_t:6d} tris   boundary {_b:2d}   non-manifold {_nm:2d}"
              f"{f' (known {_expect})' if _expect else ''}   "
              f"{'watertight' if (_b==0 and _nm==0) else ('as expected' if _ok else 'REGRESSION')}")
        if not _ok:
            _mesh_bad.append(n)
    # A boundary edge is a HOLE and is never acceptable. A non-manifold count above the
    # recorded baseline means something new broke, and is worth failing the build for.
    assert not _mesh_bad, (
        f"mesh regression in {_mesh_bad} — an open edge or more non-manifold edges than the "
        f"documented baseline. Do not raise KNOWN_NONMANIFOLD to make this pass.")

    print("\n--- BOOLEAN CLEARANCE CHECK vs vendor STEP ---")
    # Also anchored to this file, not to cwd: with `out` derived from the working directory,
    # `../ES3C28P_3D/` resolved outside the repo and the clearance check silently skipped.
    _step = _find_step()
    raw = import_step(_step)
    # !! The STEP lives in its own frame (X -52.75..-2.75, Y 6..92).  Move it into
    # !! board coords (X 0..50, Y 0..86) or every boolean silently returns empty.
    board = Pos(52.750, -6.000, 0.0) * raw
    bb = board.bounding_box()
    # Y min is -0.368: the USB-C shell overhangs the board edge (measured, expected).
    assert abs(bb.min.X) < 0.02 and abs(bb.max.X-50) < 0.02 \
       and abs(bb.max.Y-86) < 0.02 and abs(bb.max.Z-4.30) < 0.02, f"bad align {bb}"
    print(f"  board re-aligned: X {bb.min.X:.2f}..{bb.max.X:.2f}  "
          f"Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}")
    bsolids = board.solids()

    def interference(part):
        pbb = part.bounding_box(); tot = 0.0; hits = []
        for i, sd in enumerate(bsolids):
            b = sd.bounding_box()
            if (b.min.X > pbb.max.X or b.max.X < pbb.min.X or
                b.min.Y > pbb.max.Y or b.max.Y < pbb.min.Y or
                b.min.Z > pbb.max.Z or b.max.Z < pbb.min.Z):
                continue
            try: v = (part & sd).volume
            except Exception: v = 0.0
            if v > 0.01:
                tot += v; hits.append((i, v, sd.bounding_box()))
        return tot, hits

    for n in ("ember-front-bezel","ember-back-shell"):
        v, hits = interference(parts[n])
        print(f"  {n:20s} interference = {v:9.3f} mm^3   "
              f"{'CLEAR' if v < 0.5 else '*** COLLISION ***'}")
        for i, hv, hb in sorted(hits, key=lambda h:-h[1])[:6]:
            print(f"      solid #{i:4d} {hv:8.3f} mm^3  at x {hb.min.X:6.2f}..{hb.max.X:6.2f}"
                  f"  y {hb.min.Y:6.2f}..{hb.max.Y:6.2f}  z {hb.min.Z:6.2f}..{hb.max.Z:6.2f}")
    sv, _ = interference(Pos(0,0,-2.0) * parts["ember-front-bezel"])
    print(f"  [self-test] bezel sunk 2mm -> {sv:9.3f} mm^3 "
          f"({'detector WORKS' if sv > 1.0 else '!!! DETECTOR BLIND !!!'})")

    # THE TOP-ENTRY CONNECTOR MUST BE THE ONE THE SILKSCREEN CALLS SPEAKER.  #33 x #27.
    #
    # ⚠️ THIS IS THE ONLY CHECK IN THE FILE THAT TESTS THE PORT MAPPING AGAINST SOMETHING
    # PHYSICAL. #27's mapping rests on a vendor drawing; JP's #33 report rests on holding the
    # board. They agree today — the connector that is 1.30mm taller than the other four, and
    # the only one that reaches the board's own minimum Z, is exactly the one the drawing's
    # dimension chain names SPEAKER. Two witnesses of different kinds, so this asserts they
    # keep agreeing rather than letting either drift alone. It also guards the relief: cut
    # over the wrong connector, it is a hole in the case above nothing.
    _depth = []
    for _yy in CONN_R:
        _z = min((sd.bounding_box().min.Z for sd in bsolids
                  if sd.bounding_box().max.X > BW - 8
                  and sd.bounding_box().min.Y > _yy[0] - 0.5
                  and sd.bounding_box().max.Y < _yy[1] + 0.5
                  and sd.bounding_box().min.Z < -1.0), default=0.0)
        _depth.append(_z)
    print(f"  [#33] CONN_R depths {[round(z,2) for z in _depth]}  "
          f"deepest = index {_depth.index(min(_depth))}, SPK_CONN_I = {SPK_CONN_I}")
    assert _depth.index(min(_depth)) == SPK_CONN_I, (
        f"the deepest CONN_R connector is index {_depth.index(min(_depth))} but SPK_CONN_I is "
        f"{SPK_CONN_I}. The top-entry connector JP identified by hand and the one the vendor "
        f"silkscreen names SPEAKER are no longer the same solid — do not move SPK_CONN_I to "
        f"make this pass, the two witnesses disagreeing is the finding")
    assert min(_depth) < sorted(_depth)[1] - 1.0, (
        f"[self-test] the CONN_R depths are {[round(z,2) for z in _depth]} — the top-entry "
        f"connector is no longer distinguishable from the side-entry ones by depth, so the "
        f"check above cannot identify anything and is not evidence")


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY ASSERTS. These are cheap and they encode the two faults JP found by
# looking at a render — the kind a boolean clearance check cannot catch, because
# nothing intersects: the stand was simply in front of the screen.
# ─────────────────────────────────────────────────────────────────────────────
def _plan_quadrants():
    """(total, [four quadrant areas]) of the stand's PLAN profile — the ideal to compare to."""
    plan = rbox(0, ST_W, 0, ST_D, 0.0, 1.0, ST_R)
    q = [(plan & bx(x0, x1, y0, y1, -1.0, 2.0)).volume
         for (x0, x1) in ((0.0, ST_W/2), (ST_W/2, ST_W))
         for (y0, y1) in ((0.0, ST_D/2), (ST_D/2, ST_D))]
    return plan.volume, q


def _bearing_footprint(st=None):
    """What the stand RESTS ON: area in its bottom 0.4mm, and how that area is SPREAD.

    ⚠️ RE-DERIVED FOR THE PLINTH, NOT LOWERED TO FIT IT. Two things changed at once and only
    one of them is the number. The plane moved — the bearing face is now z = -PLINTH_H, and
    probing z 0..0.4 as this used to would measure a plane in the MIDDLE of the part and
    report a healthy figure for a stand with no underside at all. And the metric moved: a
    single area threshold was the right instrument when the only question was "has the well
    punched through the floor", and it is the wrong one now that the underside legitimately
    carries two large openings. 2911mm2 in a 4mm floor was a stand "standing on a ring";
    2922mm2 under a 16mm solid plinth, arranged as a full perimeter plus two full-depth
    strips, is not the same object and an area comparison cannot tell them apart.

    So this returns the distribution as well, and check 2b asserts on all of it:
      total       — against a ledger of the openings that are supposed to be there
      quadrants   — the ring test. A ring passes on area and fails here.
      rear        — contact behind the loaded CoM, which is what tipping actually needs
    """
    st = desk_stand() if st is None else st
    z0 = -PLINTH_H
    foot = st & bx(-1.0, ST_W + 1, -1.0, ST_D + 1, z0, z0 + 0.4)
    def area(sel):
        return (foot & sel).volume / 0.4
    quads = [area(bx(x0, x1, y0, y1, z0 - 1, z0 + 1))
             for (x0, x1) in ((0.0, ST_W/2), (ST_W/2, ST_W))
             for (y0, y1) in ((0.0, ST_D/2), (ST_D/2, ST_D))]
    rear = area(bx(-1.0, ST_W + 1, SLAB_COM_Y, ST_D + 1, z0 - 1, z0 + 1))
    return foot.volume / 0.4, quads, rear, foot.bounding_box().max.Y



def _check_geometry(parts=None):
    """`parts` is __main__'s dict of ALREADY-BUILT, MODEL-FRAME solids — reuse, don't rebuild.

    Two of the checks below need the bezel and the back shell, and the shell is the most
    expensive solid in the file (the hex field). It was being built here a second time while
    __main__ held one; the same "it is only made once" claim that turned out to be false for
    desk_stand() at check 2b. Optional so a standalone `_check_geometry()` still works.
    """
    import math
    _bezel = parts["ember-front-bezel"] if parts else front_bezel()
    _shell = parts["ember-back-shell"]  if parts else back_shell()
    # ------------------------------------------------------------------
    # 0. HANDEDNESS AND THE OPENING/COMPONENT LEDGER.
    #
    # These exist because of the 2026-07-30 reprint. The faults were: an opening cut over a
    # component that was not the one it was named for, and a switch pair assigned by re-reading
    # a comment. Neither is a clearance, so nothing in sections 1..n below could see either.
    # ------------------------------------------------------------------
    # 0a. the anchored bit. See the MIC_ON_HIGH_X block for why this cannot be derived.
    assert (MIC[0] > BW/2) == MIC_ON_HIGH_X, (
        f"MIC x={MIC[0]} is on the {'high' if MIC[0] > BW/2 else 'low'}-x half but "
        f"MIC_ON_HIGH_X={MIC_ON_HIGH_X}. This is the ONLY absolute x fact in the file and it is "
        f"set from a physical measurement. If the board really is mirrored, mirror ALL of "
        f"section 1 — do not flip this line to make the build pass")
    # 0b. A COUNT CANNOT BE MIRRORED. This is the only handedness-invariant instrument anyone
    #     produced for this board: three connectors on one long edge, two on the other.
    #     ⚠️ It did NOT catch the fault it was written during — a handedness-free measurement of
    #     the WRONG FEATURE is still wrong, and what was misidentified was the socket, not the
    #     edges. Kept because the invariant is real, with its limit recorded so nobody mistakes
    #     it for a mirror detector.
    assert len(CONN_R) == 3 and len(CONN_L) == 2, (
        f"the long edges carry {len(CONN_R)}/{len(CONN_L)} connectors, not 3/2 — either the "
        f"board data changed or the two tables have been swapped")
    assert (CONN_R_EDGE_X > BW/2) == (MIC[0] > BW/2), (
        "the three-connector edge and the mic must be the same long edge")
    # 0c. PARTIAL-MIRROR CATCHERS. Each is relative, so none detects a whole-board reflection
    #     (see 0a) — but a whole-board reflection is not what went wrong. ONE FEATURE MOVING
    #     WITHOUT THE OTHERS is, and that is exactly what these see.
    assert (BTN_BOOT_X < BW/2) == (_SD_CX < BW/2), (
        f"BOOT is at x={BTN_BOOT_X} and the microSD socket centres on x={_SD_CX:.2f}. JP's bench "
        f"test is 'volume button is on sd card side', so they MUST share a long edge. The big "
        f"thumb cap on hardware RESET is a device that reboots when you reach for the volume")
    assert (BTN_RESET_X > BW/2) == (MIC[0] > BW/2), (
        "RESET must share its long edge with the mic (the edge the socket is NOT on)")
    assert BTN_BOOT_X != BTN_RESET_X and {BTN_BOOT_X, BTN_RESET_X} == {x for x, _ in BTN}, (
        "the two switch x's must be exactly the two entries in BTN, once each")
    # 0d. THE OPENING/COMPONENT LEDGER — the assert the old code could not have had.
    #     Every side-wall span must have a component behind it. An opening over empty board is
    #     invisible to a clearance check: nothing collides, so it reads as agreement.
    _hi, _lo = side_channels()
    for _edge, _spans, _conns in (("x=%g" % BW, _hi, list(CONN_R)), ("x=0", _lo, list(CONN_L))):
        # Anything that may LEGITIMATELY sit behind an opening on this edge.
        _behind_ok = list(_conns)
        if (_SD_CX < BW/2) == (_edge == "x=0"):
            _behind_ok.append((SD_SOCKET[2], SD_SOCKET[3]))
        for (_a, _b) in _spans:
            assert any(not (k[1] < _a or k[0] > _b) for k in _behind_ok), (
                f"{_edge} edge has an opening at Y {_a:.2f}..{_b:.2f} with NO component behind "
                f"it. This is the phantom-opening failure: the old Y 14.0..40.5 channel had "
                f"18.54mm of nothing behind it and every check passed")
        # ⚠️ The two directions are NOT symmetric, and conflating them is a bug. A CONNECTOR has
        # a plug that must pass THROUGH the wall, so it must be WHOLLY exposed. The SOCKET must
        # not be: only a card aperture passes, and opening the full 14.66mm body would undercut
        # the socket's own side walls. 0f checks the socket's aperture separately, against the
        # card rather than against the body.
        for _k in _conns:
            assert any(_a <= _k[0] and _k[1] <= _b for (_a, _b) in _spans), (
                f"{_edge} edge connector at Y {_k[0]:.2f}..{_k[1]:.2f} is not wholly inside any "
                f"opening — it is walled in, which is how the microSD shipped")
    # 0e. the phantom's victim must stay covered. LCD_FLEX is the 0.5mm placeholder the old
    #     SD_PLATE name was attached to; the X=BW openings are the only ones that can reach it.
    for (_a, _b) in _hi:
        assert _b <= LCD_FLEX[2] or _a >= LCD_FLEX[3], (
            f"x={BW:g} opening Y {_a:.2f}..{_b:.2f} overlaps LCD_FLEX Y {LCD_FLEX[2]}.."
            f"{LCD_FLEX[3]} — that is the exact opening JP reported as 'an extra opening we "
            f"don't need where the digitizer circuit is'")
    # 0f. the slit has to pass a card, not just clear the socket body.
    _slit = [s for s in (_lo if _SD_CX < BW/2 else _hi)
             if s[0] <= (SD_SOCKET[2]+SD_SOCKET[3])/2 <= s[1]]
    assert len(_slit) == 1, "the microSD slit did not resolve to exactly one opening"
    _sw = _slit[0][1] - _slit[0][0]
    assert _sw >= SD_CARD_W + 2*0.60, (
        f"microSD slit is {_sw:.2f}mm along Y — a {SD_CARD_W}mm card plus a finger needs "
        f">={SD_CARD_W + 1.2:.2f}. JP asked for 'a finger friendly slit'")
    # 0j. EVERY FLOOR THAT MATTERS LANDS ON A LAYER BOUNDARY OF ITS OWN PART'S HEIGHT (#26).
    #
    #     ⚠️ THE LIST IS ENUMERATED, NOT BLANKET, AND THAT IS THE WHOLE DESIGN OF THIS CHECK.
    #     "Every Z dimension must be a whole number of layers" is over-strict, and over-strict is
    #     not safe — it is just wrong in the other direction, and it gets switched off. A part's
    #     overall HEIGHT landing mid-layer only makes the topmost layer thin, which no slicer minds
    #     and nothing bears on. What matters is a floor something SITS on, LOOKS at, or is MADE OF.
    #
    #     And an enumeration is exactly the countermeasure this failure needed: the defect was
    #     never that a check was wrong, it was that Z depths were never on any list. Three of the
    #     six below were mid-layer at EVERY layer height in use and no check had an opinion.
    _floors = [
        ("CBORE_DEPTH",  CBORE_DEPTH,  LAYER_H_SHELL, "the screw head bears on this floor"),
        ("LABEL_DEBOSS", LABEL_DEBOSS, LAYER_H_SHELL, "visible recess floor, back face"),
        ("DEBOSS_BIG",   DEBOSS_BIG,   LAYER_H_SHELL, "visible AND tactile cap recess floor"),
        ("DEBOSS_SMALL", DEBOSS_SMALL, LAYER_H_SHELL, "visible AND tactile cap recess floor"),
        ("HINGE_T",      HINGE_T,      LAYER_H_SHELL, "material LEFT; it sets flexure strain"),
        ("BEZEL_DEBOSS", BEZEL_DEBOSS, LAYER_H_BEZEL, "visible recess floor, front face"),
    ]
    #     DELIBERATELY EXCLUDED, stated so the omissions are decisions rather than oversights:
    #       WALL    2.60 - cavity ceiling, seen only from inside, nothing bears on it (13L @0.20)
    #       BEZEL_T 3.00 - the slab/boss shoulder, 18.75L at 0.16. Neither bearing nor visible.
    _lerr = lambda _d, _lh: abs(_d/_lh - round(_d/_lh))
    for _nm, _d, _lh, _why in _floors:
        assert _lerr(_d, _lh) < 1e-9, (
            f"{_nm} = {_d:.4f} is {_d/_lh:.3f} layers at its part's {_lh} — a floor cannot land "
            f"mid-layer, and this one matters because {_why}. Make it a whole multiple of its OWN "
            f"part's layer height; do not borrow the other part's, which is what #26 was")
    #     CONTROL — the checker must be shown to fire, and these are not invented perturbations:
    #     they are the exact values that shipped, against the shell's real layer height.
    assert _lerr(0.90, 0.20) > 1e-9, "control failed: 0.90 (old DEBOSS_BIG/HINGE_T) reads aligned"
    assert _lerr(0.48, 0.20) > 1e-9, "control failed: 0.48 (old LABEL_DEBOSS) reads aligned"
    assert _lerr(3.04, 0.20) > 1e-9, "control failed: 3.04 (old CBORE_DEPTH) reads aligned"
    # 0g. the islands must clear BOTH obstructions near each screw hole. _island_cx() solves for
    #     this, so this asserts the SOLVE rather than restating it — a second hand-typed number
    #     here would be the very thing that block was rewritten to remove.
    for _cx in (BTN_BOOT_X, BTN_RESET_X):
        _cyh, _R, _ = cap_geometry(_cx)
        _icx   = cap_center_x(_cx)
        _reach = _R + SLOT_W
        _narrow = max(0.0, _reach - abs(HOLES[0][1] - _cyh)/math.sqrt(3))
        for _hx in (HOLES[0][0], HOLES[1][0]):
            _d = abs(_icx - _hx)
            for _nm, _w, _r, _need in (("counterbore bore", _reach, CBORE_D/2,      ISLAND_SLOT_CLR),
                                       ("boss flare",       _narrow, BOSS_FLARE_D/2, FLARE_SLOT_CLR)):
                _clr = _d - _w - _r
                assert _clr >= _need - 1e-9, (
                    f"button island at x={_icx} (switch {_cx}) leaves only {_clr:.3f}mm between "
                    f"its slot and the {_nm} at x={_hx} — need {_need}")
    # 0h. THE HEAD MUST HAVE A CONTINUOUS ANNULAR SEAT AT THE COUNTERBORE FLOOR.
    #     ⚠️ Asserting the diameters and the depth separately does NOT cover this: each of
    #     d5.40 boss / d5.80 bore / 3.04 deep is individually sensible, and together they leave
    #     the head bearing on nothing. The property is the ANNULUS, so the annulus is the assert.
    def _seat_annulus(depth):
        """Annular bearing width under the head for a counterbore of this depth. Negative means
        the bore is wider than the material there, i.e. there is no seat at all."""
        _z = BACK_Z + depth
        if _z <= CAV_FLOOR:                       # still in the solid back slab
            return (BOSS_FLARE_D - CBORE_D)/2      # slab is full width; report the flare's
        _f = (_z - CAV_FLOOR) / (PCB_BOT - CAV_FLOOR)
        return ((BOSS_FLARE_D + _f*(BOSS_D - BOSS_FLARE_D)) - CBORE_D)/2
    _ann = _seat_annulus(CBORE_DEPTH)
    assert _ann >= BOSS_MIN_ANN, (
        f"a {CBORE_DEPTH:.2f}mm counterbore floors at z {BACK_Z+CBORE_DEPTH:.2f} where the boss "
        f"leaves only {_ann:.3f}mm of annulus under a d{SCREW_HEAD_D} head — need {BOSS_MIN_ANN}. "
        f"CAV_FLOOR is {CAV_FLOOR}, so a pocket past it is cutting the boss, not the wall")
    # CONTROL — the detector must be shown to FIRE. A check that has never produced a failure is
    # not evidence (verification.md 13). Two positives, and note what the second one shows:
    _unflared = (BOSS_D - CBORE_D)/2
    assert _unflared < BOSS_MIN_ANN, "annulus control did not fail on the un-flared d5.40 boss"
    assert _seat_annulus(CBORE_DEPTH + 1.00) < BOSS_MIN_ANN, (
        "annulus control did not fail with the head pushed 1.00mm deeper")
    # ⚠️ +0.50mm deeper does NOT fail, and that is reported rather than tuned away: the flare's
    # taper is gentle (3.00mm of diameter over 5.50mm of depth), so it absorbs half a millimetre
    # and the threshold is +0.66. Stating the real sensitivity beats picking a perturbation that
    # happens to trip. The un-flared control above is the sharp one — it reproduces the exact
    # shipped defect and comes out NEGATIVE, i.e. bore wider than boss, no seat whatsoever.
    # 0i. thread engagement. Socket-cap length is measured UNDER the head, so sinking the head
    #     flush COSTS NOTHING and in fact buys engagement back.
    _eng = min(SCREW_LEN - (-BACK_Z - CBORE_DEPTH), SEAM_Z + 1.5)
    assert _eng >= 3.0, (
        f"only {_eng:.2f}mm of thread engagement ({_eng/3.0:.2f}xD) for an M3 — under 1 diameter "
        f"is a stripped boss. Screw {SCREW_LEN}mm, non-engaging stack "
        f"{-BACK_Z - CBORE_DEPTH:.2f}mm")
    assert _eng <= SEAM_Z + 1.5, "the screw bottoms out on the end of the pilot before it clamps"
    # 1. the stand must not occlude any of the visible area
    engagement = (ST_H - SLOT_FLOOR) / math.cos(math.radians(TILT))
    va_start = VA[2] - OY0
    assert engagement <= va_start, (
        f"stand occludes {engagement - va_start:.1f}mm of the visible area "
        f"(engagement {engagement:.1f}mm along the slab, VA starts at {va_start:.1f}mm)")
    # 2a. the USB-C well must not breach the sealed speaker chamber
    reach = (SLOT_FLOOR - ST_WALL) / math.cos(math.radians(TILT))
    front_at_depth = SLOT_CY - math.sin(math.radians(TILT))*reach - 12.0/2
    assert front_at_depth > 22.0, (
        f"USB-C well reaches y={front_at_depth:.1f} at full depth and would breach the "
        f"speaker chamber at y=22.0")
    # 2. room under the slab for a USB-C plug
    below = SLOT_FLOOR - ST_WALL
    assert below >= 16.0, f"only {below:.1f}mm under the slab for a USB-C plug (need >=16)"
    # 2e. THE 40mm RIGID CABLE RUN MUST FIT ABOVE THE DESK.  #29 / #30.
    #
    # The measurement JP made — 40mm from the plug tip to where the cable can first bend — is
    # a length of STRAIGHT CORRIDOR, and the corridor's direction is fixed by the port, not
    # chosen. So this is one inequality and there is nothing to trade against it except height.
    #
    # ⚠️ port_z IS DERIVED FROM USB_Z, NOT TYPED, BECAUSE THE SIGN OF THE OFFSET WAS THE WHOLE
    # DISPUTE. Two derivations of the required height differed by exactly 2*pc*sin(TILT) =
    # 1.152mm on whether the port axis sits in front of or behind the slab's mid-plane. Written
    # this way the file answers it from its own data: USB_Z about the slab mid-plane, mapped by
    # the same local_y convention check 3b's cap probe uses.
    _pc = -((USB_Z[0] + USB_Z[1])/2 - (FRONT_Z + BACK_Z)/2)     # +2.2250 => BEHIND the mid-plane
    _zface = -0.368 - OY0    # connector face up the slab. -0.368 is the USB-C shell's overhang
                             # past the PCB edge, measured, and asserted against the vendor
                             # STEP's own bounding box in __main__ — not a number typed twice.
    _port_z = SLOT_FLOOR - _pc*math.sin(math.radians(TILT)) + _zface*math.cos(math.radians(TILT))
    # ⚠️ THE CENTRELINE CLEARS THE DESK, NOT THE TIP. A tail whose lowest surface just grazes
    # the desk plane is a tail whose axis is CABLE_OD/2 below it — i.e. the last few millimetres
    # of the rigid run are already being deflected by the desk, which is the exact load path
    # that levers the device out of the slot (#30). Requiring the AXIS to clear is what makes
    # this a clearance rather than a coincidence, and it is also the term that reconciles the
    # 53.82 / 54.97 figures — see the block at STAND_TOTAL_H.
    _tip_z = _port_z + PLINTH_H - CABLE_RIGID*math.cos(math.radians(TILT))   # above the desk
    assert _tip_z >= CABLE_OD/2, (
        f"the {CABLE_RIGID}mm rigid run ends {_tip_z:.3f}mm above the desk and a "
        f"d{CABLE_OD} cable needs {CABLE_OD/2:.3f} for its axis to clear. The port sits at "
        f"z={_port_z:.3f} in the cradle frame, {_port_z + PLINTH_H:.3f} above the desk. "
        f"This is what PLINTH_H is for")
    # The floor this puts on the height, stated as a height because that is the knob:
    _req = ST_H + CABLE_RIGID*math.cos(math.radians(TILT)) + CABLE_OD/2 - _port_z   # 54.969
    assert STAND_TOTAL_H >= _req, (
        f"STAND_TOTAL_H={STAND_TOTAL_H} is under the derived floor {_req:.3f}")
    # AND THE CONTROL, because the sign of _pc is the thing this file has been read backwards
    # on. The OTHER sign must produce the OTHER quoted figure — if it does not, the mapping has
    # drifted and the agreement with 53.82/54.97 that settled this was luck.
    _req_other = (ST_H + CABLE_RIGID*math.cos(math.radians(TILT)) + CABLE_OD/2
                  - (SLOT_FLOOR + _pc*math.sin(math.radians(TILT))
                     + _zface*math.cos(math.radians(TILT))))
    assert abs(_req - 54.97) < 0.005 and abs(_req_other - 53.82) < 0.005, (
        f"the two branches derive {_req:.3f} / {_req_other:.3f}, not 54.97 / 53.82. Those two "
        f"figures were reproduced EXACTLY from these constants and that is the evidence the "
        f"sign of pc is settled. If this fires, the reconciliation is broken and the height "
        f"is resting on an argument again — re-read the block at STAND_TOTAL_H before touching "
        f"anything")
    # 2c. THE PIP MUST STAY INSIDE ITS ISLAND — 0.423mm, the tightest margin on the part.
    #
    # The pip is centred on the SWITCH and the island on CAP_CX_*, so they are deliberately
    # off-centre from each other: the BOOT island is offset 3.53mm in X to clear the (46,4)
    # countersink. A flat-top hexagon narrows toward each flat, so an off-centre disc runs out
    # of hexagon long before it runs out of circumradius, and NOTHING ELSE HERE WOULD NOTICE:
    # a pip hanging over the island's edge does not collide with the board, and the minimum-wall
    # metric measures the material that IS there, never the material a feature needed and
    # missed.
    #
    # Exact, not sampled: a flat-top hexagon's six flats sit at R*sqrt(3)/2 from the centre with
    # outward normals every 60deg starting at 30deg, so the clearance is
    #     R*sqrt(3)/2  -  max over flats of (pip offset . flat normal)  -  PIP_D/2
    # BOOT 0.423mm, RESET 0.960mm. The 0.423 agrees to three decimals with the independent
    # [32.56, 33.54] feasible window that chose CAP_CX_BOOT = 33.05 (0.866 * 0.49 = 0.424),
    # which is two derivations meeting rather than one being trusted.
    #
    # 0.40 is one extrusion width at the 0.4mm nozzle. This assert is deliberately tight: BOOT
    # passes with 0.023mm to spare, so it fails the moment a cap, an island or the pip moves.
    # That is the point — PIP_D was 4.00 until recently, and at 4.00 this is NEGATIVE.
    for _cx, _cy in BTN:
        _cyh, _R, _ = cap_geometry(_cx)
        _dx, _dy = _cx - cap_center_x(_cx), _cy - _cyh
        _worst = max(_dx*math.cos(math.radians(_a)) + _dy*math.sin(math.radians(_a))
                     for _a in range(30, 360, 60))
        _clr = _R*math.sqrt(3)/2 - _worst - PIP_D/2
        assert _clr >= 0.40, (
            f"the pip at board x={_cx} clears its island's nearest flat by only {_clr:.3f}mm "
            f"(island centre {cap_center_x(_cx)}, R={_R:.4f}, PIP_D={PIP_D}) — under one "
            f"0.40mm extrusion width the pip overhangs the island into the printed-in-place "
            f"slot and has nothing to stand on")
    # ONE stand solid for every check below that needs it — it is the expensive build in this
    # file. ⚠️ THE COMMENT SAYING SO USED TO SIT AT 2d WHILE 2b CALLED `_bearing_footprint()`,
    # WHICH BUILT ITS OWN. Three desk_stand() builds per run, two of them identical, under a
    # line claiming there were not. Hoisted here so the claim is true.
    _stand = desk_stand()

    # 2b. THE STAND MUST NOT STAND ON A RING — RE-DERIVED FOR THE PLINTH.
    #
    # The original: the USB-C well once ran 30mm down the tilted axis, reaching z = -4.98 and
    # cutting through the 4mm floor — a 273mm2 hole, bearing 2911 of 4010mm2, "the stand was
    # standing on a ring". Nothing caught it, because the boolean check compares each part to
    # the BOARD and an absence cannot collide. That fault is still real and still needs a check.
    #
    # ⚠️ BUT THE OLD CHECK WOULD HAVE PASSED ON A STAND WITH NO UNDERSIDE. It probed z 0..0.4,
    # which under a plinth is a plane in the MIDDLE of the part; it would have measured the
    # cradle's floor, scored ~2900, and said nothing about what the thing rests on. A threshold
    # that survives a frame change by measuring the wrong plane is the §6 failure again — a
    # green light over an unmeasured quantity.
    #
    # AND ONE NUMBER CANNOT SETTLE IT ANY MORE. 2911mm2 was damning in a 4mm floor and 2922 is
    # fine under a 16mm plinth, because the same area is arranged differently: a full perimeter
    # plus two full-depth strips instead of a rim around a hole. So the check is now a ledger
    # plus two shape tests, and the shape tests are what would actually catch a ring.
    #
    #   plan profile (64 x 64, R10)                                        4010.2
    #   - speaker chamber access shaft, 54.0 x 15.3, driver + base plate    -826.2
    #   - egress channel, 14.0 wide, y 0..34 (it is CUT from y=-1, but the
    #     part starts at 0), less its overlap with the shaft (14.0 x 15.3)   -261.8
    #   - 0.80 perimeter chamfer (#35), MEASURED not computed                -137.8
    #   - USB-C well                                                           -0.0
    #   - rear cord tuck (#46), TUCK_W 7.00 x y 35..64 = 29.00                -203.0
    #   - 0.80 chamfer along the tuck's TWO NEW bottom edges, MEASURED         -29.4
    #                                                                     ---------
    #   expected                                                            2552.0
    #
    # ⚠️ THE TUCK COSTS MORE THAN ITS OWN AREA, and the first draft of this line missed it.
    # 7.00 x 29.00 = 203.0 predicts 2581.4; the build measured 2552. The 29.4 difference is
    # the #35 chamfer running along the two long bottom edges the groove just created — the
    # SAME effect the chamfer term above is measured rather than computed for. Cutting a
    # channel into a chamfered face does not remove w*L, it removes w*L plus the chamfer that
    # now follows two new edges. Measured, not modelled, for the same reason as the term above.
    #
    # THE WELL LINE IS ZERO ON PURPOSE, and it is listed rather than omitted because a missing
    # line and a zero line read identically in a total but not to a reader. The well used to
    # take 273mm2 of this plan (measured in the 2026-07-30 battery study,
    # scratch/hosyond-s3/battery.md; re-measured at 273.3mm2 building the old 30.0 box against
    # the z~0 plane). Deriving its depth closed it: the lowest corner now sits at z = +2.447,
    # so it cuts 0.0mm2 of the underside and the ledger has nothing to deduct.
    #
    # ⚠️ DO NOT ADD 273 BACK AS A LINE ITEM. The ledger balances at 2784.4 against a measured
    # 2784, i.e. to 0.4mm2; a 273 deduction for an opening that no longer exists would put the
    # expectation at 2511 and the assert 273mm2 below the truth — a floor low enough to sleep
    # through the exact regression it guards. If the well is ever deepened again this line
    # stops being zero, which is the reason it is written down.
    #
    # ⚠️ THE CHAMFER TERM IS MEASURED BECAUSE THE OBVIOUS ARITHMETIC OVERSTATES IT BY 37%.
    # Perimeter x CHAMFER predicts 189.1mm2; the real cost is 137.8, because part of that
    # perimeter is already the egress mouth and has no material left to lose. Computing it
    # would have set the floor 51mm2 too low and hidden a real regression of that size.
    _plan, _pq = _plan_quadrants()
    _foot, _quads, _rear, _ymax = _bearing_footprint(_stand)
    print(f"  [bearing] {_foot:.0f}mm2 of {_plan:.0f}  quadrants "
          f"{'/'.join(f'{q/p*100:.0f}%' for q, p in zip(_quads, _pq))}  "
          f"behind CoM {_rear:.0f}mm2 to y={_ymax:.1f}")
    assert _foot >= 2507.6, (
        f"stand bearing footprint {_foot:.0f}mm2 of a {_plan:.0f}mm2 plan — the ledger above "
        f"accounts for 2552, so something is piercing the plinth beyond the chamber shaft, "
        f"the egress channel, the #46 rear tuck and the #35 chamfer")
    # THE RING TEST. Area alone cannot see a ring; a quadrant that has lost most of its plan
    # can only be a rim, a strip or a hole. 47% is the worst quadrant here (the two front ones,
    # which carry the chamber shaft); the control below shows what a real ring scores.
    _QUAD_MIN = 0.30
    for _i, (_q, _p) in enumerate(zip(_quads, _pq)):
        assert _q >= _QUAD_MIN*_p, (
            f"bearing quadrant {_i} carries {_q:.0f}mm2 of its {_p:.0f}mm2 plan "
            f"({_q/_p*100:.0f}%, floor {_QUAD_MIN*100:.0f}%) — that corner of the stand is "
            f"resting on a rim or a strip, not on a face")
    # CONTROL — the detector must be shown to fire (verification.md 13). A 4mm perimeter ring
    # of the same outline: 4010 -> ~960mm2, and 25% per quadrant. It fails the shape test while
    # scoring a QUARTER of the plan, which is exactly the discrimination the area test lacked.
    _ring = (rbox(0, ST_W, 0, ST_D, 0.0, 0.4, ST_R)
             - rbox(4.0, ST_W-4, 4.0, ST_D-4, -1.0, 2.0, ST_R-4))
    _rq = [(_ring & bx(x0, x1, y0, y1, -1.0, 2.0)).volume / 0.4
           for (x0, x1) in ((0.0, ST_W/2), (ST_W/2, ST_W))
           for (y0, y1) in ((0.0, ST_D/2), (ST_D/2, ST_D))]
    assert min(q/p for q, p in zip(_rq, _pq)) < _QUAD_MIN, (
        f"[self-test] a 4mm perimeter ring scores {min(q/p for q, p in zip(_rq, _pq))*100:.0f}% "
        f"per quadrant, at or above the {_QUAD_MIN*100:.0f}% floor — the ring test cannot "
        f"detect a ring and is decoration")
    # AND THE TIPPING CONDITION, which is the thing the area was ever a proxy for. The loaded
    # slab's CoM projects to y=45.89; the stand tips about whatever contact lies behind that.
    assert _ymax >= SLAB_COM_Y + 10.0 and _rear >= 500.0, (
        f"bearing material reaches only y={_ymax:.1f} with {_rear:.0f}mm2 behind the slab's "
        f"CoM at y={SLAB_COM_Y:.2f} — the dock tips backwards when the screen is tapped")

    # 2d. THE BASE PLATE MUST ACTUALLY SEAT — the first check in this file between TWO PARTS.
    #
    # Every other clearance check here compares a part to the BOARD, so a part that is too big
    # to fit its own mating part intersects nothing anybody was measuring. The base plate was
    # 1.40mm too deep (269.136mm3 into the stand's floor) because it carried a private copy of
    # the chamber's rear wall, 21.00, from before that wall was derived to 19.30. The sealed
    # chamber could not be closed and no check said so.
    #
    # WITH ITS OWN SELF-TEST, because "0.000" is exactly the answer a check that cannot fail
    # gives: pushing the plate 0.5mm deeper must be DETECTED. That is the §6 lesson — a
    # detector that has not detected anything is not known to work.
    # (_stand was built once above check 2b — reused, not rebuilt.)
    _base = stand_base()
    _bi = (_base & _stand).volume
    assert _bi < 0.01, (
        f"the base plate interferes with the stand by {_bi:.3f}mm3 — it cannot seat, so the "
        f"speaker chamber cannot be closed. Every edge must derive from CHAM_*, not be typed")
    _bi_self = ((Pos(0, 0.5, 0) * _base) & _stand).volume
    assert _bi_self > 1.0, (
        f"[self-test] the base plate shifted 0.5mm deeper reads {_bi_self:.3f}mm3 — the "
        f"interference detector is broken, not the parts")

    # 2f. THE DOCKED SLAB MUST NOT INTERSECT THE STAND — the fit check this file never had.
    #
    # Every clearance check above compares a part to the BOARD, and check 3 measures how DEEPLY
    # the slot engages the slab. Neither can see the failure that matters here: material grown
    # into the slot so the slab cannot seat at all. Engagement is a length, not an overlap — a
    # slot half as wide as it should be scores exactly the same engagement as a correct one.
    #
    # Ported from the 2026-07-30 battery study (scratch/hosyond-s3/ember-case/bat_final.py),
    # which swept the slab against the stand and found it CLEAR at nominal with the detector
    # proven in five directions. That code lived in a scratch directory and so protected
    # nothing; this is the same boolean where the build can run it.
    #
    # >>> THE PLACEMENT MUST NOT USE SLAB_T, AND THAT IS THE WHOLE POINT. <<<
    # The slot is cut as SLAB_T + 2*SLOT_CLR. If the slab were positioned from SLAB_T too, both
    # sides of the comparison would move together and the check could never fail — the classic
    # shape of a green light over an unmeasured quantity (§6). It is placed from FRONT_Z and
    # BACK_Z, the actual extents of the two bodies, so SLAB_T drifting out of sync with
    # FRONT_Z - BACK_Z is exactly what this catches. Those are equal today (17.4); nothing
    # asserts that they stay equal, which is why this check earns its runtime.
    #
    # The three offsets are DERIVED, not the literals the study used: Rot(90) lays the slab
    # back so its thickness runs along Y, leaving x centred by -BW/2, the body centred on the
    # slot centreline by (FRONT_Z + BACK_Z)/2, and the board origin lifted to the slot floor by
    # -OY0. Transcribing -25 / -1 / 2.95 would have re-created the same drift this check exists
    # to detect, one indirection further away.
    #
    # ⚠️ MODEL FRAME. _bezel and _shell come from `parts`, which still holds model-frame solids
    # at the call site — the same property check 5 depends on, documented there. Reading them
    # after _print_oriented() had written back would silently dock a rotated slab and measure
    # nothing. Pos/Rot return NEW objects, so `parts` is not mutated and the exported STLs are
    # untouched by this check.
    def _dock(_part):
        """A model-frame part in its docked pose, in stand coordinates."""
        _loc = Pos(-BW/2, (FRONT_Z + BACK_Z)/2, -OY0) * (Rot(90, 0, 0) * _part)
        return Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT, 0, 0) * _loc)

    def _slab_hit(_dz=0.0):
        _tot, _sbb = 0.0, _stand.bounding_box()
        for _p in (_bezel, _shell):
            for _sd in (Pos(0, 0, _dz) * _dock(_p)).solids():
                _b = _sd.bounding_box()
                if (_b.min.X > _sbb.max.X or _b.max.X < _sbb.min.X or
                        _b.min.Y > _sbb.max.Y or _b.max.Y < _sbb.min.Y or
                        _b.min.Z > _sbb.max.Z or _b.max.Z < _sbb.min.Z):
                    continue
                try:
                    _v = (_stand & _sd).volume
                except Exception:
                    _v = 0.0
                if _v > 0.01:
                    _tot += _v
        return _tot

    _slab_i = _slab_hit()
    assert _slab_i < 0.01, (
        f"the docked slab intersects the stand by {_slab_i:.3f}mm3 — it cannot seat. The slot "
        f"is cut as SLAB_T({SLAB_T}) + 2*SLOT_CLR({SLOT_CLR}) while the body actually spans "
        f"{FRONT_Z - BACK_Z:.2f} (FRONT_Z {FRONT_Z} - BACK_Z {BACK_Z}); if those disagree, fix "
        f"the derivation rather than widening the slot")
    # CONTROL. 0.000 is precisely the answer a blind detector gives, so it has to be shown
    # firing (§6 / verification.md 13). Sinking the slab 2mm drives it into the slot floor.
    _slab_self = _slab_hit(-2.0)
    assert _slab_self > 1.0, (
        f"[self-test] the slab sunk 2mm into the cradle reads {_slab_self:.3f}mm3 — the "
        f"intersection detector is blind, so the 0.000 above is silence, not evidence")
    print(f"  [slab] docked slab vs stand {_slab_i:.3f}mm3 CLEAR   "
          f"[self-test] sunk 2mm -> {_slab_self:.1f}mm3 detector WORKS")

    # 3. the slot must still hold it
    assert engagement >= 12.0, f"slot engagement {engagement:.1f}mm is too shallow to retain the slab"

    # 3b. THE BUTTONS MUST BE REACHABLE WHILE DOCKED.
    #
    # THIS IS THE LENS THAT WAS MISSING, and it is the third time this project has shipped a
    # feature the stand quietly swallowed. Assert 1 asks whether the stand occludes the
    # DISPLAY. Assert 2 asks whether there is room for the USB-C PLUG. Nobody asked about the
    # BUTTONS — and the stand covered them completely, both of them, with 0.40mm of slot
    # clearance between the cap face and solid wall. Same blindness every time: the boolean
    # clearance check compares parts to the BOARD, and a stand wall sitting beside a button
    # intersects nothing at all.
    #
    # The generalisation worth keeping is that "does it collide" and "can you get at it" are
    # different questions, and passing the first says nothing about the second. Every feature
    # a human has to REACH needs its own reachability check; enumerate them rather than
    # trusting that a previous assert's neighbourhood covered them. Display, plug, buttons,
    # microSD, mic port, USB — this file now checks the first three.
    #
    # Probed as a fingertip, not as a point: a 6 x 4mm contact patch 6mm out from the cap
    # face. A centreline sample would pass through a slot the finger cannot enter.
    # (_stand was built once for check 2d above — reused, not rebuilt.)
    for _cx, _cy in BTN:
        _cyh, _R, _ = cap_geometry(_cx)
        _probe = Box(6.0, 6.0, 4.0, align=(Align.CENTER, Align.MIN, Align.CENTER))
        _probe = Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) * (
                     Pos(_cx - BW/2, SLAB_T/2, _cyh - OY0) * _probe))
        _blocked = (_stand & _probe).volume
        assert _blocked < 1.0, (
            f"cap at x={_cx} is blocked by {_blocked:.1f}mm3 of stand — a finger cannot "
            f"reach it while docked. The stand swallows the first "
            f"{(ST_H-SLOT_FLOOR)/math.cos(math.radians(TILT)):.2f}mm of the slab.")
    # and the scallops must not eat their way out through the stand's back face
    _rear = (SLOT_CY + (SLAB_T/2 + SLOT_CLR)*math.cos(math.radians(TILT))
             + ((ST_H-SLOT_FLOOR)/math.cos(math.radians(TILT)))*math.sin(math.radians(TILT)))
    # 3c. THE #35 CHAMFER MUST NOT REACH #31's RETENTION ZONES.
    #
    # The rim chamfer runs on the stand's OUTER perimeter (x=0 and x=ST_W). What holds the
    # leaning slab is the rear rim at the slot's two x-extremes — 9.55 + 10.12 = 19.67mm of
    # full-height wall either side of the #31 notch — and those start at the SLOT's edge,
    # 3.65mm inboard. So the two features are 2.85mm apart and neither knows about the other.
    #
    # ⚠️ WHICH IS EXACTLY WHY THIS IS PINNED. A chamfer is a whole-silhouette operation and a
    # retention zone is a local one; nothing in either definition mentions the other, so a
    # future CHAMFER bump would eat retention silently and no existing check would notice —
    # the engagement assert measures ST_H - SLOT_FLOOR and would not move at all.
    #
    # The rim's DEPTH also loses CHAMFER (16.92 -> 16.12mm behind the slot) and that is fine
    # and deliberate: the slab bears where it crosses the slot's rear face at y=47.08, not at
    # the outer edge the chamfer touches. Recorded so the 0.80 is not mistaken for a loss of
    # bearing line.
    _zone_x0 = ST_W/2 - SLAB_W/2 - SLOT_CLR                     # 3.65, the slot's edge
    assert CHAMFER <= _zone_x0 - 1.0, (
        f"the {CHAMFER}mm rim chamfer reaches x={CHAMFER:.2f} and #31's retention zone starts "
        f"at x={_zone_x0:.2f} — under 1mm between them the chamfer is eating the full-height "
        f"rim that stops the slab leaning back. Engagement would still read 16.56mm, so "
        f"nothing else here would catch it")
    assert ST_D - _rear - CHAMFER >= 12.0, (
        f"the rear rim is {ST_D - _rear - CHAMFER:.2f}mm deep behind the slot after the "
        f"chamfer — the bearing line at y={_rear:.2f} needs wall behind it, not just at it")
    assert ST_D - (_rear + SCALLOP_D) >= 3.0, (
        f"finger scallops leave only {ST_D-(_rear+SCALLOP_D):.1f}mm of rear wall at the rim")

    # 4. THE BUTTON PADS MUST STILL BE ATTACHED.
    #
    # This is the one assert here that tests the thing rather than a proxy for it. The
    # hexagonal slot is cut as a ring with a tab declined, and the failure mode is that the
    # tab arithmetic is wrong and the ring closes — at which point the pad is no longer a
    # printed-in-place hinge, it is a loose hexagon that falls out of the case on the print
    # bed. A dimension check cannot see that, and neither can the boolean clearance check,
    # for the reason recorded at 2b: a severed pad collides with nothing.
    #
    # Solid count answers it directly. The back shell is one connected body; sever a hinge
    # and it becomes two, sever both and three. There is no arrangement of the numbers that
    # satisfies this while the pads are detached.
    _n = len(_shell.solids())
    assert _n == 1, (
        f"back shell is {_n} solids, not 1 — a button pad has been cut free of its hinge "
        f"and will fall out of the print. Check the hinge tab width against R/2 + SLOT_W.")

    # 4b. THE HINGES MUST NOT BE STRAINED PAST THE MATERIAL.
    #
    # The only assert here about the material rather than the shape, and the one that would
    # have caught both the shipped RESET hinge (4.37%) and a proposed "fix" that took it to
    # 6.79%. Every other check in this file would pass all three variants happily: the
    # geometry is valid, nothing collides, the pad stays attached, it prints. It just breaks
    # in the user's hand after a few dozen presses, which is not a shape property.
    #
    # theta is FIXED by pip travel over the pip's lever arm and cannot be tuned away; the only
    # levers are thickness (which makes strain worse) and flexure length (which makes it
    # better). 2.0% is the threshold — the assert below reads `<= 0.020`, and this comment
    # said 2.5%. PLA yields around 2% and breaks in the 4-6% band, so the limit sits AT yield
    # and well clear of fracture, for a control pressed by hand. "Just past yield" described
    # the 2.5% figure that was never in the code.
    for _cx, _cy in BTN:
        _cyh, _R, _ = cap_geometry(_cx)
        _arm = cap_hex_top_y(_cyh, _R) - _cy
        _theta = 0.40 / _arm                     # 0.40mm = air gap + switch travel
        _strain = (HINGE_T/2) * _theta / cap_hinge_len(_cx)
        assert _strain <= 0.020, (
            f"hinge at x={_cx} bends {math.degrees(_theta):.1f}deg over "
            f"{cap_hinge_len(_cx)}mm at t={HINGE_T} -> {100*_strain:.2f}% strain. PLA yields "
            f"near 2% and breaks by 4-6%. LENGTHEN the flexure; thickening makes it worse.")

    # 5. geometry the hex caps have to satisfy, each pinned by something real
    for _d in (DEBOSS_BIG, DEBOSS_SMALL):
        assert _d <= (CAV_FLOOR - BACK_Z) - 1.20, (
            f"a {_d}mm deboss leaves under 1.20mm of pad above it out of "
            f"{CAV_FLOOR-BACK_Z:.2f}mm; the pad still has to carry the press to the pip")
    assert CAP_INSET >= 0.80, (
        f"CAP_INSET {CAP_INSET}mm leaves less than two extrusion widths of shoulder; the "
        f"raised cap can bridge the {SLOT_W}mm slot and weld the pad shut")
    for _cx, _cy in BTN:
        _cyh, _R, _ = cap_geometry(_cx)
        # the slot's OUTER edge must clear the fine hex field, which starts at HEX_FIELD_Y0
        # (19.00). This comment said 11.0 while the assert below already read the constant —
        # the check was right and its own explanation was two values out of date.
        _slot_top = cap_hex_top_y(_cyh, _R + SLOT_W)
        # the hinge cut reaches further than the slot does, so check the deeper of the two
        _reach = max(_slot_top, cap_hex_top_y(_cyh, _R) + cap_hinge_len(_cx)/2)
        assert _reach <= HEX_FIELD_Y0 - 0.80, (
            f"cap at x={_cx} reaches y={_reach:.2f}, and the hex field starts at "
            f"y={HEX_FIELD_Y0} — needs 0.80mm of clearance. Raise HEX_FIELD_Y0 or shrink R.")
        # the plunger pip must sit wholly inside the island, and the island narrows with
        # every millimetre away from its centre: half-width = R - |dy|/sqrt(3)
        # THE PIP MUST SIT WHOLLY INSIDE THE ISLAND, AND THE ISLAND IS NOW OFFSET FROM IT.
        # This is the tightest margin on the part (0.72mm on BOOT), and it is the one a
        # reviewer specifically asked to be re-checked by geometry rather than by arithmetic,
        # because both terms are small: the island hex narrows toward its bottom flat by
        # |dy|/sqrt(3), which is exactly where the switch is, AND the island centre is shifted
        # up to 3.53mm away from the switch to clear a countersink. Either alone is fine; the
        # two together are what make it tight.
        _icx = cap_center_x(_cx)
        _halfw = _R - abs(_cy - _cyh)/math.sqrt(3)
        _need = PIP_D/2 + abs(_cx - _icx)
        assert _halfw >= _need + 0.50, (
            f"cap at x={_cx}: island is {_halfw:.2f}mm half-wide at the switch (y={_cy}) and "
            f"the {PIP_D}mm pip offset {abs(_cx-_icx):.2f}mm needs {_need:.2f}mm — the pip "
            f"would hang over the printed-in-place slot and weld the pad shut")
        # ...and the ISLAND must clear the countersinks, which are 6.40mm at the outer face
        # and are the reason the island is offset in the first place. Assert the thing the
        # offset was chosen to achieve, rather than trusting the number that achieved it.
        for _hx, _hy in HOLES:
            if abs(_hy - _cyh) < _R*math.sqrt(3)/2 + 3.20:
                _gap = abs(_icx - _hx) - _R - 3.20
                assert _gap >= 0.30, (
                    f"cap island at x={_icx:.2f} (R={_R:.2f}) overlaps the countersink at "
                    f"({_hx},{_hy}) by {-_gap:.2f}mm — shift CAP_CX_*, do not shrink the cap")

    # 5. THE SCREW MUST PASS THROUGH BOTH PARTS — the only MATING check on these two.
    #
    # Every other clearance check in this file is INTRINSIC TO ONE PART, or compares a part to
    # the BOARD. Nothing has ever asked whether the bezel's pilot and the shell's clearance bore
    # are the same hole. Today they cannot diverge — both loops iterate `HOLES` — so this is
    # insurance against someone later giving either part its own table, which is precisely the
    # failure `stand_base()` already shipped once (a private copy of CHAM_Y1 that went stale)
    # and precisely the class nothing here could see.
    #
    # >>> IT PROBES THE GEOMETRY, NOT THE CONSTANT. <<< `HOLES == HOLES` is vacuous. What is
    # asserted is the functional property — a straight bore of the pilot diameter runs clean
    # from the shell's outer face to the top of the bezel's pilot — so it fails on a hole that
    # MOVED, whichever part moved it, and it also ties both parts to the board's own table
    # rather than merely to each other.
    #
    # ⚠️ ON THE IN-MEMORY PARTS, NEVER ON THE EXPORTED STLs. `_print_oriented()` rotates the
    # bezel 180deg about X (issue #25), so an STL-vs-STL comparison is mirrored in Y and fails
    # BY DESIGN — it would read as a real defect and send someone after a fault that is not
    # there. `parts` still holds the model-frame solids at the call site because
    # `_print_oriented` returns a new object rather than mutating the dict; that is load-bearing
    # here, so do not "tidy" that loop into reassigning `parts[n]`.
    _probe_d = PILOT_D - 0.40      # 2.10 — inside the tightest bore in the stack (the d2.50
                                   # pilot), with 0.20mm of radius to spare for mesh tolerance
    for _hx, _hy in HOLES:
        for _nm, _pt in (("bezel", _bezel), ("back shell", _shell)):
            _blk = (_pt & cyl(_hx, _hy, BACK_Z - 0.5, SEAM_Z + 1.4, _probe_d)).volume
            assert _blk < 0.01, (
                f"the screw axis at ({_hx},{_hy}) is blocked by {_blk:.3f}mm3 of {_nm} — a "
                f"d{_probe_d:.2f} bore does not run clean from the shell's outer face to the "
                f"top of the bezel's pilot. The two parts no longer share a hole table, or one "
                f"of them no longer agrees with HOLES")
    # CONTROL. 0.80mm of offset must block BOTH — otherwise the probe is thin enough to rattle
    # through a moved hole and the check above is decoration. The margins are asymmetric and
    # worth stating: the bezel's d2.50 pilot blocks past 0.20mm of drift, the shell's d3.30
    # clearance bore only past 0.60, so THE SHELL IS THE INSENSITIVE ONE — 0.80 is chosen to
    # clear that, not the bezel.
    _hx, _hy = HOLES[0]
    for _nm, _pt in (("bezel", _bezel), ("back shell", _shell)):
        _off = (_pt & cyl(_hx + 0.80, _hy, BACK_Z - 0.5, SEAM_Z + 1.4, _probe_d)).volume
        assert _off > 0.10, (
            f"[self-test] the screw probe shifted 0.80mm reads {_off:.3f}mm3 against the {_nm} "
            f"— it passes through a hole it should foul, so the mating check cannot detect a "
            f"hole table that has drifted")
    return engagement, va_start, below


if __name__ == "__main__":
    # `parts` still holds MODEL-FRAME solids here — _print_oriented() returned new objects into
    # a loop-local and never wrote back. The mating check at 5 depends on that; see its comment.
    _e, _v, _b = _check_geometry(parts)
    print(f"  [geometry] engagement {_e:.1f}mm | VA starts {_v:.1f}mm | {_b:.1f}mm under for USB-C  OK")

    # ── COMMIT. Every check above has passed, so the temp exports become the real STLs.
    # Reached only on success: any assert anywhere above raises and this never runs, which
    # leaves the PREVIOUS good STLs untouched on disk. That second property is the one that
    # actually bit — the old files were being clobbered before anything failed, so guarding
    # only "no new file is written" would have missed it entirely.
    for n in parts:
        _tmp = os.path.join(out, n + STL_TMP)
        if os.path.exists(_tmp):
            os.replace(_tmp, os.path.join(out, n + ".stl"))   # atomic within a filesystem
    _committed = True
    print(f"  [export] committed {len(parts)} STLs — all checks passed first")

    # ── PRINT QUEUE. Refresh the versioned, slicer-facing copies in enclosure/print/.
    # Called HERE, by the build, because a queue a human must remember to refresh is a
    # stale copy waiting to happen — the 2026-07-31 bezel near-miss was two files with
    # IDENTICAL names whose only difference was a sha256 no slicer shows. Loud on
    # failure: a silently-stale queue is the same defect, one directory over.
    import subprocess as _sp
    _pq = _sp.run([sys.executable, os.path.join(out, "tools", "print_queue.py"), "refresh"])
    if _pq.returncode != 0:
        raise RuntimeError("print_queue refresh FAILED — enclosure/print/ may be stale")
