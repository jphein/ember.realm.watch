"""
Ember MOBILE enclosure  --  ES3C28P + 18650 + integrated speaker, one handheld case
====================================================================================
Parametric source.  Run:  ../cadenv/bin/python ember_mobile_case.py
Outputs 2 new STLs and re-runs the vendor-STEP clearance boolean against both.

>>> THE BEZEL AND THE BOARD-CLAMPING STACK ARE NOT TOUCHED. <<<

`ember-front-bezel` is reused BIT-IDENTICAL from ember_case.py -- same STL, same four
M3x12 ISO 4762, same HOLES, same CBORE_DEPTH, same 5.34mm engagement. This file adds:

    ember-mobile-midframe   back_shell() + brow + bond plateau + pockets   (0.20 layers)
    ember-mobile-back       the cell/speaker cover                          (0.20 layers)

Why a backpack and not a deeper back shell: SCREW_LEN is an UNDER-HEAD length and
ember_case.py records that M3x14 bottoms out at the pilot's 6.20 end while "the failure
still looks like success". Deepening the shell moves the counterbore 21.80mm further from
the pilot and invalidates that entire derivation. Holding the midframe's back face at
BACK_Z = -9.70 means the bezel-board-midframe clamp is the SAME assembly as the desk case
and none of that analysis has to be redone.

The second consequence is the one that makes the product work: the cell sits behind a part
that carries no board load, so REMOVING THE COVER DOES NOT DISTURB THE BOARD.

COORDINATE SYSTEM: the board's own frame, identical to ember_case.py.
    X  0 .. 50    Y  0 .. 86    Z  glass +4.30 | PCB top 0 | deepest back component -6.30

⚠️ EVERY BOARD NUMBER AND EVERY SHELL NUMBER IS IMPORTED, NEVER RE-TYPED. If a constant
appears as a literal below it is because this file is the first place it exists; anything
ember_case.py already owns is read from `E`. That rule is the whole reason this file can be
trusted to stay in step with a part that is actively being printed from.
"""
from build123d import *
import os, sys, math

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import ember_case as E

# ============================================================================
# 1. WHAT IS IMPORTED.  Named here so the dependency is a list, not a grep.
# ============================================================================
OX0, OX1, OY0, OY1 = E.OX0, E.OX1, E.OY0, E.OY1        # -2.95..52.95, -2.95..88.95
BACK_Z, CAV_FLOOR, SEAM_Z, FRONT_Z = E.BACK_Z, E.CAV_FLOOR, E.SEAM_Z, E.FRONT_Z
OUT_R, WALL, CHAMFER = E.OUT_R, E.WALL, E.CHAMFER
LH = E.LAYER_H_SHELL                                    # 0.20 -- this file's ONLY layer height
BAFFLE_T = E.BAFFLE_T                                   # 2.20
HEX_R, HEX_WEB, GRILLE_INSET = E.HEX_R, E.HEX_WEB, E.GRILLE_INSET
DRIVER_W, DRIVER_H, DRIVER_T = E.DRIVER_W, E.DRIVER_H, E.DRIVER_T
DRIVER_R, DRIVER_CLR = E.DRIVER_R, E.DRIVER_CLR
CBORE_D, CBORE_DEPTH, SCREW_D, PILOT_D = E.CBORE_D, E.CBORE_DEPTH, E.SCREW_D, E.PILOT_D
SCREW_HEAD_D, SCREW_HEAD_H = E.SCREW_HEAD_D, E.SCREW_HEAD_H
bx, rbox, cyl = E.bx, E.rbox, E.cyl

# ⚠️ THE MOBILE'S OWN FLANK OPENINGS, NOT THE NOMINAL SET. JP suppressed SPK and BAT on this
# variant (SIDE_BLOCK in ember_case) — SPK because the driver lives in the cover's sealed cavity
# and its pigtail leaves through the SPK relief, BAT because the pigtail runs internally through
# the midframe's floor pass. Everything here that reasons about "where is the wall solid" must
# read THIS, not E._CH_*: the glow window's site is SOLVED at runtime from the solid spans
# between openings, so closing one silently moves a published feature. It did — see the [glow]
# line in the build log.
MOB_CH_HI, MOB_CH_LO = E.side_channels("mobile")


def cyl_y(cx, cz, d, y0, y1):
    """Cylinder with its axis along +Y. Same construction trick as E.rrect_y()."""
    return Pos(cx, y0, cz) * (Rot(-90, 0, 0) * extrude(Circle(d/2), y1 - y0))

# ============================================================================
# 2. THE COVER'S WALL, AND WHY IT IS 2.20 AND NOT THE FAMILY'S 2.60
# ============================================================================
#
# Two independent reasons converge on the same number, which is the only reason it is
# allowed to differ from WALL:
#
#   1. IT IS THE BAFFLE. The cover's outer wall over the driver IS the grille's baffle, so
#      its thickness IS the acoustic port length. The desk stand gets 2.20 by cutting
#      GRILLE_RECESS into a 4.0 wall; here the wall already is the baffle and the recess
#      disappears entirely. Setting COV_WALL = BAFFLE_T makes the port length identical to
#      the stand's BY CONSTRUCTION rather than by coincidence -- asserted at check 2.
#   2. THE X BUDGET DOES NOT CLOSE AT 2.60. Interior width must hold the cell bore (19.40)
#      plus a shared divider (2.00) plus the driver's tape footprint (28.20) = 49.60.
#      At WALL=2.60 the interior is 50.70, leaving 1.10 total; at 2.20 it is 51.50, leaving
#      1.90. The rim needs that. Asserted at check 3 so it cannot silently go negative.
#      (The bore figure was 19.60 here until 2026-08-01 -- stale since the bare-cell
#      re-primary. Check 3 measures the live constants, so only the prose had drifted.)
#
# 11 * 0.20 exactly, so the wall is a whole number of layers like everything else here.
COV_WALL = 11 * LH                                      # 2.20

# ============================================================================
# 3. THE CELL.  Designed to the LONGEST cell, not the nominal one.
# ============================================================================
#
# >>> THIS IS THE ANSWER TO "DOES A PROTECTED CELL FIT". IT IS A DIMENSION, NOT A HOPE. <<<
#
# An unprotected 18650 is 65.20 long; a protected one carries a PCB and a re-wrap and runs
# to ~71. Sizing the bay to the SHORT cell and hoping is the obvious mistake. Sizing it to
# the LONG cell and letting a spring take up the 5.80mm difference makes both fit, and turns
# the question into an arithmetic one that check 5 can actually test.
#
# ⚠️ AND IT IS NOT A FREE CHOICE. Open electrical question 3 (see the design note) is whether
# the board provides ANY over-discharge / over-charge protection. If it does not, a protected
# cell is MANDATORY -- which is exactly why this bay costs 9.55mm of case length rather than
# being sized to 65.20 and saving it.
#
# >>> 2026-08-01 REVERSAL (JP): "no, I only use bare cells, no protected tops." <<<
#
# BARE FLAT-TOP 18650 IS NOW THE ONLY CELL CLASS. Everything below is re-primaried to it, and
# two things that were true yesterday are now false:
#
#   * the 71.00 allowance existed solely for a protection PCB and its re-wrap. Gone -> the bay
#     drops 6.50 and the case drops 5.90.
#   * THE BUTTON KEYING IS VOID AND HAS BEEN REMOVED. A flat-top positive is the plain can face;
#     it cannot reach a contact recessed behind an aperture, so the keyed cover would have
#     rejected the only cells JP owns. There is NO mechanical keying available for flat-tops --
#     both ends are geometrically identical. Reverse protection is now MARKINGS ONLY. See §"MARK".
CELL_D_MAX      = 18.80     # bare flat-top can incl. wrap; bare stock is 18.4-18.6
CELL_BORE_CLR   = 0.30      # per side, hand-drop fit for a cylinder
CELL_BORE_D     = CELL_D_MAX + 2*CELL_BORE_CLR          # 19.40 = 97 layers, and the cover
                                                        # depth below must stay layer-whole
CELL_L_NOM      = 65.20     # bare 18650
CELL_L_TOL      = 0.30      # manufacturing spread, bare stock
CELL_L_MIN      = CELL_L_NOM - CELL_L_TOL               # 64.90
CELL_L_MAX      = CELL_L_NOM + CELL_L_TOL               # 65.50
CELL_L_CLR      = 0.60      # end float
# SPRING: a generic AA/18650-holder compression spring. Only three numbers matter and all
# three are asserted, because the requirement is a RANGE and a spring that suits the cell on
# the bench is precisely the kind of check docs/verification.md distrusts.
# The spring no longer spans a 5.80mm CELL CLASS difference -- only the 0.60mm manufacturing
# spread of one class. So it shrinks with the bay: travel must merely exceed CELL_L_TOL*2, and
# what actually sizes it is keeping preload at the SHORTEST cell without coil-binding on the
# LONGEST. Both directions asserted, both with controls.
SPRING_SOLID    = 2.50      # coil-bound height
SPRING_FREE     = 7.00      # free length -> 4.50 of travel against 0.60 of cell spread
SPRING_MARGIN   = 1.00      # how far off coil-bound the LONGEST cell must still leave it
BAY_L           = CELL_L_MAX + CELL_L_CLR + SPRING_SOLID + SPRING_MARGIN     # 69.60

# ============================================================================
# 4. WHERE THE COVER STOPS, AND WHY THAT IS A REACHABILITY DECISION
# ============================================================================
#
# >>> THE CHIN IS BARE ON PURPOSE. <<<
#
# docs/verification.md lists REACHABILITY as the lens none of the geometric checks have, and
# names this exact failure: "the stand in front of the screen; THE BUTTONS SEALED INSIDE IT."
# BOOT carries DEBOSS_BIG and ember_case.py calls it "BOOT/volume, the one you reach for" --
# it is a volume key. Burying it under a battery door repeats a fault already paid for once,
# and no clearance boolean in this file would say a word about it.
#
# So the cover stops short of both caps and the midframe's back face stays exposed below it,
# exactly as in the desk case. DERIVED from cap_geometry(), never typed: a cap whose R or
# PAD_Y0 moved would drag this with it.
_BOOT_TOP  = E.cap_hex_top_y(*E.cap_geometry(E.BTN_BOOT_X)[:2])     # 15.80
_RESET_TOP = E.cap_hex_top_y(*E.cap_geometry(E.BTN_RESET_X)[:2])    # 10.80
CAP_KEEPOUT = max(_BOOT_TOP, _RESET_TOP) + E.SLOT_W                 # 16.40, moat included
COVER_CLR   = 1.60          # finger room past the moat before the step starts
COVER_Y0    = CAP_KEEPOUT + COVER_CLR                               # 18.00

# ---- and everything downstream of it, in one chain so nothing can drift ----
BAY_Y0   = COVER_Y0 + COV_WALL                          # 20.20 — the cell's flat +ve face bears
# ---- KEYING REMOVED.  There is none available, and saying so is the deliverable. ----
#
# The previous revision recessed the +ve contact behind a d7.00 aperture so a reversed cell's
# flat end could not reach it. That worked ONLY because a protected cell's positive is a raised
# button. On a bare flat-top BOTH ENDS ARE GEOMETRICALLY IDENTICAL: any aperture that stops a
# reversed cell stops a correct one too, and any opening that admits a correct one admits a
# reversed one. It is not a case of finding a cleverer shape -- the information is not present
# in the geometry.
#
# >>> SO REVERSE-INSERTION PROTECTION IS NOW MARKINGS ONLY, AND THAT IS AN ELECTRICAL GAP. <<<
#
# The contact plate therefore sits FLUSH with the bay again and the tip datum is BAY_Y0.
# KEY_PLATE_T lived here -- 0.80, "a 0.30 stamped contact plus room". It was the depth of a
# pocket that located the plate and retained nothing, and section 5g replaced it with a kerf
# whose width is derived from the strip's own thickness. Deleted rather than left to rot.
CELL_TIP_Y   = BAY_Y0                                   # flat face, no recess, no offset
BAY_Y1   = CELL_TIP_Y + BAY_L                           # 89.80

# ---- POLARITY MARKINGS.  The only reverse-insertion measure left. ----
#
# "+" on the low-Y end wall, "-" on the high-Y end wall, both facing INTO the bore so they are
# read at the moment the cell goes in. Groove width is the repo's LABEL_W floor.
#
# ⚠️ min_gap IS VACUOUS ON THESE TWO GLYPHS AND MUST NOT BE USED AS THEIR PROOF. I ran it:
# "+" returns (inf, 0 pairs) because its two strokes CROSS, so _touch() excludes the only pair
# there is; "-" returns (inf, 0 pairs) because one stroke has no pair at all. Asserting
# `min_gap >= LABEL_W` would pass on `inf` for any glyph of this shape, including a broken one.
# That is this repo's own recurring defect -- an invariant insensitive to the failure it names.
# Check 15 measures the DEBOSSED VOLUME on the finished solid instead, which can fail.
MARK_H       = 14 * LH                                  # 2.80 stroke-to-stroke, layer-whole
MARK_DEPTH   = 3 * LH                                   # 0.60
MARK_PATHS_P = [[(-MARK_H/2, 0.0), (MARK_H/2, 0.0)], [(0.0, -MARK_H/2), (0.0, MARK_H/2)]]
MARK_PATHS_N = [[(-MARK_H/2, 0.0), (MARK_H/2, 0.0)]]
MARK_INK     = MARK_H + E.LABEL_W                       # 3.70 overall ink extent
MOB_OY1  = BAY_Y1 + COV_WALL                            # 98.50  <- the case's new top
BROW_Y0  = OY1                                          # 88.95, where back_shell ends
# ⚠️ THESE TWO COMMENTS SAID -31.50 AND -29.30 UNTIL 2026-08-01, i.e. they were correct for a
# CELL_BORE_D of 19.60 and the bare-cell re-primary took it to 19.40 without them following.
# Harmless here because both are DERIVED and nothing reads the comment -- but it cost real time
# downstream: a slice script written against -31.50 sliced the cover 0.20 too high and read a
# tooth 0.20 up its own skew. §11 defect #8 is this exact class, one file over.
COVER_Z0 = BACK_Z - COV_WALL - CELL_BORE_D              # -31.30, the cover's outer face
CAV_Z0   = COVER_Z0 + COV_WALL                          # -29.10, baffle inner AND bore floor
# ⚠️ CAV_Z0 IS ONE PLANE SERVING TWO FEATURES AND THAT IS DELIBERATE. The sealed cavity's
# floor and the cell bore's floor are the same surface at the same Z because both are
# "COV_WALL above the outer face". Writing them as two constants is how the stand's base
# plate went stale against CHAM_Y1 (ember_case.py:1721) -- a copy that was right when it was
# typed and wrong from a distance, with nothing able to notice.

# ---- X LANES.  A SINGLE SHARED DIVIDER, because two walls do not fit. ----
CELL_X0     = OX0 + COV_WALL                            # -0.75
CELL_X1     = CELL_X0 + CELL_BORE_D                     # 18.85
CELL_AXIS_X = (CELL_X0 + CELL_X1) / 2                   # 9.05
CELL_AXIS_Z = CAV_Z0 + CELL_BORE_D / 2                  # -19.50
DIVIDER_W   = 2.00
RIM_X0      = CELL_X1 + DIVIDER_W                       # 20.85
RIM_X1      = OX1 - COV_WALL                            # 50.75
RIM_WALL    = 8 * LH                                    # 1.60
# ⚠️ RIM_Y0 WAS BAY_Y0 -- I.E. THE RIM'S LOW-Y SIDE WAS THE COVER'S OWN BOTTOM WALL -- AND THE
# SEAL CHECK REJECTED IT. With the rim starting at the very bottom of the compartment there was
# nowhere along the bottom edge to put a screw pilot or a hook pocket that was not inside the
# seal's footprint, and the first attempt put the screw at (25.00, 19.20): the boolean measured
# the rim landing on 98.36% solid instead of 100%, because the pilot bored straight through the
# ring. 1.6mm3 of hole, and it would have vented the "sealed" cavity into the board cavity
# through the one fastener the user is meant to undo.
#
# So the rim is held off the bottom by RETENTION_STRIP, and every retention feature lives in the
# gap. That is a layout consequence of an acoustic requirement, which is exactly the kind of
# coupling that is invisible at both call sites -- check 6b now asserts it in coordinates as
# well, so the boolean is not the only thing standing between this and a leak.
RETENTION_STRIP = 9.80
RIM_Y0      = BAY_Y0 + RETENTION_STRIP                  # 30.00
RIM_INNER_Y = 44.80
RIM_Y1      = RIM_Y0 + RIM_INNER_Y                      # 74.80

# ============================================================================
# 5. ACOUSTICS.  THE QUESTION IS NOT SEALED-VS-PORTED.
# ============================================================================
#
# ember_case.py:1689 -- "It is a SEALED-BACK MODULE, not a bare driver: a plastic box
# carrying its own rear cavity ... That is why the stand's chamber volume barely matters
# acoustically -- the module brings its own. What matters is the FRONT."
#
# So porting a box behind this driver does nothing; it already has a sealed back. The only
# decision available is the FRONT cavity, and the desk stand is the reference because that
# is the enclosure the driver is KNOWN to sound acceptable in.
#
#   stand chamber  54.00 x 15.30 x 33.00        = 27264.6 mm3
#     - driver     rrect(40,27,r3) x 10.00      = -10722.7
#     - tape pad   rrect(41.2,28.2,r3.6) x 0.80 =   -920.6
#     NET SEALED FRONT AIR                      =  15621.3 mm3
#
# Check 7 recomputes that from E's live constants and measures the mobile cavity by boolean,
# so neither figure is inherited from a comment.
#
# THE DRIVER TAPES DIRECTLY TO THE MIDFRAME'S BACK FACE -- no proud pad. The stand needs
# PAD_PROUD only to stand clear of its chamber's wall/floor junction; the midframe's back
# face is a 3678mm2 printed BED FACE, the flattest plane in the project, and a strictly
# better bond surface. A proud pad here would also be the lowest feature on a bed face,
# which is the defect ember_case.py:2771 records on both shell parts in one session.
FRONT_GAP_MOBILE = (BACK_Z - DRIVER_T) - CAV_Z0         # 9.60
# ⚠️ NAMED BECAUSE IT IS A DEPARTURE, NOT BECAUSE IT IS DERIVED. The stand holds FRONT_GAP at
# 2.50 on the stated grounds that "extra depth is not extra enclosure, it is extra AIR IN
# FRONT OF THE DIAPHRAGM". That reasoning is about TOTAL front air, and total front air here
# comes out slightly BELOW the stand's -- the same air has moved from lateral to axial. I
# believe that is neutral-to-better (check 7 prints both cavities' first modes and the
# governing one goes UP), but it is an assumption and it is flagged rather than buried.

# ---- GRILLE.  Identical lattice, identical port length, and NO FLARE. ----
#
# GRILLE_FLARE exists in the stand because issue #28's grille DROOPED: there the hexes are
# horizontal bores through a VERTICAL wall, so every cell roof is an unsupported span. Here
# the cover prints outer-face-down and the hexes are VERTICAL PRISMS IN A BED FACE -- zero
# unsupported span, nothing to droop. So the mouth web stays the full HEX_WEB = 0.90 instead
# of the stand's GRILLE_MOUTH_WEB = 0.4670, and the "fin" trap that constant guards against
# cannot arise at all.
#
# ⚠️ THE STAND'S OPEN-AREA FIGURES ARE STALE AND ARE NOT INHERITED. ember_case.py:1948 records
# "THROAT 678.0 ... MOUTH 886.1 ... field itself (37 x 24, r1.5)". rrect(37,24,1.5) = 886.1
# EXACTLY, so that raster was taken with GRILLE_INSET = 1.5. The live constant is 1.0
# (ember_case.py:2015), giving a 38.0 x 25.0 r2.0 field of 946.6mm2. It is a correct
# measurement of an object the file no longer builds -- verification.md section 24. Check 8
# rasters this part's own throat and measures the stand's the same way for comparison.
GRILLE_FW = DRIVER_H - 2*GRILLE_INSET      # 25.00 across X -- driver is rotated 90deg here
GRILLE_FH = DRIVER_W - 2*GRILLE_INSET      # 38.00 along Y
DRV_CX    = (RIM_X0 + RIM_X1) / 2                       # 35.80
DRV_CY    = (RIM_Y0 + RIM_Y1) / 2                       # 52.40 -- the comment said 42.60 until
                                                        # 2026-08-01, and that was never right at
                                                        # any RIM_Y0: plainly wrong, not drift.

# ---- driver locating groove: alignment only, the tape does the work ----
LIP_DEPTH = 3 * LH                                      # 0.60
LIP_WIDTH = 1.20
# ---- the plateau that refills the vent hexes so the rim lands on solid material ----
PLATEAU_MARGIN = 2.00
# ============================================================================
# 5g. COVER RETENTION.  THE UNDERCUT HOOKS ARE DEAD.  READ THIS BEFORE REVIVING THEM.
# ============================================================================
#
# >>> VERDICT (JP, 2026-08-01): "the cavity is bridging too far for the PLA to be able to <<<
# >>> do those kind of tolerances."  THE HOOKS ARE NOT COMING BACK.                      <<<
#
# What used to be here: two L-shaped barbs on the cover at x = 4.50 and x = 45.50, each dropping
# into an 8.00 x 4.60 recess cut into the midframe's back face and sliding +Y under a lip, plus
# the one M3 x 22. The engagement was HOOK_LIP_T = 0.60 of lip standing under a HOOK_SLOT_D =
# 0.80 slot, 8.00 wide. Three separate reasons it cannot be printed, and only the first was
# JP's -- the other two are this file's own arithmetic, found while replacing it:
#
#   1. THE POCKET'S CEILING IS A BRIDGE, AND IT IS IN THE BED FACE. The midframe prints back-
#      face-down, so `p -= bx(..., BACK_Z, BACK_Z + HOOK_D)` is a void that starts AT THE BED
#      and is roofed at BACK_Z + 1.40 -- an 8.00 x 7.80 mm flat ceiling with nothing under it.
#      The evidence is a day old: issue #47, the desk stand's grille, where 0.90mm webs
#      collapsed on this machine on this filament. A 0.60mm lip cantilevered off one edge under
#      a 62mm2 bridge is a worse ask than the webs that already failed.
#   2. AND IT COULD NEVER HAVE GONE TOGETHER ANYWAY. The barb needed HOOK_BARB_L - HOOK_CLR =
#      2.90mm of +Y slide with the parts already mated. The driver hangs DRIVER_T = 10.00 below
#      BACK_Z into the cover's sealed cavity and the rim's high-Y wall stands the cavity's full
#      19.40 -- the clearance between them is (RIM_INNER_Y - DRIVER_W)/2 = 2.40mm, see check 8d.
#      A 2.90mm slide drives the rim wall through the speaker. NO CHECK IN THIS FILE LOOKED, and
#      the driver is a phantom, so no boolean could have. Check 8d now sweeps the assembly.
#   3. IT RETAINED THE WRONG 5mm OF AN 74mm COVER. Both hooks and the screw sat inside
#      y 18.60..23.40. Everything above y = 23.40 -- the cell bay, the whole sealed cavity, the
#      brow -- was held by nothing at all and would have gapped open along both long edges.
#
# ---------------------------------------------------------------------------
# THE REPLACEMENT, PICKED BY JP: DOVETAIL SLIDES ON BOTH LONG WALLS + THE SAME ONE SCREW.
# ---------------------------------------------------------------------------
#
# >>> THE DEFINING CONSTRAINT IS PRINT ORIENTATION, AND IT IS THE SAME FOR BOTH PARTS. <<<
#
# PRINT_LIFT (see section 8) translates each part in Z ONLY -- midframe by -BACK_Z, cover by
# -COVER_Z0. Neither is rotated. So MODEL +Z IS PRINT UP ON BOTH PARTS, and a face's angle in
# this file's coordinates IS its as-printed angle. That single fact is what makes the geometry
# below checkable at all, and check 8b asserts it rather than trusting this comment.
#
# The rule that follows: every face of the joint must be VERTICAL or at least 45 degrees from
# horizontal, and NO void may have a flat roof.
#
# >>> AND THE Z BUDGET IS 2.60, NOT 17.40.  THIS IS THE SECOND CONSTRAINT AND IT IS THE ONE <<<
# >>> THAT PICKED THE CROSS-SECTION.                                                        <<<
#
# The obvious place for the groove is the midframe's 2.60 side wall, which stands 17.40 tall --
# except it does not, over most of the run. ember_case.py:1541 cuts the side CABLE CHANNELS
# through the FULL wall thickness at z CAV_FLOOR..PCB_BOT, and the -X wall carries three of them
# (y 20.07..26.32, 28.91..41.06, 44.20..57.86). Over those spans the only material below the
# channel is the 2.60 floor, so the groove and everything above it has to live in 2.60 mm.
#
# A textbook flared dovetail does not fit that. Its void is DT_MOUTH + 2*undercut wide at the
# top, and a 45-degree gable to close a 1.80 void costs 0.90 on its own -- 2.40 total, leaving a
# 0.20 lintel under the cable channel. So the undercut here is a SKEW, NOT A FLARE: the void
# keeps its 1.20 width and TRANSLATES outboard as it rises. The gable then only has to close
# 1.20, and the whole groove fits in 1.80 with 0.80 of lintel left.
#
#      u = distance INBOARD from the case's outer face, on either long wall
#      z = height above BACK_Z (which is print-up on the midframe)
#
#         GROOVE (midframe, cut from its bed face)     RAIL/TOOTH (cover, proud of its top face)
#      1.80 -        /\   <- gable apex, 53.1 deg
#                   /  \                                    +------+   <- top, 0.60 wide
#      1.00 -      +    +                                   |      |
#                 /      \   <- BOTH walls skew outboard   /      /
#      0.20 -    +--------+      at 53.1 deg              +      +      <- the tooth is the
#                |        |                               |      |         same parallelogram,
#      0.00 -    +--------+   <- mouth, 1.20 wide         +------+         inset 0.30 all round
#              1.40      2.60                           1.70    2.30
#      (top of skew spans 0.80..2.00)                   (top spans 1.10..1.70)
#
# Read the groove as the void: 1.20 wide at the bed, the SAME 1.20 wide at z = 1.00, but shifted
# 0.60 outboard, then gabled shut. The outboard wall recedes as it rises (fully supported); the
# inboard wall advances, at 53.1 degrees; the gable closes at 53.1. On the cover the tooth is the
# same parallelogram and leans the same way -- one 53.1-degree overhang face, growing off a bead
# that is 0.60 wide, which is a lean, not a bridge.
#
# THERE IS NO FLAT ROOF ANYWHERE IN THE JOINT. That is the whole difference from the hooks.
#
# ⚠️ THE SKEW COSTS THE CONTINUOUS NECK, and that is a real trade, not a free win. A straight
# stem running the length of the rail cannot fit a slot that translates 0.60 -- there is no
# width left after the skew and two clearances. So the rails are teeth ONLY, at DT_PITCH, with
# nothing between them. Guidance in X comes from having twenty of them at 4.00mm centres rather
# than from one continuous rib. The two walls' skews point in OPPOSITE X directions (u is
# measured from each wall's own outer face), so the pair cannot cam its way out: escaping along
# one rail's skew drives the other's tooth into its skin.
#
# CLEARANCE. 0.30 per engaging face, and it is calibrated against what this machine actually
# did, not against a table: PRINT-SHEET's SLOT_W = 0.60 void prints open at a 0.4 nozzle with
# gap-closing at 0, and #47's 0.90 webs collapsed the same day. 0.30 per face (0.60 across the
# neck) sits exactly on the proven void and is what CELL_BORE_CLR and the old HOOK_CLR both
# used. Expect it to SLIDE BY HAND with slight friction and no tools.
DT_CLR       = 0.30                     # per engaging face
DT_SKIN      = 4 * LH                   # 0.80 of outer wall left standing outboard of the groove
DT_UNDER     = 3 * LH                   # 0.60 the skew -- how far outboard the void translates
DT_NECK      = 3 * LH                   # 0.60 tooth width: 1.5 extrusions, constant top to bottom
DT_MOUTH     = DT_NECK + 2 * DT_CLR     # 1.20 groove width, the SAME at every height
DT_WIDE      = DT_MOUTH + DT_UNDER      # 1.80 the groove's swept u-band (mouth + skew)
DT_NECK_H    = 1 * LH                   # 0.20 straight before the skew starts
DT_SKEW_H    = 4 * LH                   # 0.80 -> atan(0.80/0.60) = 53.13 deg from horizontal
DT_GABLE_H   = 4 * LH                   # 0.80 -> closes DT_MOUTH at the same 53.13 deg
DT_DEPTH     = DT_NECK_H + DT_SKEW_H + DT_GABLE_H       # 1.80 total groove depth
DT_RAIL_H    = DT_NECK_H + DT_SKEW_H                    # 1.00 rail height above BACK_Z
DT_GRIP      = DT_UNDER - DT_CLR                        # 0.30 of positive capture per rail
DT_LIFT      = DT_SKEW_H * DT_CLR / DT_UNDER            # 0.40 the cover may rise before it bites
# ⚠️ BOTH BUDGETS ARE BINDING AND THAT IS WHY EVERY NUMBER IS SMALL.
#
#   Z: DT_DEPTH 1.80 + 0.80 of lintel = 2.60, the floor left under the side cable channels.
#   X: DT_SKIN 0.80 + DT_UNDER 0.60 + DT_MOUTH 1.20 = 2.60 = WALL exactly, so the groove is cut
#      from the side wall and never reaches the board-cavity floor.
#
# On the cover the tooth's bed footprint runs to DT_SKIN + DT_UNDER + DT_CLR + DT_NECK = 2.30,
# which is 0.10 proud of COV_WALL -- the tooth's inboard 0.10 hangs over the bay's open mouth on
# its first layer. A 0.10 step under a 0.60 bead is below the resolution of the process and is
# named here rather than engineered away. Growing any term means shrinking another; the only way
# out is a wider wall, which moves the cell lane, the divider, the rim and the grille.
# ---- THE SLIDE, AND WHY IT IS ONLY 2.00mm ----
#
# >>> THE DRIVER SETS THE TRAVEL.  IT IS NOT A STYLE CHOICE. <<<
#
# The driver is taped to the midframe and hangs DRIVER_T into the cover's sealed cavity; the
# rim's low-Y and high-Y walls stand the cavity's full height. Slide the cover in Y and those
# walls sweep THROUGH the driver. The clearance between them is (RIM_INNER_Y - DRIVER_W)/2 =
# 2.40mm, so 2.40 is the hard ceiling on any Y travel, for ANY retention scheme -- which is what
# also killed the hooks (2.90 needed). Check 8d measures it by sweeping the actual solids.
#
# 2.00 of travel means each flared tooth can be at most DT_TRAVEL - 2*DT_CLR_Y = 1.40 long, so
# the rails are CASTELLATED: a continuous neck for guidance, with short flared teeth at DT_PITCH,
# and matching full-width drop-in pockets in the groove one travel-length back. Drop the cover
# on, push it 2.00mm toward the brow, fit the screw. Because the pitch is uniform the teeth are
# ONE degree of freedom, not twenty -- if any tooth lines up with its pocket they all do.
DT_TRAVEL    = 2.00                                     # +Y to seat; -Y and lift to remove
DT_CLR_Y     = 0.30                                     # end clearance on each tooth
DT_TOOTH     = DT_TRAVEL - 2 * DT_CLR_Y                 # 1.40 engaged length of one tooth
DT_PITCH     = 4.00                                     # >= tooth 1.40 + pocket 2.00 + gap 0.30
DT_ENGAGE_MIN = 12.0                                    # mm2 of plan-view capture, check 8c
# ---- WHERE THE RAILS CAN GO.  Asymmetric, because the constraints are. ----
#
#   * NOT under the seal rim's footprint. On the +X wall the rim's outboard leg IS the cover's
#     own +X wall (RIM_X1 = OX1 - COV_WALL), so a groove anywhere in y 28.40..76.40 is a hole in
#     the sealed cavity's ceiling. That is why the +X side is two short rails and not one long
#     one, and it is the same constraint that put RETENTION_STRIP where it is. The -X wall is
#     free: there the rim's inboard leg is the DIVIDER, not the case wall.
#   * NOT past the brow's corner arc at MOB_OY1 - OUT_R, where the outer face stops being flat.
#   * NOT into the cell-lead pass -- which is why LEAD_X0 moved inboard, see section 5.
#   * The groove stays within u <= WALL so it is cut from the side wall's 17.40mm of material
#     and never thins the 2.60 board-cavity floor. Check 8f measures all of these.
DT_Y0     = COVER_Y0 + 0.60                             # 18.60, clear of the cover's bottom edge
# ⚠️ DERIVED FROM THE **MIDFRAME'S** CORNER, AND THE FIRST VERSION USED THE COVER'S. It read
# MOB_OY1 - OUT_R - 0.60 = 84.95, which is where the COVER's brow starts curving. But the groove
# is cut in the MIDFRAME, and the midframe's outline is back_shell -- whose top corners turn at
# OY1 - OUT_R = 82.50, six millimetres earlier. Over y 82.50..84.95 the +X wall's outer surface
# is already arcing inboard, so the 0.80 of skin outboard of the groove thins toward breakout
# and the shoulder the tooth pulls against stops being there.
#
# CHECK 8f FOUND IT, on the artifact, at 79.7% of one shoulder -- which is the whole reason that
# probe measures the midframe instead of trusting these constants. Two parts, two outlines, and
# the rail belongs to both: that is the CHAM_Y1 class of defect this file keeps naming, and it
# arrived by taking the right formula from the wrong part.
DT_Y1     = min(MOB_OY1, OY1) - OUT_R - 0.60            # 81.90, clear of BOTH parts' arcs
DT_RAILS  = (("lo", DT_Y0, DT_Y1),                      # -X: the whole flank
             ("hi", DT_Y0, RIM_Y0 - RIM_WALL - 0.40),   # +X: below the seal (28.00)
             ("hi", RIM_Y1 + RIM_WALL + 0.60, DT_Y1))   # +X: above it   (77.00..84.95)


def _dt_teeth(y0, y1):
    """Seated Y start of every flared tooth on a rail spanning y0..y1.

    The first tooth sits DT_TRAVEL + DT_CLR_Y past the rail's start, so its drop-in pocket
    begins exactly at y0 and the groove never has to run out from under the cover.
    """
    first = y0 + DT_TRAVEL + DT_CLR_Y
    n = int((y1 - DT_TOOTH - first) // DT_PITCH) + 1
    return [first + k * DT_PITCH for k in range(max(n, 0))]


# Cross-sections, as (u, z-above-BACK_Z), listed anticlockwise. u runs INBOARD from the case's
# outer face, so ONE profile serves both walls. GROOVE and POCKET are cut from the midframe;
# TOOTH is added to the cover, and it is the groove inset by DT_CLR on every engaging face.
_A, _B = DT_SKIN + DT_UNDER, DT_SKIN + DT_UNDER + DT_MOUTH      # 1.40, 2.60 -- the mouth
_C, _D = DT_SKIN, DT_SKIN + DT_MOUTH                            # 0.80, 2.00 -- the skew's top
DT_P_GROOVE = ((_A, 0.0), (_B, 0.0),                            # mouth, on the bed face
               (_B, DT_NECK_H), (_D, DT_NECK_H + DT_SKEW_H),    # inboard wall: straight, skewed
               (DT_SKIN + DT_MOUTH / 2, DT_DEPTH),              # gable apex
               (_C, DT_NECK_H + DT_SKEW_H), (_A, DT_NECK_H))    # outboard wall: skewed, straight
DT_P_POCKET = ((_C, 0.0), (_B, 0.0),                            # ...the same, with the shoulder
               (_B, DT_NECK_H), (_D, DT_NECK_H + DT_SKEW_H),    # taken away: the outboard wall
               (DT_SKIN + DT_MOUTH / 2, DT_DEPTH),              # runs straight down to the bed
               (_C, DT_NECK_H + DT_SKEW_H))                     # so the tooth drops in
DT_P_TOOTH  = ((_A + DT_CLR, 0.0), (_B - DT_CLR, 0.0),
               (_B - DT_CLR, DT_NECK_H), (_D - DT_CLR, DT_RAIL_H),
               (_C + DT_CLR, DT_RAIL_H), (_A + DT_CLR, DT_NECK_H))


def _yprism(pts, y0, y1):
    """Extrude an ABSOLUTE (x, z) cross-section along +Y.

    Rot(-90,0,0) sends sketch +v to world -Z and the extrude direction to world +Y -- the same
    trick cyl_y() and the polarity markings use -- so a sketch point (x, -z) lands at (x, y, z).
    """
    sk = make_face(Polyline(*[(x, -z) for (x, z) in pts], close=True))
    return Pos(0, y0, 0) * (Rot(-90, 0, 0) * extrude(sk, y1 - y0))


def _dt_prism(pts, side, y0, y1):
    """Extrude a (u, z-above-BACK_Z) cross-section along +Y on the named long wall.

    Rot(-90,0,0) sends sketch +v to world -Z and the extrude direction to world +Y (the same
    trick cyl_y() and the polarity markings use), so a sketch point (u, -dz) lands at
    (outer face +/- u, y, BACK_Z + dz). The point order is reversed on the +X wall because
    mirroring u would otherwise hand the face to OCC inside out.
    """
    s = 1.0 if side == "lo" else -1.0
    x0 = OX0 if side == "lo" else OX1
    seq = pts if side == "lo" else tuple(reversed(pts))
    sk = make_face(Polyline(*[(s * u, -dz) for (u, dz) in seq], close=True))
    return Pos(x0, y0, BACK_Z) * (Rot(-90, 0, 0) * extrude(sk, y1 - y0))


GRILLE_CELL_N = None                                    # set by back_cover(), read by the checks
# Narrowest a clipped grille opening may be before it is dropped from the cutting set. Above
# HEX_WEB's 0.90 print floor and above SLOT_W's 0.60 proven void, with margin: a hole this
# narrow in a 2.20 baffle is a slot the nozzle has to trace, not a feature that resolves.
GRILLE_MIN_W  = 1.20

# ============================================================================
# 5c. THE FAST-CHARGE OPTION.  A POCKET THAT COSTS NOTHING WHEN EMPTY.
# ============================================================================
#
# Onboard charging (5b) is the DEFAULT and needs no extra hardware -- but at 290 mA a 3400 mAh
# cell is ~15.8 h. A TP4056-class module (or its USB-C sibling, TP4057/IP2312) runs ~1 A, which
# is 3400/1000 x 1.35 = ~4.6 h. That is the option; it is not a necessity, and the geometry is
# shaped so an unpopulated build pays nothing for it:
#
#   * THE POCKET IS THREE RIBS ON A FLOOR THAT WAS ALREADY EMPTY. No cavity is hollowed for it,
#     no wall is thinned, no check depends on it. Leave it unpopulated and it is decoration.
#   * THE APERTURE IS A KNOCK-OUT, NOT A HOLE. The default cover is SOLID here: the port is cut
#     from the INNER face only, leaving TP_KNOCKOUT of wall standing at the outer face. Populate
#     the module and you slice that membrane out with a knife. Ship it empty and there is no
#     opening into the cell bay at all -- asserted both ways at check 13.
#
# ⚠️ ELECTRICAL, AND EXPLICITLY NOT DECIDED HERE: with the board's own charger AND a TP4056 both
# wired to one cell, plugging in both USB ports at once puts TWO CC/CV chargers on the same
# cell, fighting each other. The safe wirings are (a) the TP4056 as the ONLY charge path with
# the board's BAT as load-only, or (b) a "never both at once" usage rule. Picking between them
# is JP's call -- see the issue. This file provides the pocket, the aperture and the warning.
TP_W, TP_L, TP_H = 26.00, 17.00, 4.00      # generic TP4056 module: X x Y x Z, lying flat
# ---- AND A PROTECTION STRIP, WHICH IS WHAT THE POCKET NOW HOLDS ----
#
# >>> RE-PRIMARYING TO BARE CELLS SHRANK THE FREE COMPARTMENT PAST WHAT A TP4056 NEEDS. <<<
#
# The free region above the seal rim is RIM_Y1+RIM_WALL .. BAY_Y1 = 13.40mm of Y, and a TP4056
# is 17.00 in its short axis -- it does not fit in EITHER orientation (26.00 in the other).
# Check 13 measures that rather than asserting it in prose. Getting it back costs the entire
# 5.90mm the bare-cell re-primary just saved, because the rim cannot move: RIM_INNER_Y is set
# by the driver's 41.20 tape pad. THAT IS A TRADE FOR JP, NOT A CALL FOR ME -- and with bare
# cells the missing protection is the sharper of the two gaps, so the pocket is sized for a
# protection strip by default and the issue states the price of the alternative.
# ============================================================================
# 5f. THE 1S PROTECTION STRIP.  REQUIRED EQUIPMENT, NOT AN OPTION.
# ============================================================================
#
# >>> SETTLED BY THE PRIMARY SOURCE: docs/vendor/ES3C28P_Schematic.pdf. <<<
#
# I read the sheet rather than the note beside it. The battery area is exactly two blocks --
# "Battery charge and discharge management" (TP4054 U2, PROG R12 3.3K -> ~290 mA, SL2305 P-FET
# power path Q3, B5819W D8) and "Battery level detection" (200K/200K divider -> BAT_ADC).
# THERE IS NO PROTECTION BLOCK. JP1 (BAT) goes straight to the cell.
#
# So with bare cells the over-discharge floor is only the ME6217 LDO's dropout -- the device
# browns out around 3.4 V and THEN KEEPS DRAINING, ~9 uA through the divider alone plus
# quiescent. A cell left flat in a drawer goes to zero. That is why the strip is required
# equipment and not a nicety, and it is the part of the story a "it browns out first" reading
# misses.
#
# PROT_L is ESTIMATED, not measured: JP, 2026-08-01, "20mm about" -- an eyeball figure,
# so it carries +/-2 and the seat leaves that much end slack. W and T remain the class
# placeholders. If calipers ever land, the three constants are still the whole edit.
# Same date, JP froze the length trade: the case STAYS at 94.95 -- in-case TP4056 is
# permanently out (external bay chargers cover fast-charge for removable cells).
#
# THE CLASS IS CERTAIN (JP's photo): a 1S DW01 + dual-FET PCB with pre-welded nickel tabs at
# both ends, components on one face. Briefed class figure: 31.00 x 6.50 x 2.50.
#
# ⚠️ AND THE BRIEFED 31.00 DOES NOT FIT. The free compartment is RIM_X0..RIM_X1 = 30.10 wide,
# so the longest PCB that seats flat is 30.10 - 2*PROT_CLR = 29.30 -- short by 0.90. It does not
# fit rotated either (the compartment is only 13.40 in Y), nor on edge (a 31 strip against 19.40
# of depth), nor diagonally in plan (a 31 x 6.5 rectangle needs 30.96 of X at its best angle).
# The compartment cannot grow: X is pinned by the cell bore on one side and the case wall on the
# other, and Y by the driver's tape pad setting RIM_INNER_Y. So the placeholder is set to the
# MAXIMUM THAT FITS and the assert enforces it -- if JP's strip measures over 29.30 the build
# fails and says by how much, which is the right time to learn it rather than at assembly.
PROT_L_CLASS  = 31.00                                   # briefed class figure, for the record
PROT_CLR      = 0.40
PROT_L_MAX    = (RIM_X1 - RIM_X0) - 2*PROT_CLR          # 29.30, the compartment's hard limit
PROT_L        = 21.50           # JP re-measured: "a little over 21" — seat derives to 22.30 between ribs
PROT_W        = 6.50            # UNMEASURED
PROT_T        = 2.50            # UNMEASURED
PROT_COMP_CLR = 1.00            # over the component face (the FETs are the tall parts)
PROT_RIB_W    = 1.60
# ---- THE STRIP'S Z-RETENTION IS ITS TABS, AND THAT IS STATED, NOT IMPLIED. ----
#
# JP asked what holds the metalwork. For the strip the honest answer is: the two nickel tabs it
# is soldered to at BOTH ends, one running into the divider's wire groove and one to the
# spring. Those are real anchors, not friction, and a lid-clip over the strip would be a
# DOWNWARD-FACING ledge in the cover's print orientation -- the bridging class JP rejected --
# and would also make the strip unfittable, since a 21.50 PCB cannot slide under clips inside a
# 22.30 seat. So: no clip, reliance recorded.
#
# What the ribs CAN do for free is stop it tipping, and at 1.20 against a 2.50 strip they did
# not: the PCB could ride up on one edge and sit proud. Raised to 12 layers = 2.40, just under
# the strip's own thickness so the ribs never lift it off its flat floor. Check 13b measures
# that the floor stays flat and that the sky above the component face stays clear.
PROT_RIB_H    = 12 * LH                                 # 2.40, was 1.20
PROT_CX       = (RIM_X0 + RIM_X1) / 2
# ⚠️ HELD CLEAR OF THE INTERIOR'S CORNER FILLET, AND THE FIRST VERSION WAS NOT. At
# PROT_Y1 = BAY_Y1 - 1.00 the strip's high-X/high-Y corner sat 5.04 from the fillet centre
# against a 4.25 radius -- i.e. in material -- and the phantom fouled by 1.71 mm3. That is
# EXACTLY defect #1 (the cell vs the same rbox's low-Y fillet) recurring at the opposite corner
# of the same cut, which is the tell that the corner radius is a hazard of the construction and
# not a one-off. Squaring the corner off is not the fix here: the outer corner is rounded at
# OUT_R, so a square inner corner would leave 0.44mm of wall on the diagonal. Instead the strip
# is held at or below the fillet's CENTRE line, where the void is full width by construction.
_INT_R        = max(OUT_R - COV_WALL, 1.0)              # the interior rbox's own radius, 4.25
PROT_Y1       = BAY_Y1 - _INT_R - 0.55
# ---- NICKEL TAB SLOTS.  The tabs are the wiring, and they are FLAT. ----
#
# ⚠️ TOPOLOGY CORRECTION, because these strips are SOLD to be spot-welded to a cell under its
# wrap and that is emphatically not what happens here. THE STRIP IS FIXED IN THE CASE AND THE
# CELL STAYS BARE AND REMOVABLE. Nothing attaches to the cell. The chain is:
#
#     bay spring (-)  --tab-->  B-        P-  --.
#     + contact plate --tab-->  B+        P+  --'--> JST 1.25 2P pigtail --> BAT (CONN_L[0])
#
# The tabs are ~5mm x 0.15 flat conductors, so they run in SHALLOW SLOTS rather than round-wire
# channels, and the excess is trimmed. Solder access is the thing these pockets always forget:
# here the whole compartment is open from +Z until the midframe goes on, so every joint is
# reachable with an iron while the strip is seated. That is a property of the assembly order,
# and check 13b measures that nothing overhangs the pocket to spoil it.
TAB_W         = 5.40            # 5.00 tab plus clearance
TAB_D         = 2 * LH          # 0.40 deep: 0.15 of tab plus solder

# ============================================================================
# 5g. THE BAY'S METALWORK.  A SPRING THAT FALLS OUT IS A DESIGN FAILURE.
# ============================================================================
#
# >>> JP, 2026-08-01: "we need features to hold the spring, and to hold the metal strips." <<<
#
# Until now the bay specified its metalwork and retained none of it: the "+" contact sat in a
# 10 x 10 x 0.80 pocket that located it and held it not at all, and the "spring seat" was a
# d9.00 scallop 1.00 deep in the cradle -- which, read as a print, is also a 9mm horizontal
# bore roof over a 1.00 span, i.e. the same bridging class JP rejected the hooks for.
#
# THE ACCEPTANCE BEHAVIOUR IS JP'S AND IT IS SHARP: cell OUT, case held OPEN-SIDE-DOWN, the
# spring stays put. That single sentence eliminates most of the obvious answers, because the
# cradle is open above the cell's axis (it has to be -- that is how the cell goes in), so
# gravity in that pose points STRAIGHT OUT OF THE BAY.
#
# ---- WHY A TUNNEL AND NOT A BOSS OR A CUP.  The brief offered both; neither survives. ----
#
#   * A BOSS the spring's ID slips over would sit on the cell's axis, which is 9.70mm above
#     the bottom of the bore with NOTHING UNDER IT. In the cover's print orientation that is a
#     horizontal cantilever starting in mid-air -- its first layer is a hairline hanging off
#     the end wall. Gusseting it downward fails too: the gusset would have to pass through the
#     spring's own coil to reach material.
#   * A CUP 1.20 deep captures 1.20mm of a spring whose FREE length is 7.00. With no cell in,
#     the other 5.80 cantilevers, droops, and levers itself out. A cup locates; it does not
#     capture, and the acceptance test is about capture.
#   * A TUNNEL is the cup taken as far as it goes: a short length of the bay where the bore
#     CLOSES OVER, so the spring is threaded into a hole rather than laid in a trough. Three
#     millimetres of a 7.00 free length inside a closed bore cannot fall in any orientation.
#
# And it is printable, which the other two are not, because the bore is GABLED rather than
# round -- the same 45-degree trick the dovetail's groove uses, for the same reason. A round
# d8.60 horizontal bore roofs a 8.60 span flat at its crown; a gable roofs nothing.
#
# ⚠️ IT ALSO BECOMES AN OVER-TRAVEL STOP, WHICH IS A CONSEQUENCE, NOT A DESIGN. The tunnel's
# mouth is an annular face a cell can bottom on. Normally it never does -- at CELL_L_MAX the
# cell's end sits 0.50 clear of it -- but a hard push now lands on plastic at a spring length
# of 3.00 instead of driving the coil toward its 2.50 solid height. Asserted both ways below:
# the mouth must NOT be reachable in normal service, and it must stop short of coil-bound.
SPRING_OD      = 8.00                       # the generic AA/18650-holder spring of section 3
# ⚠️ 0.50 PER SIDE, NOT THE 0.30 EVERYTHING ELSE HERE USES, AND THE GABLE IS WHY. A gable is a
# chord across the corner of the bore, so it comes CLOSER to a round spring than the flat it
# replaces: for a 45-degree roof to clear a radius r, the straight sides must run to
# r/cos45 - w above the axis before the roof starts. At 0.30 per side that tangency lands with
# 0.03mm to spare, which is not a clearance, it is a coincidence. 0.50 buys 0.31 of real margin
# and costs nothing -- the spring is being CAPTURED here, not located.
SPRING_CLR     = 0.50
SPRING_BORE    = SPRING_OD + 2 * SPRING_CLR             # 9.00 across the flats
# ⚠️ THE GABLE RUNS AT 53.13, NOT 45, AND THE FIRST VERSION RAN AT 45. A slice of the built mesh
# measured its ridge at exactly 0.200mm of material per 0.20 layer per edge -- printable, and
# precisely ON the limit. The dovetail is held to 50 for the stated reason that tessellation
# must not be able to eat the margin, and there is no principled reason for a second roof in the
# same part to be held to less. It costs a taller block inside a bay that has the room.
SPRING_GABLE_Z    = 6 * LH                  # 1.20 of straight side above the axis, then the roof
SPRING_GABLE_RISE = SPRING_BORE / 2 * 4 / 3             # 6.00 over 4.50 -> 53.13 deg
SPRING_APEX_Z     = SPRING_GABLE_Z + SPRING_GABLE_RISE  # 7.20 above the axis
SPRING_TUN_L   = 3.00                       # how much of the spring is inside a closed bore
SPRING_TUN_Y0  = BAY_Y1 - SPRING_TUN_L                  # 86.80
SPRING_TUN_CAP = 4 * LH                     # 0.80 of material over the bore's gable apex
SPRING_TUN_TOP = CELL_AXIS_Z + SPRING_APEX_Z + SPRING_TUN_CAP       # -12.60, the block's top
SPRING_TAB_W   = 0.25 + 0.10                # the -ve tab's exit slot, same kerf as the + plate

# ---- THE "+" CONTACT.  A KERF, NOT A POCKET. ----
#
# CONTACT_T IS JP-CONFIRMED, THE KERF IS NOT. JP confirmed the MATERIAL: 0.25mm nickel strip,
# his words on the thickness only -- "I don't know the kerf". So the slot width is DERIVED here
# and owned here: CONTACT_T + CONTACT_PLAY, where the play is this design's FDM fit allowance
# and is the first constant to move if the printed slot binds or rattles. Neither number is
# calipered; if a fit issue ever appears, CONTACT_T is the second thing to measure.
CONTACT_T      = 0.25                       # JP-CONFIRMED DEFAULT (material), not calipered
CONTACT_PLAY   = 0.10                       # MINE: FDM fit allowance, tune this first
CONTACT_KERF   = CONTACT_T + CONTACT_PLAY               # 0.35
CONTACT_W      = 10.00                      # plate width in X -- was the old pocket's 10
CONTACT_H      = 10.00                      # plate height in Z
CONTACT_Z0     = CELL_AXIS_Z - CONTACT_H / 2            # -24.50, the kerf's floor
CONTACT_Z1     = CONTACT_Z0 + CONTACT_H                 # -14.50, the plate's top when seated
# ---- and the detent, because friction alone is not retention ----
#
# The kerf has to be OPEN AT THE TOP or the plate cannot be got in: it is 10mm square and
# nothing 10mm square passes a closed slot. Open at the top means it can also come back out, so
# a bar is left standing across the back of the slot just above the seated plate, filling
# CONTACT_DETENT of the kerf's 0.35. The plate has to deform past 0.05 of interference going in
# and the same coming out. Printability is free here: the bar's underside overhangs by the
# kerf's own 0.35 depth and nothing else, which is under one extrusion width.
CONTACT_DETENT = 0.15                       # how much of the kerf the bar fills
CONTACT_DET_H  = 2 * LH                     # 0.40, the bar's height

def prot_phantom():
    """The optional protection strip, so its fit is measured rather than asserted in words."""
    return bx(PROT_CX - PROT_L/2, PROT_CX + PROT_L/2, PROT_Y1 - PROT_W, PROT_Y1,
              CAV_Z0, CAV_Z0 + PROT_T)

def tp4056_phantom():
    """The module that NO LONGER FITS. Kept so check 13 can prove that, not just claim it."""
    return bx(PROT_CX - TP_W/2, PROT_CX + TP_W/2, BAY_Y1 - 1.00 - TP_L, BAY_Y1 - 1.00,
              CAV_Z0, CAV_Z0 + TP_H)
# ---- THE ONE SCREW.  At the bottom edge, where the hand is. ----
#
# ⚠️ ITS PILOT IS THE INTERESTING PART. At y~19 the midframe is only its 2.60 floor, and a
# blind 2.60 pilot cannot hold a cover. A boss on the compartment side would stand proud of the
# bed face -- the defect ember_case.py:2771 records on both shell parts in one session. So the
# boss grows the OTHER way, UP into the board cavity, where standing proud costs nothing.
# Whether it fits is not something to reason about: the STEP clearance boolean measures it.
# ⚠️ y WAS 19.20 AND THE d5.80 COUNTERBORE BROKE OUT THROUGH THE COVER'S BOTTOM EDGE.
# At 19.20 the counterbore spans y 16.30..22.10 against a part that starts at COVER_Y0 = 18.00,
# so 1.70mm of it was off the end: the "hole" was a notch in the outline and the head had no
# annular seat on its low-Y side. EVERY NUMERIC CHECK PASSED -- the screw still had 3.20mm of
# engagement, the pilot still cleared the board, the seal ring was still 100% solid. It was
# visible immediately in a slice of the finished mesh and invisible in the arithmetic, which is
# verification.md's "prefer measuring the artifact to reasoning about the source", earned again.
# Check 11b now measures the edge distance so the next move of this screw is caught in code.
#
# ⚠️ AND 21.50 WAS STILL TOO CLOSE, for a second reason the first fix did not cover. At 21.50
# the counterbore clears the outline by 0.60 -- but the bed face carries a 0.80 CHAMFER, and a
# chamfer that runs into a hole 0.60 away cannot produce a valid face. OCC threw
# StdFail_NotDone from inside chamfer_outline(). So the edge distance owes the counterbore's own
# radius AND the chamfer AND margin, and the assert lives at MODULE level below rather than in
# the check suite, because the check suite runs after the geometry that would already have died.
SCREW_EDGE_MIN  = CBORE_D/2 + CHAMFER + 0.50            # 4.20
SCREW_XY        = (25.00, COVER_Y0 + SCREW_EDGE_MIN + 0.40)     # y = 22.60
# ⚠️ 7.00 WAS TOO SMALL, and the reason is worth stating because it is not obvious from the
# section: CBORE_DEPTH is 3.00 and COV_WALL is only 2.20, so THE COUNTERBORE IS DEEPER THAN THE
# WALL IT IS SUNK IN. Its floor lands 0.80 above CAV_Z0 -- inside the compartment -- which means
# the head does not bear on the outer wall at all, it bears on this boss. At d7.00 that gave
# (7.00-5.80)/2 = 0.60mm of annulus against ember_case's BOSS_MIN_ANN of 1.00, i.e. under the
# family's own floor for exactly this measurement. The seat probe read 86.9% and found it.
SCREW_BOSS_D    = 9.00                                  # (9.00-5.80)/2 = 1.60 of annulus
SCREW_BOSS_H    = 4.00                                  # CAV_FLOOR -7.10 -> -3.10, PCB is -1.60
MOB_SCREW_LEN   = 22.00                                 # M3 x 0.5 x 22 ISO 4762, under-head
MOB_PILOT_DEPTH = (BACK_Z - CAV_FLOOR) * -1 + SCREW_BOSS_H   # 2.60 floor + 4.00 boss = 6.60
# MODULE-LEVEL, so it cannot be outrun by the geometry it constrains.
for _e, _d in (("cover bottom edge", SCREW_XY[1] - COVER_Y0),
               ("cover top edge",    MOB_OY1 - SCREW_XY[1]),
               ("cover -X edge",     SCREW_XY[0] - OX0),
               ("cover +X edge",     OX1 - SCREW_XY[0])):
    assert _d >= SCREW_EDGE_MIN, (
        f"the d{CBORE_D} counterbore at {SCREW_XY} is {_d:.2f}mm from the {_e}, under the "
        f"{SCREW_EDGE_MIN:.2f} it needs (its own radius + the {CHAMFER} bed chamfer + margin). "
        f"Too close and it is a notch in the outline; closer still and the chamfer will not "
        f"build at all")
assert (19.20 - COVER_Y0) < SCREW_EDGE_MIN and (21.50 - COVER_Y0) < SCREW_EDGE_MIN, (
    "control failed: the two rejected screw positions (19.20 notched the outline, 21.50 killed "
    "the chamfer) both read as having adequate edge distance")
# and the boss must not run into the seal rim's wall on its way back
assert SCREW_XY[1] + SCREW_BOSS_D/2 <= RIM_Y0 - RIM_WALL + 1e-9, (
    f"the screw boss reaches y={SCREW_XY[1] + SCREW_BOSS_D/2:.2f}, past the retention strip's "
    f"end at {RIM_Y0 - RIM_WALL:.2f} -- it would foul the seal rim's low-Y wall")
# ---- cell lead pass into the board cavity, landing on CONN_L[0] = BAT ----
#
# BAT is a 1.25mm JST 2P on the SAME LONG EDGE as UART -- docs/enclosure.md:160 ("...BAT (2P),
# UART (4P)") and :213 ("all four 1.25 mm JST positions"), which agrees with ember_case's
# CONN_L labelling. So the bay-to-board lead is a JST 1.25 2P pigtail leaving the cell's
# contacts, up through this pass, to CONN_L[0] on the x=0 edge. The cell lane is deliberately
# on that side: it is the shortest possible route.
# ⚠️ MOVED INBOARD 1.25 FOR THE -X DOVETAIL, 2026-08-01. It used to start at OX0 + COV_WALL -
# 0.40 = -1.15, i.e. 0.40 INSIDE the cover's wall footprint, for no stated reason -- the pass is
# a slot in the midframe's FLOOR and the pigtail leaves the bay well inboard of the wall. The
# dovetail groove needs u <= WALL of that wall unbroken over y 18.60..85.25, and at -1.15 this
# slot punched straight through it for 6.50mm of that run. Same width, same Y, shifted to clear
# the groove's inboard face (u = 2.60, x = -0.35) by 0.45. Check 8f measures the gap.
LEAD_X0, LEAD_X1 = 0.10, 3.75
LEAD_Y0, LEAD_Y1 = 20.00, 26.50

# ============================================================================
# 5b. CHARGING.  ONBOARD, AND THAT ANSWERS THE QUESTION THIS FILE ONCE ASKED.
# ============================================================================
#
# >>> THE BOARD CHARGES THE CELL ITSELF.  NO EXTRA HARDWARE IS REQUIRED. <<<
#
# docs/enclosure.md:165 (a verified-vs-inferred audited section): "Battery input is 3.7 V LiPo,
# charging at 290 mA actual / 500 mA max."  Corroborated independently, with the mechanism, by
# an earlier investigation -- scratch/hosyond-s3/battery.md, morpheus-battery 2026-07-30:
# "the board's TP4054 charges at a fixed 290 mA (R12 = 3.3 kOhm), there is no boost".
# 290 mA is attested twice; the TP4054/R12 detail is single-source, so it is cited as such.
#
# TWO CONSEQUENCES THAT ARE NOT ABOUT GEOMETRY BUT BELONG NEXT TO THE CELL:
#
#   1. NO PROTECTION CIRCUIT ON THE BOARD. ⚠️ THIS PARAGRAPH SAID "so a PROTECTED cell is
#      mandatory ... this case is 9.55mm longer than a bare-cell design would be" UNTIL
#      2026-08-01, WHICH CONTRADICTED SECTION 3 OF THIS SAME FILE. JP reversed to bare flat-tops
#      only ("no protected tops"), the bay was re-primaried to CELL_L_MAX = 65.50, and the case
#      got 5.90mm SHORTER rather than 9.55 longer. The electrical conclusion did not go away, it
#      MOVED: with bare cells the missing protection is carried by the 1S DW01 strip in section
#      5f, which is required equipment for exactly this reason. Two statements of the same fact,
#      and the stale one was still asserting the opposite design.
#   2. NO BOOST. On battery, +5 becomes the raw cell, and battery.md's finding is that the
#      device "browns out rather than shutting down". The strip's own cut-off is now what stops
#      the cell going to zero afterwards. Either way there is no graceful low-battery shutdown,
#      which is a firmware question and is flagged in the issue, not solved here.
#
# CHARGE TIME. Recomputed rather than inherited, using battery.md's own method so the two are
# comparable: it quotes 2000 mAh -> 9.3 h, i.e. C/I x 1.35 (6.90 h of CC plus a CV tail).
# Applying the same 1.35 to a 3400 mAh protected cell at 290 mA gives 11.72 x 1.35 = ~15.8 h.
# Overnight, and worth stating so nobody files it as a fault later.
CHARGE_MA        = 290.0        # docs/enclosure.md:165, "actual" (500 max)
CHARGE_CV_FACTOR = 1.35         # battery.md's implied CC/CV factor, reused for comparability
CELL_CAPACITY_MAH = 3400.0      # a typical protected 18650
# ---- negative-lead groove down the divider's cell-facing face ----
WGROOVE_D, WGROOVE_Z = 1.00, 27 * LH   # 5.40 deep in Z: widened from 3.20 so a FLAT 5mm nickel
                                       # tab lies in it instead of a round wire

# ============================================================================
# 5d. THE CELL-BAY FAILURE VENT.  A LABYRINTH FOLDED INSIDE A 2.20 WALL.
# ============================================================================
#
# A Li-ion cell in a sealed plastic box is the one thing in this design that can hurt someone,
# and "the compartment is not sealed to the board cavity" was too weak an answer. The bay now
# has a DELIBERATE path to outside air, and the enclosure is not the restriction:
#
#   ASSUMPTION, STATED BECAUSE IT SETS THE TARGET: an 18650's positive cap carries 3-4 vent
#   ports; taking 3 x d2.0mm gives ~9.42 mm2. That is general cell construction, not a
#   datasheet I hold -- if JP has real numbers, VENT_N is the knob.
#
# ⚠️ AND IT MUST NOT BE A HOLE. A straight slot through the wall is a light and dust path into
# the bay, and it is also the easy mistake to make while "adding a vent". So the path is folded
# INSIDE the 2.20 wall: cut VENT_D from the inside at one Y, VENT_D from the outside at a
# different Y, and let the two overlap in depth to leave a connecting band. Gas turns twice; a
# straight line finds 0.80mm of skin. Check 16 probes for exactly that, with a control that
# drills the wall through and proves the probe can see it.
#
#   band width = 2*VENT_D - COV_WALL = 0.60, which is SLOT_W -- this repo's proven void at a
#   0.4 nozzle with gap-closing set to 0 (PRINT-SHEET). Not a number picked for the vent.
#
# Every cut runs its long axis along model Z, which is the PRINT Z once the cover is on its bed
# face: these are vertical slots, self-supporting, with no bridge anywhere. That is why the vent
# is in a side wall and not the floor.
VENT_N     = 4
VENT_W     = 2.00       # slot width in Y
VENT_RIB   = 1.20       # material between a unit's inner and outer slot -- forces the turn
VENT_GAP   = 1.60       # material between units
VENT_PITCH = 2*VENT_W + VENT_RIB + VENT_GAP             # 6.80
VENT_D     = 7 * LH                                     # 1.40 from each face
VENT_BAND  = 2*VENT_D - COV_WALL                        # 0.60
VENT_SKIN  = COV_WALL - VENT_D                          # 0.80 left standing at each face
VENT_Y0    = 30.00                                      # clear of every retention feature
CELL_PORTS_MM2 = 3 * math.pi * (2.0/2)**2               # 9.42, the assumption above

def _vent_units():
    """(inner slot y, outer slot y, band y) for each labyrinth unit."""
    out = []
    for i in range(VENT_N):
        iy0 = VENT_Y0 + i*VENT_PITCH
        oy0 = iy0 + VENT_W + VENT_RIB
        out.append(((iy0, iy0+VENT_W), (oy0, oy0+VENT_W), (iy0, oy0+VENT_W)))
    return out
VENT_Z0 = CELL_AXIS_Z + 1.00                            # -18.50, above the cradle's tangent
VENT_Z1 = BACK_Z - 1.80                                 # -11.50, below the mating plane

# ============================================================================
# 5e. THE WS2812 GLOW WINDOW.  LIGHT DOES NOT NEED LINE OF SIGHT.
# ============================================================================
#
# Check 14 proves there is no straight path from the LED to anywhere useful: it sits inside the
# driver's footprint and the driver cannot be moved off it. That conclusion stands and is still
# asserted. It is also the wrong question, because a diffuse pocket does not need one.
#
# >>> THE POCKET THE LED FIRES INTO IS THE BOARD CAVITY, AND IT REACHES BOTH SIDE WALLS. <<<
#
# The proof is already in the part: side_channels() cuts its openings at z CAV_FLOOR..PCB_BOT --
# EXACTLY the cavity's own Z band. Those holes could not exist unless the cavity touched the
# walls there. So the light path is LED -> cavity -> a thinned patch of side wall, one bounce,
# no pipe and no extra parts. That is the decision rule's option A, and B is not needed.
#
# ⚠️ A LIGHT PIPE WAS EVALUATED AND REJECTED ON BEND COUNT. The only bore that starts at the LED
# runs -Z into the sealed speaker cavity and hits the driver's back 2.60mm later. Getting out
# means: turn 90deg into the 2.60 floor (which a d2.0 bore leaves 0.30 of wall either side of),
# run ~10mm to x<18.85, turn 90deg down into the cell compartment, then turn again to an exterior
# face. THREE hard corners, and the brief's own rule is that two or more loses most of the light.
#
# THE SITE IS SOLVED, NOT TYPED. The LED's own Y (45.60) lands inside a cable channel on BOTH
# walls, so "put the window at the LED" is not available. _glow_site() searches the solid spans
# between channels for the nearest one that can hold the window -- so if a connector moves, the
# window follows instead of quietly landing in a hole.
GLOW_N        = 2
# ⚠️ PINNED, not shared. This WAS `HEX_R` ("same cell as the grille") until the stand's
# grille re-parameterized 4.50 -> 4.75 AF for printable webs (#47) and this window --
# in a DIFFERENT PART -- silently inherited the change and stopped fitting its 5.50
# cavity band (assert below fired at 4.75 > 4.70; the export gate refused the STL).
# A window's size is set by the band it lives in, not by another part's lattice. The
# motif survives: same shape, same orientation, 0.25 finer than the new grille.
GLOW_R        = 4.50 / math.sqrt(3)                     # AF exactly 4.50, this part's own
GLOW_AF       = math.sqrt(3) * GLOW_R                   # 4.50 across flats -> the Z extent
GLOW_AC       = 2 * GLOW_R                              # 5.196 across corners -> the Y extent
# ⚠️ PINNED FOR THE SAME REASON GLOW_R IS, AND THE FIRST FIX ONLY DID HALF THE JOB. This was
# `HEX_WEB` until 2026-08-01 -- so when #47 took the stand's grille web 0.90 -> 1.25 for
# printable webs, THIS WINDOW, IN A DIFFERENT PART, silently followed it and GLOW_SPAN_Y went
# 11.29 -> 11.64. The GLOW_R pin above caught the radius and left the web behind, which is the
# tell that a cross-part coupling has to be broken everywhere at once or not at all. A window's
# web is set by the wall it lives in, not by another part's lattice. Designed value, restated.
GLOW_WEB      = 0.90                                    # this part's own, = the repo's print floor
GLOW_EDGE     = 1.20                                    # material left at each end of the span
# ⚠️ NOT A LAYER COUNT. This membrane's thickness runs along X -- it is a VERTICAL wall in the
# print, so the criterion is extrusion width, not layer height: 0.80 is exactly two passes of a
# 0.40 nozzle. (Compare BEZ_WEB 0.70, which the file records as 1.75 extrusions printing as one
# wide bead -- acceptable on a decorative face but not for something that must stay closed.)
GLOW_MEMBRANE = 2 * 0.40                                # 0.80
GLOW_SPAN_Y   = GLOW_N * GLOW_AC + (GLOW_N - 1) * GLOW_WEB          # 11.29

def _solid_spans(chans, lo=0.0, hi=E.BL):
    """Y ranges on a side wall with NO channel cut through them."""
    out, c = [], lo
    for a, b in sorted(chans):
        if a - c > 0.5:
            out.append((c, a))
        c = max(c, b)
    if hi - c > 0.5:
        out.append((c, hi))
    return out

def _glow_site():
    """(wall, centre y, straight-line distance from the LED) — the nearest usable solid span."""
    need = GLOW_SPAN_Y + 2 * GLOW_EDGE
    best = None
    for wall, chans, wx in (("hi", MOB_CH_HI, E.BW + E.FIT), ("lo", MOB_CH_LO, -E.FIT)):
        for (a, b) in _solid_spans(chans):
            if (b - a) < need:
                continue
            cy = min(max(E.LED[1], a + need/2), b - need/2)      # as near the LED as it fits
            d = math.hypot(wx - E.LED[0], cy - E.LED[1])
            if best is None or d < best[2]:
                best = (wall, cy, d)
    assert best is not None, (
        f"no solid span on either side wall can hold a {need:.2f}mm glow window -- every gap "
        f"between cable channels is too narrow. Reduce GLOW_N or fall back to a light pipe")
    return best
GLOW_WALL, GLOW_CY, GLOW_DIST = _glow_site()
# >>> AND THE SITE IS RECORDED, BECAUSE A SOLVED FEATURE THAT MOVES IN SILENCE IS A DEFECT <<<
# >>> EVEN WHEN THE MOVE IS AN IMPROVEMENT.  THIS IS #47's SHAPE, SECOND APPEARANCE.       <<<
#
# _glow_site() searches the solid spans BETWEEN flank openings, so it is a function of features
# that have nothing to do with it. Suppressing SPK's opening on this variant merged two spans on
# the +X wall and the solver promptly relocated the window by 12.30mm -- into the space that
# channel used to occupy, and 6.86mm CLOSER to the LED. Nobody asked for that and nothing would
# have reported it: the first time this shape appeared (#47, GLOW_R inheriting the stand's
# lattice) it was caught only because an unrelated assert happened to fire.
#
# So the site is pinned to an EXPECTATION rather than merely computed. Moving it is allowed --
# it is a solver, that is the point -- but moving it now costs one deliberate line, and the
# build says where it went either way.
#
# ⚠️ luna's independent simulation of the same block put this at cy 36.82 / 23.1mm, and the
# 0.17 difference is not noise -- it is the GLOW_WEB pin three sections up. At the inherited
# HEX_WEB of 1.25 the span needs 14.04 and clamps to 36.82; at this part's own pinned 0.90 it
# needs 13.69 and clamps to 36.99. Two defects in the same feature, and fixing one moved the
# other. Recorded because that is the kind of interaction a single figure hides.
GLOW_SITE_EXPECT = ("hi", 36.99, 23.02)     # (wall, centre y, straight-line distance to the LED)
assert (GLOW_WALL == GLOW_SITE_EXPECT[0]
        and abs(GLOW_CY - GLOW_SITE_EXPECT[1]) < 0.05
        and abs(GLOW_DIST - GLOW_SITE_EXPECT[2]) < 0.05), (
    f"the WS2812 window has RELOCATED: solved to ({GLOW_WALL}, cy {GLOW_CY:.2f}, "
    f"{GLOW_DIST:.2f}mm from the LED) against a recorded ({GLOW_SITE_EXPECT[0]}, cy "
    f"{GLOW_SITE_EXPECT[1]:.2f}, {GLOW_SITE_EXPECT[2]:.2f}). Something changed the solid spans "
    f"this searches -- a flank opening, a connector table, GLOW_WEB, GLOW_N. The move may well "
    f"be right; update GLOW_SITE_EXPECT deliberately and re-render the figures that name it")
GLOW_CZ = (CAV_FLOOR + E.PCB_BOT) / 2                   # centred in the cavity band, derived
assert GLOW_AF <= (E.PCB_BOT - CAV_FLOOR) - 0.80, (
    f"the {GLOW_AF:.2f}mm-tall window does not fit the "
    f"{E.PCB_BOT-CAV_FLOOR:.2f}mm cavity band with margin")


# ============================================================================
# 6. PARTS
# ============================================================================
def _brow():
    """The solid block above OY1 that closes the cell bore's ceiling.

    SOLID IN THE MODEL ON PURPOSE, per the plinth precedent in PRINT-SHEET: "Set infill by
    the SLICER, not by hollowing the CAD." A hollowed brow would put a ~50mm bridge over its
    own void on a part that has no other bridge worth mentioning.

    It earns its place three times: it is the cell bore's lid over the spring end, it is
    solid material for the cover screw's pilot, and it keeps the silhouette from stepping
    twice.
    """
    # ⚠️ THE OVERLAP IS DERIVED, NOT DECORATIVE. RectangleRounded refuses height <= 2*radius,
    # and the brow's own extent (MOB_OY1 - BROW_Y0 = 9.55) is under 2*OUT_R = 12.90. So the
    # rounded profile is built tall enough to be legal and the surplus -- which carries the
    # low-Y rounded corners -- is trimmed away, leaving a square butt against back_shell.
    _ovl = 2 * OUT_R + 2.0                              # 14.90
    p = rbox(OX0, OX1, BROW_Y0 - _ovl, MOB_OY1, BACK_Z, SEAM_Z, OUT_R)
    assert (MOB_OY1 - (BROW_Y0 - _ovl)) > 2 * OUT_R, "brow profile is still degenerate"
    # trim the overlap back to a clean butt against back_shell's top wall
    p -= bx(OX0-1, OX1+1, OY0-1, BROW_Y0, BACK_Z-1, SEAM_Z+1)
    # Chamfer only the brow's OWN exposed bed-side outline. The seam face at y=BROW_Y0
    # disappears into back_shell and must not be chamfered, so the selector excludes it --
    # this is E.chamfer_outline's "touching the silhouette" rule with min-Y removed.
    bb = p.bounding_box()
    sel = [e for e in p.edges()
           if abs(e.bounding_box().min.Z - BACK_Z) < 1e-6
           and abs(e.bounding_box().max.Z - BACK_Z) < 1e-6
           and (e.bounding_box().max.X > bb.max.X - 1e-6
                or e.bounding_box().min.X < bb.min.X + 1e-6
                or e.bounding_box().max.Y > bb.max.Y - 1e-6)]
    assert sel, "brow: no bed-side perimeter edge selected -- an absent chamfer is silent"
    return chamfer(sel, length=CHAMFER)


def _plateau_region():
    """Footprint the midframe's back face must be SOLID over, for the seal to be a seal.

    ⚠️ CLAMPED INBOARD OF THE OUTLINE, AND THAT CLAMP IS A BUG FIX. The first version ran to
    RIM_X1 + PLATEAU_MARGIN = 52.75 against an OX1 of 52.95, and the bed-side chamfer starts at
    52.15 -- so the plateau, a plain box with no chamfer of its own, SILENTLY RE-SQUARED 39.65mm
    of the shell's high-X bed edge. PRINT-SHEET calls those chamfers functional, not cosmetic:
    "a chamfer there absorbs elephant's foot", and the Z-offset here runs deliberately squished
    at -2.14.

    Nothing was looking for this. It surfaced because the seal probe reports its four legs
    separately, the high-X leg alone read 99.36%, and a slice of the committed STL showed the
    chamfer's sloping edge surviving ONLY at y<28.00, y>76.80 and inside the speaker relief's
    notch -- i.e. exactly where the plateau was not. The 0.457mm2 the probe called a leak was
    the last unfilled scrap of the chamfer it had eaten everywhere else.

    Stopping at OX1 - WALL also costs nothing: past HEX_FIELD_X1 = 41 there are no vent cells to
    fill, and the bond area and the labels under the driver both end well inboard of 50.35.
    """
    return (RIM_X0 - PLATEAU_MARGIN, min(RIM_X1 + PLATEAU_MARGIN, OX1 - WALL),
            RIM_Y0 - PLATEAU_MARGIN, min(RIM_Y1 + PLATEAU_MARGIN, MOB_OY1 - WALL))


def midframe():
    """back_shell() plus the mobile additions. Composition, not a fork.

    Nothing here edits ember_case.py. The board pocket, the four bosses and counterbores,
    the side channels, the SD slit, the printed-in-place caps, the SPK relief and every
    label come through unchanged and unre-derived.
    """
    p = E.back_shell("mobile")
    p += _brow()

    # ---- BOND PLATEAU: refill the vent hexes under and around the seal rim ----
    # The rim must land on continuous material or the "sealed" cavity vents straight into the
    # board cavity through a honeycomb. This ADDS material flush to BACK_Z; it never stands
    # proud of the bed face.
    px0, px1, py0, py1 = _plateau_region()
    plate = bx(px0, px1, py0, py1, BACK_Z, CAV_FLOOR)
    # ...but NOT over the speaker relief, which is the wire's only way out of the cavity.
    plate -= bx(E.SPK_RELIEF_X0 - 1.0, OX1 + 1.0,
                E.SPK_RELIEF_Y[0], E.SPK_RELIEF_Y[1], BACK_Z - 1, CAV_FLOOR + 1)
    p += plate

    # ---- DRIVER LOCATING GROOVE. A thin outline, not a pocket: the tape needs a flat,
    # continuous bond and a pocket leaves it bridging a step (ember_case.py:1673).
    gw, gh = DRIVER_H + 2*DRIVER_CLR, DRIVER_W + 2*DRIVER_CLR
    outer = rbox(DRV_CX-gw/2, DRV_CX+gw/2, DRV_CY-gh/2, DRV_CY+gh/2,
                 BACK_Z, BACK_Z + LIP_DEPTH, DRIVER_R + DRIVER_CLR)
    inner = rbox(DRV_CX-gw/2+LIP_WIDTH, DRV_CX+gw/2-LIP_WIDTH,
                 DRV_CY-gh/2+LIP_WIDTH, DRV_CY+gh/2-LIP_WIDTH,
                 BACK_Z - 1, BACK_Z + LIP_DEPTH + 1, max(DRIVER_R + DRIVER_CLR - LIP_WIDTH, 0.5))
    p -= (outer - inner)

    # ---- CELL LEAD PASS -> CONN_L[0] (BAT) ----
    p -= bx(LEAD_X0, LEAD_X1, LEAD_Y0, LEAD_Y1, BACK_Z - 1, CAV_FLOOR + 1)

    # ---- DOVETAIL GROOVES: one constant-section slot per rail, with a full-width drop-in
    # pocket one travel-length behind each of the cover's flared teeth. The shoulder left
    # between the pockets is what the cover hangs from, and it is SOLID MATERIAL STANDING ON
    # THE BED -- not a lip under a bridged void, which is what this replaced.
    for _side, _y0, _y1 in DT_RAILS:
        p -= _dt_prism(DT_P_GROOVE, _side, _y0, _y1 + DT_CLR_Y)
        for _ty in _dt_teeth(_y0, _y1):
            p -= _dt_prism(DT_P_POCKET, _side,
                           _ty - DT_TRAVEL - DT_CLR_Y, _ty - DT_CLR_Y)

    # ---- THE ONE SCREW: boss UP into the board cavity, pilot down through it ----
    p += cyl(SCREW_XY[0], SCREW_XY[1], CAV_FLOOR, CAV_FLOOR + SCREW_BOSS_H, SCREW_BOSS_D)
    p -= cyl(SCREW_XY[0], SCREW_XY[1], BACK_Z, BACK_Z + MOB_PILOT_DEPTH, PILOT_D)

    # ---- WS2812 GLOW WINDOW: hex cells cut into the side wall's INNER face, leaving a
    # GLOW_MEMBRANE skin at the exterior. Cutting from the inside keeps the outer face flat and
    # unbroken -- the hexes are invisible until lit -- and puts the membrane flush with the
    # outside rather than at the bottom of a recess that would shadow it.
    #
    # rotation=30 is load-bearing here for a DIFFERENT reason than in the lattice: it puts the
    # hex's FLATS on +/-Z, so the window is GLOW_AF (4.50) tall and fits the cavity band. Flat-top
    # would need GLOW_AC (5.196) in Z and would not fit with margin.
    _wx = (E.BW + E.FIT) if GLOW_WALL == "hi" else -E.FIT       # inner face of the chosen wall
    _depth = WALL - GLOW_MEMBRANE                               # 1.80 cut, 0.80 skin left
    _x0 = _wx if GLOW_WALL == "hi" else _wx - _depth
    for _i in range(GLOW_N):
        _cy = GLOW_CY - GLOW_SPAN_Y/2 + GLOW_AC/2 + _i * (GLOW_AC + GLOW_WEB)
        p -= Pos(_x0, _cy, GLOW_CZ) * (
            Rot(0, 90, 0) * extrude(RegularPolygon(GLOW_R, 6, rotation=30), _depth))
    return p


def back_cover():
    """The cell + speaker cover. Prints OUTER FACE DOWN.

    Bed face = the outer face at COVER_Z0. Everything cut into it goes INWARD (the grille is
    through-holes, the screw counterbore is a recess); nothing stands proud of it. The cell
    trough opens upward as a concave cradle and the grille cells are vertical prisms, so the
    whole part is self-supporting with no bridge worth naming.
    """
    p = rbox(OX0, OX1, OY0, MOB_OY1, COVER_Z0, BACK_Z, OUT_R)
    # the chin belongs to the midframe -- cut the cover back to COVER_Y0
    p -= bx(OX0 - 1, OX1 + 1, OY0 - 1, COVER_Y0, COVER_Z0 - 1, BACK_Z + 1)

    # ---- ONE interior void for the whole compartment. Its floor at CAV_Z0 is simultaneously
    # the baffle's inner face and the cell bore's floor, which is why CAV_Z0 exists.
    p -= rbox(OX0 + COV_WALL, OX1 - COV_WALL, BAY_Y0, BAY_Y1,
              CAV_Z0, BACK_Z + 1, max(OUT_R - COV_WALL, 1.0))
    # ⚠️ AND SQUARE OFF THE LOW-Y END. rbox rounds all four corners with one radius, which is
    # right at the case's real corners up at MOB_OY1 and WRONG here: the bay's low-Y boundary is
    # a straight internal wall, and the 4.25 fillet left a sliver of material projecting into
    # the cell bore. The cell-vs-cradle boolean caught it at 13.107 mm3 -- an interference that
    # no part-vs-part or part-vs-board check could ever have seen, because the object it
    # collides with is not in any STL.
    p -= bx(OX0 + COV_WALL, OX1 - COV_WALL, BAY_Y0, BAY_Y0 + OUT_R, CAV_Z0, BACK_Z + 1)

    # ---- CRADLE: put the flat floor back as a half-cylinder so the cell self-centres.
    # Added material whose top surface is the bore, i.e. two lobes rising from the floor --
    # concave, self-supporting, no overhang anywhere.
    p += (bx(CELL_X0, CELL_X1, BAY_Y0, BAY_Y1, CAV_Z0, CELL_AXIS_Z)
          - cyl_y(CELL_AXIS_X, CELL_AXIS_Z, CELL_BORE_D, BAY_Y0 - 1, BAY_Y1 + 1))

    # ---- THE SHARED DIVIDER. One wall doing two jobs: the cell trough's inboard wall and
    # the seal rim's inboard wall. Two separate walls do not fit in the X budget (see
    # COV_WALL) and check 3 asserts the budget stays closed.
    p += bx(CELL_X1, RIM_X0, BAY_Y0, BAY_Y1, CAV_Z0, BACK_Z)
    # ---- the rim's two genuinely new sides; the other two are the divider and the case wall
    p += bx(RIM_X0, RIM_X1, RIM_Y1, RIM_Y1 + RIM_WALL, CAV_Z0, BACK_Z)
    p += bx(RIM_X0, RIM_X1, RIM_Y0 - RIM_WALL, RIM_Y0, CAV_Z0, BACK_Z)

    # ---- LOCAL THICKENING FOR THE SCREW. A d3.30 bore does not fit inside a 2.20 wall: at
    # y=SCREW_XY[1] the bore's extremes fall outside the wall on both sides and it is a notch,
    # not a hole. The boss grows +Y into the retention strip, which is open compartment.
    # ...and it runs all the way back to the rim's low-Y wall so the two tie together.
    p += bx(SCREW_XY[0] - SCREW_BOSS_D/2, SCREW_XY[0] + SCREW_BOSS_D/2,
            COVER_Y0, RIM_Y0 - RIM_WALL, CAV_Z0, BACK_Z)

    # ---- NEGATIVE-LEAD GROOVE, down the divider's cell-facing face at the top corner,
    # where the cell's curve has already fallen away.
    p -= bx(CELL_X1 - WGROOVE_D, CELL_X1, BAY_Y0, BAY_Y1, BACK_Z - WGROOVE_Z, BACK_Z)

    # ---- THE "+" CONTACT: ONE KERF, doing three jobs (see 5g) ----
    # A bare flat-top's +ve face is the plain can end, so the plate must be reachable by a flat
    # surface — but "flush" was never an answer to "held by WHAT". The slot below is the plate's
    # seat, the throat it is inserted through, and the lane its tab leaves by, in one cut,
    # because all three want the same 0.35 of depth in the same wall. Open to BACK_Z: vertical
    # walls, no roof, nothing bridged. It runs to CELL_X1 so the tab meets the divider's wire
    # groove (which starts at BAY_Y0, where this stops) without a second feature.
    p -= bx(CELL_AXIS_X - CONTACT_W/2, CELL_X1,
            CELL_TIP_Y - CONTACT_KERF, CELL_TIP_Y,
            CONTACT_Z0, BACK_Z)
    # ...and the detent bar, left standing across the BACK of the kerf just above the seated
    # plate. Adding it back after the cut keeps one source for the kerf's own depth.
    p += bx(CELL_AXIS_X - CONTACT_W/2, CELL_AXIS_X + CONTACT_W/2,
            CELL_TIP_Y - CONTACT_KERF, CELL_TIP_Y - CONTACT_KERF + CONTACT_DETENT,
            CONTACT_Z1, CONTACT_Z1 + CONTACT_DET_H)

    # ---- POLARITY MARKINGS, debossed into the two end walls, facing into the bore ----
    # Rot(-90,0,0) sends sketch +v to world -Z; both glyphs are vertically symmetric so the
    # flip is harmless here — noted because it is NOT harmless for lettering.
    # ⚠️ THE "-" IS CUT AFTER THE TUNNEL BLOCK BELOW, not here, because it is debossed INTO
    # that block's mouth face and the block does not exist yet. Cutting it here would remove
    # nothing and the check would find a marking that was never made -- which check 15 would
    # catch, but only after a 15-minute build.
    _sk_p = E._label_sketch(MARK_PATHS_P, E.LABEL_W)
    _mx, _mz, _my0, _my1 = _mark_face("+")
    p -= Pos(_mx, _my0, _mz) * (Rot(-90, 0, 0) * extrude(_sk_p, MARK_DEPTH))

    # ---- THE SPRING TUNNEL: the last SPRING_TUN_L of the bay closes over (see 5g) ----
    # A block across the cell lane, then a GABLED bore through it. The block is supported off
    # the cavity floor the whole way; the bore's roof is two 45-degree faces meeting at a
    # ridge, so there is no crown to droop. The old d9.00 scallop this replaces was a round
    # horizontal bore -- flat at its crown over 9mm, which is the hooks' defect in miniature.
    _sc = SPRING_BORE / 2
    p += bx(CELL_X0, CELL_X1 - WGROOVE_D, SPRING_TUN_Y0, BAY_Y1,
            CAV_Z0, SPRING_TUN_TOP)
    p -= _yprism(((CELL_AXIS_X - _sc, CELL_AXIS_Z - _sc),
                  (CELL_AXIS_X + _sc, CELL_AXIS_Z - _sc),
                  (CELL_AXIS_X + _sc, CELL_AXIS_Z + SPRING_GABLE_Z),   # straight to here...
                  (CELL_AXIS_X,       CELL_AXIS_Z + SPRING_APEX_Z),    # ...then 45 deg to a ridge
                  (CELL_AXIS_X - _sc, CELL_AXIS_Z + SPRING_GABLE_Z)),
                 SPRING_TUN_Y0 - 1.0, BAY_Y1)
    # ...and the -ve tab's way out of the closed bore: a vertical slot up through the cap.
    # Vertical walls, open at the top, and it clears the "-" marking, which is on the END WALL
    # beyond BAY_Y1 rather than on this block.
    p -= bx(CELL_AXIS_X - SPRING_TAB_W/2, CELL_AXIS_X + SPRING_TAB_W/2,
            SPRING_TUN_Y0, BAY_Y1, CELL_AXIS_Z, SPRING_TUN_TOP + 1.0)
    # ---- "-" ON THE TUNNEL'S MOUTH FACE, beside the bore. See _mark_face(). ----
    _sk_n = E._label_sketch(MARK_PATHS_N, E.LABEL_W)
    _nx, _nz, _ny0, _ny1 = _mark_face("-")
    p -= Pos(_nx, _ny0, _nz) * (Rot(-90, 0, 0) * extrude(_sk_n, MARK_DEPTH))

    # ---- THE FAILURE VENT: VENT_N labyrinth units through the cell lane's -X wall ----
    for (iy0, iy1), (oy0, oy1), (by0, by1) in _vent_units():
        p -= bx(CELL_X0 - VENT_D, CELL_X0, iy0, iy1, VENT_Z0, VENT_Z1)      # in, from the bay
        p -= bx(OX0, OX0 + VENT_D, oy0, oy1, VENT_Z0, VENT_Z1)              # out, to the air
        p -= bx(OX0 + VENT_D - VENT_BAND, OX0 + VENT_D, by0, by1,
                VENT_Z0, VENT_Z1)                                           # the connecting band

    # ---- GRILLE. E._hex_panel is the SAME lattice maths as the stand's _hex_field: pass
    # aflat = sqrt(3)*HEX_R and dx, dy and R all evaluate identically. It is reused rather
    # than reimplemented because rotation=30 is load-bearing there (without it the field is
    # one hole with loose prisms in it) and a second copy would be free to lose it.
    global GRILLE_CELL_N
    # ⚠️ THE FIELD IS CLIPPED, AND THE FIRST VERSION WAS NOT.  _hex_panel keeps only cells
    # WHOLLY inside its rectangle, which is the safe behaviour it was written for and the wrong
    # behaviour here: it discarded every boundary cell and the measured throat came out at
    # 438.4 mm2 against a 946.6 mm2 field -- 46%, where the stand runs at ~70%. The claim that
    # the mobile throat was "identical by construction" was FALSE AS BUILT, and only the raster
    # said so; the lattice constants were identical the whole time.
    #
    # So: build over a rectangle enlarged by one pitch, then intersect with the field's rounded
    # rect. That is exactly what the stand does, and it inherits the stand's hazard too -- a
    # clipped cell can leave a sliver -- so the minimum surviving opening is measured below.
    _fx0, _fx1 = DRV_CX - GRILLE_FW/2, DRV_CX + GRILLE_FW/2
    _fy0, _fy1 = DRV_CY - GRILLE_FH/2, DRV_CY + GRILLE_FH/2
    _fr = max(DRIVER_R - GRILLE_INSET, 0.8)
    _pad = math.sqrt(3) * HEX_R + HEX_WEB
    _field = rbox(_fx0, _fx1, _fy0, _fy1, COVER_Z0 - 2.0, CAV_Z0 + 2.0, _fr)
    _mk = lambda web: (E._hex_panel(_fx0 - _pad, _fx1 + _pad, _fy0 - _pad, _fy1 + _pad,
                                    COVER_Z0 - 1.0, CAV_Z0 + 1.0,
                                    math.sqrt(3) * HEX_R, web) & _field)
    cells = _mk(HEX_WEB)
    # ---- NO SLIVERS.  A clipped cell can survive as a hairline the printer will not resolve;
    # the first clipped build produced one of 4.15 mm2. Rather than lower the bar, the slivers
    # are DROPPED FROM THE CUTTING SET -- an undersized hole becomes solid baffle, which costs
    # a little open area and cannot print badly.
    #
    # ⚠️ AND THE CRITERION IS WIDTH, NOT AREA. verification.md: "area is insensitive to
    # connectivity". A 10 x 0.5mm crescent has 5mm2 and is unprintable; an 8mm2 hex is 3.0mm
    # across flats and is fine. Filtering on area would have kept exactly the wrong ones.
    _depth = (CAV_Z0 + 1.0) - (COVER_Z0 - 1.0)
    _kept, _dropped, _minw = None, 0, None
    for _s in cells.solids():
        _sb = _s.bounding_box()
        _w = min(_sb.size.X, _sb.size.Y)
        if _w < GRILLE_MIN_W:
            _dropped += 1
            continue
        _minw = _w if _minw is None else min(_minw, _w)
        _kept = _s if _kept is None else _kept + _s
    assert _kept is not None, "every grille cell was filtered out as a sliver"
    cells = _kept
    _areas = sorted(s.volume / _depth for s in cells.solids())
    assert _minw >= GRILLE_MIN_W, "the sliver filter did not filter"
    print(f"  [grille]  {len(_areas)} openings kept ({_dropped} slivers dropped), narrowest "
          f"{_minw:.2f} mm across, smallest {_areas[0]:.2f} mm2, largest {_areas[-1]:.2f} mm2")
    GRILLE_CELL_N = len(cells.solids())
    assert GRILLE_CELL_N >= 20, (
        f"mobile grille collapsed to {GRILLE_CELL_N} solid(s) -- the cells have merged, so the "
        f"web is negative and the baffle would print as one opening with loose prisms in it")
    # >>> AND THE CONTROL THE STAND'S VERSION DOES NOT HAVE. <<<
    # ember_case.py:2397 asserts >= 30 on `_cells`, whose web is HEX_WEB by construction, and
    # records that the assert therefore "has never been able to fail for the reason it names".
    # Rebuilding the same lattice at web = 0 proves this counter can actually see a merge.
    _fused = len(_mk(0.0).solids())
    assert _fused < GRILLE_CELL_N, (
        f"control failed: a zero-web lattice still resolves to {_fused} separate solids, so "
        f"counting solids cannot detect a merged grille and this check is not evidence")
    p -= cells

    # ---- SCREW: clearance bore + counterbore in the bed face (inward, so bed-legal).
    # No tube is needed: at y=SCREW_XY[1] the cover is solid wall from CAV_Z0 to BACK_Z.
    p -= cyl(SCREW_XY[0], SCREW_XY[1], COVER_Z0 - 1, BACK_Z + 1, SCREW_D)
    p -= cyl(SCREW_XY[0], SCREW_XY[1], COVER_Z0 - 1, COVER_Z0 + CBORE_DEPTH, CBORE_D)

    # ---- PROTECTION-STRIP POCKET ----
    # Long axis along X (the only axis with room). Ribs sit OUTSIDE the PCB footprint and the
    # floor under it is left FLAT — a rib under a PCB is a rock under a board, and the component
    # face is the one that must not be loaded.
    _px0, _px1 = PROT_CX - PROT_L/2 - PROT_CLR, PROT_CX + PROT_L/2 + PROT_CLR
    _py0, _py1 = PROT_Y1 - PROT_W - 2*PROT_CLR, PROT_Y1
    for _r in (bx(_px0 - PROT_RIB_W, _px0, _py0, _py1, CAV_Z0, CAV_Z0 + PROT_RIB_H),
               bx(_px1, _px1 + PROT_RIB_W, _py0, _py1, CAV_Z0, CAV_Z0 + PROT_RIB_H),
               bx(_px0 - PROT_RIB_W, _px1 + PROT_RIB_W, _py0 - PROT_RIB_W, _py0,
                  CAV_Z0, CAV_Z0 + PROT_RIB_H)):
        p += _r
    # ---- TAB SLOTS: flat runs from each end of the strip toward the bay contacts ----
    # -X end -> the divider's wire groove (which carries B+ the length of the bay to the plate,
    # and P+/P- on to the BAT pass). +X end stays inside the pocket for B- to the spring.
    p -= bx(CELL_X1 - WGROOVE_D, _px0, PROT_CX*0 + _py1 - TAB_W, _py1,
            CAV_Z0, CAV_Z0 + TAB_D)
    p -= bx(CELL_X1 - WGROOVE_D, CELL_X1, BAY_Y0, _py1, CAV_Z0, CAV_Z0 + TAB_D)

    # ---- DOVETAIL TEETH: short skewed parallelograms at DT_PITCH, nothing between them (the
    # skew leaves no width for a continuous stem -- see 5g). Proud of BACK_Z is fine: that is
    # the cover's TOP when it prints, not its bed face, and the lean is a 53.1-degree overhang
    # growing off a 0.60 bead, so nothing here is bridged.
    for _side, _y0, _y1 in DT_RAILS:
        for _ty in _dt_teeth(_y0, _y1):
            p += _dt_prism(DT_P_TOOTH, _side, _ty, _ty + DT_TOOTH)

    p = E.chamfer_outline(p, COVER_Z0, CHAMFER, "mobile cover bed face")
    return p


def cell_phantom(dz=0.0, dy=0.0):
    """The 18650 itself, as a solid, so the checks can ask questions about it.

    A cell is not part of any STL, so nothing in a normal build would ever notice it fouling
    the board or its own cradle. Modelling it is the only way those become checkable.
    Resting in the cradle: a CELL_D_MAX cell in a CELL_BORE_D cradle sits CELL_BORE_CLR low.
    """
    return cyl_y(CELL_AXIS_X, CELL_AXIS_Z - CELL_BORE_CLR + dz, CELL_D_MAX,
                 BAY_Y0 + CELL_L_CLR/2 + dy, BAY_Y0 + CELL_L_CLR/2 + CELL_L_MAX + dy)


def spring_phantom(length, dz=0.0):
    """The compression spring as a plain cylinder, so the bay can be asked about it.

    Like the cell, the spring is in no STL, so nothing in a normal build would notice it
    fouling the tunnel, the cell, or the cradle. Modelled ON the bore's axis rather than
    resting at its bottom: the seated test then asks the harder question (is there room all
    the way round) and the captivity test at dz=+2.00 asks the real one.
    """
    return cyl_y(CELL_AXIS_X, CELL_AXIS_Z + dz, SPRING_OD, BAY_Y1 - length, BAY_Y1)


def driver_phantom():
    """The sealed-back module, taped to the midframe's back face, diaphragm facing the grille."""
    return rbox(DRV_CX - DRIVER_H/2, DRV_CX + DRIVER_H/2,
                DRV_CY - DRIVER_W/2, DRV_CY + DRIVER_W/2,
                BACK_Z - DRIVER_T, BACK_Z, DRIVER_R)


# ============================================================================
# 7. CHECKS.  Every one with a control that can fire.
# ============================================================================
def _lerr(depth, lh):
    """Distance from `depth` to the nearest whole multiple of `lh`. E's idiom, replicated
    here rather than imported because ember_case defines it inside _check_geometry()."""
    return abs(depth / lh - round(depth / lh)) * lh


def _rrect_area(w, h, r):
    return w * h - (4 - math.pi) * r * r


def _mark_face(which):
    """(centre z, face z-lo, face z-hi) for a polarity marking. ONE derivation, read by BOTH
    the geometry and check 15, so a marking cannot drift off its face without the check
    following it there.

    BOTH MOVED ON 2026-08-01, and both for the same reason: the bay grew features where they
    used to sit, which is the right way round -- retention beats decoration.

      "+"  sat on the end-wall face ABOVE the plate pocket. The kerf has to be open to BACK_Z
           or a 10mm-square plate cannot be got into it, so that face is a slot now. The face
           left is the strip between the kerf's floor and the cavity floor, BELOW the plate.
      "-"  sat on the high-Y end wall. THE SPRING TUNNEL NOW STANDS IN FRONT OF THAT WALL, so
           the old spot is a marking nobody can see -- the exact failure class the markings
           exist to avoid, since they are the ONLY reverse-insertion measure a flat-top cell
           allows. It moves onto the tunnel's own mouth face, beside the bore: the surface you
           are actually looking at when you look into the bay at the negative end.

    Both are still read at the moment the cell goes in, which is the whole job.
    """
    if which == "+":
        return (CELL_AXIS_X, (CAV_Z0 + CONTACT_Z0) / 2,
                BAY_Y0 - MARK_DEPTH, BAY_Y0)
    return ((CELL_X0 + CELL_AXIS_X - SPRING_BORE / 2) / 2, CELL_AXIS_Z,
            SPRING_TUN_Y0, SPRING_TUN_Y0 + MARK_DEPTH)


def _dirsign(wall):
    """+1 if the named side wall's material lies at increasing X from its inner face."""
    return 1.0 if wall == "hi" else -1.0


def _check_mobile(parts):
    print("\n--- MOBILE GEOMETRY CHECKS ---")

    # ---- 1. LAYER ALIGNMENT, every floor and recess against this part's own 0.20 ----
    for _d, _what in ((COV_WALL, "COV_WALL"), (LIP_DEPTH, "driver locating groove"),
                      (DT_DEPTH, "dovetail groove depth"), (RIM_WALL, "rim wall"),
                      (CBORE_DEPTH, "cover counterbore"), (WGROOVE_Z, "lead groove"),
                      (DT_RAIL_H, "dovetail tooth height"), (DT_NECK_H, "dovetail straight"),
                      (DT_SKEW_H, "dovetail skew"), (DT_GABLE_H, "dovetail gable"),
                      (DT_SKIN, "dovetail skin"), (DT_UNDER, "dovetail skew offset"),
                      (SPRING_TUN_CAP, "spring tunnel cap"), (SPRING_GABLE_Z, "spring gable"),
                      (CONTACT_DET_H, "contact detent bar"), (PROT_RIB_H, "strip rib"),
                      (CELL_BORE_D, "cell bore"),
                      (COV_WALL + CELL_BORE_D, "cover depth")):
        assert _lerr(_d, LH) < 1e-9, (
            f"{_what} = {_d:.4f} is not a whole multiple of LAYER_H_SHELL={LH} -- it would "
            f"land mid-layer, which is issue #26's defect")
    assert _lerr(0.90, LH) > 1e-9, "control failed: 0.90 reads aligned at 0.20"
    assert _lerr(0.48, LH) > 1e-9, "control failed: 0.48 reads aligned at 0.20"
    assert _lerr(3.04, LH) > 1e-9, "control failed: 3.04 reads aligned at 0.20"
    print(f"  [layers]  every mobile depth is a whole multiple of {LH}; 3 controls fired")

    # ---- 2. THE PORT-LENGTH IDENTITY ----
    assert abs(COV_WALL - BAFFLE_T) < 1e-9, (
        f"COV_WALL {COV_WALL} != BAFFLE_T {BAFFLE_T}. The cover's outer wall IS the baffle, so "
        f"these being equal is what makes the mobile's acoustic port length identical to the "
        f"stand's rather than merely similar. Do not fix this by editing BAFFLE_T.")

    # ---- 3. THE X BUDGET.  The reason COV_WALL is 2.20. ----
    _pad_x = DRIVER_H + 2*DRIVER_CLR
    _slack = (RIM_X1 - RIM_X0) - _pad_x
    assert _slack >= 0.50, (
        f"only {_slack:.2f}mm of X slack for the driver's {_pad_x:.2f}mm tape footprint inside "
        f"a {RIM_X1-RIM_X0:.2f}mm rim. The cell bore, the shared divider and the driver do not "
        f"fit across {OX1-OX0-2*COV_WALL:.2f}mm of interior")
    assert (OX1 - COV_WALL) - (OX0 + COV_WALL) - CELL_BORE_D - DIVIDER_W - _pad_x >= 0.0, (
        "the interior width budget is negative -- cell bore + divider + driver overruns")
    print(f"  [X budget] interior {OX1-OX0-2*COV_WALL:.2f} = bore {CELL_BORE_D:.2f} + divider "
          f"{DIVIDER_W:.2f} + rim {RIM_X1-RIM_X0:.2f}; driver slack {_slack:.2f}/2 per side")

    # ---- 4. REACHABILITY.  The check that exists because a boolean cannot see it. ----
    for _cx, _nm in ((E.BTN_BOOT_X, "BOOT"), (E.BTN_RESET_X, "RESET")):
        _cy, _R, _ = E.cap_geometry(_cx)
        _top = E.cap_hex_top_y(_cy, _R) + E.SLOT_W
        assert COVER_Y0 >= _top, (
            f"the cover starts at y={COVER_Y0:.2f} but the {_nm} cap+moat reaches y={_top:.2f} "
            f"-- the button is sealed under the battery door. This is verification.md's "
            f"reachability class and no clearance check in this file would notice it")
    assert COVER_Y0 < _BOOT_TOP + E.SLOT_W + 8.0, (
        "control: COVER_Y0 has drifted so far up that the assert above is vacuous")
    # USB-C and the SD slit both live at the board plane, far above the cover's top edge
    assert BACK_Z <= E.USB_Z[0], (
        f"the cover's mating plane {BACK_Z} is not below the USB-C body {E.USB_Z} -- the cover "
        f"would foul the plug")
    print(f"  [reach]   BOOT top {_BOOT_TOP + E.SLOT_W:.2f} / cover starts {COVER_Y0:.2f}; "
          f"USB-C at z {E.USB_Z[0]}..{E.USB_Z[1]} is clear of the cover at {BACK_Z}")

    # ---- 5. THE CELL BAY ACCEPTS BOTH CELLS ----
    for _nm, _L in (("unprotected", CELL_L_MIN), ("protected", CELL_L_MAX)):
        _gap = BAY_L - _L - CELL_L_CLR          # what the spring has to occupy
        assert _gap >= SPRING_SOLID, (
            f"a {_nm} cell at {_L} leaves the spring {_gap:.2f}mm -- below its {SPRING_SOLID} "
            f"coil-bound height, so the cell physically will not go in")
        assert SPRING_FREE - _gap > 0.0, (
            f"a {_nm} cell at {_L} leaves a {_gap:.2f}mm gap against a {SPRING_FREE}mm free "
            f"length -- the spring is not compressed at all and the cell rattles with no contact")
    _travel = SPRING_FREE - SPRING_SOLID
    assert _travel >= (CELL_L_MAX - CELL_L_MIN), (
        f"spring travel {_travel:.2f} < the {CELL_L_MAX-CELL_L_MIN:.2f} cell-length range -- one "
        f"of the two cell types cannot be accommodated")
    # CONTROL: a spring with too little travel must be rejected by the same arithmetic.
    _bad = 3.0
    assert not (_bad - SPRING_SOLID >= CELL_L_MAX - CELL_L_MIN), (
        "control failed: a spring with 3.0mm free length reads as covering a 5.80mm range")
    print(f"  [cell]    bay {BAY_L:.2f}; unprotected {CELL_L_MIN} -> spring at "
          f"{BAY_L-CELL_L_MIN-CELL_L_CLR:.2f}, protected {CELL_L_MAX} -> "
          f"{BAY_L-CELL_L_MAX-CELL_L_CLR:.2f}; travel {_travel:.2f} vs "
          f"{CELL_L_MAX-CELL_L_MIN:.2f} needed. BOTH FIT")

    # ---- 6. THE SEAL LANDS ON SOLID MATERIAL.  The two-parts-must-agree case. ----
    #
    # This is the CHAM_Y1 lesson. The rim is on the cover, the surface it seals against is on
    # the midframe, and nothing else in this file compares them. Measured as an APERTURE --
    # intersect the midframe with the rim wall's own footprint in its own plane and require it
    # FULL -- not by comparing the constants that produced both, which would be vacuous.
    mf = parts["ember-mobile-midframe"]
    _probe_t = 0.40
    # ⚠️ THE PROBE STOPS AT THE CHAMFER. RIM_X1 + RIM_WALL = 52.35 runs 0.20 into the bed-side
    # chamfer that starts at OX1 - CHAMFER = 52.15, and BOTH parts carry that chamfer -- it is
    # exterior relief, not a leak path into the board cavity. Measuring it as unsealed is a
    # false positive, and one that would be "fixed" by deleting a functional chamfer.
    _rx1 = min(RIM_X1 + RIM_WALL, OX1 - CHAMFER)
    _ry1 = min(RIM_Y1 + RIM_WALL, MOB_OY1 - CHAMFER)
    ring = (rbox(RIM_X0 - RIM_WALL, _rx1, RIM_Y0 - RIM_WALL, _ry1,
                 BACK_Z, BACK_Z + _probe_t, 1.0)
            - rbox(RIM_X0, RIM_X1, RIM_Y0, RIM_Y1, BACK_Z - 1, BACK_Z + _probe_t + 1, 1.0))
    _want = ring.volume
    _got = (mf & ring).volume
    _frac = _got / _want if _want else 0.0
    # ---- WHERE, not just how much. One number for the whole ring told me it was holed and
    # nothing about which feature did it; finding the screw pilot took a hand search. Break the
    # ring into its four legs so the next leak names itself.
    for _lnm, _lg in (("low-Y ", bx(RIM_X0-RIM_WALL, _rx1, RIM_Y0-RIM_WALL, RIM_Y0,
                                    BACK_Z, BACK_Z + _probe_t)),
                      ("high-Y", bx(RIM_X0-RIM_WALL, _rx1, RIM_Y1, _ry1,
                                    BACK_Z, BACK_Z + _probe_t)),
                      ("low-X ", bx(RIM_X0-RIM_WALL, RIM_X0, RIM_Y0, RIM_Y1,
                                    BACK_Z, BACK_Z + _probe_t)),
                      ("high-X", bx(RIM_X1, _rx1, RIM_Y0, RIM_Y1,
                                    BACK_Z, BACK_Z + _probe_t))):
        _lw = _lg.volume
        _lf = (mf & _lg).volume / _lw if _lw else 0.0
        print(f"    seal leg {_lnm}  {100*_lf:6.2f}% solid  "
              f"({(1-_lf)*_lw/_probe_t:6.3f} mm2 open)")
    # ---- 6c. THE BED-SIDE CHAMFER SURVIVES THE PLATEAU. ----
    #
    # This check exists because the plateau ate 39.65mm of it and NOTHING NOTICED. The plateau
    # is additive, and every other check in this file looks for material that is missing --
    # a feature destroyed by material that was added is invisible to all of them. PRINT-SHEET:
    # the bed-side chamfers "absorb elephant's foot", and the Z-offset runs squished at -2.14.
    _pl = _plateau_region()
    _wedge = bx(OX1 - CHAMFER, OX1, _pl[2], _pl[3], BACK_Z, BACK_Z + CHAMFER)
    _wfill = (mf & _wedge).volume / _wedge.volume
    assert _wfill <= 0.60, (
        f"the high-X bed-side chamfer is {100*_wfill:.1f}% filled over the plateau's y span "
        f"(a 45deg chamfer reads ~50%) -- something additive has re-squared the edge that "
        f"absorbs elephant's foot")
    _solid = bx(OX1 - 2*CHAMFER, OX1 - CHAMFER, _pl[2], _pl[3], BACK_Z, BACK_Z + CHAMFER)
    _sfill = (mf & _solid).volume / _solid.volume
    assert _sfill > 0.90, (
        f"control failed: material just inboard of the chamfer reads {100*_sfill:.1f}% filled, "
        f"so this probe cannot tell a chamfer from a missing wall")
    print(f"  [chamfer] high-X bed edge {100*_wfill:.1f}% filled (45deg reads ~50); "
          f"control on solid material inboard {100*_sfill:.1f}%")

    assert _frac >= 0.999, (
        f"only {100*_frac:.2f}% of the seal rim's footprint lands on solid midframe back face "
        f"({_got:.1f} of {_want:.1f} mm3). The bond plateau is not covering the vent hexes under "
        f"the rim, so the 'sealed' cavity vents into the board cavity through a honeycomb")
    # CONTROL: the same ring, moved onto the untouched vent field, must NOT read solid.
    _ctl = Pos(0, -12.0, 0) * ring
    _cfrac = (mf & _ctl).volume / _want if _want else 1.0
    assert _cfrac < 0.98, (
        f"control failed: the seal probe reads {100*_cfrac:.2f}% solid even when moved onto the "
        f"open hex vent field, so it cannot detect an unsealed rim")
    print(f"  [seal]    rim footprint {100*_frac:.2f}% solid; control on the vent field "
          f"{100*_cfrac:.2f}% (must be < 98)")

    # ---- 6b. NO FASTENER MAY PIERCE THE SEAL.  In coordinates, as well as by boolean. ----
    #
    # The boolean above is the real check, but it reports one number for the whole ring and
    # says nothing about WHICH feature holed it -- it took a hand search to find that the
    # screw pilot was the culprit. This states the invariant per feature, so the next person
    # who moves a fastener is told what they broke rather than that a percentage dropped.
    # ⚠️ REWRITTEN AS RECTANGLE-OVERLAP, 2026-08-01, AND THE POINT+RADIUS FORM WAS WRONG FOR
    # ANYTHING LONG. It tested a CENTRE against the ring's bounds inflated by r, which is only
    # sound for a disc: fed a 66mm rail its centre lands mid-rim and r inflates the bounds past
    # the whole part, so it reported a pierce that does not exist AND would have missed one
    # whose centre fell outside. The rails made a general form necessary, and the general form
    # is the right one for the screw too -- it is now the same test for both.
    _ring_y = (RIM_Y0 - RIM_WALL, RIM_Y1 + RIM_WALL)
    _ring_x = (RIM_X0 - RIM_WALL, RIM_X1 + RIM_WALL)

    def _hits_ring(x0, x1, y0, y1):
        """Does an axis-aligned footprint touch the seal RING (outer rect minus inner rect)?"""
        _ov = (x0 < _ring_x[1] and x1 > _ring_x[0]
               and y0 < _ring_y[1] and y1 > _ring_y[0])          # touches the outer rect...
        _in = (x0 >= RIM_X0 and x1 <= RIM_X1
               and y0 >= RIM_Y0 and y1 <= RIM_Y1)                # ...but not wholly inside it
        return _ov and not _in

    _pierce = [("screw pilot", SCREW_XY[0] - PILOT_D/2, SCREW_XY[0] + PILOT_D/2,
                SCREW_XY[1] - PILOT_D/2, SCREW_XY[1] + PILOT_D/2)]
    # The rails are pockets cut in the same back face and answer to the same rule. Their
    # footprint is the groove's full u-band over the whole rail, drop-in pockets included.
    for _side, _ry0, _ry1 in DT_RAILS:
        _gx0 = (OX0 + DT_SKIN) if _side == "lo" else (OX1 - DT_SKIN - DT_WIDE)
        _pierce.append((f"dovetail groove {_side} y {_ry0:.2f}..{_ry1:.2f}",
                        _gx0, _gx0 + DT_WIDE, _ry0, _ry1 + DT_CLR_Y))
    for _nm, _x0, _x1, _y0, _y1 in _pierce:
        assert not _hits_ring(_x0, _x1, _y0, _y1), (
            f"{_nm} (x {_x0:.2f}..{_x1:.2f}, y {_y0:.2f}..{_y1:.2f}) lands on or across the "
            f"seal rim's footprint (x {_ring_x[0]:.2f}..{_ring_x[1]:.2f}, "
            f"y {_ring_y[0]:.2f}..{_ring_y[1]:.2f}). A pocket through the seal vents the "
            f"cavity into the board cavity")
    # CONTROLS, in both directions, because a predicate that always returns False passes the
    # loop above silently. (1) the rejected screw position, sitting in the middle of the rim
    # wall, must read as piercing; (2) the +X rail moved 1.00 up into the seal's Y span must
    # ALSO read as piercing -- that one is the failure this rewrite exists to catch; and
    # (3) a footprint wholly inside the rim must NOT.
    assert _hits_ring(25.00 - PILOT_D/2, 25.00 + PILOT_D/2,
                      RIM_Y0 - RIM_WALL/2 - PILOT_D/2, RIM_Y0 - RIM_WALL/2 + PILOT_D/2), (
        "control failed: a bore placed deliberately in the middle of the rim wall does not "
        "read as piercing, so this test cannot detect a fastener through the seal")
    assert _hits_ring(OX1 - DT_SKIN - DT_WIDE, OX1 - DT_SKIN,
                      RIM_Y0 - RIM_WALL - 0.40, RIM_Y0 + 1.00), (
        "control failed: a +X rail run 1.00mm up into the seal's Y span does not read as "
        "piercing, so nothing stops the next person lengthening it")
    assert not _hits_ring(RIM_X0 + 1.0, RIM_X0 + 3.0, RIM_Y0 + 1.0, RIM_Y0 + 3.0), (
        "control failed: a footprint wholly INSIDE the rim reads as piercing, so this test "
        "would reject the speaker relief and every legitimate feature in the cavity")
    print(f"  [seal 6b] {len(_pierce)} back-face pockets, all clear of the rim footprint; "
          f"retention strip y {BAY_Y0:.2f}..{RIM_Y0-RIM_WALL:.2f} is what makes room for the "
          f"screw, and y>{RIM_Y1+RIM_WALL:.2f} / y<{RIM_Y0-RIM_WALL:.2f} for the +X rails")

    # ---- 7. FRONT CAVITY, MEASURED BY BOOLEAN, against the stand computed the same way ----
    cov = parts["ember-mobile-back"]
    envelope = bx(RIM_X0, RIM_X1, RIM_Y0, RIM_Y1, CAV_Z0, BACK_Z)
    void = envelope - cov
    _net = void.volume - driver_phantom().volume
    _stand_cham = ((E.CHAM_X1 - E.CHAM_X0) * (E.CHAM_Y1 - E.CHAM_Y0) * (37.0 - E.ST_WALL))
    _stand_drv = _rrect_area(DRIVER_W, DRIVER_H, DRIVER_R) * DRIVER_T
    _stand_pad = _rrect_area(DRIVER_W + 2*DRIVER_CLR, DRIVER_H + 2*DRIVER_CLR,
                             DRIVER_R + DRIVER_CLR) * E.PAD_PROUD
    _stand_net = _stand_cham - _stand_drv - _stand_pad
    _delta = 100.0 * (_net - _stand_net) / _stand_net
    assert abs(_delta) <= 25.0, (
        f"mobile front air {_net:.0f}mm3 is {_delta:+.1f}% off the stand's {_stand_net:.0f}mm3, "
        f"which is the only volume this driver is known to sound acceptable in")
    c = 343000.0
    _sm = min(c/(2*54.0), c/(2*33.0), c/(2*(E.CHAM_Y1 - E.CHAM_Y0)))
    _mm = min(c/(2*(RIM_Y1-RIM_Y0)), c/(2*(RIM_X1-RIM_X0)), c/(2*(BACK_Z-CAV_Z0)))
    assert _mm >= _sm, (
        f"the mobile's governing cavity mode {_mm:.0f}Hz is BELOW the stand's {_sm:.0f}Hz -- "
        f"the redistribution of front air from lateral to axial has made it worse, not neutral")
    print(f"  [acoustic] front air: stand {_stand_net:8.1f} mm3   mobile {_net:8.1f} mm3  "
          f"({_delta:+.1f}%)")
    print(f"             FRONT_GAP  stand {E.FRONT_GAP:.2f}      mobile {FRONT_GAP_MOBILE:.2f}   "
          f"(declared departure)")
    print(f"             governing cavity mode: stand {_sm:.0f} Hz   mobile {_mm:.0f} Hz")

    # ---- 8. GRILLE THROAT, RASTERED.  Neither figure inherited from a comment. ----
    #
    # Measured by intersecting the finished part with a thin slab mid-baffle and subtracting
    # from the field's area -- i.e. the aperture, not the sum of the cells that were cut.
    _zmid = COVER_Z0 + BAFFLE_T / 2
    slab = bx(DRV_CX - GRILLE_FW/2 - 2, DRV_CX + GRILLE_FW/2 + 2,
              DRV_CY - GRILLE_FH/2 - 2, DRV_CY + GRILLE_FH/2 + 2, _zmid - 0.05, _zmid + 0.05)
    _mat = (cov & slab).volume / 0.10
    _throat = (GRILLE_FW + 4) * (GRILLE_FH + 4) - _mat
    _radiating = _rrect_area(GRILLE_FW, GRILLE_FH, max(DRIVER_R - GRILLE_INSET, 0.8))
    # The lattice's own ceiling: open fraction of an infinite field is (a/(a+w))^2. Clipping at
    # the field boundary can only lose against that, and how much it loses is the thing worth
    # checking -- 46% against a 69% ceiling is what exposed the unclipped-field bug.
    _ideal = _radiating * (math.sqrt(3)*HEX_R / (math.sqrt(3)*HEX_R + HEX_WEB))**2
    assert _throat >= 0.85 * _ideal, (
        f"grille throat {_throat:.1f}mm2 is more than 15% below the {_ideal:.1f}mm2 this "
        f"lattice can deliver over this field -- boundary cells are being thrown away, and the "
        f"baffle rather than the box is what limits this driver (ember_case.py:2017)")
    print(f"  [grille]  {GRILLE_CELL_N} openings, throat {_throat:.1f} mm2 over a "
          f"{_radiating:.1f} mm2 field ({100*_throat/_radiating:.0f}%, lattice ceiling "
          f"{100*_ideal/_radiating:.0f}%); vs the driver's ~700 mm2 radiating area = "
          f"{100*_throat/700.0:.0f}%")
    print(f"             mouth web {HEX_WEB:.2f} unflared (stand: {E.GRILLE_MOUTH_WEB:.4f}, "
          f"flared -- issue #28's droop needs a horizontal bore and these are vertical prisms)")

    # ---- 8b. THE DOVETAIL IS PRINTABLE.  NO BRIDGE, AND EVERY FACE >= 45 deg. ----
    #
    # >>> THIS IS THE CHECK THE HOOKS DID NOT HAVE, AND IT IS WHY THEY ARE GONE. <<<
    #
    # It runs in three layers, weakest first, and the last one is measured on the mesh:
    #
    #   (i)   the as-printed frame IS the model frame. Both parts are exported by a pure Z
    #         translation (PRINT_LIFT), so an angle in this file is an angle on the bed. If a
    #         future variant ever rotates a part for printing, every conclusion below dies --
    #         so it is asserted, not assumed.
    #   (ii)  the analytic face angles of the profile, from the constants.
    #   (iii) THE ARTIFACT. Sweep thin slabs up through the finished solids and watch how much
    #         MATERIAL each layer gains over the one below. A face at 45 degrees gains LH per
    #         layer; a flat roof gains its whole width in one. Bounding the gain at LH makes a
    #         bridge unmissable.
    #
    # ⚠️ THE SWEEP IS SPLIT AT THE GABLE APEX, AND THE UNSPLIT VERSION WAS BLIND IN THE ONE
    # DIRECTION THAT MATTERS. Measuring total material across the whole u-band nets the two
    # edges against each other -- and this joint's whole trick is a void that TRANSLATES, so
    # through the skew one edge gains exactly what the other loses and the total reads a flat
    # 0.60 the whole way up. That is the correct answer here, but only by luck: an edge running
    # at 20 degrees would have been cancelled just as neatly by a shrink on the other side.
    # Split at u = DT_SKIN + DT_MOUTH/2 and each half has exactly ONE moving edge, so the number
    # is per-face and cannot be cancelled. This is the same lesson as the vent-throat and
    # polarity probes: a measurement that sums over a feature can hide the feature.
    #
    # The control is the deleted hook pocket itself, rebuilt as a phantom and run through the
    # same sweep. It has to fail, or this check is decoration.
    assert PRINT_LIFT["ember-mobile-midframe"] == -BACK_Z and \
           PRINT_LIFT["ember-mobile-back"] == -COVER_Z0, (
        "PRINT_LIFT is no longer a pure Z translation of the model frame, so 'vertical in the "
        "model' no longer means 'vertical on the bed' and every angle below is meaningless")
    _a_skew = math.degrees(math.atan2(DT_SKEW_H, DT_UNDER))         # from HORIZONTAL
    _a_gable = math.degrees(math.atan2(DT_GABLE_H, DT_MOUTH / 2))
    _a_worst = min(_a_skew, _a_gable)
    assert _a_worst >= 50.0, (
        f"the shallowest face in the dovetail runs at {_a_worst:.1f} deg from horizontal "
        f"(skew {_a_skew:.1f}, gable {_a_gable:.1f}). 45 is the print limit and this joint is "
        f"held to 50 so tessellation cannot eat the margin. Raise DT_SKEW_H / DT_GABLE_H")
    assert math.degrees(math.atan2(1.0, 1.0)) < 50.0, (
        "control failed: a 45-degree face reads as clearing the 50-degree bar")

    # ⚠️ THE METRIC IS MATERIAL GROWTH, NOT VOID CHANGE, AND THE FIRST VERSION HAD IT BACKWARDS.
    # Void width also jumps at the TOP OF THE RAIL, where the part simply ends and there is
    # nothing above to overhang -- a perfectly legal upward-facing face read as a 1.20mm step.
    # An overhang is material APPEARING over void, so the quantity is how much wider the
    # material gets from one layer to the next. Material narrowing is always free.
    def _mat_widths(part, side, y, z0, z1, u0, u1):
        """Material width (mm) inside a wall's u-band, layer by layer, from the ARTIFACT."""
        s = 1.0 if side == "lo" else -1.0
        xa = (OX0 if side == "lo" else OX1) + s * u0
        xb = (OX0 if side == "lo" else OX1) + s * u1
        out, _t, _dy = [], LH * 0.5, 0.40
        _z = z0 + LH / 2
        while _z <= z1:
            _pr = bx(min(xa, xb), max(xa, xb), y - _dy/2, y + _dy/2, _z - _t/2, _z + _t/2)
            out.append((part & _pr).volume / (_t * _dy))
            _z += LH
        return out

    def _worst_growth(ws):
        return max((b - a for a, b in zip(ws, ws[1:])), default=0.0)

    _step_max = LH * 1.15              # ONE edge at the 45 deg limit, plus 15% for the mesh
    # The u-window starts at CHAMFER so the midframe's own bed-side chamfer -- a legitimate
    # 45-degree exterior face -- is not swept in and counted against the joint's budget.
    _apex = DT_SKIN + DT_MOUTH / 2
    _halves = ((CHAMFER, _apex), (_apex, DT_SKIN + DT_WIDE))
    _worst, _where = 0.0, "nothing"
    for _side, _ry0, _ry1 in DT_RAILS:
        _t0 = _dt_teeth(_ry0, _ry1)[0]
        for _nm, _y, _part, _pn in (("groove shoulder", _t0 + DT_TOOTH/2, mf, "midframe"),
                                    ("groove pocket", _t0 - DT_TRAVEL/2, mf, "midframe"),
                                    ("rail tooth", _t0 + DT_TOOTH/2, cov, "cover")):
            _z1 = BACK_Z + (DT_DEPTH + 0.40 if _part is mf else DT_RAIL_H + 0.20)
            for _ua, _ub in _halves:
                _st = _worst_growth(_mat_widths(_part, _side, _y, BACK_Z, _z1, _ua, _ub))
                if _st > _worst:
                    _worst, _where = _st, (f"the {_pn}'s {_nm} on the {_side} wall at "
                                           f"y={_y:.2f}, u {_ua:.2f}..{_ub:.2f}")
    assert _worst <= _step_max, (
        f"material grows {_worst:.2f}mm in one {LH} layer at {_where}, over the {_step_max:.2f} "
        f"a single 45-degree face can produce. Something in the joint is BRIDGED -- that is "
        f"the defect JP rejected the hooks for, reintroduced")
    # >>> THE CONTROL IS THE THING THAT WAS DELETED. <<<
    # The old hook pocket: an 8.00-wide void cut from BACK_Z to BACK_Z + 1.40 in the bed face,
    # roofed flat. Rebuilt here on a scrap block and swept identically. If it passes, the sweep
    # cannot see a bridge and nothing above is evidence.
    _blk = bx(OX0, OX0 + 12.0, 0.0, 12.0, BACK_Z, BACK_Z + 6.0)
    _blk -= bx(OX0 + 1.0, OX0 + 9.0, 2.0, 10.0, BACK_Z, BACK_Z + 1.40)      # HOOK_W x HOOK_D
    _hw = _mat_widths(_blk, "lo", 6.0, BACK_Z, BACK_Z + 2.20, 0.0, 6.0)     # one half of it
    assert _worst_growth(_hw) > _step_max, (
        f"control failed: the deleted hook pocket -- an 8.00 x 1.40 flat-roofed void in the bed "
        f"face -- grows only {_worst_growth(_hw):.2f}mm per layer, inside the "
        f"{_step_max:.2f} budget. The sweep cannot detect a bridge")
    print(f"  [dovetail] as-printed frame = model frame (pure Z lift, both parts). Worst face "
          f"{_a_worst:.1f} deg from horizontal (skew {_a_skew:.1f}, gable {_a_gable:.1f})")
    print(f"             per-face material growth: worst {_worst:.3f}mm/{LH} layer over "
          f"{len(DT_RAILS)*3*len(_halves)} sweeps, split at the gable apex (budget "
          f"{_step_max:.2f}); NO FLAT ROOF ANYWHERE")
    print(f"             control: the deleted hook pocket grows {_worst_growth(_hw):.2f}mm in "
          f"one layer -- it fails the same sweep, which is why it is deleted")

    # ---- 8c. THE DOVETAIL CAPTURES.  Engagement area measured, and bounded BOTH ways. ----
    #
    # ⚠️ THIS FILE'S DEFECT LOG SAYS SINGLE-BOUNDED PROBES LIE. Three times: the vent throat swept
    # fresh air, the polarity probe swept the contact pocket, the solder-access probe swept the
    # compartment walls. So the shoulder is measured with a floor AND the pockets with a ceiling,
    # from the same probe. A groove with no shoulders holds nothing; a groove with no pockets
    # cannot be assembled at all. One number cannot tell those apart -- two can.
    _sh_area, _pk_open, _n_teeth = 0.0, 0.0, 0
    _sh_min, _pk_max = 1.0, 0.0
    _sh_where, _pk_where = "", ""            # WHICH tooth, because "one shoulder" cost a build
    for _side, _ry0, _ry1 in DT_RAILS:
        _s = 1.0 if _side == "lo" else -1.0
        _x0 = (OX0 if _side == "lo" else OX1) + _s * DT_SKIN
        _x1 = _x0 + _s * DT_UNDER               # the skew band: material only over a shoulder
        # ...and only in the STRAIGHT section. Above DT_NECK_H the void itself moves into this
        # band, so a probe run any taller would read the joint's own clearance as a missing
        # shoulder. The probe's extent is the feature's extent -- this file's standing rule.
        _za, _zb = BACK_Z + 0.04, BACK_Z + DT_NECK_H - 0.04
        for _ty in _dt_teeth(_ry0, _ry1):
            _n_teeth += 1
            for _nm, _ya, _yb in (("shoulder", _ty, _ty + DT_TOOTH),
                                  ("pocket", _ty - DT_TRAVEL, _ty - DT_TRAVEL + DT_TOOTH)):
                _pr = bx(min(_x0, _x1), max(_x0, _x1), _ya, _yb, _za, _zb)
                _f = (mf & _pr).volume / _pr.volume
                if _nm == "shoulder":
                    if _f < _sh_min:
                        _sh_min, _sh_where = _f, f"{_side} wall, tooth at y={_ty:.2f}"
                    _sh_area += _f * DT_TOOTH * DT_UNDER
                else:
                    if _f > _pk_max:
                        _pk_max, _pk_where = _f, f"{_side} wall, tooth at y={_ty:.2f}"
                    _pk_open += (1 - _f) * DT_TOOTH * DT_UNDER
    assert _sh_min > 0.98, (
        f"the dovetail shoulder on the {_sh_where} is only {100*_sh_min:.1f}% solid -- the "
        f"midframe has no material over that tooth, so the rail there retains nothing. Look "
        f"first at what else owns that Y: a corner arc, a channel, a boss flare")
    assert _pk_max < 0.02, (
        f"the drop-in pocket on the {_pk_where} is {100*_pk_max:.1f}% material -- the tooth "
        f"cannot enter the groove and the cover cannot be assembled. Every static clearance "
        f"check would still pass")
    assert _sh_area >= DT_ENGAGE_MIN, (
        f"only {_sh_area:.1f} mm2 of dovetail capture over {_n_teeth} teeth, under the "
        f"{DT_ENGAGE_MIN:.1f} mm2 floor. That floor is a load argument, not a taste: at PLA's "
        f"conservative 20 MPa in shear it is ~240 N, three orders over the cover's own weight "
        f"and past any hand pull, and it is the ONLY thing holding the long edges between the "
        f"one screw at the chin and the brow")
    # THE CAPTURE CONDITION ITSELF, with a control. The tooth is only trapped if its widest
    # point cannot pass back out through the groove's mouth, i.e. if the undercut EXCEEDS the
    # clearance. That is one inequality and it is the whole joint; state it, and prove the
    # statement can fail by feeding it an undercut equal to the clearance.
    def _captures(under, clr):
        return under - clr > 0.05
    assert _captures(DT_UNDER, DT_CLR) and abs(DT_GRIP - (DT_UNDER - DT_CLR)) < 1e-9, (
        f"a {DT_UNDER:.2f} undercut at {DT_CLR:.2f} clearance leaves {DT_GRIP:.2f}mm of grip. "
        f"At or below the clearance the tooth lifts straight back out of the mouth and the "
        f"rail is a decorative fin")
    assert not _captures(DT_CLR, DT_CLR), (
        "control failed: an undercut exactly equal to the clearance reads as capturing, so the "
        "capture condition cannot reject a joint that holds nothing")
    # >>> AND THE KINEMATIC FORM, ON THE TWO REAL SOLIDS.  Area is a proxy; THIS is the property.
    # Seated, the cover may sink DT_LIFT before the skewed flanks touch. Push it DT_LIFT + 0.20
    # and it MUST bite. At the insertion offset the identical push has to pass clean through,
    # because that is where the pockets are. One probe, both directions -- and neither reading
    # means anything without the other: a joint that never bites does not retain, and a joint
    # that always bites cannot be taken apart.
    _bite = (Pos(0, 0, -(DT_LIFT + 0.20)) * cov & mf).volume
    _free = (Pos(0, -DT_TRAVEL, -(DT_LIFT + 0.20)) * cov & mf).volume
    assert _bite > 1.0, (
        f"pulling the seated cover {DT_LIFT + 0.20:.2f}mm off the mating plane finds only "
        f"{_bite:.2f} mm3 of midframe in the way -- the teeth are NOT captured and the cover "
        f"lifts straight off with the screw out")
    assert _free < 0.5, (
        f"the same {DT_LIFT + 0.20:.2f}mm at the insertion offset already fouls the midframe by "
        f"{_free:.2f} mm3, so the teeth never line up with their pockets and the cover cannot "
        f"be fitted at all")
    print(f"  [capture] {_n_teeth} teeth, {DT_TOOTH:.2f} x {DT_UNDER:.2f} each: "
          f"{_sh_area:.1f} mm2 of shoulder measured on the midframe (floor {DT_ENGAGE_MIN:.1f}); "
          f"worst shoulder {100*_sh_min:.1f}% solid")
    print(f"             control: the {_n_teeth} drop-in pockets measure {_pk_open:.1f} mm2 OPEN "
          f"(worst {100*_pk_max:.1f}% material) -- the cover can actually go on")
    print(f"             grip {DT_GRIP:.2f}mm per rail past the mouth; the cover may rise "
          f"{DT_LIFT:.2f}mm before the flanks bite, then it is solid against solid")

    # ---- 8d. THE SLIDE IS POSSIBLE, AND THE DRIVER IS WHAT LIMITS IT. ----
    #
    # >>> THE HOOK DESIGN FAILED THIS AND NOTHING IN THE FILE LOOKED. <<<
    #
    # It wanted 2.90mm of +Y slide with the parts mated. The driver hangs into the cover's sealed
    # cavity and the rim's end walls stand the cavity's full height, so a Y slide sweeps those
    # walls THROUGH the speaker. The driver is a phantom -- it is in no STL -- so the part-vs-part
    # boolean could never have seen it, exactly like the cell-vs-cradle interference at 13.1 mm3.
    # Measured by sweeping the real solid, not by comparing constants.
    _gap_drv = (RIM_INNER_Y - DRIVER_W) / 2
    assert DT_TRAVEL <= _gap_drv - 0.30, (
        f"the slide is {DT_TRAVEL:.2f}mm but the rim's end walls only clear the driver by "
        f"{_gap_drv:.2f}mm. Sliding the cover drives a {BACK_Z-CAV_Z0:.2f}mm wall through a "
        f"{DRIVER_T:.2f}mm speaker. This is the hard ceiling on ANY Y-travel retention here")
    # The path, in the order a hand does it: drop the cover on 2.00mm low (the vertical approach,
    # dz), then push it +Y to seat (dy). Sampled as poses rather than unioned into one swept
    # solid -- a union of seven grille-bearing covers costs minutes and proves nothing extra,
    # because a collision at any pose is a collision.
    _drv = driver_phantom()
    _path = ([(-DT_TRAVEL, -_d) for _d in (2.40, 1.20, 0.40)]        # coming down into the pockets
             + [(-DT_TRAVEL * _k / 4.0, 0.0) for _k in (4, 3, 2, 1, 0)])   # then sliding home
    _fo_drv = max((Pos(0, _dy, _dz) * cov & _drv).volume for _dy, _dz in _path)
    _fo_mf = max((Pos(0, _dy, _dz) * cov & mf).volume for _dy, _dz in _path)
    assert _fo_drv < 0.5, (
        f"the cover passes {_fo_drv:.2f} mm3 through the driver somewhere on its way in -- it "
        f"will not go together with the speaker fitted, and the speaker is fitted first")
    assert _fo_mf < 0.5, (
        f"the cover passes {_fo_mf:.2f} mm3 through the midframe on its way in. Either a tooth "
        f"misses its drop-in pocket or something outside the joint fouls during the slide")
    # >>> AND THE CONTENTS RIDE WITH IT.  The cell and the spring are loaded into the cover
    # BEFORE it goes on, so they sweep the same path and they are in no STL either. Nothing
    # else in this file would notice a cell that clears when seated and grazes on the way.
    _load = max(max((Pos(0, _dy, _dz) * _ph & mf).volume for _dy, _dz in _path)
                for _ph in (cell_phantom(), spring_phantom(SPRING_FREE)))
    assert _load < 0.5, (
        f"the cell or the spring passes {_load:.2f} mm3 through the midframe during the slide "
        f"-- the cover goes on with them already in it")
    # CONTROL: the hooks' own 2.90mm must be reported as a collision, or this proves nothing.
    _fo_ctl = max((Pos(0, -2.90 * _k / 4.0, 0.0) * cov & _drv).volume for _k in range(5))
    assert _fo_ctl > 1.0, (
        f"control failed: the 2.90mm slide the deleted hooks required reads {_fo_ctl:.2f} mm3 "
        f"of driver interference, i.e. clear. The sweep cannot detect the failure it exists for")
    print(f"  [slide]   {DT_TRAVEL:.2f}mm of +Y travel to seat, against a {_gap_drv:.2f}mm "
          f"rim-to-driver gap. Worst pose on the assembly path: vs driver {_fo_drv:.3f} mm3, "
          f"vs midframe {_fo_mf:.3f} mm3 over {len(_path)} poses")
    print(f"             control: the hooks' 2.90mm slide drives {_fo_ctl:.1f} mm3 of rim wall "
          f"THROUGH the driver -- printability was not the only thing wrong with them")

    # ---- 8e. THE ONE SCREW LOCKS THE SLIDE OUT.  That is now its second job. ----
    _shank_play = (SCREW_D - 3.00) / 2.0                  # M3 shank in the cover's clearance bore
    assert _shank_play * 2 < DT_TRAVEL - 1.00, (
        f"with the screw fitted the cover can still shift {2*_shank_play:.2f}mm in Y against a "
        f"{DT_TRAVEL:.2f}mm travel -- the screw does not block the slide and the cover can be "
        f"walked off with the fastener still in")
    for _side, _ry0, _ry1 in DT_RAILS:
        _gx0 = (OX0 + DT_SKIN) if _side == "lo" else (OX1 - DT_SKIN - DT_WIDE)
        assert (SCREW_XY[0] + CBORE_D/2 < _gx0 or SCREW_XY[0] - CBORE_D/2 > _gx0 + DT_WIDE), (
            f"the d{CBORE_D} counterbore at x={SCREW_XY[0]:.2f} reaches into the {_side} rail's "
            f"u-band (x {_gx0:.2f}..{_gx0 + DT_WIDE:.2f}) -- the screw boss and the rail are "
            f"fighting for the same wall")
    # >>> AND IT MUST ONLY GO IN AT FULL ENGAGEMENT.  A REACH CHECK, NOT A FIT CHECK. <<<
    #
    # The deleted hooks carried "travel need 2.90 / have 3.60" -- an assert that the mechanism
    # can REACH its engaged state, not merely occupy it. That class of question is the one this
    # repo keeps paying for (docs/verification.md's buried buttons; the hooks' own 2.90mm slide
    # that no boolean could see), so the dovetails owe an equivalent. Here it is inverted and
    # therefore stronger: a half-slid cover must be IMPOSSIBLE to screw down. Measured by
    # pushing an M3 shank through and asking whether the cover is in its way.
    _shank = cyl(SCREW_XY[0], SCREW_XY[1], COVER_Z0 - 1, BACK_Z + 1, 3.00)
    _seated_blk = (_shank & cov).volume
    _part_blk = min((_shank & (Pos(0, -DT_TRAVEL * _k / 3.0, 0) * cov)).volume
                    for _k in (1, 2, 3))
    assert _seated_blk < 0.02, (
        f"the M3 shank fouls the seated cover by {_seated_blk:.3f} mm3 -- the clearance bore "
        f"does not line up with the pilot even when the slide IS home")
    assert _part_blk > 1.0, (
        f"a cover slid only part way still passes the screw ({_part_blk:.2f} mm3 of the shank "
        f"blocked at the worst partial pose). It can be fastened half-engaged, with the teeth "
        f"sitting in their drop-in pockets and nothing retaining the cover at all")
    print(f"  [lock]    M3 shank in a d{SCREW_D} bore leaves {2*_shank_play:.2f}mm of Y freedom "
          f"against {DT_TRAVEL:.2f} of travel: the screw is the slide's stop, not just a clamp")
    print(f"             reach: seated, the shank is {_seated_blk:.3f} mm3 obstructed; at the "
          f"best partial slide {_part_blk:.1f} mm3 -- it CANNOT be screwed down half-engaged")

    # ---- 8g. THE BAY HOLDS ITS METALWORK.  JP's question, answered in geometry. ----
    #
    # >>> "we need features to hold the spring, and to hold the metal strips." <<<
    #
    # The acceptance behaviour is JP's: cell OUT, case OPEN-SIDE-DOWN, the spring stays put.
    # That is a CAPTIVITY question, and captivity is not an area or a depth -- it is "does the
    # part collide with the enclosure when you try to take it out the way gravity would".
    # So it is asked that way, with the escape direction and a control that must NOT collide.
    _spr_free = spring_phantom(SPRING_FREE)
    _spr_fit = (cov & _spr_free).volume
    assert _spr_fit < 0.5, (
        f"the spring at its {SPRING_FREE} free length fouls the bay by {_spr_fit:.2f} mm3 -- it "
        f"does not go in, never mind stay in")
    # THE CAPTIVITY TEST. Open-side-down is +Z out of the bay, so lift the spring that way and
    # the tunnel must be in the road. 2.00 is past any rattle and short of clearing the bore.
    _spr_up = (cov & spring_phantom(SPRING_FREE, dz=2.00)).volume
    assert _spr_up > 5.0, (
        f"lifting the spring 2.00mm toward the bay's open side finds only {_spr_up:.2f} mm3 of "
        f"cover in the way. The tunnel is not capturing it and it will fall out when the cell "
        f"comes out -- which is JP's stated acceptance behaviour, failed")
    # CONTROL: the same lift applied to a spring sitting OUTSIDE the tunnel, where the cradle
    # is open above the axis, must be free. Without this, "captive" and "the probe collides
    # with everything" are the same reading.
    _spr_out = (cov & cyl_y(CELL_AXIS_X, CELL_AXIS_Z + 2.00, SPRING_OD,
                            SPRING_TUN_Y0 - 12.0, SPRING_TUN_Y0 - 2.0)).volume
    assert _spr_out < 0.5, (
        f"control failed: a spring lifted 2.00mm OUTSIDE the tunnel still reads {_spr_out:.2f} "
        f"mm3 of interference, so the captivity probe cannot tell the tunnel from the trough")
    # THE TUNNEL MOUTH IS NOT IN NORMAL SERVICE, AND IS A STOP WHEN IT IS.
    _cell_end = BAY_Y0 + CELL_L_CLR/2 + CELL_L_MAX
    assert SPRING_TUN_Y0 > _cell_end + 0.30, (
        f"the tunnel's mouth at y={SPRING_TUN_Y0:.2f} is inside the longest cell's reach "
        f"({_cell_end:.2f}) -- the cell bottoms on plastic in normal service instead of on its "
        f"spring")
    assert BAY_Y1 - SPRING_TUN_Y0 > SPRING_SOLID, (
        f"the tunnel is {BAY_Y1-SPRING_TUN_Y0:.2f} long against a {SPRING_SOLID} coil-bound "
        f"height -- as an over-travel stop it lets the spring go solid before the cell lands")
    # THE GABLE CLEARS A ROUND SPRING, AND IT IS A TANGENCY, NOT A WIDTH. The roof is a chord
    # across the corner, so "the bore is wider than the spring" is not the question -- the
    # perpendicular distance from the axis to the roof line is. Stated as the inequality it is,
    # with the angle held to the same 50 the dovetail is.
    _sa = math.degrees(math.atan2(SPRING_GABLE_RISE, SPRING_BORE / 2))
    _sd = (SPRING_GABLE_Z + SPRING_GABLE_RISE) * math.cos(math.radians(_sa))
    assert _sa >= 50.0, (
        f"the spring tunnel's gable runs at {_sa:.1f} deg from horizontal. 45 is the print "
        f"limit and every roof in this part is held to 50 -- there is no reason for this one "
        f"to be the exception")
    assert _sd >= SPRING_OD / 2 + 0.20, (
        f"the gable line passes {_sd:.2f}mm from the bore's axis against a {SPRING_OD/2:.2f} "
        f"spring radius. The roof is a CHORD across the corner: it comes closer than the flat "
        f"it replaces, and 'the bore is wide enough' is the wrong question")
    assert (SPRING_GABLE_Z + SPRING_BORE/2) * math.cos(math.radians(45.0)) < SPRING_OD/2 + 0.20, (
        "control failed: a 45-degree gable on this bore reads as clearing the spring with "
        "margin, so the tangency test cannot reject the profile it was written to reject")
    print(f"  [spring]  tunnel y {SPRING_TUN_Y0:.2f}..{BAY_Y1:.2f} ({SPRING_TUN_L:.2f} of a "
          f"{SPRING_FREE:.2f} free length inside a closed d{SPRING_BORE:.2f} bore, gable "
          f"{_sa:.1f} deg, roof {_sd:.2f} from the axis vs a {SPRING_OD/2:.2f} radius)")
    print(f"             CAPTIVE: lifted 2.00 toward the open side it hits {_spr_up:.1f} mm3 of "
          f"cover; the same lift outside the tunnel is free ({_spr_out:.2f} mm3)")
    print(f"             mouth at {SPRING_TUN_Y0:.2f} vs the longest cell's {_cell_end:.2f}: "
          f"{SPRING_TUN_Y0-_cell_end:.2f} clear in service, and a hard stop at a "
          f"{BAY_Y1-SPRING_TUN_Y0:.2f} spring length vs {SPRING_SOLID} solid")

    # ---- 8h. THE "+" CONTACT KERF.  Bounded BOTH ways, because one bound is meaningless. ----
    #
    # A slot too narrow does not take the strip; a slot too wide does not hold it. The same
    # probe answers both, measured on the finished solid at the plate's own mid-height.
    _kz = (CONTACT_Z0 + CONTACT_Z1) / 2
    _kpr = bx(CELL_AXIS_X - 0.20, CELL_AXIS_X + 0.20, CELL_TIP_Y - 1.50, CELL_TIP_Y,
              _kz - 0.20, _kz + 0.20)
    _kw = (_kpr - cov).volume / (0.40 * 0.40)          # the slot's depth in Y, measured
    assert _kw >= CONTACT_T + 0.05, (
        f"the contact kerf measures {_kw:.3f}mm deep against a {CONTACT_T}mm strip -- it will "
        f"not take the metal it is dimensioned for")
    assert _kw <= CONTACT_KERF + 0.05, (
        f"the contact kerf measures {_kw:.3f}mm against a designed {CONTACT_KERF:.2f} -- the "
        f"strip rattles, and a rattling contact is an intermittent one")
    # THE DETENT ACTUALLY INTERFERES. Above the seated plate the bar must leave LESS than the
    # strip's thickness, or it is decoration; and MORE than nothing, or the plate cannot pass.
    _dz = CONTACT_Z1 + CONTACT_DET_H / 2
    _dpr = bx(CELL_AXIS_X - 0.20, CELL_AXIS_X + 0.20, CELL_TIP_Y - 1.50, CELL_TIP_Y,
              _dz - 0.10, _dz + 0.10)
    _dw = (_dpr - cov).volume / (0.40 * 0.20)
    assert _dw < CONTACT_T, (
        f"the detent leaves {_dw:.3f}mm of clear kerf against a {CONTACT_T}mm strip -- the "
        f"plate slides straight back out and the detent is decoration")
    assert _dw > 0.05, (
        f"the detent leaves only {_dw:.3f}mm -- that is a wall, not a detent, and the plate "
        f"cannot be got in past it at all")
    # THE TAB HAS A WAY OUT. The kerf must run unbroken from the plate to the divider's wire
    # groove, or the strip is captive and its tab is not.
    _tpr = bx(CELL_X1 - WGROOVE_D - 0.20, CELL_X1 - WGROOVE_D + 0.20,
              CELL_TIP_Y - CONTACT_KERF + 0.05, CELL_TIP_Y, BACK_Z - 3.0, BACK_Z - 2.6)
    _topen = (_tpr - cov).volume / _tpr.volume
    assert _topen > 0.90, (
        f"the tab lane is only {100*(1-_topen):.0f}% open where it meets the divider's wire "
        f"groove -- the +ve tab has no route to the protection strip")
    print(f"  [contact] kerf {_kw:.3f} measured (CONTACT_T {CONTACT_T} JP-confirmed material + "
          f"CONTACT_PLAY {CONTACT_PLAY} derived here); detent leaves {_dw:.3f} < {CONTACT_T}")
    print(f"             plate seat z {CONTACT_Z0:.2f}..{CONTACT_Z1:.2f}, throat open to "
          f"{BACK_Z:.2f}, tab lane to the divider {100*_topen:.0f}% open")

    # ---- 9. THE SPEAKER RELIEF IS INSIDE THE CAVITY, NOT STRADDLING ITS WALL ----
    #
    # Inside is correct and wanted: it is the shortest possible route from the driver's pigtail
    # to the connector #33 pins down, and it is ONE hole to seal after wiring. Straddling the
    # rim wall would be unsealable at all, which is the failure this assert exists for.
    assert (E.SPK_RELIEF_Y[0] > RIM_Y0 and E.SPK_RELIEF_Y[1] < RIM_Y1
            and E.SPK_RELIEF_X0 > RIM_X0 and E.SPK_RELIEF_X0 < RIM_X1), (
        f"the SPK relief (x>={E.SPK_RELIEF_X0}, y {E.SPK_RELIEF_Y}) is not wholly inside the "
        f"seal rim (x {RIM_X0}..{RIM_X1}, y {RIM_Y0}..{RIM_Y1}). If it straddles the rim wall "
        f"the cavity cannot be sealed after wiring at all")
    print(f"  [spk wire] relief x>={E.SPK_RELIEF_X0} y {E.SPK_RELIEF_Y} lies inside the rim. "
          f">>> SEAL IT AFTER WIRING -- silicone, hot glue or putty <<<")

    # ---- 10. THE CELL LEAD PASS IS ACTUALLY OPEN.  Measure the aperture. ----
    # ember_case.py's own lesson at the stand's wire pass: "an absence cannot collide, and
    # neither can an absence that failed to happen." So probe the hole, not the constants.
    lead_probe = bx(LEAD_X0 + 0.2, LEAD_X1 - 0.2, LEAD_Y0 + 0.2, LEAD_Y1 - 0.2,
                    BACK_Z, CAV_FLOOR)
    _blocked = (mf & lead_probe).volume
    assert _blocked < 0.01, (
        f"{_blocked:.3f}mm3 of material still blocks the cell-lead pass through the midframe "
        f"floor -- the battery has no route to CONN_L[0] (BAT)")
    _ctl_probe = Pos(12.0, 0, 0) * lead_probe
    assert (mf & _ctl_probe).volume > 1.0, (
        "control failed: the lead-pass probe reads open even where the floor is solid")
    print(f"  [bat wire] lead pass to CONN_L[0] {E.CONN_L[0]} is open ({_blocked:.4f} mm3 "
          f"blocked); control on solid floor blocks "
          f"{(mf & _ctl_probe).volume:.1f} mm3")

    # ---- 11. THE COVER SCREW ----
    _head_z = COVER_Z0 + CBORE_DEPTH
    _tip_z = _head_z + MOB_SCREW_LEN
    _eng = _tip_z - BACK_Z
    assert _eng >= 3.0, (
        f"only {_eng:.2f}mm of thread engagement into the brow with an M3x{MOB_SCREW_LEN:.0f} "
        f"-- the cover is not clamped")
    assert _eng <= MOB_PILOT_DEPTH - 0.5, (
        f"the screw tip reaches {_eng:.2f}mm into a {MOB_PILOT_DEPTH}mm pilot -- it bottoms out "
        f"on the end of the hole before it clamps, and that failure looks exactly like success")
    print(f"  [screw]   M3 x {MOB_SCREW_LEN:.0f} under-head; head at z {_head_z:.2f}, "
          f"{_eng:.2f}mm engaged in an {MOB_PILOT_DEPTH:.1f}mm pilot")

    # ---- 11b. THE COUNTERBORE IS A HOLE, NOT A NOTCH. ----
    #
    # The widest circular feature at a fastener is the counterbore, and it must clear every
    # edge of the part it is sunk into or the head loses its annular seat on that side. This is
    # the check that was missing when the screw sat at y=19.20 and d5.80 hung 1.70mm off the
    # cover's bottom edge -- caught by looking at a slice, not by any number.
    # The coordinate form of this runs at module level (it has to -- the chamfer dies first).
    # Here it is measured on the ARTIFACT: the counterbore's rim must be a closed ring of
    # material, not a shape interrupted by the part's outline.
    _fx, _fy = SCREW_XY
    _ann = (SCREW_BOSS_D - CBORE_D) / 2
    assert _ann >= E.BOSS_MIN_ANN, (
        f"the head bears on only {_ann:.2f}mm of annulus, under ember_case's BOSS_MIN_ANN of "
        f"{E.BOSS_MIN_ANN}. CBORE_DEPTH {CBORE_DEPTH} exceeds COV_WALL {COV_WALL}, so the seat "
        f"is the boss and not the wall -- widen SCREW_BOSS_D, do not thin the counterbore")
    _seat = (cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH, COVER_Z0 + CBORE_DEPTH + 0.20,
                 SCREW_BOSS_D - 0.40)
             - cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH - 1, COVER_Z0 + CBORE_DEPTH + 2, CBORE_D))
    _sfrac = (cov & _seat).volume / _seat.volume
    assert _sfrac > 0.98, (
        f"the counterbore's seat is only {100*_sfrac:.1f}% material -- the head has no annular "
        f"bearing on part of its circumference, which is what a bore that breaks out looks like")
    # CONTROL: an annulus wider than the boss must NOT read solid, or the probe proves nothing.
    _wide = (cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH, COVER_Z0 + CBORE_DEPTH + 0.20,
                 SCREW_BOSS_D + 6.0)
             - cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH - 1, COVER_Z0 + CBORE_DEPTH + 2,
                   SCREW_BOSS_D + 1.0))
    _wfrac2 = (cov & _wide).volume / _wide.volume
    assert _wfrac2 < 0.95, (
        f"control failed: the seat probe reads {100*_wfrac2:.1f}% solid even outside the boss, "
        f"so it cannot distinguish a seated head from an unsupported one")
    print(f"  [cbore]   d{CBORE_D} counterbore at ({_fx:.2f}, {_fy:.2f}): "
          f"{_fy - COVER_Y0:.2f}mm to the bottom edge (needs {SCREW_EDGE_MIN:.2f}); "
          f"annulus {_ann:.2f} (min {E.BOSS_MIN_ANN}); seat {100*_sfrac:.1f}% solid, "
          f"control outside the boss {100*_wfrac2:.1f}%")

    # ---- 8f. THE RAILS STAND ON SOMETHING, AND CLEAR EVERYTHING THEY MUST. ----
    #
    # The old hook B needed a purpose-built pillar because it sat over open compartment. The
    # rails do not -- they sit on the cover's own long walls the whole way -- but "sits on the
    # wall" is exactly the sort of claim that survives a wall moving, so it is measured.
    # ⚠️ THE PROBE IS CLAMPED TO THE COVER'S OWN WALL, and that clamp is the documented 0.10.
    # The tooth's bed footprint runs to u = 2.30 against a COV_WALL of 2.20, so 0.10 of it hangs
    # over the bay's open mouth by design (see 5g). Probing the full 0.60 would read 83% and
    # report a defect that is a stated tolerance; probing the wall's share reads what the
    # question actually is -- is there a wall under this tooth at all.
    _cant = (DT_SKIN + DT_UNDER + DT_CLR + DT_NECK) - COV_WALL
    assert 0.0 <= _cant <= 0.20, (
        f"the tooth's bed footprint overhangs the cover's wall by {_cant:.2f}mm. Up to 0.20 is "
        f"a step the process absorbs under a {DT_NECK:.2f} bead; past that it is a cantilever "
        f"and needs a buttress")
    _root_min = 1.0
    for _side, _ry0, _ry1 in DT_RAILS:
        _s = 1.0 if _side == "lo" else -1.0
        _a = (OX0 if _side == "lo" else OX1) + _s * (DT_SKIN + DT_UNDER + DT_CLR)
        _b = (OX0 if _side == "lo" else OX1) + _s * COV_WALL
        for _ty in _dt_teeth(_ry0, _ry1):
            _pr = bx(min(_a, _b), max(_a, _b), _ty, _ty + DT_TOOTH, BACK_Z - 0.60, BACK_Z - 0.10)
            _root_min = min(_root_min, (cov & _pr).volume / _pr.volume)
    assert _root_min > 0.95, (
        f"a dovetail tooth stands on only {100*_root_min:.1f}% material just under the mating "
        f"plane -- the rail is growing out of open bay and would print as a floating fin")
    # CONTROL: the same probe run over the bay, one wall thickness inboard, must read ~empty.
    _cpr = bx(CELL_X0 + 0.10, CELL_X0 + 0.70, _dt_teeth(*DT_RAILS[0][1:])[3],
              _dt_teeth(*DT_RAILS[0][1:])[3] + DT_TOOTH, BACK_Z - 0.60, BACK_Z - 0.10)
    _croot = (cov & _cpr).volume / _cpr.volume
    assert _croot < 0.10, (
        f"control failed: the root probe reads {100*_croot:.1f}% solid over the OPEN cell bay, "
        f"so it cannot tell a tooth on a wall from a tooth on nothing")
    # ---- and the four things a groove in a side wall can run into. All in coordinates,
    # because each of them is a different part of the file that has no idea the rails exist.
    # ⚠️ THE GLOW WINDOW'S SITE IS SOLVED AT RUNTIME, so whether it shares a wall AND a Y band
    # with a rail is a RESULT, not a constant — and it changed the day SPK's flank opening was
    # suppressed, because that widened the solid span the search runs over. So the Z clearance
    # is asserted where the two actually overlap in Y and REPORTED where they do not, rather
    # than asserted unconditionally and quietly becoming an invariant that cannot fail.
    _gtop = BACK_Z + DT_DEPTH
    _glow_z0 = GLOW_CZ - GLOW_AF / 2
    _gy0, _gy1 = GLOW_CY - GLOW_SPAN_Y/2, GLOW_CY + GLOW_SPAN_Y/2
    _glow_shares = [(_a, _b) for _s, _a, _b in DT_RAILS
                    if _s == GLOW_WALL and _a < _gy1 and _b + DT_CLR_Y > _gy0]
    if _glow_shares:
        assert _gtop <= _glow_z0 - 0.60, (
            f"a {GLOW_WALL}-wall rail shares y {_glow_shares} with the WS2812 window and the "
            f"groove's gable reaches z={_gtop:.2f} against a window pocket starting at "
            f"z={_glow_z0:.2f} -- under 0.60 of material between two voids in one wall")
    else:
        assert min(abs(_a - _gy1) for _s, _a, _b in DT_RAILS if _s == GLOW_WALL) > 0.0, (
            "control: the rails and the window were compared on the wrong wall")
    assert DT_SKIN + DT_WIDE <= WALL + 1e-9, (
        f"the groove reaches {DT_SKIN + DT_WIDE:.2f} inboard of the outer face, past the "
        f"{WALL:.2f} side wall, so it is cutting the board-cavity floor instead of the wall")
    # >>> AND THE Z BUDGET, WHICH IS THE CONSTRAINT THAT PICKED THE CROSS-SECTION. <<<
    #
    # The side wall is 17.40 tall, but ember_case.py:1541 cuts the CABLE CHANNELS through its
    # full thickness at z CAV_FLOOR..PCB_BOT, and the rails cross every one of them. Over those
    # Y spans the only material the groove has is the 2.60 floor beneath. Measured on the
    # midframe rather than asserted from constants, because the channels are computed in
    # ember_case from the connector tables and can move without anyone here noticing.
    _lint_min, _lint_where = 99.0, "no channel crosses a rail"
    for _side, _ry0, _ry1 in DT_RAILS:
        _s = 1.0 if _side == "lo" else -1.0
        _bx0 = (OX0 if _side == "lo" else OX1) + _s * DT_SKIN
        _bx1 = (OX0 if _side == "lo" else OX1) + _s * (DT_SKIN + DT_WIDE)
        for _ca, _cb in (MOB_CH_LO if _side == "lo" else MOB_CH_HI):
            _oa, _ob = max(_ca, _ry0), min(_cb, _ry1)
            if _ob - _oa < 0.5:
                continue
            _pr = bx(min(_bx0, _bx1), max(_bx0, _bx1), _oa + 0.2, _ob - 0.2,
                     BACK_Z + DT_DEPTH, CAV_FLOOR)
            _lf = (mf & _pr).volume / _pr.volume if _pr.volume > 0 else 1.0
            if _lf < 0.98:
                _lint_min = 0.0
                _lint_where = f"{_side} wall, channel y {_ca:.2f}..{_cb:.2f}"
            else:
                _lint_min = min(_lint_min, CAV_FLOOR - (BACK_Z + DT_DEPTH))
                _lint_where = f"{_side} wall, channel y {_ca:.2f}..{_cb:.2f}"
    assert _lint_min >= 0.60, (
        f"the lintel between the groove's gable and the side cable channel measures "
        f"{_lint_min:.2f}mm at {_lint_where}. Under 0.60 (3 layers) the groove and the channel "
        f"are one void and the wall loses its section -- shorten DT_DEPTH, do not move the rail")
    print(f"             cable-channel lintel {_lint_min:.2f}mm ({_lint_where}); the groove is "
          f"{DT_DEPTH:.2f} of the {CAV_FLOOR - BACK_Z:.2f} that lies under those channels")
    assert DT_SKIN >= CHAMFER, (
        f"only {DT_SKIN:.2f} of skin outboard of the groove against a {CHAMFER} bed chamfer -- "
        f"the groove would break out through the chamfered edge and stop being a groove")
    _lead_gap = LEAD_X0 - (OX0 + DT_SKIN + DT_WIDE)
    assert _lead_gap >= 0.30, (
        f"the cell-lead pass starts at x={LEAD_X0:.2f}, only {_lead_gap:.2f} from the -X "
        f"groove's inboard face -- it punches through the rail's own wall")
    _vent_gap = BACK_Z - VENT_Z1
    assert _vent_gap >= 1.20, (
        f"only {_vent_gap:.2f}mm of cover wall between the vent's top and the mating plane the "
        f"rail grows from -- the rail has no root over the vent's Y span")
    for _side, _ry0, _ry1 in DT_RAILS:
        _gx0 = (OX0 + DT_SKIN) if _side == "lo" else (OX1 - DT_SKIN - DT_WIDE)
        # ⚠️ BOTH OUTLINES, NOT JUST THE COVER'S. The tooth belongs to the cover and the groove
        # to the midframe, and they turn their top corners at DIFFERENT Y -- MOB_OY1 - OUT_R
        # for the cover's brow, OY1 - OUT_R for back_shell, 6.45 apart. Checking only the
        # cover's let a rail run 3.05mm into the midframe's arc, where the skin outboard of the
        # groove thins toward breakout. Check 8c measured it at 79.7% of a shoulder.
        for _lim, _whose in ((MOB_OY1 - OUT_R, "the cover's brow"),
                             (OY1 - OUT_R, "back_shell (the midframe's outline)")):
            assert _ry1 + DT_CLR_Y <= _lim, (
                f"a rail runs to y={_ry1 + DT_CLR_Y:.2f}, into {_whose}'s OUT_R corner arc "
                f"which starts at {_lim:.2f} -- the outer face is no longer flat there, so the "
                f"skin outboard of the groove thins and the shoulder stops being solid")
        for _cx, _cn in ((E.BTN_BOOT_X, "BOOT"), (E.BTN_RESET_X, "RESET")):
            _cy, _R, _ = E.cap_geometry(_cx)
            assert abs(_cx - (_gx0 + DT_WIDE/2)) > _R + DT_WIDE, (
                f"the {_side} groove passes within {abs(_cx - _gx0):.2f} of the {_cn} cap at "
                f"x={_cx} -- a slot there cuts the living hinge")
    print(f"  [rails]   {len(DT_RAILS)} rails, worst tooth root {100*_root_min:.1f}% solid on "
          f"the cover's own wall (no pillars needed, unlike the hooks)")
    print(f"             clearances: glow window {_glow_z0 - _gtop:.2f} in Z (shares Y with a rail: "
          f"{bool(_glow_shares)}), lead pass "
          f"{_lead_gap:.2f} in X, vent-to-mating-plane {_vent_gap:.2f}, groove depth "
          f"{DT_SKIN + DT_WIDE:.2f}/{WALL:.2f} of side wall, skin {DT_SKIN:.2f} vs "
          f"{CHAMFER} chamfer")

    # ---- 13. THE UPPER COMPARTMENT: what fits now, and what stopped fitting ----
    _prot = prot_phantom()
    _pf = (cov & _prot).volume
    assert _pf < 0.5, (
        f"the protection strip fouls the cover by {_pf:.2f} mm3 -- the pocket does not hold the "
        f"part it is shaped for")
    # >>> AND THE LOSS, MEASURED RATHER THAN CLAIMED. <<<
    # Re-primarying to bare cells shortened the compartment past a TP4056. Saying "it no longer
    # fits" in a comment is the kind of statement that goes stale silently; this collides the
    # phantom and reports the number, so if the compartment ever grows back the assert stops
    # holding and somebody has to look.
    _tpf = (cov & tp4056_phantom()).volume
    _free_y = BAY_Y1 - (RIM_Y1 + RIM_WALL)
    assert _tpf > 1.0, (
        f"a TP4056 phantom now fits the compartment ({_tpf:.2f} mm3 of interference) -- the "
        f"design note and #44 say it does not. One of them is wrong")
    # ---- 13b. THE PCB SITS ON A FLAT FLOOR, AND THE JOINTS ARE REACHABLE ----
    # A rib under a PCB is a rock under a board. Measured, because "the ribs are outside the
    # footprint" is exactly the kind of claim that survives a footprint moving.
    _floor = bx(PROT_CX - PROT_L/2, PROT_CX + PROT_L/2, PROT_Y1 - PROT_W, PROT_Y1,
                CAV_Z0 + 0.02, CAV_Z0 + PROT_RIB_H)
    _fint = (cov & _floor).volume
    assert _fint < 0.5, (
        f"{_fint:.2f} mm3 of material stands inside the strip's own footprint -- a rib or a tab "
        f"slot wall is under the PCB and it will not sit flat")
    # SOLDER ACCESS: nothing may overhang the pocket from above, or an iron cannot reach the
    # tabs with the strip seated. The compartment is open to +Z by construction; prove it.
    # ⚠️⚠️ CLAMPED TO THE FOOTPRINT — AND THIS IS THE THIRD TIME. The vent throat probe swept
    # air outside the part; the polarity-marking probe swept the contact pocket; this one, at
    # +/-1.0 of margin, swept 0.60 of divider on one side and 0.60 of case wall on the other and
    # reported 162.24 mm3 of "overhang" that is simply the compartment's own walls.
    #
    # >>> STANDING RULE FOR EVERY PROBE IN THIS FILE: its extent is the FEATURE's extent. <<<
    # A margin "to be safe" is not safe — it silently annexes whatever is next door, and the
    # error is always in the direction that makes the number look worse or better than it is.
    # Two of the three were caught only because the check carried a bound in BOTH directions.
    _sky = bx(PROT_CX - PROT_L/2, PROT_CX + PROT_L/2,
              PROT_Y1 - PROT_W, PROT_Y1,
              CAV_Z0 + PROT_T + PROT_COMP_CLR, BACK_Z)
    _sint = (cov & _sky).volume
    assert _sint < 0.5, (
        f"{_sint:.2f} mm3 overhangs the strip pocket above the component face -- the joints are "
        f"not reachable with an iron once the strip is seated")
    assert PROT_L <= PROT_L_MAX + 1e-9, (
        f"the protection strip is {PROT_L:.2f} long but the compartment only seats "
        f"{PROT_L_MAX:.2f} flat -- short by {PROT_L-PROT_L_MAX:.2f}mm. It does not fit rotated "
        f"({_free_y:.2f} of Y), on edge ({BACK_Z-CAV_Z0:.2f} of depth) or diagonally. Either the "
        f"strip is wrong for this case or the case has to grow in X, which moves the bezel")
    print(f"  [strip]   1S protection PCB {PROT_L:.2f} x {PROT_W:.2f} x {PROT_T:.2f} "
          f"(⚠️ UNMEASURED — awaiting JP's calipers); max that seats flat {PROT_L_MAX:.2f}")
    print(f"             ⚠️ the briefed class figure {PROT_L_CLASS:.2f} EXCEEDS that by "
          f"{PROT_L_CLASS-PROT_L_MAX:.2f}mm and will not fit in any orientation")
    print(f"             floor under the PCB {_fint:.2f} mm3 (flat, no ribs); "
          f"clear sky above {_sint:.2f} mm3 (iron reaches the joints)")
    print(f"             tabs: {TAB_W:.2f} x {TAB_D:.2f} slots, -X end -> divider groove -> "
          f"+plate & BAT pass; +X end -> spring. Cell stays BARE and removable.")
    print(f"  [pocket]  free compartment {RIM_X1-RIM_X0:.2f} x {_free_y:.2f}; strip "
          f"{PROT_L}x{PROT_W}x{PROT_T} FITS ({_pf:.2f} mm3 foul)")
    print(f"             TP4056 {TP_W}x{TP_L} DOES NOT ({_tpf:.0f} mm3 of interference) -- its "
          f"short axis is {TP_L} against {_free_y:.2f} of Y. Restoring it costs the "
          f"{5.90:.2f}mm the bare-cell re-primary saved. JP's trade, stated in #44.")
    print(f"             charge: onboard {CHARGE_MA:.0f} mA -> "
          f"{CELL_CAPACITY_MAH/CHARGE_MA*CHARGE_CV_FACTOR:.1f} h  (docs/enclosure.md:165)")

    # ---- 14. THE WS2812.  OCCLUDED, AND THE OCCLUSION IS PROVEN, NOT ASSUMED. ----
    #
    # docs/enclosure.md:161 already states the general case: "WS2812 RGB LED (GPIO42) is on the
    # BACK, inboard, and fires backwards. A CLOSED BACK COVER HIDES IT COMPLETELY." So this is a
    # documented property of any back cover, not something this variant introduced. What IS
    # this variant's to answer is whether the geometry leaves a way out, and it does not:
    #
    #   * the LED is inside the DRIVER's footprint, so the module's body is the first thing in
    #     front of it -- a window in the plateau would look straight at the back of the speaker;
    #   * and the driver CANNOT be moved off it. The sealed cavity must contain the SPK relief
    #     (the wire's only exit, check 9), the driver is DRIVER_W long, and clearing the LED
    #     would need the driver wholly above or wholly below it. Both overrun the cavity.
    #
    # That second clause is the real finding, so it is computed rather than asserted in prose:
    # if a future change frees the LED, this stops being true and the note above becomes wrong.
    _lx, _ly = E.LED
    _in_drv = (DRV_CX - DRIVER_H/2 <= _lx <= DRV_CX + DRIVER_H/2
               and DRV_CY - DRIVER_W/2 <= _ly <= DRV_CY + DRIVER_W/2)
    _above_ok = (_ly + 0.5) + DRIVER_W <= RIM_Y1      # driver entirely beyond the LED, +Y
    _below_ok = (_ly - 0.5) - DRIVER_W >= RIM_Y0      # ...or entirely before it, -Y
    _relief_in = RIM_Y0 < E.SPK_RELIEF_Y[0] and E.SPK_RELIEF_Y[1] < RIM_Y1
    assert _in_drv and not _above_ok and not _below_ok and _relief_in, (
        f"the WS2812 occlusion derivation no longer holds: LED {E.LED} in driver footprint="
        f"{_in_drv}, could sit above={_above_ok}, below={_below_ok}, relief inside rim="
        f"{_relief_in}. If the LED is now clear of the driver, DO NOT delete this assert -- "
        f"add the hex diffuser window (a thinned floor of 2-4 x {LH}, never a through-hole, so "
        f"the cavity stays sealed) and re-point it at that")
    print(f"  [ws2812]  LED {E.LED} lies inside the driver footprint "
          f"x {DRV_CX-DRIVER_H/2:.2f}..{DRV_CX+DRIVER_H/2:.2f} "
          f"y {DRV_CY-DRIVER_W/2:.2f}..{DRV_CY+DRIVER_W/2:.2f}; a {DRIVER_W:.0f}mm driver "
          f"cannot clear it inside a {RIM_Y1-RIM_Y0:.2f}mm cavity that must hold the SPK "
          f"relief. OCCLUDED BY CONSTRUCTION (docs/enclosure.md:161 says as much for any "
          f"closed back cover). The 2.8in display is the battery indicator.")

    # ---- 15. POLARITY MARKINGS.  The only reverse-insertion measure that remains. ----
    #
    # ⚠️ min_gap IS NOT THE PROOF HERE AND MUST NOT BE. Measured: min_gap(MARK_PATHS_P, LABEL_W)
    # returns (inf, 0 pairs) -- the "+" strokes cross, so _touch() drops the only pair; "-" has
    # a single stroke and no pair at all. `min_gap >= LABEL_W` would therefore pass on `inf` for
    # ANY glyph of this shape, sound or broken. So the debossed VOLUME is measured on the
    # finished solid against the ink area x depth, which fails if a groove closes up, lands off
    # the wall, or is swallowed by the pocket behind it.
    import strokefont as _SF
    for _nm, _pp in (("+", MARK_PATHS_P), ("-", MARK_PATHS_N)):
        _d, _pair, _n = _SF.min_gap(_pp, E.LABEL_W)
        assert _n == 0 and _d == float("inf"), (
            f"min_gap now reports {_n} pairs on '{_nm}' -- it has become meaningful and should "
            f"be asserted properly instead of documented as vacuous")
    # two stadium strokes crossing, minus the doubly-counted square; "-" is one stadium
    _ink_p = 2*(MARK_H*E.LABEL_W + math.pi*(E.LABEL_W/2)**2) - E.LABEL_W**2
    _ink_n = MARK_H*E.LABEL_W + math.pi*(E.LABEL_W/2)**2
    # ⚠️ THE PROBE IS CLAMPED TO THE FREE END-WALL FACE, and the first version was not. At
    # +/-MARK_INK it reached DOWN into the contact pocket and UP past BACK_Z into open air,
    # reporting 25.48 mm2 against 4.87 of ink -- 20 mm2 of it space that is not the marking.
    # Exactly the vent-throat probe's mistake, caught this time only because this check carries
    # an UPPER bound as well as a lower one. A one-sided assert would have sailed through.
    # ...and the probe now follows _mark_face() in ALL FOUR coordinates, because the two glyphs
    # no longer share a face, a wall, or even a part of the bay: "+" is on the low-Y end wall
    # below the contact kerf, "-" is on the spring tunnel's mouth. One derivation feeds the
    # geometry and this probe, so a marking cannot move without its check moving with it -- and
    # the box is clamped to the ink in X and Z as well as Y, which the old whole-face version
    # was not.
    for _nm, _ink in (("+", _ink_p), ("-", _ink_n)):
        _mx, _mz, _y0, _y1 = _mark_face(_nm)
        _pr = bx(_mx - MARK_INK/2 - 0.30, _mx + MARK_INK/2 + 0.30, _y0, _y1,
                 _mz - MARK_INK/2 - 0.30, _mz + MARK_INK/2 + 0.30)
        _cut = (_pr - cov).volume / MARK_DEPTH
        assert _cut >= 0.80 * _ink, (
            f"the '{_nm}' marking removed only {_cut:.2f} mm2 of face against {_ink:.2f} of ink "
            f"-- the deboss is missing, clipped by the end wall, or absorbed into the pocket")
        assert _cut <= 1.60 * _ink, (
            f"the '{_nm}' probe reads {_cut:.2f} mm2 against {_ink:.2f} of ink -- it is counting "
            f"the bore or the contact pocket, not the marking")
    print(f"  [marks]   '+' and '-' debossed {MARK_DEPTH:.2f} into the bay end walls, "
          f"{MARK_H:.2f} tall, {E.LABEL_W} groove; area measured against ink both ways")
    print(f"             min_gap is VACUOUS on these glyphs (inf, 0 pairs) and is asserted to "
          f"STAY vacuous rather than used as a proof")
    print(f"             ⚠️ NO MECHANICAL KEYING IS POSSIBLE FOR FLAT-TOP CELLS -- both ends are "
          f"identical. Reverse-insertion protection is MARKINGS ONLY. Electrical, JP's call.")

    # ---- 16. THE FAILURE VENT: throat area, AND no line of sight. ----
    #
    # Two properties, and each is silent without the other: a vent big enough to be useful that
    # is a straight hole, or a proper labyrinth so tight nothing flows.
    # ⚠️ THE PROBE IS CLAMPED TO THE WALL, AND THE FIRST VERSION WAS NOT. Spanning
    # OX0-0.5 .. CELL_X0+0.5 swept in 0.50mm of air OUTSIDE the part and 0.50mm of BAY INTERIOR
    # either side of a 2.20 wall: 4.50 + 4.50 mm2 of free space per unit on top of the 4.20 that
    # is actually the vent. It reported 52.80 where the truth is 16.80 -- and worse, with the
    # band deleted entirely it would still have read 36.00 and passed. AN ASSERT THAT CANNOT
    # FAIL. It only surfaced because the measured number beat the analytic one by 3x and that
    # is a defect signal, not a win.
    _throat = 0.0
    for (iy0, iy1), (oy0, oy1), _b in _vent_units():
        _yr = (iy1 + oy0) / 2.0          # the rib: the one Y where only the band is open
        _pr = bx(OX0, CELL_X0, _yr - 0.01, _yr + 0.01, VENT_Z0 - 1, VENT_Z1 + 1)
        _throat += (_pr - cov).volume / 0.02
    # CONTROL, in the direction the old probe could not go: between two units the wall is solid
    # and the same measurement must read ~0. Without this, "the wall is open" and "the probe is
    # measuring fresh air" are the same number.
    _solid_y = VENT_Y0 + 2*VENT_W + VENT_RIB + VENT_GAP/2
    _spr = bx(OX0, CELL_X0, _solid_y - 0.01, _solid_y + 0.01, VENT_Z0 - 1, VENT_Z1 + 1)
    _sopen = (_spr - cov).volume / 0.02
    assert _sopen < 0.5, (
        f"control failed: the wall between two vent units measures {_sopen:.2f} mm2 open, so "
        f"the throat probe is counting something other than the vent")
    assert _throat >= CELL_PORTS_MM2, (
        f"the vent throat is {_throat:.2f} mm2 against an assumed {CELL_PORTS_MM2:.2f} mm2 of "
        f"cell vent port -- the ENCLOSURE is the restriction, which is the one thing it must "
        f"not be")
    # >>> AND NO STRAIGHT PATH.  At each OUTER slot's Y the wall must still be obstructed. <<<
    _los_min = 1.0
    for _i, (_ii, (oy0, oy1), _b) in enumerate(_vent_units()):
        _pr = bx(OX0, CELL_X0, (oy0+oy1)/2 - 0.01, (oy0+oy1)/2 + 0.01,
                 VENT_Z0 + 0.5, VENT_Z1 - 0.5)
        _los_min = min(_los_min, (cov & _pr).volume / _pr.volume)
    assert _los_min > 0.25, (
        f"a straight line through the wall at a vent's outer slot finds only "
        f"{100*_los_min:.1f}% material -- the labyrinth has become a hole, and it is a light "
        f"and dust path straight into the cell bay")
    # CONTROL: drill one unit through and prove the probe actually detects it.
    (_ci, (_co0, _co1), _cb) = _vent_units()[0]
    _drilled = cov - bx(OX0 - 1, CELL_X0 + 1, _co0, _co1, VENT_Z0, VENT_Z1)
    _cpr = bx(OX0, CELL_X0, (_co0+_co1)/2 - 0.01, (_co0+_co1)/2 + 0.01,
              VENT_Z0 + 0.5, VENT_Z1 - 0.5)
    _cfr = (_drilled & _cpr).volume / _cpr.volume
    assert _cfr < 0.05, (
        f"control failed: a wall deliberately drilled through still reads {100*_cfr:.1f}% "
        f"material, so the line-of-sight probe cannot detect a straight hole")
    # >>> AND IT IS INDEPENDENT OF THE FLANK OPENINGS, WHICH IS NOW WORTH SAYING OUT LOUD. <<<
    #
    # Suppressing SPK and BAT on this variant removed an INCIDENTAL secondary path a cell's gas
    # could have taken -- bay -> the shell's hex field -> board cavity -> a side channel -> out.
    # That path was never the answer and was never measured; the engineered one is these four
    # labyrinth units, and they are in the COVER's -X wall, exiting straight to outside air at
    # a Z band (VENT_Z0..VENT_Z1) nowhere near the midframe's flank channels
    # (CAV_FLOOR..PCB_BOT, a different part). So the blocks cannot have tightened it -- but
    # "cannot" is what this file measures rather than argues, and the throat above is the
    # re-measured number, taken after the blocks, on the built solid.
    assert VENT_Z1 < CAV_FLOOR and VENT_Z0 < CAV_FLOOR, (
        f"the cell vent's Z band ({VENT_Z0:.2f}..{VENT_Z1:.2f}) has risen into the midframe's "
        f"flank-channel band (from {CAV_FLOOR:.2f} up) -- the two features now share a wall and "
        f"suppressing a channel could throttle the vent")
    print(f"  [vent]    {VENT_N} labyrinth units, throat {_throat:.2f} mm2 vs an assumed "
          f"{CELL_PORTS_MM2:.2f} mm2 of cell port ({_throat/CELL_PORTS_MM2:.2f}x); "
          f"band {VENT_BAND:.2f} x {VENT_Z1-VENT_Z0:.2f}, skin {VENT_SKIN:.2f} each face")
    print(f"             UNAFFECTED BY THE FLANK BLOCKS: this exits the COVER's -X wall direct "
          f"to air at z {VENT_Z0:.2f}..{VENT_Z1:.2f}; the suppressed channels are in the "
          f"MIDFRAME at z {CAV_FLOOR:.2f}..{E.PCB_BOT:.2f}. Re-measured after the blocks.")
    print(f"             control: solid wall between units {_sopen:.2f} mm2 open (must be ~0)")
    print(f"             line of sight: worst outer slot is {100*_los_min:.0f}% obstructed; "
          f"control on a drilled wall {100*_cfr:.1f}% (must be ~0)")

    # ---- 17. THE WS2812 GLOW WINDOW.  Area measured, membrane proven, sited clear. ----
    _wx = (E.BW + E.FIT) if GLOW_WALL == "hi" else -E.FIT
    _ox = OX1 if GLOW_WALL == "hi" else OX0
    _depth = WALL - GLOW_MEMBRANE
    _y0, _y1 = GLOW_CY - GLOW_SPAN_Y/2 - 1, GLOW_CY + GLOW_SPAN_Y/2 + 1
    _z0, _z1 = GLOW_CZ - GLOW_AF/2 - 1, GLOW_CZ + GLOW_AF/2 + 1
    # EXIT AREA: the void in a thin plane just inside the membrane. This is what JP sees lit.
    _cutx = _wx + _dirsign(GLOW_WALL) * (_depth - 0.10)
    _pr = bx(min(_cutx, _cutx + 0.10*_dirsign(GLOW_WALL)),
             max(_cutx, _cutx + 0.10*_dirsign(GLOW_WALL)), _y0, _y1, _z0, _z1)
    _exit = (_pr - mf).volume / 0.10
    _ideal = GLOW_N * 1.5 * math.sqrt(3) * GLOW_R**2
    assert _exit >= 0.90 * _ideal, (
        f"the glow window's exit area measures {_exit:.2f} mm2 against {_ideal:.2f} for "
        f"{GLOW_N} cells -- the cells are being clipped by the wall or by a channel")
    # THE MEMBRANE IS INTACT: the window must be a WINDOW, not a hole into the board cavity.
    _mx0 = _ox - GLOW_MEMBRANE if GLOW_WALL == "hi" else _ox
    _mpr = bx(_mx0, _mx0 + GLOW_MEMBRANE, GLOW_CY - GLOW_SPAN_Y/2, GLOW_CY + GLOW_SPAN_Y/2,
              GLOW_CZ - GLOW_AF/2, GLOW_CZ + GLOW_AF/2)
    _mfrac = (mf & _mpr).volume / _mpr.volume
    assert _mfrac > 0.98, (
        f"the glow membrane is only {100*_mfrac:.1f}% material -- the window has become an open "
        f"hole into the board cavity. Cut from the inner face only")
    # CONTROL: inside the pocket the same probe must read ~empty, or it cannot tell a window
    # from a solid wall.
    _cx = _wx + _dirsign(GLOW_WALL) * 0.60
    _cpr2 = bx(min(_cx, _cx + 0.40*_dirsign(GLOW_WALL)), max(_cx, _cx + 0.40*_dirsign(GLOW_WALL)),
               GLOW_CY - GLOW_AC/2 + 0.6, GLOW_CY - GLOW_AC/2 + 1.4,
               GLOW_CZ - 1.0, GLOW_CZ + 1.0)
    _cfrac2 = (mf & _cpr2).volume / _cpr2.volume
    assert _cfrac2 < 0.10, (
        f"control failed: the wall reads {100*_cfrac2:.1f}% solid INSIDE the window pocket, so "
        f"the membrane probe cannot distinguish a window from an unmodified wall")
    # SITED CLEAR: not in a cable channel (that is what _glow_site solves), and clear of the
    # bosses. The seal rim and the vent are on other faces/parts and cannot be reached from here.
    for _a, _b in (MOB_CH_HI if GLOW_WALL == "hi" else MOB_CH_LO):
        assert (GLOW_CY + GLOW_SPAN_Y/2) < _a or (GLOW_CY - GLOW_SPAN_Y/2) > _b, (
            f"the glow window at y {GLOW_CY-GLOW_SPAN_Y/2:.2f}..{GLOW_CY+GLOW_SPAN_Y/2:.2f} "
            f"overlaps the cable channel at y {_a:.2f}..{_b:.2f} -- it would open into a hole")
    for _hx, _hy in E.HOLES:
        assert math.hypot(_hx - _wx, _hy - GLOW_CY) > E.BOSS_FLARE_D/2 + GLOW_AC/2, (
            f"the glow window is inside the boss flare at {(_hx, _hy)}")
    print(f"  [glow]    WS2812 window: {GLOW_N} hex cells, {GLOW_WALL} wall, GLOW_CY "
          f"{GLOW_CY:.2f} (y {GLOW_CY-GLOW_SPAN_Y/2:.2f}..{GLOW_CY+GLOW_SPAN_Y/2:.2f}), z "
          f"{GLOW_CZ-GLOW_AF/2:.2f}..{GLOW_CZ+GLOW_AF/2:.2f}, GLOW_DIST {GLOW_DIST:.2f}")
    print(f"             SITE IS SOLVED, NOT TYPED, and pinned to GLOW_SITE_EXPECT "
          f"{GLOW_SITE_EXPECT} -- it searches the solid spans between the flank openings, so "
          f"closing one moves it. Web pinned at {GLOW_WEB:.2f} vs the stand's {HEX_WEB:.2f}.")
    print(f"             EXIT AREA {_exit:.2f} mm2 (about {GLOW_SPAN_Y:.1f} x {GLOW_AF:.1f} mm of "
          f"glow, not a pinhole); {GLOW_DIST:.1f} mm from the LED across the cavity")
    print(f"             membrane {GLOW_MEMBRANE:.2f} = 2 extrusions, {100*_mfrac:.1f}% intact "
          f"(control inside the pocket {100*_cfrac2:.1f}%). SEALED — not a hole.")
    print(f"             ⚠️ BRIGHTNESS IS FILAMENT-DEPENDENT: PRINT-SHEET records that white/"
          f"natural PLA is translucent enough for the WS2812 to light the shell. In charcoal "
          f"this will be dim. GLOW_MEMBRANE = 0 makes them true through-holes, which adds no "
          f"ingress class this wall does not already have (3 open cable channels).")
    print(f"             ⚠️ THIS FEATURE IS ON THE MIDFRAME, NOT THE COVER.")

    # ---- 12. BED-FACE RULE: nothing proud of min Z on the cover ----
    # ember_case.py:2771 records this defect on BOTH shell parts in one session, on opposite
    # faces. The tell there was coplanar area at MIN z (71.9mm2) against MAX z (1847.9).
    for _nm in ("ember-mobile-back", "ember-mobile-midframe"):
        _p = parts[_nm]
        _bb = _p.bounding_box()
        _skin = bx(_bb.min.X-1, _bb.max.X+1, _bb.min.Y-1, _bb.max.Y+1,
                   _bb.min.Z, _bb.min.Z + 0.10)
        _area = (_p & _skin).volume / 0.10
        assert _area > 600.0, (
            f"{_nm} touches the bed over only {_area:.1f}mm2 at min Z -- it is balancing on a "
            f"proud feature, which is the bed-face defect ember_case.py:2771 records")
        print(f"  [bed]     {_nm:24s} min-Z contact {_area:8.1f} mm2")
    return True


# ============================================================================
# 8. BUILD
# ============================================================================
# ---- PRINT LIFT.  Both parts are modelled entirely below z=0 (the midframe's bed face is
# BACK_Z, the cover's is COVER_Z0), so the exported mesh must be raised to rest on the bed.
# ember_case.py:2939 -- "a slicer silently drops it onto the bed, so the mistake never surfaces
# as an error", only as a part whose Z is off everywhere a measurement is taken from the mesh.
# Asserted at export, in the same words, for the same reason.
#
# ⚠️ MODULE LEVEL SINCE THE DOVETAILS, AND THAT IS DELIBERATE. It is now load-bearing FOR THE
# GEOMETRY, not just for the export: because it is a pure Z translation with no rotation, model
# +Z is print-up on both parts, which is the only reason an angle written in this file is an
# angle on the bed. Check 8b asserts it before trusting a single overhang number, and a check
# cannot assert a constant that only exists inside `if __name__`.
PRINT_LIFT = {"ember-mobile-midframe": -BACK_Z, "ember-mobile-back": -COVER_Z0}

if __name__ == "__main__":
    assert E._selftest_export_gate()
    out = _HERE
    _committed = False
    print("building mobile parts (midframe composes back_shell, so this takes a while)...")
    parts = {"ember-mobile-midframe": midframe(),
             "ember-mobile-back":     back_cover()}

    import atexit
    atexit.register(lambda: None if _committed else (
        E._discard_partials(out, parts),
        print("\n!! BUILD DID NOT PASS -- nothing committed, no debris. The .stl files on "
              "disk are the previous good set, untouched.")))

    for n, p in parts.items():
        bb = p.bounding_box()
        print(f"{n:24s} vol={p.volume/1000:7.2f} cm^3   "
              f"bbox {bb.size.X:6.2f} x {bb.size.Y:6.2f} x {bb.size.Z:6.2f}   "
              f"model z {bb.min.Z:7.2f}..{bb.max.Z:6.2f}")
        lifted = Pos(0, 0, PRINT_LIFT[n]) * p
        lb = lifted.bounding_box()
        assert abs(lb.min.Z) < 1e-6, (
            f"{n} exports with min Z = {lb.min.Z:.4f}, not 0 -- PRINT_LIFT "
            f"({PRINT_LIFT[n]}) does not match how far below z=0 the part is modelled")
        export_stl(lifted, os.path.join(out, n + E.STL_TMP))

    print("\n--- MESH CHECK (the STL itself, not the solid) ---")
    _mesh_bad = []
    for n in parts:
        _t, _b, _nm_, _dd = E._check_manifold(os.path.join(out, n + E.STL_TMP))
        _ok = (_b == 0 and _nm_ == 0)
        print(f"  {n:24s} {_t:6d} tris   boundary {_b:2d}   non-manifold {_nm_:2d}   "
              f"{'watertight' if _ok else 'REGRESSION'}")
        if not _ok:
            _mesh_bad.append(n)
    assert not _mesh_bad, f"mesh regression in {_mesh_bad} -- an open edge or a non-manifold one"

    print("\n--- BOOLEAN CLEARANCE CHECK vs vendor STEP ---")
    board = Pos(52.750, -6.000, 0.0) * import_step(E._find_step())
    bb = board.bounding_box()
    assert abs(bb.min.X) < 0.02 and abs(bb.max.X - 50) < 0.02 \
       and abs(bb.max.Y - 86) < 0.02 and abs(bb.max.Z - 4.30) < 0.02, f"bad align {bb}"
    print(f"  board re-aligned: X {bb.min.X:.2f}..{bb.max.X:.2f}  "
          f"Y {bb.min.Y:.2f}..{bb.max.Y:.2f}  Z {bb.min.Z:.2f}..{bb.max.Z:.2f}")
    bsolids = board.solids()

    def interference(part):
        pbb = part.bounding_box(); tot = 0.0
        for sd in bsolids:
            b = sd.bounding_box()
            if (b.min.X > pbb.max.X or b.max.X < pbb.min.X or
                b.min.Y > pbb.max.Y or b.max.Y < pbb.min.Y or
                b.min.Z > pbb.max.Z or b.max.Z < pbb.min.Z):
                continue
            try: v = (part & sd).volume
            except Exception: v = 0.0
            if v > 0.01: tot += v
        return tot

    for n in parts:
        v = interference(parts[n])
        print(f"  {n:24s} interference = {v:9.3f} mm^3   "
              f"{'CLEAR' if v < 0.5 else '*** COLLISION ***'}")
        assert v < 0.5, f"{n} collides with the board by {v:.3f} mm3"
    # THE CELL IS NOT IN ANY STL, so nothing above can see it foul anything.
    _cv = interference(cell_phantom())
    print(f"  {'18650 cell phantom':24s} interference = {_cv:9.3f} mm^3   "
          f"{'CLEAR' if _cv < 0.5 else '*** COLLISION ***'}")
    assert _cv < 0.5, f"the cell fouls the board by {_cv:.3f} mm3"
    # ...and it must also fit its own cradle, which is a different question again.
    _cc = (cell_phantom() & parts["ember-mobile-back"]).volume
    assert _cc < 0.5, f"the cell fouls its own cradle by {_cc:.3f} mm3"

    # ---- CONTROLS, in both directions, on every one of those ----
    #
    # ⚠️ THE DIRECTION IS NOT ARBITRARY AND THE FIRST VERSION OF THIS GOT IT WRONG. ember_case
    # sinks the BEZEL by -2.0 because the bezel sits IN FRONT of the board and -Z drives it into
    # the glass. Every part here sits BEHIND the board, so -Z moves them further AWAY and the
    # probe finds nothing: -2.0 on the midframe returned 0.051 mm3 and read as "detector blind".
    # A displacement control has to push the part at the thing it is supposed to hit.
    _s1 = interference(Pos(0, 0, 22.0) * parts["ember-mobile-back"])
    _s2 = interference(Pos(0, 0, 2.0) * parts["ember-mobile-midframe"])
    _s3 = interference(Pos(0, 0, 12.0) * cell_phantom())
    print(f"  [self-test] cover +22mm -> {_s1:9.3f}   midframe +2mm -> {_s2:9.3f}   "
          f"cell +12mm -> {_s3:9.3f}   (+Z is toward the board for all three)")
    for _v, _w in ((_s1, "cover"), (_s2, "midframe"), (_s3, "cell")):
        assert _v > 1.0, f"!!! DETECTOR BLIND on {_w} -- a displaced part reads as clear !!!"

    assert _check_mobile(parts)

    for n in parts:
        os.replace(os.path.join(out, n + E.STL_TMP), os.path.join(out, n + ".stl"))
    _committed = True
    print(f"\n[export] committed {len(parts)} STLs -- all checks passed first")
    print(f"[envelope] {OX1-OX0:.2f} x {MOB_OY1-OY0:.2f} x {FRONT_Z-COVER_Z0:.2f} mm  "
          f"(desk case: {OX1-OX0:.2f} x {OY1-OY0:.2f} x {FRONT_Z-BACK_Z:.2f})")
