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
HEX_FIELD_X0 = E.HEX_FIELD_X0                           # 9.00, the back field's -X edge
DRIVER_W, DRIVER_H, DRIVER_T = E.DRIVER_W, E.DRIVER_H, E.DRIVER_T
DRIVER_R, DRIVER_CLR = E.DRIVER_R, E.DRIVER_CLR
CBORE_D, CBORE_DEPTH, SCREW_D, PILOT_D = E.CBORE_D, E.CBORE_DEPTH, E.SCREW_D, E.PILOT_D
SCREW_HEAD_D, SCREW_HEAD_H = E.SCREW_HEAD_D, E.SCREW_HEAD_H
bx, rbox, cyl, hexp = E.bx, E.rbox, E.cyl, E.hexp

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
# ============================================================================
# 3b. NO COIL SPRING.  A FOLDED NICKEL LEAF, AND THE CASE GETS SHORTER FOR IT.
# ============================================================================
#
# >>> JP: "design the mechanism to be just PLA printed and the nickel strips."  <<<
#
# The coil is gone. What takes up the cell's length tolerance is now a FOLD in nickel strip --
# the same 0.25 stock the contacts and the protection strip's tabs are already made of -- seated
# in a printed pocket at the bay's -Y end. Best case it is not even a separate part: the
# protection strip now lies in the lower band a few millimetres away (§5f), so its pre-welded
# B- tab can be folded up into the pocket and BE the spring and the contact in one, with zero
# extra hardware. If a tab turns out too short or too narrow to fold well, a separate folded
# nickel piece drops into the same pocket and the tab laps onto it -- the pocket does not care
# which, and check 5 measures the pocket rather than the metal.
#
# ⚠️ AND THE ALTERNATIVE -- A PRINTED PLA FLEXURE -- IS REJECTED ON CREEP, NOT ON PRINTABILITY.
# A cantilever in PLA holding a cell against a contact is under CONSTANT load for the life of
# the device, and PLA stress-relaxes: the deflection stays and the force does not. The printed-
# in-place button hinges in this family survive because they flex for a fraction of a second and
# spend their lives unloaded. A battery contact is the opposite duty cycle. So PLA does GEOMETRY
# here -- the datum, the travel stop and the retention -- and the metal does the force.
#
# ⚠️ THE FORCE IS JP-TUNABLE AND THAT IS DELIBERATE. A hand-formed fold's rate is whatever his
# fingers and pliers produce; nothing in this file can predict it. So the pocket is sized to
# accept a RANGE of fold depths and the numbers below bound the geometry, not the newtons.
LEAF_T          = 0.25      # nickel strip stock -- the same CONTACT_T the plate is
LEAF_FOLDS      = 3         # a Z-fold: three thicknesses plus bend radii when fully closed
LEAF_SOLID      = LEAF_FOLDS * LEAF_T                   # 0.75, the fold closed up
LEAF_FREE       = 3.60      # ⚠️ JP-TUNABLE: the fold's height at rest, formed by hand
# >>> AND THE MARGIN CAN BE SMALL HERE IN A WAY IT COULD NOT BE FOR THE COIL. <<<
# SPRING_MARGIN was 1.00 because a coil at its solid height is a SOLID CYLINDER: reach it and
# the cell physically will not go in, so the bay had to guarantee never reaching it. A fold has
# no such stop -- it just gets stiffer as it closes, and it can always take another tenth. So
# the margin is what the case length leaves over rather than a floor the case must respect,
# and it is DERIVED below and PRINTED, not chosen.
BAY_L           = None      # solved in section 4, against the desk profile. See MOB_OY1.

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
BAY_Y0   = COVER_Y0 + COV_WALL                          # 20.20 — the leaf's seat (see 3b)
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
#
# >>> POLARITY IS THE OTHER WAY ROUND SINCE THE LEAF LANDED, AND IT IS NOT COSMETIC. <<<
#
# The coil used to live at the +Y end and the "+" plate at -Y. Both moved, because the protection
# strip moved: with the strip lying in the LOWER band (§5f) its pre-welded B- tab is inches from
# the -Y end wall, so putting the leaf there makes the tab and the spring the same piece of
# metal. The "+" plate goes to the +Y end and keeps its kerf, its detent and its throat
# unchanged in FORM -- only the wall it is cut into changed. The consequences are tracked:
# both polarity markings swap ends (_mark_face), and the divider's wire groove now carries B+
# the length of the bay instead of B-.
CELL_TIP_Y   = None                                     # -> BAY_Y1, solved below
# ============================================================================
# 4b. THE CASE'S LENGTH, SOLVED AGAINST THE DESK PROFILE.  "WHY DO WE HAVE A BROW?"
# ============================================================================
#
# >>> JP ASKED, AND WITH THE COIL GONE THE ANSWER IS: WE DO NOT. <<<
#
# This chain used to run FORWARD -- BAY_L from the cell and the coil, then BAY_Y1, then
# MOB_OY1 = 92.00 -- and the 3.05mm by which that overshot the desk shell's OY1 = 88.95 was the
# brow. Every version of the brow (a bolted-on block, then a one-profile extension) was a
# consequence of a coil spring's 2.50mm solid height plus the 1.00 of margin a solid height
# forces you to keep away from it.
#
# Take the coil out and the chain runs forward off the CELL instead of off the spring:
LEAF_MARGIN  = 0.50                                     # how far off closed the LONGEST cell
                                                        # must still leave the fold
CELL_TIP_Y   = BAY_Y0 + CELL_L_MAX + LEAF_SOLID + LEAF_MARGIN   # 86.95, the "+" plate's face
# >>> ⚠️ AND THE FIRST ATTEMPT AT THIS SET MOB_OY1 = OY1 AND DECLARED THE BROW DEAD. IT WAS <<<
# >>> WRONG, AND ONLY THE CELL-vs-CRADLE BOOLEAN SAID SO -- 21.218 mm3, at x -0.45..3.50,   <<<
# >>> y 84.07..86.75.  THE COIL WAS NEVER THE ONLY REASON FOR THE BROW.                     <<<
#
# The cell lane runs hard against the -X wall (CELL_X0 = OX0 + COV_WALL, by construction -- the
# X budget has nothing to spare, see check 3). The case's own corner rounds at OUT_R, so over
# the last 6.45mm of the profile the outer skin curves IN toward the bore, which is already
# only 0.10 inside the interior wall on the flat. Where they converge the wall between the
# battery and the outside air runs out, and the interior rbox's own corner fillet -- which is
# just the constant-wall offset of that arc -- eats into the bore before the wall does.
#
# So the bay cannot end where the case does, whatever the spring is. This SETBACK is what the
# coil's 2.50 solid height plus 1.00 of margin had been paying for by accident, which is why
# nobody had ever had to name it: at BAY_Y1 = 89.80 the longest cell stopped at 86.00, 3.80
# short, and 3.80 happens to be more than enough. Delete the coil and the debt comes due.
#
# Derived, not chosen: the distance back from the corner at which the outer arc still leaves
# MIN_SOLID between itself and the bore's -X extreme.
_BORE_X0     = OX0 + COV_WALL                           # -0.75 -- the bore's -X extreme IS the
                                                        # interior wall; that is the X budget
                                                        # (CELL_X0 below, same expression)
_ARC_CX      = OX0 + OUT_R                              # 3.50, the corner arc's centre
_MIN_SOLID   = 4 * 0.40          # 1.60; MIN_SOLID itself is named in 5g, below
_ARC_DY      = math.sqrt(max(OUT_R**2 - (_MIN_SOLID + _ARC_CX - _BORE_X0)**2, 0.0))
CELL_END_SETBACK = OUT_R - _ARC_DY                      # 3.53
MOB_OY1      = CELL_TIP_Y + max(COV_WALL, CELL_END_SETBACK)     # 90.48
BAY_Y1       = MOB_OY1 - COV_WALL                       # 88.28, the COMPARTMENT's void end
BAY_L        = CELL_TIP_Y - BAY_Y0                      # 66.75, the cell's own working length
# ...and the cell lane is SOLID from the plate to BAY_Y1, so the fillet is filled rather than
# dodged: back_cover() adds that bulkhead and cuts the "+" kerf into its -Y face.
assert CELL_END_SETBACK > COV_WALL, (
    f"the corner setback solved to {CELL_END_SETBACK:.2f}, at or under the {COV_WALL} end wall "
    f"-- if so the corner has stopped being the binding constraint and this whole block "
    f"can collapse back to MOB_OY1 = CELL_TIP_Y + COV_WALL")
# CONTROL, and it is the one that would have caught the mistake: a cell reaching all the way to
# BAY_Y1 must still be REJECTED by the same arithmetic, or the setback is not being applied.
assert (OUT_R - (BAY_Y1 - CELL_TIP_Y)) > 0 and \
       (math.sqrt(max(OUT_R**2 - (OUT_R - COV_WALL)**2, 0.0)) - (_ARC_CX - _BORE_X0)) < _MIN_SOLID, (
    "control failed: a bay ending COV_WALL from the case's end reads as leaving MIN_SOLID "
    "between the bore and the corner arc, so the setback above is not defending anything")
assert LEAF_FREE - (BAY_L - CELL_L_MIN) > 0.30, (
    f"the SHORTEST cell ({CELL_L_MIN}) leaves {BAY_L-CELL_L_MIN:.2f}mm against a {LEAF_FREE} "
    f"free fold -- under 0.30mm of preload, so a short cell rattles and the contact is "
    f"intermittent. LEAF_FREE is the knob and JP forms it by hand")
assert (LEAF_FREE - LEAF_SOLID) >= 2 * CELL_L_TOL, (
    f"the fold's travel {LEAF_FREE-LEAF_SOLID:.2f} does not span the cell's "
    f"{2*CELL_L_TOL:.2f}mm length spread -- one end of the tolerance band will not seat")
# CONTROL: the coil this replaced must FAIL the same bay, or the shortening is not evidence.
assert BAY_L - CELL_L_MAX - 2.50 < 1.00, (
    "control failed: the deleted coil's 2.50 solid height plus its 1.00 margin still fits this "
    "bay, so the bay did not actually shrink and the leaf bought nothing")
# ...and the saving, stated as the number it is rather than as the number I wanted it to be.
MOB_OY1_WAS  = 92.00            # the coil-and-tunnel case, for the record
assert MOB_OY1 < MOB_OY1_WAS, (
    f"the case is {MOB_OY1:.2f} long against the coil version's {MOB_OY1_WAS:.2f} -- the leaf "
    f"has not shortened anything and the whole exercise is a wash")

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
# ---- DEBOSS DEPTHS: "as deep as we can", DERIVED PER WALL (JP, r11) ----
#
# JP: "all debosses should be even deeper as deep as we can." So no deboss depth in this file is
# a chosen number any more -- each is (local wall - that feature's own floor), and the floors are
# the ones already proven here. What "as deep as we can" MEANS depends on the face's print class,
# and the two classes quantize on DIFFERENT axes:
#
#   BED / CAVITY FACE (horizontal)  depth runs in Z  -> quantize to LAYER_H. Layer boundaries.
#   SIDE WALL        (vertical)     depth runs in X/Y -> layer height does NOT govern it
#                                   (ember_case.py:291 says so for the label grooves already).
#                                   Quantize to EXTRUSION WIDTH instead.
#
# ⚠️ AND A DEPTH THAT LANDS EXACTLY ON ITS FLOOR IS NOT "AS DEEP AS WE CAN", IT IS ON A
# CONSTRAINT BOUNDARY. LABEL_DEBOSS's own block settled this: 3 layers left the cap wall at
# exactly 1.20 against a 1.20 floor, so it took 2 and kept 0.20 of slack. Same rule here --
# every depth below leaves at least one quantum over its floor.
_EXTRUSION = 0.40                       # one bead at the 0.40 nozzle; MIN_SOLID is 4 of these
#
# >>> AND "AS DEEP AS WE CAN" HAS A SECOND BOUND THAT IS NOT THE WALL. <<<
# A groove deeper than it is WIDE stops being a marking: the nozzle cannot reach the bottom
# cleanly, the floor prints ragged, and the slot becomes a dirt trap that fills and reads as a
# solid line. So every glyph-class deboss is capped at its own stroke width -- aspect <= 1:1 --
# and the wall budget only binds when it is the SMALLER of the two. Both bounds are printed in
# the [deboss] table so it is visible which one is doing the work for each feature.
_ASPECT_MAX = 1.0

def _max_deboss(wall, floor=None, quantum=None, on_floor_ok=False):
    """Deepest deboss a `wall` can carry while keeping `floor` of material, quantized DOWN.

    Quantized down and then checked for slack, so the answer is never sitting on the floor it
    was derived from. Returns 0.0 rather than a negative number if the wall cannot carry one.
    """
    # _MIN_SOLID, not MIN_SOLID: this helper is defined ABOVE the public alias (§5g binds it).
    # Same ordering trap that put check 6d before `cov` existed -- a dependency read before it
    # is bound fails only when the line actually runs, which for a default arg is every call.
    floor = _MIN_SOLID if floor is None else floor
    quantum = LH if quantum is None else quantum
    # ⚠️ THE TOLERANCE IS LOAD-BEARING AND ITS ABSENCE WAS ALREADY CHANGING ANSWERS.
    # Two features sit behind a 2.20 wall -- the driver outline and the blind top mesh -- and the
    # bare `>=` sent them different ways purely on float dust (2.20 arrives as 2.2000000000000028
    # from one derivation chain and 2.2 from another, so `3*quantum >= wall-floor` was True for
    # one and False for the other). A print-floor rule decided by the last bit of a mantissa is
    # not a rule. Rounded to a tenth of a quantum, both now answer the same way.
    _n = int((wall - floor) / quantum + 1e-9)
    _lands_on_floor = round(_n * quantum, 6) >= round(wall - floor, 6) - 1e-9
    if _lands_on_floor and _n > 0 and not on_floor_ok:
        _n -= 1                          # never land ON the floor -- LABEL_DEBOSS's precedent
    return max(_n, 0) * quantum


# ---- the two polarity marks, each derived against ITS OWN face ----
# "+" cuts +Y into the bay's +Y end wall: solid behind it runs CELL_TIP_Y -> MOB_OY1.
# "-" cuts -Z into the cover's mating face in the chin band, where the cover is solid for
# tens of millimetres -- so there the ASPECT cap is what binds, not the wall, and that is
# exactly the case the cap was written for.
MARK_DEPTH_WALL = min(_max_deboss(MOB_OY1 - CELL_TIP_Y, quantum=_EXTRUSION),
                      int(_ASPECT_MAX * E.LABEL_W / _EXTRUSION) * _EXTRUSION)
# The "-" mark's face is the cover's MATING FACE, and the cover is solid for tens of millimetres
# under the chin band -- so the ASPECT cap binds and the wall never does. Stated that way rather
# than derived from COVER_Z0 because COVER_Z0 is defined further down this file and a constant
# that reads a not-yet-bound name is the ordering trap this round has now hit twice. The claim
# that the wall does not bind is not left as a comment: check 8a's min-solid sweep covers this
# face, and _deboss_ledger() below re-derives it against the real number every build.
MARK_DEPTH_MATE = int(_ASPECT_MAX * E.LABEL_W / LH) * LH        # 0.80 = 4 layers
MARK_DEPTH   = MARK_DEPTH_MATE      # kept as the shared name every existing caller already reads
                                    # (was a typed 3*LH = 0.60; JP r11: as deep as we can)


MARK_PATHS_P = [[(-MARK_H/2, 0.0), (MARK_H/2, 0.0)], [(0.0, -MARK_H/2), (0.0, MARK_H/2)]]
MARK_PATHS_N = [[(-MARK_H/2, 0.0), (MARK_H/2, 0.0)]]
MARK_INK     = MARK_H + E.LABEL_W                       # 3.70 overall ink extent
# MOB_OY1 and BROW_Y0 used to be defined here. MOB_OY1 moved UP to section 4b, because it is
# now an INPUT to the bay rather than an output of it. BROW_Y0 is deleted outright: there is no
# brow, so there is no y at which one starts.
# ⚠️ THESE TWO COMMENTS SAID -31.50 AND -29.30 UNTIL 2026-08-01, i.e. they were correct for a
# CELL_BORE_D of 19.60 and the bare-cell re-primary took it to 19.40 without them following.
# Harmless here because both are DERIVED and nothing reads the comment -- but it cost real time
# downstream: a slice script written against -31.50 sliced the cover 0.20 too high and read a
# tooth 0.20 up its own skew. §11 defect #8 is this exact class, one file over.
# ============================================================================
# 4c. THE BAY IS DEEPER THAN THE BORE, AND THE EXTRA LANDS AT THE BOTTOM.
# ============================================================================
#
# >>> JP: "the lid is flat teh battery is round isn't there space?"  --  YES, AND HE IS  <<<
# >>> RIGHT.  My tangency finding measured the bore's EXTREMES and called the bay full.   <<<
#
# The bore is tangent to CELL_X0, CELL_X1 and the bay floor -- all three gaps 0.00 -- and I
# read that as "no room". It is not: a ROUND bore in a SQUARE bay leaves four CORNER SOLIDS,
# 4.53mm of diagonal each at the top pair, 4.11 at the bottom (the cell rides CELL_BORE_CLR
# low, which costs the bottom corners 0.42 of diagonal and buys the top ones the same). That
# is where the BMS body goes -- pocketed into a corner, lying against the cell, which is
# exactly what "hugs the battery" means.
#
# ⚠️ AND IT IS STILL 0.33 SHORT, WITH JP'S CALIPERED BODY. A 4.50 x 2.50 body plus 0.40 of
# clearance needs 2.90 of depth at 5.30 of width, and the best corner offers 2.17. So the bay
# grows -- but by BAY_EXTRA, not by the 2.50 I first estimated, because the corner does four
# fifths of the work. +1.20 misses by 0.01, which is a coincidence and not a fit; 8 layers
# lands it with 0.39 of real clearance and keeps every depth layer-whole.
#
# ⚠️ AND THE BORE IS HUNG FROM THE MATING PLANE SO THE EXTRA LANDS AT THE BOTTOM, which is
# JP's own refinement ("or even better at teh bottom") and it is the better call for a reason
# he did not have to state: the strip lays into the bottom channel FIRST and the cell DROPS ON
# TOP OF IT. No threading a part down beside a cylinder that already fills the bore. Note the
# derivation is a NO-OP today -- BACK_Z - CELL_BORE_D/2 and CAV_Z0 + CELL_BORE_D/2 are the same
# number until BAY_EXTRA is non-zero -- which is why it is written this way rather than as a
# constant: it says WHICH END the growth belongs to.
# ⚠️ BACK TO ZERO.  JP: "i want it flush with teh main body. i don't thingk gorwing it is the
# answer."  The corner-solid growth of the previous checkpoint is reverted and the envelope is
# 39.00 again. What houses the body instead is the DIVIDER's own 2.00, deleted across the span
# the strip needs -- his call, made after being told plainly what it costs (§5f-c).
BAY_EXTRA = 0 * LH                                      # flush. See 5f-c for what pays for it.
COVER_Z0 = BACK_Z - COV_WALL - CELL_BORE_D - BAY_EXTRA  # -32.90, the cover's outer face
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
CELL_AXIS_Z = BACK_Z - CELL_BORE_D / 2                  # -19.40, HUNG from the
                                                        # mating plane: see 4c
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
# ---- THE BOND LINE, WHICH WAS NEVER A NUMBER UNTIL THE COVER STOPPED SLIDING ----
#
# ⚠️ AN ALLOWANCE, NOT A MEASUREMENT, AND IT IS FLAGGED AS ONE. JP's words are "double-stick
# tape" and nothing more; the class runs from 0.05 (transfer tape) to 1.10 (foam). 1.00 is the
# PESSIMISTIC end, chosen because every question this number is asked is a clearance question
# and the wrong direction to be optimistic in. Check 8d sweeps the driver at this position;
# check 7's acoustics are indifferent to it (they difference volumes, and the module's volume
# does not move). If it ever turns out to matter, it is one constant.
TAPE_T = 1.00                                           # ⚠️ ALLOWANCE, not calipered
FRONT_GAP_MOBILE = (BACK_Z - TAPE_T - DRIVER_T) - CAV_Z0        # 8.60
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
# ============================================================================
# THE FULL SEPARATOR WALL, AND THE DRIVER SHIFT THAT PAYS FOR IT  (JP, r11 final)
# ============================================================================
#
# JP: "Shift it -- build the wall." Authorised with the trade in front of him.
#
# >>> AND THE LANE MATTERS AGAIN: THIS WALL GOES +X OF RIM_X0, NOT IN THE STUB LANE. <<<
# The partial wall this replaces stood in the old divider's lane (x CELL_X1..RIM_X0) and could
# not span the strip's Y range, because the strip loads STRAIGHT DOWN through a PROT_W column
# that the cell pins to exactly that lane. A wall on the DRIVER'S side of RIM_X0 never enters
# that column at all -- the pocket ends AT RIM_X0 -- so it can run the chamber's whole length.
# That is the actual reason the shift works, and it is not the reason I first gave.
# _MIN_SOLID: this block sits ABOVE §5g where the public MIN_SOLID alias is bound. That is the
# THIRD time this round a constant defined up here reached for a name bound further down, so it
# is worth stating as a rule rather than a bug: everything above §5g uses the private names.
SEP_WALL_T = _MIN_SOLID                                 # 1.60, four extrusions
SEP_WALL_X0 = RIM_X0
SEP_WALL_X1 = RIM_X0 + SEP_WALL_T                       # 22.25, the chamber's new -X face
#
# THE SHIFT IS DERIVED FROM A WINDOW, NOT CHOSEN, AND JP'S 0.45 IS OUTSIDE IT.
# At +0.45 the driver clears the wall by 0.40 as intended -- but the MIDFRAME'S LOCATING GROOVE
# is drawn at driver + 2*DRIVER_CLR, so it is 1.20 wider per side than the driver, and at +0.45
# its -X edge lands 0.20 INSIDE the new wall's footprint. That groove is a 0.60-deep channel cut
# into the very face this wall bears on, so the overlap would be a leak path running the entire
# length of the wall built to stop leaks. Two bounds, therefore:
#
#     groove -X edge >= the wall's chamber face   ->  shift >= 0.65
#     groove +X edge <= RIM_X1 (the case wall)    ->  shift <= 0.95
#
# and the shift is the CENTRE of that window, so neither bound is sat on. 0.80.
_GRV_HALF = (DRIVER_H + 2 * DRIVER_CLR) / 2
_shift_lo = (SEP_WALL_X1 + _GRV_HALF) - (RIM_X0 + RIM_X1) / 2
_shift_hi = (RIM_X1 - _GRV_HALF) - (RIM_X0 + RIM_X1) / 2
assert _shift_hi > _shift_lo, (
    f"no driver shift satisfies both the wall face and the case wall: window is "
    f"[{_shift_lo:.2f}, {_shift_hi:.2f}]. The wall cannot be {SEP_WALL_T:.2f} thick here")
# >>> AND THE GATE KILLED IT AT 21.50 mm3. THE SHIFT IS NOT BUILT. HERE IS WHY, IN NUMBERS. <<<
#
# The window above is real but it is not the binding one, because it never asked where the STRIP
# actually sits. prot_phantom() places the body at PROT_PKT_X0 + PROT_PKT_CLR, so its +X face is
# at x 21.05 -- 0.40 PAST RIM_X0, into space that used to be open chamber and is now wall. The
# strip fouled the cover by exactly PROT_L * PROT_T * PROT_PKT_CLR = 21.50 mm3 and check 13 said
# so. The assembly clearance the pocket was always carrying is the thing the wall wants to stand
# in.
#
#   the wall cannot start before          x 21.05   (the strip's own +X face)
#   the groove must stay off the rim  ->  DRV_CX <= 36.65
#   so the thickest wall available is         1.50
#   MIN_SOLID is                              1.60   -> SHORT BY 0.10
#
# And the pocket cannot move -X to buy the 0.40 back: at the pocket's top Z the cell bore's edge
# is 15.87 and PROT_PKT_X0 is 16.15, i.e. 0.28 available against 0.40 needed. The 18650 pins it.
#
# ONE CHANGE DOES CLOSE IT, and it is not mine to make: DRIVER_CLR 0.60 -> 0.40 shrinks the
# locating groove by 0.20 a side, which lifts the ceiling to 1.90 and the wall fits at 1.60 with
# room over. That is a FIT DIMENSION on the driver -- the groove it drops into -- and JP is
# bench-testing the r10 cover with that driver as this is written. Changing a drop-in fit while
# the owner is measuring the drop-in fit is how you invalidate his test and your own answer.
#
# So: DRV_SHIFT = 0, no full wall, the r11 partial wall stands, and the 0.10 goes to JP.
DRV_SHIFT = 0.0
DRV_CX    = (RIM_X0 + RIM_X1) / 2 + DRV_SHIFT           # 36.50
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
# ---------------------------------------------------------------------------
# ROUND 2, THE SKEW RAILS: ALSO DEAD, AND FOR A DIFFERENT REASON THAN THE HOOKS.
# ---------------------------------------------------------------------------
#
# They ran along both long walls, and their cross-section was a SKEW rather than a flare --
# the void kept its 1.20 width and translated 0.60 outboard as it rose -- because the side
# cable channels (ember_case.py:1541) cut the flank at z CAV_FLOOR..PCB_BOT, leaving only the
# 2.60 floor beneath them, and a flared dovetail's 45-degree gable would not fit in it.
#
# That reasoning was sound and the geometry gated green. It was still unprintable, because the
# whole exercise was conducted in the wrong units: squeezing a joint into 2.60 of Z and 2.60 of
# X produced a 0.60mm SOLID tongue, which is a third thinner than the solid webs #47 measured
# collapsing on this machine. THE CONSTRAINT WAS REAL AND THE CONCLUSION WAS WRONG -- the right
# answer to "the joint does not fit in the wall" was never "make the joint smaller", it was
# "this is the wrong wall". Kept here because the arithmetic below reuses it: the long walls
# are eliminated by exactly the budgets this paragraph worked out.
#
# >>> ROUND 3, AND THE FIRST TWO ARE THE EVIDENCE.  JP, ON SEEING THE SKEW RAILS RENDERED: <<<
# >>> "the dovetail is way too tiny of features for my Ender 3 with PLA."  HE IS RIGHT.      <<<
#
# ⚠️ AND THE ERROR WAS MINE IN A PRECISE, NAMEABLE WAY. The comment that used to sit here cited
# both halves of this machine's calibration set on ONE LINE -- "SLOT_W's 0.60 VOID prints open
# and #47's 0.90 WEBS collapsed" -- and then made the tongue a 0.60 SOLID rib, citing the void
# as its justification. A void is not a solid. 0.60 of solid is a THIRD THINNER than the solid
# class this machine is documented to have failed, and the counter-evidence was in the same
# sentence. Nothing in the check suite could see it: every check here measures whether the
# geometry is SELF-CONSISTENT and printable in principle -- no bridge, faces >= 50 degrees,
# capture > clearance -- and NOT ONE OF THEM KNOWS WHAT THIS MACHINE CAN HOLD. That missing
# lens is why check 8a now exists, and why its control is #47's own 0.90.
#
# ---------------------------------------------------------------------------
# WHERE A CHUNKY JOINT CAN GO.  THE ANSWER IS NOT "THE SAME PLACE, BIGGER".
# ---------------------------------------------------------------------------
#
# At a 1.60 minimum solid and a 0.45 per-face clearance, measured against the live constants:
#
#   -X WALL IS DEAD. OX0 to the cell's own surface is 2.50 of X, total. Skin 1.60 + clearance
#     0.45 leaves a 0.45 tongue; even at a 1.20 skin (already below the failed class) it is
#     0.85. The cell bore sits CELL_BORE_CLR from the wall's inner face and that is the whole
#     story -- there is no arrangement that reaches 1.60.
#   +X WALL IS ALSO DEAD, less obviously. A chunky joint needs 4.90 of X and is 3.13 deep. The
#     side wall is WALL wide; past it the midframe is only the 2.60 floor, and the gable's apex
#     lands over that floor. It would break into the board cavity.
#   THE TOP BLOCK IS THE ONLY VIABLE SITE, and it is viable by a mile: solid BACK_Z..SEAM_Z,
#     14.40 tall, full width, no cell, no seal rim, no cable channel.
#
# ---------------------------------------------------------------------------
# ROUND 4: AND THE BROW DOVETAIL DIED TOO, ON THE ONE AXIS NOBODY WAS MEASURING.
# ---------------------------------------------------------------------------
#
# >>> JP, having double-stick-taped the speaker to the printed midframe:                  <<<
# >>> "the backpack can't involve any sliding, it has to come straight down."             <<<
#
# A dovetail is an undercut, and an undercut needs a slide. The driver is now a TAPED PART on
# the midframe's back face, so any Y travel shears the cover's rim wall across a bonded
# speaker. Rounds 1-3 all died on this same axis and it is worth naming: hooks (a bridged
# pocket in a bed face), skew rails (0.60 SOLID ribs on a machine that failed 0.90 ones), brow
# dovetail (needs a slide). EVERY SLIDE-BASED SCHEME WAS DOOMED FROM THE MOMENT THE DRIVER
# BECAME A TAPED PART -- which this model already implied, because RIM_INNER_Y is set by the
# driver's tape pad, and which nobody read as an ASSEMBLY-ORDER constraint until JP put tape on
# plastic. Check 8d is now a straight-down sweep and it sweeps the driver, because that is the
# object the whole question is about.
#
# ---------------------------------------------------------------------------
# WHAT IT IS NOW: TWO M3 x 22, ON THE CASE'S OWN CENTRELINE, STRAIGHT DOWN.
# ---------------------------------------------------------------------------
#
# >>> AND THE CENTRELINE IS THE FINDING, NOT A TIDY-UP. <<<
#
# Round 4b/4c proved that THE CELL LANE MAKES THE ENTIRE -X HALF OF THE COVER UNFASTENABLE:
# for x < CELL_X1 the bore owns y 20.20..89.80, y >= BAY_Y1 fails SCREW_EDGE_MIN against the
# y = MOB_OY1 end, and y <= BAY_Y0 fails it against COVER_Y0. There is no valid -X screw
# position at any y. The instinct after that is to put the top screw where there is room --
# out at x = 46 on the +X half -- and that is exactly wrong: it would leave the -X edge
# 28.95mm from the nearest fastener and the +X edge 26.95, i.e. it would SPEND the asymmetry
# rather than absorb it. Putting BOTH screws on (OX0+OX1)/2 makes the two long edges
# equidistant at 27.95 each. The -X half still cannot hold a screw; the centreline is simply
# the furthest -X that any fastener can legally reach, and standing there costs the +X edge
# nothing. Check 8f prints both numbers.
# ⚠️ SCREW_EDGE_MIN IS NOT A STYLE RULE. Two builds were lost to it and both are worth keeping.
# At y = 19.20 the d5.80 counterbore spanned y 16.30..22.10 against a part starting at
# COVER_Y0 = 18.00, so 1.70mm of it hung off the end: the "hole" was a NOTCH in the outline and
# the head had no annular seat on its low-Y side. EVERY NUMERIC CHECK PASSED -- 3.20mm of
# engagement, pilot clear of the board, seal ring 100% solid. Only a slice of the finished mesh
# showed it. Then 21.50 failed for a second reason the first fix did not cover: the bed face
# carries a 0.80 CHAMFER, and a chamfer running into a hole 0.60 away cannot produce a valid
# face -- OCC threw StdFail_NotDone from inside chamfer_outline(). So the edge distance owes the
# counterbore's own radius AND the chamfer AND margin, and its assert lives at MODULE level
# because the check suite runs after the geometry that would already have died.
SCREW_EDGE_MIN  = CBORE_D/2 + CHAMFER + 0.50            # 4.20
# ⚠️ THE LANE IS SOLVED, AND IT IS SOLVED AGAINST THE PROTECTION STRIP, NOT AGAINST SYMMETRY.
# Both screws share one x, and that x is as far -X as the d5.80 counterbore can sit before it
# breaks into the shared divider's base (the counterbore's floor lands 0.80 above CAV_Z0, i.e.
# INSIDE the compartment, so "the wall is thick enough" is not the question -- the divider is).
# Everything else about the lane follows: it leaves the widest possible +X pocket for the strip
# in the lower band (§5f), and it carries both fasteners 1.45mm closer to the -X edge, which is
# the one edge of this part that can never hold a screw at all.
SCREW_LANE_X    = RIM_X0 + CBORE_D/2                    # 23.55
# ⚠️ 7.00 WAS TOO SMALL, and the reason is not obvious from the section: CBORE_DEPTH is 3.00
# and COV_WALL is only 2.20, so THE COUNTERBORE IS DEEPER THAN THE WALL IT IS SUNK IN. Its
# floor lands 0.80 above CAV_Z0 -- inside the compartment -- so the head does not bear on the
# outer wall at all, it bears on a boss. At d7.00 that is (7.00-5.80)/2 = 0.60mm of annulus
# against ember_case's BOSS_MIN_ANN of 1.00. The seat probe read 86.9% and found it. It is
# defined HERE, above the screw positions, because the TOP screw is placed by the boss's
# radius rather than by its counterbore's -- see below.
SCREW_BOSS_D    = 9.00                                  # (9.00-5.80)/2 = 1.60 of annulus
SCREW_BOSS_H    = 4.00                                  # CAV_FLOOR -7.10 -> -3.10, PCB is -1.60
SCREW_XY        = (SCREW_LANE_X, COVER_Y0 + SCREW_EDGE_MIN + 0.40)   # (23.55, 22.60) the chin
# ⚠️ THE TOP SCREW'S EDGE DISTANCE IS SET BY THE BOSS, NOT THE COUNTERBORE, AND THE FIRST
# VERSION USED THE COUNTERBORE. SCREW_BOSS_D/2 is 4.50 against SCREW_EDGE_MIN's 4.20, so a
# screw placed by the counterbore's rule left the d9.00 boss standing 0.30 PROUD of the case's
# own end face -- on BOTH parts. The bounding box said 90.98 where the profile says 90.68, and
# the dock check found it as interference. A bump on the silhouette is the defect JP caught by
# eye at the top of this case once already.
TOP_SCREW_XY    = (SCREW_LANE_X,
                   MOB_OY1 - max(SCREW_EDGE_MIN, SCREW_BOSS_D/2 + 0.20))    # (23.55, 85.98)
SCREWS          = (SCREW_XY, TOP_SCREW_XY)
# ⚠️ LENGTH IS DERIVED FROM THE COVER'S DEPTH, NOT CHOSEN -- and JP has explicitly released it
# as a constraint ("i don't ccare about the lendthte of the screws"). Every millimetre the
# backpack grows comes off the thread one for one: at BAY_EXTRA 1.60 this had to be 25 because
# an M3x22 engaged only 1.80, under check 11's floor, and it would have felt perfectly tight
# going in. Back at flush, 22 engages 3.40. Check 11 is the arbiter; the report carries the
# shopping line.
MOB_SCREW_LEN   = 22.00                                 # M3 x 0.5 x 22 ISO 4762, under-head
MOB_PILOT_DEPTH = (BACK_Z - CAV_FLOOR) * -1 + SCREW_BOSS_H   # 2.60 floor + 4.00 boss = 6.60
# ---- WHY THE TOP SCREW ALSO NEEDS A MIDFRAME BOSS, WHICH IS NOT WHAT THE SITE LOOKS LIKE ----
#
# At (25.00, 87.80) the midframe is solid BACK_Z..SEAM_Z -- 14.40mm, no pocket, no cavity. The
# obvious reading is "bore a pilot into it and stop thinking". That reading is wrong by 1.40mm.
# The board pocket's +Y wall is at PY1 = 86.35 and the pilot's own -Y extreme is at
# 87.80 - PILOT_D/2 = 86.55, so ABOVE CAV_FLOOR the web between the bore and the board cavity is
# 0.20mm. Not a hole -- a 0.20 wall, which is a quarter of the thinnest thing this machine has
# ever printed successfully, and the self-tapper would push it into the cavity on the first
# turn. Every check in this file would have passed: engagement 3.40, edge distances fine, no
# collision with the board, seal untouched.
#
# The fix is the chin screw's own trick, mirrored: a boss that grows UP into the board cavity,
# where standing proud costs nothing. Coaxial with the screw and the same d9.00, it fills
# y 83.30..86.35 of the pocket's +Y end locally and the web becomes the boss's own radius less
# the pilot's -- 3.25mm, all the way round. Whether that intrudes on anything is not reasoned
# about: the STEP clearance boolean measures it, and the region it fills (x 20.50..29.50,
# y 83.30..86.35, z -7.10..-3.10) reads EMPTY in the vendor solid -- the nearest back-side
# feature is the PCB antenna pour at z -1.65, 1.45mm above the boss's top.
#
# ⚠️ AND THE PILOT MUST STOP AT THE BOSS'S TOP. MOB_PILOT_DEPTH lands it exactly there
# (BACK_Z + 6.60 = -3.10 = CAV_FLOOR + SCREW_BOSS_H). One millimetre deeper and its last
# millimetre is back in the 0.20 web this boss exists to abolish.
# ---- THE UNVALIDATED LATTICE.  Shared with the stand ON PURPOSE. ----
#
# >>> JP: "we have proven two that collapse and none that survives." <<<
#
# The cooling fields below use HEX_R / HEX_WEB -- the STAND'S OWN grille constants, 4.75 across
# flats on a 1.25 web -- and that is the OPPOSITE call from GLOW_R and GLOW_WEB three sections
# down, which were deliberately PINNED away from this same pair after #47. The difference is
# what the two features are for. The glow window's size is set by the 5.50mm cavity band it
# lives in, so inheriting another part's lattice was pure accident and it broke the fit. The
# cooling fields have no such constraint and exist precisely to BE the pattern under test: if
# JP prints these and the 1.25 web survives, that answers #47 for the whole family at once,
# and one shared pair of constants is how the answer propagates. If it collapses, it collapses
# everywhere in one place.
#
# ⚠️ SO THIS WEB IS BELOW THE 1.60 MINIMUM SOLID FLOOR AND IT IS *NOT* IN CHECK 8a's LIST.
# It is not an oversight and it must not be "fixed" by adding it -- 8a would fail the build on
# a pattern that is deliberately on trial. It is printed as an [unvalidated] line instead, so
# it is loud rather than silent.
# ---- THE SMALL MESH, AND WHY ITS WEB IS NOT ONE NUMBER ----
#
# >>> JP: "i want the top hex vents at the top of both peices to be the same hex grill on <<<
# >>> the back of the midframe; the hexasgons are too big"                                <<<
#
# The reference is the back grill: 3.2 across flats on a 0.80 web, and it has PRINTED -- his r1
# midframe carries ~113 of those cells. So MESH_AF matches it exactly.
#
# ⚠️ BUT THE WEB CANNOT MATCH EVERYWHERE, AND THE REASON IS BORE DIRECTION, NOT WIDTH. The
# back grill's cells are VERTICAL PRISMS IN A BED FACE -- every layer supported by the one
# below, which is why 0.80 survives there. The fields at the +Y ends are HORIZONTAL BORES, the
# same class as the stand's grille, where 0.90 COLLAPSED (#47) and 1.25 is the current
# unvalidated fix. Matching 0.80 into a horizontal bore would put these fields THINNER THAN THE
# WEB THAT ACTUALLY FAILED, so the web is chosen per class and the class is stated per field:
#
#   blind battery-side deboss  0.60 of surface relief, NO BORE  -> MESH_WEB_BLIND 0.80, and it
#                              cannot fail as a web at all: the material behind it is 1.60 of
#                              continuous membrane, not a rib.
#   LED-side through field     horizontal bores, 2.20 long      -> MESH_WEB_BORE 1.25
#   midframe +Y end vent       horizontal bores, 2.60 long      -> MESH_WEB_BORE 1.25
#
# JP asked for the HEXAGONS to be smaller, which is cell size; that is delivered exactly. The
# web is the one thing he did not ask about and the one thing #47 measured.
MESH_AF        = 3.20                   # = the back grill's, JP's own reference
MESH_R         = MESH_AF / math.sqrt(3)
MESH_WEB_BLIND = 0.80                   # PROVEN: the back grill's own web, printed on r1
MESH_WEB_BORE  = 1.25                   # horizontal bores stay clear of #47's 0.90 collapse
LAT_AF   = math.sqrt(3) * HEX_R                         # 4.75 across flats -- the stand's own
LAT_WEB  = HEX_WEB                                      # 1.25 -- the stand's own
LAT_R    = HEX_R                                        # circumradius; AC = 2*LAT_R = 5.485
MIN_SOLID = _MIN_SOLID                  # 1.60 = four extrusion widths. Check 8a enforces it.

# ---- MODULE-LEVEL SCREW ASSERTS, so they cannot be outrun by the geometry they constrain ----
for _sxy, _who in ((SCREW_XY, "chin"), (TOP_SCREW_XY, "top")):
    for _e, _d in (("cover bottom edge", _sxy[1] - COVER_Y0),
                   ("cover top edge",    MOB_OY1 - _sxy[1]),
                   ("cover -X edge",     _sxy[0] - OX0),
                   ("cover +X edge",     OX1 - _sxy[0])):
        assert _d >= SCREW_EDGE_MIN - 1e-9, (
            f"the d{CBORE_D} {_who} counterbore at {_sxy} is {_d:.2f}mm from the {_e}, under "
            f"the {SCREW_EDGE_MIN:.2f} it needs (its own radius + the {CHAMFER} bed chamfer + "
            f"margin). Too close and it is a notch in the outline; closer still and the chamfer "
            f"will not build at all")
assert (19.20 - COVER_Y0) < SCREW_EDGE_MIN and (21.50 - COVER_Y0) < SCREW_EDGE_MIN, (
    "control failed: the two rejected screw positions (19.20 notched the outline, 21.50 killed "
    "the chamfer) both read as having adequate edge distance")
# and the chin boss must not run into the seal rim's wall on its way back
assert SCREW_XY[1] + SCREW_BOSS_D/2 <= RIM_Y0 - RIM_WALL + 1e-9, (
    f"the chin screw boss reaches y={SCREW_XY[1] + SCREW_BOSS_D/2:.2f}, past the retention "
    f"strip's end at {RIM_Y0 - RIM_WALL:.2f} -- it would foul the seal rim's low-Y wall")
# ...and the top boss must not reach back into it from the other side
assert TOP_SCREW_XY[1] - SCREW_BOSS_D/2 >= RIM_Y1 + RIM_WALL + 1e-9, (
    f"the top screw boss reaches y={TOP_SCREW_XY[1] - SCREW_BOSS_D/2:.2f}, into the seal rim's "
    f"high-Y wall at {RIM_Y1 + RIM_WALL:.2f}")
# THE ONE THAT KILLED ROUND 4c, STATED SO IT CANNOT COME BACK SILENTLY: a top screw cannot go
# on the -X half at any y, because the cell lane owns it.
assert not (SCREW_LANE_X - CBORE_D/2 >= OX0 + COV_WALL and SCREW_LANE_X + CBORE_D/2 <= CELL_X1), (
    "control failed: the screw lane reads as fitting inside the cell bore's X span, so the "
    "arithmetic that eliminated every -X fastener position is no longer being applied")


def _yprism(pts, y0, y1):
    """Extrude an ABSOLUTE (x, z) cross-section along +Y.

    ⚠️ ITS CALLER LIST HAS TURNED OVER COMPLETELY AND A HANDOFF NOTE SAID OTHERWISE. It was
    written for the dovetail, then "kept because the spring tunnel uses it" -- and both of
    those are now deleted. Its one live caller is the +Y end cooling vent (§5h). Kept on that
    evidence, not on the note: `grep _yprism` is the check, and it is two lines long.

    Rot(-90,0,0) sends sketch +v to world -Z and the extrude direction to world +Y -- the same
    trick cyl_y() and the polarity markings use -- so a sketch point (x, -z) lands at (x, y, z).
    """
    sk = make_face(Polyline(*[(x, -z) for (x, z) in pts], close=True))
    return Pos(0, y0, 0) * (Rot(-90, 0, 0) * extrude(sk, y1 - y0))


GRILLE_CELL_N = None                                    # set by back_cover(), read by the checks
TOPMESH_N     = None                                    # ditto, the blind end-face mesh
TOPVENT_N     = None                                    # ditto, the LED-side through field
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
# ⚠️ THIS IS NO LONGER THE BINDING LIMIT AND IT IS KEPT AS THE RECORD OF WHAT WAS. The bare
# compartment would seat 29.30; the chin screw's boss pad takes the -X end of the lower band,
# so the real limit is the one derived beside the strip's placement below. Both are printed.
PROT_L_MAX    = (RIM_X1 - RIM_X0) - 2*PROT_CLR          # 29.30, the bare compartment
PROT_L        = 21.50           # JP re-measured: "a little over 21" — seat derives to 22.30 between ribs
PROT_W        = 4.50            # JP-MEASURED 2026-08-02: "like 4.5mm wide"
PROT_T        = 2.50            # JP-MEASURED 2026-08-02: "and 2.5mm thick"
                                # (the placeholder was right, which is luck, not evidence)
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
# ⚠️ AND 2.40 WAS WRONG ONCE THE DETENTS WENT ON, IN A WAY ONLY THE MESH CHECK CAUGHT. A rib
# 0.10 SHORTER than the PCB has nothing at the PCB's top edge for a detent to grow out of, so
# the first version's bumps were FLOATING BOXES 0.10mm off the rib and 0.40mm off the board --
# and every numeric check passed. `_check_manifold` reported one non-manifold edge on the cover
# and that was the only sign. The ribs are OUTSIDE the strip's footprint, so their height was
# never what kept the board flat; 15 layers puts the detent's root on solid rib.
PROT_RIB_H    = 15 * LH                                 # 3.00 = PROT_T + PROT_DET_H, exactly
# >>> THE STRIP MOVES TO THE LOWER BAND, AND IT FIXES THREE THINGS AT ONCE. <<<
#
# JP's constraint is the metal, not the plastic: "the strip has to lie flat close to the battery
# so the already-soldered nickel strips reach the places." It used to sit CENTRED in the UPPER
# compartment, PROT_CX = 35.70, PROT_Y1 = 85.00, which was the worst place in the part:
#
#   1. IT BLOCKED THE TOP SCREW. Round 4c: the boss must reach y 83.30 (the edge rule less its
#      own radius) and the strip's top was 85.00 -- a 1.70mm overlap, and there is no x in a
#      30.10mm compartment where a d9.00 boss clears a 25.50mm pocket. Three escapes were tried
#      and all fail on arithmetic (move it -X: the conflict is the 83.30 line, not x; move it
#      -Y: its lowest legal top is 83.40 against the boss's 83.30, short by 0.10; thicken the
#      cover wall past CBORE_DEPTH: the pad lands exactly where the strip sits).
#   2. ITS B- TAB HAD TO REACH THE OTHER END OF THE BAY. The negative contact is at the bay's
#      -Y end; the strip was at +Y. That is a ~60mm run for a pre-welded tab, and it was the
#      LONGER of the two runs rather than the shorter.
#   3. ITS PIGTAIL HAD TO REACH THE LEAD PASS, which is at y 20.00..26.50 -- the far end again.
#
# In the lower band, y BAY_Y0..RIM_Y0-RIM_WALL, all three invert: the boss is unobstructed, the
# B- tab folds up into the leaf pocket a few millimetres away and IS the spring (§3b), and the
# pigtail exits into the lead pass directly across the divider. Only B+ makes the long run, in
# the groove that already exists for it.
#
# ⚠️ AND THE LOWER BAND WAS NOT FREE EITHER -- THE CHIN SCREW WAS ALREADY IN IT. Its boss pad
# runs x SCREW_LANE_X +/- 4.50 the full height of the band. At the old lane x = 25.00 that left
# x 29.50..50.75 = 21.25 for a pocket needing PROT_L + 2*PROT_CLR = 22.30. Short by 1.05. So
# the SCREW LANE moved -X to the furthest point its own d5.80 counterbore can reach without
# breaking into the divider's base -- see §5g -- which buys 1.45 and leaves 1.20 of clearance.
# That the same move also carries both screws 1.45mm closer to the -X edge, the one edge that
# can never hold a fastener, is a second reason and not the first one.
# >>> THE BODY LIVES IN THE BAY'S BOTTOM +X CORNER NOW.  §4c is why it fits at all. <<<
#
# Centred along the bay so both 34.25 tabs reach their fold seats (check 13d), tucked into the
# corner solid under the cell's shoulder, opening onto the bore so the cell lies on it.
# +X rather than -X because the other three corners are spent: -X bottom bought the ease
# (1.87 of wall left on its diagonal), -X top is the vent labyrinth's (z -18.40..-11.50), and
# the top pair cost the same growth as the bottom while making JP thread the strip in beside a
# seated cell instead of laying it down first.
PROT_PKT_CLR  = 0.40                                    # all round the body in its pocket
PROT_SOLDER   = 3.00                                    # joint room at the output end
PROT_CX       = None                                    # -> the bay, not the chin band
PROT_Y0       = (BAY_Y0 + CELL_TIP_Y)/2 - PROT_L/2      # body centred along the bay
PROT_Y1       = PROT_Y0 + PROT_L
# ============================================================================
# 5f-c. THE STRIP LIES BESIDE THE BATTERY, IN THE DIVIDER'S PLACE.
# ============================================================================
#
# >>> JP, after being told what it costs: "no strip and nickel lay besid ethe batteyr like <<<
# >>> i toild you" / "you can delete that inner wall it's fine" / "or modify it".           <<<
#
# Every other construction was measured and none closes at 39.00: the bay's corner solid is
# 0.73 short axis-aligned and cannot be rotated into a fit (no angle satisfies both the divider
# and the outer wall); a midframe straddle is 0.21 short; the upper compartment fits but puts
# the body 74.70mm of tab-path from the far leaf seat, needing 52.08mm of NEW soldered nickel
# against 23.25 of surplus. The divider's own 2.00 is the only space in the case, and it is
# 4.17 with the corner -- real clearance, plus room for the solder JP correctly points out will
# make his part thicker than 2.50.
#
# ⚠️ WHAT IT COSTS, SO NOBODY RE-LEARNS IT: the divider IS the sealed speaker chamber's -X
# wall -- one wall doing two jobs, as its own definition has said since it was written. Over
# RIM_Y0..RIM_Y1 the chamber and the cell bay become ONE VOLUME. Check 7b reports that side
# instead of asserting it, check 19c restates the ingress picture, and the report carries the
# opening map. This is an informed owner's decision, not an oversight, and it is recorded as
# one.
#
# The body lies FLAT ON THE BAY FLOOR beside the cell, mid-bay -- which is also what keeps the
# 34.25 tabs closing with no extension at all (check 13d). Its +X half stands clear of the cell
# entirely (the cell's surface has fallen away by then), so THE SOLDER JOINTS GO ON THAT SIDE
# and their thickness stops being a constraint.
PROT_PKT_X1   = RIM_X0                                  # up to where the divider used to be
PROT_PKT_X0   = PROT_PKT_X1 - PROT_W                    # 16.15, the body's -X edge
PROT_PKT_Z0   = CAV_Z0                                  # it stands on the bay's own floor
PROT_PKT_Z1   = PROT_PKT_Z0 + PROT_T + PROT_PKT_CLR
PROT_BOSS_CLR = 0.50            # plan clearance, strip corner to the chin screw's boss
# ============================================================================
# 5f-b. THE STRIP IS CASE-RESIDENT AND ITS HOME IS UNRESOLVED.  READ BEFORE MOVING IT.
# ============================================================================
#
# >>> JP, 2026-08-02: "the bms strip hugs teh battery" / "no the nickel struip stays in <<<
# >>> the case with the excess strip as little leaf springs" / "entire strip with nickel <<<
# >>> strips included is 90mm" / "soldered to the battery wires"                         <<<
#
# The architecture he describes is: the strip lives in the case permanently, lying flat in the
# CELL BAY against the cell's side; the surplus nickel folds into leaf springs at BOTH ends;
# its output is soldered to the pigtail. That is coherent and the length budget closes -- see
# the arithmetic in check 13d, which is printed every build.
#
# ⚠️ AND IT DOES NOT FIT, FOR A REASON THAT IS ARITHMETIC AND NOT PREFERENCE. The cell bore is
# INSCRIBED EXACTLY in the bay -- tangent on three sides, measured, not estimated:
#
#     -X extreme  -0.75 vs CELL_X0  -0.75    gap 0.00
#     +X extreme  18.65 vs CELL_X1  18.65    gap 0.00
#     bottom     -29.10 vs CAV_Z0  -29.10    gap 0.00
#     seated cell top -10.30 vs BACK_Z -9.70 -> 0.60 of headroom
#
# That is the X budget closing (check 3: bore + divider + driver pad = 51.50 of 51.50), not
# slack anyone forgot to use. A PROT_T strip needs PROT_T of clearance somewhere and there is
# 0.00 on three sides. The spendable X slack is (rim - driver pad - 0.50) = 1.40, still short,
# and spending it moves the divider, the rim, DRV_CX, the grille field and the bond plateau.
#
# So the case-resident strip needs the CASE to grow -- COVER_Z0 down ~2.5, or the X budget
# re-cut -- and PROT_W/PROT_T are still ⚠️ UNMEASURED placeholders. JP calipered the LENGTH
# (21.50) and the FLAT ASSEMBLY (90.0); he has never measured the section. Growing the backpack
# 2.5mm on a guessed thickness is not a change this file should make on its own.
#
# UNTIL THEN THE STRIP IS MODELLED WHERE IT WAS: the chin band pocket below. That is a
# STATEMENT OF AN UNRESOLVED ITEM, not a claim that the chin band is right -- if it stays
# there, the leaf-spring-at-both-ends chain and the "hugs the battery" geometry are both
# unbuilt, and the chamber wall's deletion loses the premise it was granted on (that the band
# would be empty).
BMS_PACK_FLAT_L = 90.00         # JP-MEASURED: strip body + both nickel tabs, laid flat
_INT_R        = max(OUT_R - COV_WALL, 1.0)              # the interior rbox's own radius, 4.25
_pkt_dx = PROT_PKT_X0 - CELL_AXIS_X
_pkt_need = math.sqrt(max((CELL_D_MAX/2)**2 - _pkt_dx**2, 0.0))
assert (CELL_AXIS_Z - CELL_BORE_CLR) - PROT_PKT_Z1 >= _pkt_need, (
    f"the seated body's top is {(CELL_AXIS_Z-CELL_BORE_CLR)-PROT_PKT_Z1:.2f} below the cell's "
    f"axis and the cell's own surface is {_pkt_need:.2f} down at that x -- THE CELL WOULD SIT "
    f"ON THE BODY. Move PROT_PKT_X0 +X (the cell's surface falls away fast there) or thin the "
    f"seat; do NOT grow the case, the envelope is JP's one hard line")
# THE SOLDER SIDE MUST BE CELL-FREE. JP: "once i solder teh battery wires it wil be thikcer."
# Past the cell's +X extreme there is no cell at any height, so joints and wire roots have the
# whole compartment above them and their thickness stops being a dimension anyone has to know.
assert PROT_PKT_X1 > CELL_AXIS_X + CELL_D_MAX/2, (
    f"the body's +X edge at {PROT_PKT_X1:.2f} does not clear the cell's surface at "
    f"{CELL_AXIS_X+CELL_D_MAX/2:.2f} -- there is nowhere on it for a solder joint to stand, and "
    f"JP has said twice that his joints make the part thicker")
# ...and the body must sit inside the span the divider actually vacated.
assert PROT_Y0 >= RIM_Y0 and PROT_Y1 <= RIM_Y1, (
    f"the body at y {PROT_Y0:.2f}..{PROT_Y1:.2f} runs outside the divider's deleted span "
    f"({RIM_Y0:.2f}..{RIM_Y1:.2f}) -- past either end a STUB is still standing and the body "
    f"would have to pass through it")
assert PROT_Y0 > BAY_Y0 and PROT_Y1 < CELL_TIP_Y, (
    f"the body at y {PROT_Y0:.2f}..{PROT_Y1:.2f} has run past a contact face "
    f"({BAY_Y0:.2f}/{CELL_TIP_Y:.2f}) -- the tabs fold at those faces")

# ---- THE HOLD-DOWN.  JP: "secured with the ... strip-securing features", not tape or hope. ----
#
# The ribs stop it sliding; nothing stopped it LIFTING, and the previous revision said so out
# loud ("no clip, reliance recorded") because a lid-clip over the PCB is a downward-facing
# ledge in the cover's print orientation -- the bridging class JP rejected the hooks for.
#
# The answer is already in this file, at the contact kerf: a DETENT, not a clip. A bump left
# standing on the rib faces at the PCB's top edge overhangs by its own PROT_DETENT and nothing
# else -- under one extrusion width, which is what makes the contact bar printable. The PCB
# deflects past 0.30 of interference going in and the same coming out, and 0.30 on a 2.50 board
# is a positive snap rather than a friction fit.
PROT_DETENT   = 0.30            # how far each bump overhangs the seated PCB
PROT_DET_H    = 2 * LH          # 0.40, the bump's height -- same as the contact bar's
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
# 5g. THE BAY'S METALWORK.  A CONTACT THAT FALLS OUT IS A DESIGN FAILURE.
# ============================================================================
#
# >>> JP, 2026-08-01: "we need features to hold the spring, and to hold the metal strips." <<<
# >>> AND LATER THE SAME DAY: "just PLA printed and the nickel strips."                    <<<
#
# The second sentence deleted the first one's subject. There is no spring to hold any more --
# the coil is gone (§3b) and what takes its place is a FOLD in the same nickel the contacts are
# made of. So the bay's metalwork is now exactly two pieces of 0.25 strip and they are RETAINED
# THE SAME WAY, by one construction used at both ends of the bay:
#
#     -Y end   the FOLDED LEAF  -- its root in a kerf, its fold projecting into the bay
#     +Y end   the FLAT PLATE   -- its whole body in a kerf, flush with the end wall
#
# ⚠️ ONE CONSTRUCTION, TWO ENDS, AND THAT IS THE POINT. The version this replaces had a
# d9.00 gabled tunnel for the coil and a kerf for the plate -- two unrelated retention schemes,
# two sets of constants, two ways to be wrong. A kerf with a detent bar does the whole job at
# both ends: it is the seat, the insertion throat and the tab's lane in one cut, its walls are
# vertical, it has no roof, and the bar left standing across the back of it is what stops the
# metal coming out the way it went in. The tunnel's over-travel stop is not lost either -- the
# end wall behind the leaf IS the stop, and it is a whole wall rather than an annular lip.
#
# THE ACCEPTANCE BEHAVIOUR IS STILL JP'S AND IT IS STILL SHARP: cell OUT, case held
# OPEN-SIDE-DOWN, the metal stays put. Check 8g asks it that way at BOTH ends now, with the
# escape direction and a control that must NOT collide.
#
# ---- WHY THE LEAF IS METAL AND NOT A PRINTED FLEXURE.  CREEP, NOT PRINTABILITY. ----
#
# A PLA cantilever pressing a cell against a contact is loaded CONSTANTLY for the life of the
# device, and PLA stress-relaxes under constant strain: a month later the deflection is still
# there and the force is not. This family's printed-in-place button hinges are the counter-
# example that proves the rule -- they flex for a fraction of a second and spend the rest of
# their lives unloaded, which is why they survive. A battery contact is the opposite duty
# cycle, so PLA does the GEOMETRY (datum, travel stop, retention) and nickel does the force.
#
# ---- AND THE FORCE IS JP-TUNABLE, WHICH THE POCKET HAS TO ALLOW FOR ----
#
# A hand-formed fold's rate is whatever his fingers and pliers produce. Nothing here can
# predict it, so the pocket is dimensioned to accept a RANGE of fold depths: the kerf fixes the
# root and the bay is open in front of it, so a deeper fold simply starts further +Y. What IS
# bounded is the geometry -- LEAF_FREE against the shortest cell for preload, LEAF_SOLID
# against the longest for closure -- and both are asserted in section 4b, on the constants, and
# again in check 5 on the built solid.
#
# ⚠️ CONTACT WIPE IS A FEATURE AND IS RECORDED AS ONE. The cell's flat can face slides across
# the fold's crown as it seats, which scrubs the oxide off both. A flat-to-flat plate contact
# does not do that, which is part of why the + end keeps its own detent pressure.
LEAF_SEAT_Y   = BAY_Y0          # the fold's back bears on the bay's -Y end wall
                                # (LEAF_W and LEAF_KERF alias the plate's, below)


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
# ---- and the leaf's root uses the SAME kerf, because it is the same metal ----
LEAF_W    = CONTACT_W                       # 10.00
LEAF_KERF = CONTACT_KERF                    # 0.35
assert abs(LEAF_T - CONTACT_T) < 1e-9, (
    f"the leaf is {LEAF_T} stock and the plate is {CONTACT_T} -- they no longer share a kerf, "
    f"so LEAF_KERF has to stop being an alias and become its own derivation")


def leaf_phantom(height, dz=0.0):
    """The folded nickel leaf, as the envelope its fold sweeps, so the bay can be asked about it.

    Modelled as a plain box: a fold's exact profile is whatever JP's pliers produce and the
    questions asked of it are all envelope questions -- does it fit, is it captive, does the
    cell reach it. Its Z window is the PLATE's, because both are cut from the same strip into
    the same kerf and the cell's can face is what both have to meet.

    ⚠️ IT INCLUDES THE ROOT, AND THE FIRST VERSION DID NOT -- it started at LEAF_SEAT_Y, i.e.
    it modelled only the part of the leaf standing in the bay. The captivity test then lifted a
    phantom that was nowhere near the detent bar and read 0.00 mm3 of interference, which the
    gate correctly called a failure: THE THING THAT MAKES IT CAPTIVE IS THE PART THAT WAS
    MISSING FROM THE MODEL. A phantom that omits the retained feature cannot test retention.
    """
    return bx(CELL_AXIS_X - LEAF_W/2, CELL_AXIS_X + LEAF_W/2,
              LEAF_SEAT_Y - LEAF_KERF + 0.02, LEAF_SEAT_Y + height,
              CONTACT_Z0 + dz, CONTACT_Z1 + dz)

def plate_phantom():
    """The FLAT +Y contact plate, as its own phantom.  IT HAD NONE, AND A CHECK NEEDED IT.

    ⚠️ WHY THIS EXISTS: check 15 measures whether a polarity marking can be SEEN, and it ran
    that lens against `leaf_phantom()` alone -- the -Y metalwork. The "+" marking is on the
    OTHER end wall, 66mm away, so the lens was measuring the "+" mark against a piece of metal
    that is nowhere near it. That is the identical defect `leaf_phantom`'s own docstring records
    ("a phantom that omits the retained feature cannot test retention"), one end further along:
    a phantom that omits the +Y metalwork cannot test the +Y marking.

    The plate lies FLUSH IN ITS KERF -- body from CELL_TIP_Y to CELL_TIP_Y + CONTACT_KERF, i.e.
    entirely BEHIND the wall face the mark is cut into, projecting nothing into the bore. That
    is the whole reason the two markings are placed asymmetrically, and now it is MEASURED
    instead of asserted in a comment.
    """
    return bx(CELL_AXIS_X - CONTACT_W/2, CELL_AXIS_X + CONTACT_W/2,
              CELL_TIP_Y, CELL_TIP_Y + CONTACT_KERF,
              CONTACT_Z0, CONTACT_Z1)


def prot_phantom():
    """The 1S protection body, in its bay pocket, so its fit is measured and not asserted.

    All three dimensions are JP-calipered now, so this phantom is the real part rather than a
    class placeholder -- which is what makes the 0.39mm of cell clearance over it (§4c) a
    clearance and not a hope. Its 4.50 face lies against the cell; its 2.50 goes into the
    corner solid.
    """
    return bx(PROT_PKT_X0 + PROT_PKT_CLR, PROT_PKT_X0 + PROT_PKT_CLR + PROT_W,
              PROT_Y0, PROT_Y1,
              PROT_PKT_Z0, PROT_PKT_Z0 + PROT_T)

def tp4056_phantom():
    """The module that NO LONGER FITS. Kept so check 13 can prove that, not just claim it.

    Placed where the STRIP is, because that is the only free floor left: the lower band. Its
    17.00 short axis against a band of RIM_Y0-RIM_WALL - BAY_Y0 = 8.20 is the arithmetic, and
    the boolean is what says so.
    """
    _cx = (RIM_X0 + RIM_X1) / 2
    return bx(_cx - TP_W/2, _cx + TP_W/2, RIM_Y1 + RIM_WALL, RIM_Y1 + RIM_WALL + TP_L,
              CAV_Z0, CAV_Z0 + TP_H)
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
# 5h. COOLING.  THE MOBILE PLUGGED THE HEAT SOURCE'S OWN VENT, AND NOBODY NOTICED.
# ============================================================================
#
# >>> JP: "cooling hexagons all over the parts as the agent deems best thermally      <<<
# >>> advantageous."  So: WHERE IS THE HEAT, AND WHERE CAN IT ACTUALLY GO.            <<<
#
# THE SOURCE IS MEASURED, NOT ASSUMED. No constant in either file names the ESP32-S3 -- the
# board is a pocket, `PY0,PY1 = -FIT, BL+FIT`, and nothing inside it is modelled. So it is read
# out of the vendor STEP: the only 7.01 x 7.01 x 0.90 back-side solid on the board is a QFN56
# at x 20.51..27.52, y 61.11..68.12, z -2.50..-1.60. That is the SoC, on the BACK, firing into
# the board cavity. Check 18 re-derives it from the STEP so this stops being a transcription.
S3_XY0, S3_XY1 = (20.51, 61.11), (27.52, 68.12)         # MEASURED, vendor STEP, back side
S3_Z           = (-2.50, -1.60)
S3_PKG         = 7.01                                   # QFN56, nominal 7.00
#
# ⚠️ AND THE VARIANTS DO NOT VENT THROUGH THE SAME FACE, WHICH IS THE FINDING.
#
#   DESK:   the S3's footprint sits WHOLLY inside the back hex field (x 9..41, y 19..75). Its
#           heat crosses 4.60mm of cavity air, 2.60mm of floor, and leaves through ~113 holes
#           into open room air. The desk vents the SoC optimally already and gets NOTHING here
#           -- byte-identical desk output is the gate's whole point.
#   MOBILE: the SAME field exists, and the BOND PLATEAU REFILLS IT over x 18.65..50.35,
#           y 28.00..76.80 -- which covers the S3's footprint completely. Behind the plug is
#           the SEALED SPEAKER CAVITY. So on the mobile the SoC's back-face exit is closed
#           twice over, and it was closed by an acoustic requirement that had no idea it was
#           also a thermal one. That is not fixable here and must not be: a hex through the
#           plateau vents the "sealed" cavity into the board cavity, which is check 6's whole
#           subject. The heat has to leave some other way.
#
# WHERE IT CAN GO, ELIMINATED IN ORDER (numbers in check 18, not just here):
#
#   * back face          -- plateau + sealed cavity. See above. FORBIDDEN.
#   * cell-bay wall      -- the failure vent is a LABYRINTH on purpose (§5d): a straight hole
#                           into the bay is a light and dust path, and that was settled. Adding
#                           a hex field beside it re-opens a closed decision. DECLINED.
#   * midframe side walls-- the only air they touch is the cavity band, CAV_FLOOR..PCB_BOT =
#                           5.50mm. A LAT_AF cell is 4.75 across flats and this file's own rule
#                           (the GLOW_AF assert, twelve lines up, the one that caught GLOW_R
#                           inheriting 4.75) wants 0.80 of margin -> 4.70 is the ceiling. Short
#                           by 0.05, and the lattice is not negotiable. NO FIELD.
#   * upper compartment  -- would need a hex field in the midframe's back face at y 76.80..86.35
#                           to have any air in it, i.e. 0.40mm from the seal ring's high-Y leg,
#                           and would then need an exit through the cover's top wall directly
#                           over the 1S protection PCB. Two new ingress paths onto live battery
#                           electronics to vent a dead volume. DECLINED.
#   * +Y END FACE        -- the case's top block is solid BACK_Z..SEAM_Z for y 86.35..92.00, and
#                           the board cavity's own +Y wall is the far side of it. A bore through
#                           5.65mm of that block opens the cavity STRAIGHT TO ATMOSPHERE at the
#                           one end that is UP in both poses that matter -- docked (the slab
#                           leans back TILT degrees, +Y up) and in the hand. **THIS ONE.**
#
# It is also the only candidate that adds no ingress class: the board cavity already has four
# open flank channels. And it is 5.65mm of bore, not a window, so nothing sees in.
# ---- ORIENTATION IS THE DESIGN DECISION HERE, AND #28 IS WHY ----
#
# These cells are HORIZONTAL BORES in the print (the midframe prints back-face-down, so a bore
# along +Y runs sideways). A hexagon has exactly two orientations and BOTH have a cost:
#
#   VERTEX UP  -- no flat crown, but the two roof faces run at atan(0.5r / 0.866r) = 30 deg
#                 from horizontal. THIS IS THE STAND'S GRILLE. It is `rotation=30` fed through
#                 `Rot(-90,0,0)`, and it is issue #28: the cells DROOPED and needed
#                 GRILLE_FLARE to recover. 30 degrees is not a roof, it is a sag.
#   FLAT UP    -- roof shoulders at 60 deg and a FLAT CROWN of one side length, LAT_R = 2.74.
#
# Flat-up wins and it is not close. A 2.74mm bridge is ordinary; this same part already bridges
# CBORE_D = 5.80 flat, four times, in its own bed face, and those print. A 30-degree slope has
# nothing to anchor to and this project has the failed part to prove it. So: flats on +/-Z, the
# Z extent is LAT_AF (4.75) and the X extent is 2*LAT_R (5.485) -- which is the opposite way
# round from every other lattice in the family, and is the reason the pitch below is written
# against 2*LAT_R rather than the usual aflat + web.
EV_EDGE   = 1.60                        # material left at each end of the row
EV_SEAM   = 1.60                        # shell left under the bezel seam at SEAM_Z
EV_FLOOR  = 3 * LH                      # 0.60 the lowest face sits above the cavity's floor
EV_CROWN  = MESH_R                      # the flat span the roof bridges
EV_PITCH  = 2 * MESH_R + MESH_WEB_BORE  # across-corners plus the shared web
# The cell wants the BACK cavity's own centreline -- that is the band the SoC radiates into --
# and is raised only as far as keeping its lowest face clear of the cavity floor requires.
EV_CZ     = max((CAV_FLOOR + E.PCB_BOT) / 2, CAV_FLOOR + MESH_AF/2 + EV_FLOOR)
EV_Y0     = E.PY1 - 1.00                # cut starts inside the pocket, so it cannot dead-end
EV_Y1     = MOB_OY1 + 1.00
# ⚠️ THE ROW IS PHASED ON THE SCREW LANE AND THE CENTRE CELL IS THEN DELETED. That gap is the
# top screw, and it is deliberate on both counts: phasing the lattice anywhere else puts a cell
# 1.62mm from the pilot instead of 6.73, and leaving the cell in would bore through the one
# fastener the top edge has. A keyhole reads as intent in a render; a 0.63mm web does not.
#
# The row is bounded by the BOARD POCKET's straight span, not by the outer profile, so that
# every bore is a clean constant-length tunnel that breaks through into the cavity. Cells out
# on the pocket's own POCK_R corner would still open -- the cut runs to PY1-1.00 -- but they
# would break through at a different depth on each side, which is a shape nobody chose.
_EV_LO = E.PK0 + E.POCK_R + EV_EDGE + MESH_R
_EV_HI = E.PK1 - E.POCK_R - EV_EDGE - MESH_R
EV_XS = tuple(_x for _k in range(-12, 13)
              for _x in (SCREW_LANE_X + _k * EV_PITCH,)
              if _EV_LO - 1e-9 <= _x <= _EV_HI + 1e-9 and abs(_x - SCREW_LANE_X) > 1e-9)
assert EV_XS, "the +Y end vent solved to zero cells -- the pocket's straight span is too narrow"
assert min(abs(_x - SCREW_LANE_X) for _x in EV_XS) - MESH_R - PILOT_D/2 >= MIN_SOLID, (
    f"the nearest end-vent cell leaves "
    f"{min(abs(_x-SCREW_LANE_X) for _x in EV_XS) - MESH_R - PILOT_D/2:.2f}mm of block between it "
    f"and the top screw's pilot, under the {MIN_SOLID:.2f} floor")
assert EV_CZ - MESH_AF/2 >= CAV_FLOOR - 1e-9, (
    f"the end vent's floor is at z {EV_CZ-MESH_AF/2:.2f}, below the cavity floor "
    f"{CAV_FLOOR:.2f} -- the bottom of every bore would dead-end in the 2.60 floor")
assert EV_CZ + MESH_AF/2 <= SEAM_Z - EV_SEAM + 1e-9, (
    f"the end vent's crown is at z {EV_CZ+MESH_AF/2:.2f}, leaving "
    f"{SEAM_Z-(EV_CZ+MESH_AF/2):.2f}mm of shell under the bezel seam at {SEAM_Z:.2f}")


# ============================================================================
# 5i. THE BATTERY SIDE IS EASED.  A ROUND WOULD NOT PRINT, AND THAT IS THE FINDING.
# ============================================================================
#
# >>> JP: "i want the rounded back edge of the battery backpack so it feels better in <<<
# >>> the hand."  The goal is ERGONOMIC -- the -X back edge should not be a corner in a <<<
# >>> closed palm.  It is NOT literal tangency to the cell bore, and it could not be.    <<<
#
# ⚠️ A TRUE ROUND ON THIS EDGE IS UNPRINTABLE, AND THE REASON IS THE PRINT ORIENTATION, NOT
# THE WALL. The cover prints OUTER-FACE-DOWN, so COVER_Z0 is the bed. Round the (-X, -Z) corner
# with radius R and the arc meets the bed TANGENT TO HORIZONTAL: at R = 3.20 the outline moves
# 1.11mm OUTWARD in the first 0.20 layer. That is not a knife edge, it is a 1.11mm unsupported
# outward lean off the first layer, and no wall thickness fixes it. The deferred "constant-
# offset wrap at r 11.90 about the cell axis" is the same thing worse: tangent 0.10 BELOW the
# bed face, i.e. the first layer is a hairline.
#
# WHAT IS PRINTABLE, AND WHAT THIS IS: an arc that is tangent to VERTICAL where it leaves the
# side wall and rolls over only as far as a 45-DEGREE TANGENT, then runs out to the bed on that
# 45. Every facet is >= 45 by construction -- the arc is truncated at exactly the angle where
# it would stop being printable, rather than drawn and then apologised for.
#
# ⚠️ AND ITS SIZE IS CAPPED BY THE 2.20 WALL, NOT CHOSEN. The corner's diagonal from the outer
# corner to the bay's inner corner is COV_WALL*sqrt(2) = 3.111, and an arc of radius R eats
# (sqrt(2)-1)*R of it. Holding MIN_SOLID puts the ceiling at R = 3.65. R = 3.00 leaves 1.87 --
# against the 0.80 chamfer that was there, about four times the edge relief.
#
# Going further is possible and is NOT free: moving the cell lane +1.40 (the X budget's slack,
# check 3) would take the bed-face reach from 1.76 to ~3.54, and it ripples into the divider,
# the seal rim, DRV_CX, the grille field and the bond plateau. That is a round with its own
# gate, and it is JP's call after he has held this one.
EASE_R      = 3.00                      # arc radius; ceiling 3.65 at MIN_SOLID, see above
EASE_FACETS = 8                         # segments across the 45 degrees of arc
EASE_TAN45  = 1.0 - math.sqrt(2) / 2    # 0.2929 -- where the arc's tangent hits 45 degrees
EASE_BED    = 2 * EASE_TAN45 * EASE_R   # 1.76 across the bed face
EASE_RISE   = EASE_R                    # 3.00 up the battery side
# the thinnest wall the ease leaves, on the diagonal to the bay's inner corner
EASE_WALL   = COV_WALL * math.sqrt(2) - (math.sqrt(2) - 1) * EASE_R
assert EASE_WALL >= MIN_SOLID, (
    f"the eased battery edge at R={EASE_R:.2f} leaves {EASE_WALL:.2f}mm of wall on the corner's "
    f"diagonal, under the {MIN_SOLID:.2f} floor. The ceiling is R = "
    f"{(COV_WALL*math.sqrt(2) - MIN_SOLID)/(math.sqrt(2)-1):.2f} and the only way past it is to "
    f"move the cell lane +X, which moves the divider, the rim, the driver and the grille")


# ============================================================================
# 5j. TWO THINGS JP ASKED FOR IN THE TOP OF THE BACKPACK.  ONE IS A HOLE, ONE IS NOT.
# ============================================================================
#
# >>> "a hexagon mesh at the top of the backpack on battery side of the boss"          <<<
# >>> "there's room for a RGB LED in that upper compartment ... so there should be a   <<<
# >>>  hexagon in the mid plate to get in there with a wire"                           <<<
#
# ⚠️ THE FIRST ONE CANNOT BE A THROUGH-VENT, AND THE REASON IS WHAT IS BEHIND IT.
# "Battery side of the boss" is x < the boss's -X edge. Working back from the +Y end face on
# that side: 2.20 of top wall, then the CELL-LANE BULKHEAD (§4b, solid), then at y < CELL_TIP_Y
# the 18650 BORE itself. So a hole either dead-ends in the bulkhead or breaks into the cell bay
# -- and the cell bay's ingress rule is already settled and is the strictest in the part: §5d's
# vent is a LABYRINTH specifically so no straight light or dust path reaches a Li-ion cell. A
# hex field would be that path, several times over.
#
# So this one is BLIND: debossed TOPMESH_D into the end face, leaving MIN_SOLID of wall. It is
# what JP can see and feel -- the family's own motif on the face his fingers sit on -- and it
# is not an opening. The honest place for a through-vent on that end is the OTHER side of the
# boss, over the upper compartment, which is where the LED below is going; that is a choice for
# JP to make deliberately rather than to inherit from a hex field pointed at a battery.
TOPMESH_D    = 3 * LH                   # 0.60 deep; COV_WALL - 0.60 = 1.60 left, the floor
TOPMESH_EDGE = 1.60                     # material at each edge of the field
assert COV_WALL - TOPMESH_D >= MIN_SOLID - 1e-9, (
    f"the blind top mesh is {TOPMESH_D:.2f} deep in a {COV_WALL:.2f} wall, leaving "
    f"{COV_WALL-TOPMESH_D:.2f} against the {MIN_SOLID:.2f} floor -- at that depth it stops "
    f"being a deboss and starts being a window into the cell bay")
# the field: the flat part of the +Y end face, from the corner arc to the boss, and clear of
# the eased edge below and the mating plane above.
TOPMESH_X0 = OX0 + OUT_R + TOPMESH_EDGE
TOPMESH_X1 = (SCREW_LANE_X - SCREW_BOSS_D/2) - TOPMESH_EDGE
# ⚠️ THE Z BOUNDS ARE TIGHT AND THAT IS WHY THERE IS A COUNT FLOOR. At the first attempt the
# field was 16.00 tall against the 16.75 three staggered rows need, so exactly ONE cell landed
# -- a single hexagon where JP asked for a mesh, and every assert passed because a field of one
# is still a valid field. TOPMESH_N_MIN is the invariant that was missing: the count is the
# feature, so the count is what gets asserted.
TOPMESH_Z0 = COVER_Z0 + EASE_RISE + 0.40        # just clear of the eased edge below
TOPMESH_Z1 = BACK_Z - 1.20                      # 3 extrusions under the mating plane
# ⚠️ NOT A CELL COUNT ANY MORE.  I typed 8, the gate said 7; I typed 6, the gate said 5. Twice
# guessing at a number the lattice and the field bounds already determine between them -- and a
# floor set above what the geometry affords is the over-strict check ember_case.py warns about
# ("over-strict is not safe -- it is just wrong in the other direction, AND IT GETS SWITCHED
# OFF"). The invariant I actually wanted is not "how many cells" but "is enough of the panel
# patterned to read as a mesh", which is an AREA FRACTION and is derived, not chosen. It still
# catches what the count was for: a field that collapses to one cell reads ~4% and fails.
TOPMESH_FRAC_MIN = 0.15
#
# ---- AND THE SECOND ONE IS A REAL APERTURE, IN THE MIDFRAME ----
#
# One hex through the midframe's 2.60 floor, from the BOARD CAVITY into the upper compartment,
# so an RGB LED sitting in that compartment can be wired to the board. It is the first thing
# ever to open those two volumes to each other, so the ingress picture is stated rather than
# assumed: the board cavity already has four open flank channels and ~100 back-face vent cells,
# and the upper compartment is dry, dead space above the seal rim. What the aperture does NOT
# touch is the two volumes that have rules -- the sealed speaker cavity (it is +Y of the rim's
# high-Y wall) and the cell bay (it is +X of the divider).
#
# ⚠️ IT MUST OPEN INTO THE CAVITY, NOT INTO THE BLOCK. Above PY1 the midframe is solid
# BACK_Z..SEAM_Z, so a hex placed there would be a blind hole that looks identical from the
# back face. Sited below PY1, above the bond plateau, and clear of the mic bore, the +X boss
# and the top screw's pilot collar -- all measured in check 19, not eyeballed here.
# ---- (b) THE THROUGH FIELD, +X OF THE BOSS.  JP took the alternative: light out the top. ----
#
# The blind field above is blind because the cell bay is behind it. On the OTHER side of the
# boss the top wall backs onto the UPPER COMPARTMENT -- dry, above the seal rim, and about to
# hold an RGB LED. So this one is a real bore, and it is a light window as much as a vent.
# Same cells, same lattice, same flats-on-Z orientation as the +Y end vent, for the same
# printability reason: these are horizontal bores and a vertex-up cell is issue #28.
TOPVENT_X0 = (SCREW_LANE_X + SCREW_BOSS_D/2) + TOPMESH_EDGE
TOPVENT_X1 = (OX1 - OUT_R) - TOPMESH_EDGE
TOPVENT_Z0, TOPVENT_Z1 = TOPMESH_Z0, TOPMESH_Z1          # one band across the whole end face

# ---- (c) THE INTERNAL VENT, CELL BAY <-> LED COMPARTMENT.  A LABYRINTH, NOT A HOLE. ----
#
# JP: "there can be a hex vent between the battery compartment and the led compartment."
#
# ⚠️ IT CANNOT BE A STRAIGHT BORE, AND THE THROUGH FIELD ABOVE IS WHY. With (b) cut, the
# compartment is open to the sky; a plain hex through the divider would then be a straight
# path from outside air into a Li-ion bay, which is the exact thing §5d's labyrinth was built
# to refuse. Geometry, not opinion: a ray from a top cell at x 30 to a divider hole at x 20.65
# leaves the bore at 41 degrees to its axis and the bore only collimates to 65, so it passes.
#
# So this is §5d's own construction moved into the divider: notch IVENT_D from the cell-bay
# face at one Y, IVENT_D from the compartment face at ANOTHER Y, and connect the two through
# the band where their depths overlap. Air turns twice; a straight line finds material. The
# divider is DIVIDER_W thick against the outer wall's COV_WALL, so the numbers differ from
# §5d's and are re-derived rather than copied.
IVENT_D    = 1.30                                       # from each face of the 2.00 divider
IVENT_BAND = 2*IVENT_D - DIVIDER_W                      # 0.60 -- SLOT_W, the proven void
# ⚠️ THE OFFSET IS IN Z, NOT Y, AND THE BOSS IS WHY. §5d offsets its two slots along the wall's
# length; here that length is Y, and the only Y window the divider has between the seal rim
# (76.40) and the top screw's boss (81.48) is 5.08mm -- one cell wide, not two. The divider is
# 19.40 TALL, so the pair goes one above the other and the air turns in Z instead. Same
# construction, different axis, because the obstruction is different.
IVENT_Y    = 79.00                                      # both notches, in the one free window
IVENT_CZ_O = -22.50                                     # compartment-side notch (lower)
IVENT_CZ_I = IVENT_CZ_O + LAT_AF + 1.20                 # cell-bay-side notch (upper), -16.55
assert IVENT_CZ_I + LAT_AF/2 < BACK_Z - 1.20 and IVENT_CZ_O - LAT_AF/2 > CAV_Z0 + 1.20, (
    f"the internal vent's notches span z {IVENT_CZ_O-LAT_AF/2:.2f}..{IVENT_CZ_I+LAT_AF/2:.2f} "
    f"and have run off the divider ({CAV_Z0:.2f}..{BACK_Z:.2f})")
# the cell-bay-side notch must open into OPEN BAY, not into the cradle: below CELL_AXIS_Z the
# divider's cell face is backed by cradle material everywhere outside the bore.
assert IVENT_CZ_I - LAT_AF/2 >= CELL_AXIS_Z, (
    f"the cell-bay-side notch reaches z {IVENT_CZ_I-LAT_AF/2:.2f}, below the cell's axis "
    f"{CELL_AXIS_Z:.2f} -- there the divider's face is backed by the CRADLE, so the notch opens "
    f"into solid and the vent is two blind pockets")
assert IVENT_Y + LAT_AF/2 <= TOP_SCREW_XY[1] - SCREW_BOSS_D/2 and \
       IVENT_Y - LAT_AF/2 >= RIM_Y1 + RIM_WALL, (
    f"the internal vent at y {IVENT_Y-LAT_AF/2:.2f}..{IVENT_Y+LAT_AF/2:.2f} does not fit the "
    f"divider's free window, {RIM_Y1+RIM_WALL:.2f}..{TOP_SCREW_XY[1]-SCREW_BOSS_D/2:.2f} -- "
    f"the seal rim is below it and the top screw's boss above")
assert IVENT_BAND > 0.0, (
    f"the internal vent's two notches are {IVENT_D:.2f} deep in a {DIVIDER_W:.2f} divider and "
    f"do not meet -- {2*IVENT_D:.2f} of cut in {DIVIDER_W:.2f} of wall leaves no band, so it "
    f"is two blind pockets and not a vent")
LED_PASS_XY    = (32.00, 80.50)
LED_PASS_BREAK = 3 * LH                 # 0.60 edge break at the CAVITY-side mouth, where the
                                        # wire turns from running flat to going through. That
                                        # mouth is the TOP of the hole in the print, so a flare
                                        # there widens upward and cannot overhang.


def _ease_profile():
    """(x, ABSOLUTE z) polygon of the material the eased battery edge REMOVES.

    Arc tangent to vertical where it leaves the -X face, truncated at a 45-degree tangent, then
    a straight 45 run-out to the bed. Returned as the CUT, so every point outside the part is
    pushed 1.0 clear and the polygon closes in air.
    """
    _cx, _cz = OX0 + EASE_R, COVER_Z0 + EASE_R
    pts = [(OX0 - 1.0, COVER_Z0 - 1.0), (OX0 + EASE_BED, COVER_Z0 - 1.0),
           (OX0 + EASE_BED, COVER_Z0)]
    for _i in range(EASE_FACETS + 1):                       # 225 deg -> 180 deg
        _a = math.radians(225.0 - 45.0 * _i / EASE_FACETS)
        pts.append((_cx + EASE_R * math.cos(_a), _cz + EASE_R * math.sin(_a)))
    pts.append((OX0 - 1.0, COVER_Z0 + EASE_RISE))
    return tuple(pts)


def _hex_xz(cx, cz, r):
    """A hexagon in the (x, ABSOLUTE z) plane with FLATS ON +/-Z. See the block above.

    Written out as points rather than passed as a `rotation=` that has to be reasoned about --
    the one time this family got a hex rotation wrong it produced a field of loose prisms
    (_hex_panel's own docstring), and the one time it got the orientation right but chose the
    wrong one it produced #28.
    """
    return tuple((cx + r*math.cos(math.radians(60*k)), cz + r*math.sin(math.radians(60*k)))
                 for k in range(6))


# ============================================================================
# 6. PARTS
# ============================================================================
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


# ============================================================================
# 5k. SIDE LABELS ON THE MIDFRAME'S FLANKS  --  UART / I2C / IO  (JP, r11)
# ============================================================================
#
# JP: "also all the lables should be smaller and onthe side of the mnidrame for the uart, sd, io,
# and i2c."
#
# >>> HIS LIST OF FOUR IS NOT TYPED HERE. IT IS DERIVED, AND IT COMES OUT EXACTLY RIGHT. <<<
# The mobile blocks two connectors outright (SIDE_BLOCK: BAT, because the cell pigtail is
# entirely internal, and SPK, because the driver's lead leaves through the SPK relief inside the
# sealed rim). Those two have NO OPENING ON THIS VARIANT. Everything else does, plus the microSD
# slit -- and `served minus blocked + SD` is {I2C, IO, SD, UART}, which is JP's list character
# for character. So the set is computed from SIDE_BLOCK and ASSERTED against his four, which
# means the day a connector is unblocked its label appears, and the day one is blocked its label
# DIES WITH ITS OPENING. That is the mic-label rule (a label over no bore is the founding hazard
# of this repo, and "a label is the same lie told in ink") generalised from one feature to a set.
SIDE_LBL_SITES = []          # (name, face, y-centre) -- filled below, derived
for _i, _nm in enumerate(E.CONN_LBL_L):
    if ("L", _i) not in E.SIDE_BLOCK["mobile"]:
        SIDE_LBL_SITES.append((_nm, "-X", sum(E.CONN_L[_i]) / 2))
for _i, _nm in enumerate(E.CONN_LBL_R):
    if ("R", _i) not in E.SIDE_BLOCK["mobile"]:
        SIDE_LBL_SITES.append((_nm, "+X", sum(E.CONN_R[_i]) / 2))
SIDE_LBL_SD = ("SD", "-X" if (E.SD_SOCKET[0] + E.SD_SOCKET[1]) / 2 < E.BW / 2 else "+X",
               (E.SD_SOCKET[2] + E.SD_SOCKET[3]) / 2)
assert sorted([n for n, _, _ in SIDE_LBL_SITES] + ["SD"]) == ["I2C", "IO", "SD", "UART"], (
    f"the served-connector set on the mobile is "
    f"{sorted([n for n,_,_ in SIDE_LBL_SITES] + ['SD'])}, which is no longer JP's four. Either a "
    f"connector changed hands or SIDE_BLOCK moved -- the LABELS follow the openings, so fix the "
    f"opening first and let this list re-derive")

# ---- THE BAND A LABEL CAN LIVE IN, and it is small ----
# The flanks are cut through at z CAV_FLOOR..PCB_BOT for the cable channels, so a label has to
# sit ABOVE that band, between the channel roof and the bezel seam.
SIDE_LBL_Z0   = E.PCB_BOT + E.LABEL_MARGIN
SIDE_LBL_Z1   = E.SEAM_Z - E.LABEL_MARGIN
SIDE_LBL_BAND = SIDE_LBL_Z1 - SIDE_LBL_Z0                      # 4.70
SIDE_WALL_T   = 2.60          # measured off the built solid on both flanks, not assumed

# ---- STROKE AND DEPTH: A DIFFERENT PRINT CLASS FROM EVERY OTHER LABEL IN THIS PROJECT ----
#
# The back-face labels are grooves in a face that prints AGAINST THE BED: their width is a
# horizontal dimension (nozzle-limited, LABEL_W 0.90) and their DEPTH runs in Z, so it is
# quantized to LAYER_H -- that is why LABEL_DEBOSS is "2 * LAYER_H_SHELL" and not a distance.
# A groove in a VERTICAL WALL inverts both of those:
#
#   depth   runs horizontally into the wall  -> layer height does NOT govern it
#                                              (ember_case.py:291 already says exactly this
#                                              about the 0.90 label grooves and the hex webs)
#                                           -> quantize to EXTRUSION WIDTH
#   strokes running along Y  are gaps in the LAYER STACK   -> layer-quantized
#   strokes running along Z  are gaps WITHIN a layer       -> nozzle-limited
#
# So the stroke stays at two extrusions -- 0.80, which is the BACK GRILL's web, the one field in
# this project that has actually PRINTED on a vertical wall. Below that is unproven territory and
# a groove that the perimeter simply bridges over is an invisible label, which is the one failure
# mode this file has already shipped once.
# ---- THE DRIVER OUTLINE'S DEPTH, AND IT IS THE ONE FEATURE r11 MAKES SHALLOWER ----
#
# >>> FLAGGED RATHER THAN QUIETLY REGRESSED, because JP asked for DEEPER everywhere. <<<
# The witness ring lives on the chamber floor, and that floor is the BAFFLE -- 2.20mm, the
# thinnest wall in this part, already carrying 31 grille openings and doubling as the bed face.
# At the 0.60 it inherited it left exactly MIN_SOLID (1.60) behind it: not a violation, but sitting
# ON the constraint with zero slack, which this file has an explicit precedent against --
# LABEL_DEBOSS took 2 layers instead of 3 for exactly this reason ("a value sitting on a
# constraint boundary has no slack"). Raising MARK_DEPTH to 0.80 for the polarity marks dragged
# the ring with it, the ledger's own wall assert caught it, and the honest answer is not to
# exempt the ring -- it is to give it its own derivation and let it come out SHALLOWER:
#
#     0.40 = 2 layers, leaving 1.80 of baffle, i.e. one whole layer of slack over the floor.
#
# 0.40 is also exactly the depth every label on the desk case is cut at, so this is not a
# thin mark -- it is the proven one, and the ring is 1.20 wide so it reads on width, not depth.
OUTLINE_DEPTH = _max_deboss(CAV_Z0 - COVER_Z0, quantum=LH)      # 0.40
assert OUTLINE_DEPTH < MARK_DEPTH, (
    "the driver outline is no longer the shallow exception -- re-read the ledger note above, "
    "because the reason it is shallow is the baffle and the baffle has not got thicker")

SIDE_LBL_W     = 2 * _EXTRUSION                                 # 0.80, proven on a vertical wall
SIDE_LBL_GAP   = SIDE_LBL_W + 1.00                              # 1.00 of material inside a word
SIDE_LBL_DEPTH = min(_max_deboss(SIDE_WALL_T, quantum=_EXTRUSION),
                     int(_ASPECT_MAX * SIDE_LBL_W / _EXTRUSION) * _EXTRUSION)   # 0.80
# height: the tallest that fits the band, then floored by what each glyph needs at this stroke
SIDE_LBL_H     = round(SIDE_LBL_BAND - SIDE_LBL_W, 2)           # ink height == the whole band

# ---- AND THIS IS WHERE JP'S FOURTH LABEL DOES NOT FIT.  NUMBER, NOT AN OPINION. ----
#
# The stroke font is normalised but the STROKE IS NOT, so every counter shrinks with h while the
# 0.80 groove does not -- ember_case.py records the same trap costing the desk set a size ("S's
# material at h = (0.98 + 0.90)*h/5.50 - 0.90 -> S needs h >= 5.27"). SD CONTAINS AN S. At this
# stroke the smallest S that keeps two extrusions of material between its own strokes needs
# h 4.70, i.e. ink 5.50 tall, against a band of 4.70. Short by 0.80mm, and there is no margin
# left to shave: the 0.80 keepouts are against a THROUGH-CUT channel below and the bezel SEAM
# above. Buying it with a narrower stroke means going under two extrusions on a vertical wall,
# which is exactly the unproven groove this file refuses to ship blind.
# >>> JP, ASKED DIRECTLY, ANSWERED "try on the sude anyway." SO IT IS BUILT -- EXPERIMENTAL. <<<
# This is the owner overriding a print floor with the number in front of him, the same class of
# call as the open chamber. It is built at the ONLY size that fits the band, and the ONE variable
# changed is the stroke: depth stays at its three neighbours' 0.80 so that if it fails, the
# failure is attributable to stroke width and nothing else.
#
#   stroke 0.50 = 1.25 extrusions at the 0.40 nozzle.  THE RISK IS NOT THE WEB -- the material
#   BETWEEN strokes measures 0.83 here, over the 0.80 the back grill proved. The risk is the
#   GROOVE: at 1.25 extrusions the perimeter may simply bridge across it and leave no mark at
#   all, which is an invisible label -- the defect this file has already shipped once (the "-"
#   behind the leaf). Nothing structural depends on it; the cost of failure is a blank patch.
#   The physical print is the verdict.
SIDE_LBL_SD_W  = 0.50           # ⚠️ EXPERIMENTAL, below the proven two-extrusion groove
SIDE_LBL_SD_H  = 3.90           # ink 4.40 tall in the 4.70 band -- 0.30 of slack
SIDE_LBL_SD_GAP = SIDE_LBL_SD_W + 1.00
_SD_H_MIN = 4.70
SIDE_LBL_SD_SHORTFALL = (_SD_H_MIN + SIDE_LBL_W) - SIDE_LBL_BAND        # +0.80
assert SIDE_LBL_SD_SHORTFALL > 0, (
    "SD now fits the flank band -- delete this shortfall block, add SD to the built sites and "
    "let the gate re-measure it, rather than leaving a constant that says it cannot")


def _side_label(paths, face, cy, cz, depth, w=None):
    """A label sketch laid onto a flank, authored in READING SPACE and mirrored on placement.

    ⚠️ THE +X FLANK READS BACKWARDS IF NOBODY WRITES THIS DOWN -- the same hazard as
    _back_label()'s X mirror, on a different pair of faces. For a viewer at -X (forward +X,
    up +Z) their right hand is up x forward = (0,0,1)x(1,0,0) = +Y, so model +Y reads LEFT TO
    RIGHT and no mirror is wanted. For a viewer at +X, forward is -X and their right hand is
    (0,0,1)x(-1,0,0) = -Y, so +Y runs RIGHT TO LEFT and the glyphs MUST be mirrored in u.
    Two of the three labels are on the +X flank, so getting this backwards mirrors most of them.
    """
    _p = paths if face == "-X" else [[(-u, v) for u, v in _path] for _path in paths]
    _sk = E._label_sketch(_p, SIDE_LBL_W if w is None else w)
    # sketch u -> world +Y, v -> world +Z (so its normal lands on +X): Rz90 after Rx90
    _sk = Rot(0, 0, 90) * (Rot(90, 0, 0) * _sk)
    _x = OX0 if face == "-X" else OX1 - depth
    return Pos(_x, cy, cz) * extrude(_sk, depth)


def midframe():
    """back_shell() plus the mobile additions. Composition, not a fork.

    Nothing here edits ember_case.py. The board pocket, the four bosses and counterbores,
    the side channels, the SD slit, the printed-in-place caps, the SPK relief and every
    label come through unchanged and unre-derived.
    """
    # ONE PROFILE, to the mobile's real top. _brow() used to bolt a separately-rounded
    # block on here and the silhouette stepped 5.48 PER SIDE at the join -- JP's "weird
    # bump on the top". back_shell draws it now; see its top_y argument.
    p = E.back_shell("mobile", MOB_OY1)

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

    # ---- THE TWO SCREWS: boss UP into the board cavity, pilot down through it ----
    
    # Identical treatment at both ends and that is not tidiness, it is the same problem twice.
    # At the CHIN the midframe is only its 2.60 floor, so a blind 2.60 pilot cannot hold a
    # cover; at the TOP the block is 14.40 of solid but the board pocket's +Y wall leaves a
    # 0.20mm web beside the bore above CAV_FLOOR. Both are answered by a boss that grows the
    # OTHER way -- UP into the board cavity, where standing proud costs nothing, instead of out
    # of the bed face, which is the defect ember_case.py:2771 records on both shell parts in one
    # session. Whether either fits is not reasoned about: the STEP clearance boolean measures it.
    for _sxy in SCREWS:
        p += cyl(_sxy[0], _sxy[1], CAV_FLOOR, CAV_FLOOR + SCREW_BOSS_H, SCREW_BOSS_D)
        p -= cyl(_sxy[0], _sxy[1], BACK_Z, BACK_Z + MOB_PILOT_DEPTH, PILOT_D)

    # ---- WS2812 GLOW WINDOW: hex cells cut into the side wall's INNER face, leaving a
    # GLOW_MEMBRANE skin at the exterior. Cutting from the inside keeps the outer face flat and
    # unbroken -- the hexes are invisible until lit -- and puts the membrane flush with the
    # outside rather than at the bottom of a recess that would shadow it.
    
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

    # ---- RGB LED WIRE PASS: board cavity -> upper compartment, one hex (see 5j) ----
    # hexp() is the family's own flat-top prism, the one the button caps use -- reused rather
    # than re-derived, because the one time this project wrote its own hex orientation it got
    # a field of loose prisms (_hex_panel's docstring).
    p -= hexp(LED_PASS_XY[0], LED_PASS_XY[1], LAT_R, BACK_Z - 1.0, CAV_FLOOR + 1.0)
    # ...and the edge break at the CAVITY-side mouth, where the wire turns from running flat to
    # going through. That mouth is the TOP of the hole in the print, so a wider hex over the
    # last LED_PASS_BREAK flares UPWARD and cannot overhang.
    p -= hexp(LED_PASS_XY[0], LED_PASS_XY[1], LAT_R + LED_PASS_BREAK,
              CAV_FLOOR - LED_PASS_BREAK, CAV_FLOOR + 1.0)

    # ---- +Y END COOLING VENT: the board cavity's only exit on this variant (see 5h) ----
    # Cut LAST, after the boss, so a bore stays a bore: the top boss's cylinder runs the full
    # y 83.30..92.30 and its +Y half lies inside material that is already solid, so cutting
    # first and adding second would refill a sliver of two bores with a no-op.
    for _cx in EV_XS:
        p -= _yprism(_hex_xz(_cx, EV_CZ, MESH_R), EV_Y0, EV_Y1)
    # ---- SIDE LABELS on the flanks (see 5k). Cut LAST, so nothing lands on top of them. ----
    # One loop over the DERIVED site list -- if a connector's opening disappears its label is not
    # in SIDE_LBL_SITES and is never cut, which is the whole point of deriving the set.
    for _nm, _face, _cy in SIDE_LBL_SITES:
        p -= _side_label(E._LBL_SIDE[_nm], _face, _cy,
                         (SIDE_LBL_Z0 + SIDE_LBL_Z1) / 2, SIDE_LBL_DEPTH)
    # SD last and separately -- its own stroke, its own paths, so its risk cannot reach the
    # other three by sharing a constant with them.
    p -= _side_label(E._LBL_SIDE_SD, SIDE_LBL_SD[1], SIDE_LBL_SD[2],
                     (SIDE_LBL_Z0 + SIDE_LBL_Z1) / 2, SIDE_LBL_DEPTH, w=SIDE_LBL_SD_W)

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
    # ⚠️ AND NOW THE HIGH-Y END TOO, OVER THE CELL LANE ONLY -- the same defect at the opposite
    # corner, and it cost a gate to find. The +Y fillet IS right for the compartment (that is
    # the case's real corner) and WRONG over the cell, whose bore runs to x = CELL_X0 and is
    # already only 0.10 inside the wall. It reached 4.15mm into the bore and the cell-vs-cradle
    # boolean measured 21.218 mm3 of it. Squaring it here is safe because the bulkhead below
    # then fills everything from the plate to BAY_Y1 -- so the corner ends up SOLID, not thin.
    p -= bx(OX0 + COV_WALL, CELL_X1, BAY_Y1 - _INT_R, BAY_Y1, CAV_Z0, BACK_Z + 1)

    # ---- CRADLE: put the flat floor back as a half-cylinder so the cell self-centres.
    # Added material whose top surface is the bore, i.e. two lobes rising from the floor --
    # concave, self-supporting, no overhang anywhere.
    p += (bx(CELL_X0, CELL_X1, BAY_Y0, BAY_Y1, CAV_Z0, CELL_AXIS_Z)
          - cyl_y(CELL_AXIS_X, CELL_AXIS_Z, CELL_BORE_D, BAY_Y0 - 1, BAY_Y1 + 1))

    # ---- THE +Y BULKHEAD.  The cell lane stops short of the compartment, and §4b says why:
    # the case's OUT_R corner curves in over the last 6.45mm and the bore is already only 0.10
    # inside the -X wall, so the last CELL_END_SETBACK of the lane has to be MATERIAL. Filling
    # it also disposes of the interior rbox's own corner fillet, which is what the cell was
    # colliding with -- 21.218 mm3, found by the cell-vs-cradle boolean and by nothing else.
    # The "+" plate's kerf is cut into this block's -Y face, so the plate is where the cell
    # reaches rather than where the case ends.
    p += bx(CELL_X0, RIM_X0, CELL_TIP_Y, BAY_Y1, CAV_Z0, BACK_Z)

    # ---- THE SHARED DIVIDER. One wall doing two jobs: the cell trough's inboard wall and
    # the seal rim's inboard wall. Two separate walls do not fit in the X budget (see
    # COV_WALL) and check 3 asserts the budget stays closed.
    # ---- THE DIVIDER IS NOW TWO STUBS.  §5f-c: JP's call, informed, and what it costs. ----
    # He was told in plain terms that this wall is the sealed chamber's -X boundary and that
    # removing it merges the chamber with the bay, and he reaffirmed the architecture: "no strip
    # and nickel lay besid ethe batteyr like i toild you" / "you can delete that inner wall it's
    # fine" / "or modify it". Modified, then -- because the latitude is worth taking:
    #
    #   KEPT  y BAY_Y0..RIM_Y0            and  y RIM_Y1..BAY_Y1     (9.80 and 13.68 of stub)
    #   GONE  y RIM_Y0..RIM_Y1            (the chamber's own span, and the strip's home)
    #
    # The stubs are not decoration. A rigid 65mm cylinder located in +X at BOTH ENDS cannot
    # migrate mid-span, so the cell keeps its lateral datum without the wall that used to give
    # it; and they keep the screw lane's derivation subject (its counterbore still stops at the
    # divider's base) and a root for the internal labyrinth vent's region.
    # ---- THE SEPARATOR WALL: the stubs grown into two long walls (JP, r11) ----
    #
    # JP: "i think there is roomn for a sepeartor wall there between the batter and teh speaker."
    # HE WAS RIGHT AND MY FIRST ANSWER WAS WRONG, so the correction is recorded here rather than
    # buried: I derived the thickness from the DRIVER-PAD SLACK (+X of RIM_X0, 1.55 against a 1.60
    # floor -> "short 0.05") and reported that it does not close. That is the wrong lane. The
    # stubs -- the features JP was pointing at -- live in the OLD DIVIDER'S lane, x CELL_X1..
    # RIM_X0, which is DIVIDER_W = 2.00 wide, i.e. 0.40 OVER MIN_SOLID. A wall there closes
    # comfortably, needs no clearance from the driver at all (it is behind RIM_X0), and does not
    # touch the bore: CELL_X1 IS the bore's +X tangent.
    #
    # >>> WHAT ACTUALLY BOUNDS IT IS ASSEMBLY, NOT THICKNESS, AND IT IS PINNED BY THE CELL. <<<
    # The strip lies flat in a pocket x PROT_PKT_X0..PROT_PKT_X1, and it is loaded STRAIGHT DOWN
    # like everything else in this bay -- so the full PROT_W of that column has to stay clear to
    # the top. The pocket cannot be shifted -X to free the wall's lane either: at the pocket's own
    # top Z the cell bore's +X edge is 15.87 and PROT_PKT_X0 is 16.15, i.e. 0.28mm away. The
    # column is pinned by the 18650.
    #
    # So the wall runs the WHOLE bay except the strip's own Y span, which leaves ONE window
    # instead of the two-stub gap -- and check 7b measures what that window costs. It is a
    # PARTIAL separation and the report says so in those words: the residual window sits directly
    # over the BMS, which is the one thing JP wanted out of the acoustic volume.
    p += bx(CELL_X1, RIM_X0, BAY_Y0, PROT_Y0 - PROT_PKT_CLR, CAV_Z0, BACK_Z)
    p += bx(CELL_X1, RIM_X0, PROT_Y1 + PROT_PKT_CLR, BAY_Y1, CAV_Z0, BACK_Z)
    # (THE FULL WALL IS NOT BUILT -- see the DRV_SHIFT block in Sec 5f. It is short by 0.10 against
    #  MIN_SOLID once the strip's own 0.40 pocket clearance is respected, and the only thing that
    #  closes it is a change to the driver's locating fit while JP is bench-testing that fit.)
    # ---- the rim's two genuinely new sides; the other two are the divider and the case wall
    p += bx(RIM_X0, RIM_X1, RIM_Y1, RIM_Y1 + RIM_WALL, CAV_Z0, BACK_Z)
    # ⚠️ THE LOW-Y WALL IS DELETED.  JP's standing call, and its premise is TRUE again.
    #
    # It was granted on "with the strip in the bay, the band the deletion opens is EMPTY", then
    # my tangency measurement briefly falsified that and I held the deletion rather than run it
    # on a dead premise. §4c put the strip in the bay for real, so the band IS empty and the
    # call stands. What it costs, measured before it was cut and re-measured by check 7b now:
    # a 584 mm2 opening against the grille's 562.7 -- a second mouth 1.04x the intended one --
    # and +24% of front air, which check 7 bounds. What it buys is JP's cable room, the whole
    # retention band, with nothing left in it to buzz.
    # (The rim's high-Y wall stays: nothing asked for it and it is the cavity's other end.)

    # ---- LOCAL THICKENING FOR THE SCREWS. CBORE_DEPTH 3.00 is DEEPER THAN COV_WALL 2.20, so
    # the head's seat is 0.80 inside the compartment and it bears on a boss, not on the wall.
    # Without one the annulus is whatever the wall happens to leave, which at the chin was a
    # notch rather than a hole.
    
    # CHIN: a rectangular pad from the cover's own bottom edge back to the rim's low-Y wall, so
    # the two tie together across the retention strip band.
    p += bx(SCREW_XY[0] - SCREW_BOSS_D/2, SCREW_XY[0] + SCREW_BOSS_D/2,
            COVER_Y0, RIM_Y0 - RIM_WALL, CAV_Z0, BACK_Z)
    # TOP: a plain d9.00 column, because it has something better to tie into. It reaches
    # y 92.30, past BAY_Y1 = 89.80 where the cover's top wall is solid COVER_Z0..BACK_Z for its
    # full 21.60 depth -- so the column is buttressed into a block rather than standing alone,
    # and no rectangular pad is needed to get it there. Vertical walls off the compartment
    # floor: self-supporting in the cover's own print orientation, nothing bridged.
    p += cyl(TOP_SCREW_XY[0], TOP_SCREW_XY[1], CAV_Z0, BACK_Z, SCREW_BOSS_D)

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
    # ⚠️ IT IS AT THE +Y END NOW. The polarity flipped when the strip moved to the lower band
    # (§4, §5f) -- the leaf and its B- tab want to be next to each other, so the leaf took the
    # -Y end and the plate took this one. Cut INTO the wall, i.e. +Y of CELL_TIP_Y.
    p -= bx(CELL_AXIS_X - CONTACT_W/2, CELL_X1,
            CELL_TIP_Y, CELL_TIP_Y + CONTACT_KERF,
            CONTACT_Z0, BACK_Z)
    # ...and the detent bar, left standing across the BACK of the kerf just above the seated
    # plate. Adding it back after the cut keeps one source for the kerf's own depth.
    p += bx(CELL_AXIS_X - CONTACT_W/2, CELL_AXIS_X + CONTACT_W/2,
            CELL_TIP_Y + CONTACT_KERF - CONTACT_DETENT, CELL_TIP_Y + CONTACT_KERF,
            CONTACT_Z1, CONTACT_Z1 + CONTACT_DET_H)

    # ---- THE "-" LEAF: THE SAME KERF, MIRRORED ONTO THE -Y END WALL (see 5g) ----
    # The fold's root drops into this slot and the fold itself stands +Y into the bay, where the
    # cell meets it. The wall behind the slot is the leaf's datum AND its over-travel stop, so
    # the coil tunnel's annular lip is not needed and is not missed. Runs to CELL_X1 so the
    # root's tab meets the divider's wire groove without a second feature -- the same reason
    # the plate's kerf does at the other end.
    p -= bx(CELL_AXIS_X - LEAF_W/2, CELL_X1,
            LEAF_SEAT_Y - LEAF_KERF, LEAF_SEAT_Y,
            CONTACT_Z0, BACK_Z)
    p += bx(CELL_AXIS_X - LEAF_W/2, CELL_AXIS_X + LEAF_W/2,
            LEAF_SEAT_Y - LEAF_KERF, LEAF_SEAT_Y - LEAF_KERF + CONTACT_DETENT,
            CONTACT_Z1, CONTACT_Z1 + CONTACT_DET_H)

    # ---- THE CROSSING LANE IS GONE WITH THE CHIN-BAND STRIP. ----
    # It carried a tab from the compartment, over the divider and the chin boss, into the cell
    # lane -- a 17mm vertical climb to a wiring plane at BACK_Z. With the body in the BAY
    # (§4c) both tabs run along the bay's own floor to their fold seats and never leave it.
    # The route stopped existing, so the feature did.

    # ---- POLARITY MARKINGS, debossed into the two end walls, facing into the bore ----
    # Rot(-90,0,0) sends sketch +v to world -Z; both glyphs are vertically symmetric so the
    # flip is harmless here — noted because it is NOT harmless for lettering.
    # ⚠️ THE "-" IS CUT AFTER THE TUNNEL BLOCK BELOW, not here, because it is debossed INTO
    # that block's mouth face and the block does not exist yet. Cutting it here would remove
    # nothing and the check would find a marking that was never made -- which check 15 would
    # catch, but only after a 15-minute build.
    for _glyph, _paths in (("+", MARK_PATHS_P), ("-", MARK_PATHS_N)):
        _pl, _cx, _cy, _cz = _mark_face(_glyph)
        _sk = E._label_sketch(_paths, E.LABEL_W)
        if _pl == "y":
            p -= Pos(_cx, _cy, _cz) * (Rot(-90, 0, 0) * extrude(_sk, MARK_DEPTH))
        else:
            p -= Pos(_cx, _cy, _cz - MARK_DEPTH) * extrude(_sk, MARK_DEPTH)

    # ---- THE SPRING TUNNEL IS GONE.  There is no coil to capture (§3b). ----
    # It was a block across the cell lane with a gabled bore through it, and it cost 3.00mm of
    # bay length plus the coil's own 2.50 solid height plus 1.00 of margin -- 6.50mm that the
    # case carried as the brow. The leaf's kerf does the same retention job in 0.35mm of wall.
    # ---- "-" ON THE BAY'S -Y END WALL, beside the leaf's kerf. See _mark_face(). ----
    # (both glyphs are cut in the one loop above -- the "-" is on the mating face now, not on
    # a bay end wall, so there is nothing left to cut here. See _mark_face().)

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

    # ---- SCREWS: clearance bore + FLAT-FLOORED counterbore in the bed face (inward, so
    # bed-legal). No tube is needed at either: the boss above already carries the seat.
    
    # ⚠️ THE COUNTERBORE DEPTH IS THE DISCIPLINE, NOT A FINISH. It is CBORE_DEPTH = exactly the
    # head height, so the head lands FLUSH. Shallower and the head stands proud -- and a proud
    # head on a case that docks in a slot is a case that will not seat, discovered at the dock
    # rather than at the bench. Deeper and the tip drives further into the pilot: ember_case
    # records that M3x14 bottoms out at the pilot's 6.20 end and that "the failure still looks
    # like success" -- you feel resistance, you stop, and the cover was never clamped. Check 11
    # bounds engagement from BOTH sides for exactly that reason and 11b measures the seat.
    for _sxy in SCREWS:
        p -= cyl(_sxy[0], _sxy[1], COVER_Z0 - 1, BACK_Z + 1, SCREW_D)
        p -= cyl(_sxy[0], _sxy[1], COVER_Z0 - 1, COVER_Z0 + CBORE_DEPTH, CBORE_D)

    # ---- PROTECTION-STRIP POCKET ----
    # Long axis along X (the only axis with room). Ribs sit OUTSIDE the PCB footprint and the
    # floor under it is left FLAT — a rib under a PCB is a rock under a board, and the component
    # face is the one that must not be loaded.
    # ---- THE BMS BODY'S POCKET, in the bay's bottom +X corner solid (see 4c / 5f-b) ----
    # A plain rectangular channel cut into the corner between the round bore and the flat
    # faces. It opens onto the bore, so the body lies against the cell and the cell holds it
    # down -- no clip, no detent, no bridged ledge. The chin-band pocket, its ribs, its
    # hold-down detents and the crossing lane over the divider are all GONE with it: they
    # housed a part that is not there any more, and a pocket for an absent part is the dead
    # SD_PLATE hazard this repo has paid for twice.
    # ⚠️ IT IS CUT UP TO THE BORE, NOT JUST TO PROT_PKT_Z1, AND THE GATE IS WHY. A pocket only
    # PROT_T tall leaves the corner solid ROOFING it -- 295 mm3 of cradle over the +X half,
    # because the bore's surface climbs away from the corner. That is a blind slot the strip
    # cannot be laid into and a bridge in the cover's print orientation, both at once. Cutting
    # to CELL_AXIS_Z removes the roof; everything above the bore's own surface is already void,
    # so the extra costs nothing and the channel is open to the cell along its whole width.
    p -= bx(PROT_PKT_X0, PROT_PKT_X1, PROT_Y0 - PROT_PKT_CLR, PROT_Y1 + PROT_PKT_CLR,
            PROT_PKT_Z0, CELL_AXIS_Z)
    # ---- NICKEL RUN GUIDES: shallow channels carrying each 34.25 tab from the body's ends to
    # its fold seat, in the shoulder gap where the round cell has already fallen away from the
    # flat face. TAB_D deep, so the run sits below the bore's surface and the cell cannot shave
    # it on the way in -- which check 8d's descent sweep now has a reason to look for.
    # ⚠️ THE GUIDES RUN IN THE CELL LANE, NOT UP TO RIM_X0, AND THE MESH CHECK IS WHY. Taken to
    # the divider's old face they grazed both screw bosses TANGENTIALLY -- a cut edge meeting a
    # cylinder's surface at a single line, four faces on one edge, non-manifold at exactly
    # (20.650, 22.600) and (20.650, 85.984), which are the two screw positions. It is also the
    # wrong place for them: the run should hug the CELL, which is where the leaf seats are.
    p -= bx(CELL_X1 - TAB_W, CELL_X1, BAY_Y0, PROT_Y0, PROT_PKT_Z0, PROT_PKT_Z0 + TAB_D)
    p -= bx(CELL_X1 - TAB_W, CELL_X1, PROT_Y1, CELL_TIP_Y, PROT_PKT_Z0, PROT_PKT_Z0 + TAB_D)
    # ---- SOLDER ROOM + THE WIRE ROUTE.  JP: "soldered to the battery wires."
    # The output joints stand proud of the body's 2.50, so the pocket is locally deeper at the
    # -Y end, and the pigtail leaves along the same corner to the cell-lead pass at the chin --
    # a route that never crosses the cell's insertion path because it is under the shoulder the
    # whole way.
    p -= bx(PROT_PKT_X0, PROT_PKT_X1, PROT_Y0 - PROT_PKT_CLR - PROT_SOLDER,
            PROT_Y0 - PROT_PKT_CLR, PROT_PKT_Z0, CELL_AXIS_Z)

    # ---- NOTHING STANDS PROUD OF BACK_Z ANY MORE. The six dovetail tongues that used to be
    # added here are gone with the slide (§5g). The cover's mating face is now a plain plane and
    # the retention is two screws through it -- which is also why check 8d could be turned from
    # a Y-slide sweep into a straight-down one.

    p = E.chamfer_outline(p, COVER_Z0, CHAMFER, "mobile cover bed face")

    # ---- THE EASED BATTERY EDGE (see 5i).  Full length, cut LAST. ----
    # After chamfer_outline deliberately: the ease's own 45-degree run-out IS the bed relief
    # over its span, and asking OCC to chamfer an edge that is about to be replaced is how
    # StdFail_NotDone arrives. It runs the cover's whole length, so there is no step in the
    # silhouette to blend -- and it dies EASE_RISE above the bed, ~19mm below the mating plane,
    # which is why the midframe, the vent labyrinth and the "-" marking are all untouched.
    p -= _yprism(_ease_profile(), COVER_Y0 - 1.0, MOB_OY1 + 1.0)

    # ---- THE DRIVER'S OUTLINE, PROJECTED ONTO THE CHAMBER FLOOR ----
    #
    # >>> JP: "the speaker outline should also go on the speaker backpack so weknow how much <<<
    # >>> tolrenece we have there at a glance."                                              <<<
    #
    # The midframe has carried this since r1 -- it is the groove he taped the driver against.
    # This is its twin on the cover: the driver's ACTUAL body footprint (DRIVER_H x DRIVER_W,
    # DRIVER_R corners) debossed where it projects onto the chamber floor, so the distance from
    # this line to any chamber structure IS the tolerance. Nothing is derived from a nominal --
    # the outline is drawn from the same constants driver_phantom() uses, so if the driver moves
    # the ruler moves with it.
    #
    # It lands on the 1.1mm ring of solid baffle between the driver's edge and the grille field
    # (GRILLE_INSET), so it interrupts no port and changes no acoustics. 0.60 deep leaves
    # MIN_SOLID of baffle, and it is nowhere near the rim's bearing face, which is at BACK_Z.
    _do_out = rbox(DRV_CX - DRIVER_H/2, DRV_CX + DRIVER_H/2,
                   DRV_CY - DRIVER_W/2, DRV_CY + DRIVER_W/2,
                   CAV_Z0 - OUTLINE_DEPTH, CAV_Z0 + 1.0, DRIVER_R)
    _do_in = rbox(DRV_CX - DRIVER_H/2 + LIP_WIDTH, DRV_CX + DRIVER_H/2 - LIP_WIDTH,
                  DRV_CY - DRIVER_W/2 + LIP_WIDTH, DRV_CY + DRIVER_W/2 - LIP_WIDTH,
                  CAV_Z0 - OUTLINE_DEPTH - 1.0, CAV_Z0 + 2.0, max(DRIVER_R - LIP_WIDTH, 0.5))
    p -= (_do_out - _do_in)

    # ---- THE BLIND TOP MESH on the battery side of the boss (see 5j). NOT a vent. ----
    # Debossed TOPMESH_D into the +Y end face, leaving MIN_SOLID of wall. Cells are the family
    # lattice, flats on +/-Z like the end vent's, so the two read as the same pattern on the
    # two ends of the same edge -- but this one is closed, because what is behind it is the
    # cell-lane bulkhead and then the 18650.
    global TOPMESH_N
    TOPMESH_N = 0
    # blind field: the back grill's own web, because a 0.60 deboss has no rib to lose
    _tm_pitch_x, _tm_pitch_z = 2*MESH_R + MESH_WEB_BLIND, MESH_AF + MESH_WEB_BLIND
    # through field: the wider web, because these are horizontal BORES (#47's class)
    _tv_pitch_x, _tv_pitch_z = 2*MESH_R + MESH_WEB_BORE, MESH_AF + MESH_WEB_BORE
    _tm_cx = (TOPMESH_X0 + TOPMESH_X1) / 2
    _tm_cz = (TOPMESH_Z0 + TOPMESH_Z1) / 2
    for _j in range(-9, 10):
        _z = _tm_cz + _j * _tm_pitch_z
        if not (TOPMESH_Z0 + MESH_AF/2 <= _z <= TOPMESH_Z1 - MESH_AF/2):
            continue
        for _i in range(-9, 10):
            _x = _tm_cx + _i * _tm_pitch_x + (_tm_pitch_x/2 if _j % 2 else 0)
            if not (TOPMESH_X0 + MESH_R <= _x <= TOPMESH_X1 - MESH_R):
                continue
            p -= _yprism(_hex_xz(_x, _z, MESH_R), MOB_OY1 - TOPMESH_D, MOB_OY1 + 1.0)
            TOPMESH_N += 1
    # ---- (b) THE THROUGH FIELD on the LED side of the boss. Real bores, into the compartment.
    global TOPVENT_N
    TOPVENT_N = 0
    _tv_cx = (TOPVENT_X0 + TOPVENT_X1) / 2
    _tv_cz = (TOPVENT_Z0 + TOPVENT_Z1) / 2
    for _j in range(-6, 7):
        _z = _tv_cz + _j * _tv_pitch_z
        if not (TOPVENT_Z0 + MESH_AF/2 <= _z <= TOPVENT_Z1 - MESH_AF/2):
            continue
        for _i in range(-9, 10):
            _x = _tv_cx + _i * _tv_pitch_x + (_tv_pitch_x/2 if _j % 2 else 0)
            if not (TOPVENT_X0 + MESH_R <= _x <= TOPVENT_X1 - MESH_R):
                continue
            p -= _yprism(_hex_xz(_x, _z, MESH_R), BAY_Y1 - 1.0, MOB_OY1 + 1.0)
            TOPVENT_N += 1
    _tv_frac = TOPVENT_N * (1.5 * math.sqrt(3) * MESH_R**2) / \
               ((TOPVENT_X1-TOPVENT_X0) * (TOPVENT_Z1-TOPVENT_Z0))
    assert _tv_frac >= TOPMESH_FRAC_MIN, (
        f"the LED-side through field patterns only {100*_tv_frac:.0f}% of its field "
        f"({TOPVENT_N} cells) -- under {100*TOPMESH_FRAC_MIN:.0f}% it is not a field, and it is "
        f"also the LED's window, so thin coverage is a dim window as well as a weak vent")

    # ---- (c) THE INTERNAL LABYRINTH VENT through the divider (see 5j). Two notches + a band.
    # Cell-bay face at one Z, compartment face at another, joined only through the IVENT_BAND
    # of depth where the two cuts overlap. Gas turns twice; a straight line finds material.
    # Hex cells, so the field reads as the family's -- but what makes it safe is the offset.
    p -= Pos(CELL_X1, 0, 0) * (Rot(0, 90, 0) * extrude(make_face(Polyline(
             *[(-(IVENT_CZ_I + LAT_R*math.sin(math.radians(60*_k))),
                IVENT_Y + LAT_R*math.cos(math.radians(60*_k))) for _k in range(6)],
             close=True)), IVENT_D))
    p -= Pos(RIM_X0 - IVENT_D, 0, 0) * (Rot(0, 90, 0) * extrude(make_face(Polyline(
             *[(-(IVENT_CZ_O + LAT_R*math.sin(math.radians(60*_k))),
                IVENT_Y + LAT_R*math.cos(math.radians(60*_k))) for _k in range(6)],
             close=True)), IVENT_D))
    p -= bx(RIM_X0 - IVENT_D, RIM_X0 - IVENT_D + IVENT_BAND,
            IVENT_Y - LAT_AF/2, IVENT_Y + LAT_AF/2,
            IVENT_CZ_O - LAT_AF/2, IVENT_CZ_I + LAT_AF/2)

    _cell_a = 1.5 * math.sqrt(3) * MESH_R**2
    _tm_frac = TOPMESH_N * _cell_a / ((TOPMESH_X1-TOPMESH_X0) * (TOPMESH_Z1-TOPMESH_Z0))
    assert _tm_frac >= TOPMESH_FRAC_MIN, (
        f"the blind top mesh patterns only {100*_tm_frac:.0f}% of its "
        f"{TOPMESH_X1-TOPMESH_X0:.2f} x {TOPMESH_Z1-TOPMESH_Z0:.2f} field ({TOPMESH_N} cells) "
        f"-- under {100*TOPMESH_FRAC_MIN:.0f}% it does not read as a mesh. Most likely the boss, "
        f"the ease or the mating plane moved and squeezed it; a field of ONE is still a valid "
        f"field, which is exactly why this is measured and not just built")
    return p


def cell_phantom(dz=0.0, dy=0.0):
    """The 18650 itself, as a solid, so the checks can ask questions about it.

    A cell is not part of any STL, so nothing in a normal build would ever notice it fouling
    the board or its own cradle. Modelling it is the only way those become checkable.
    Resting in the cradle: a CELL_D_MAX cell in a CELL_BORE_D cradle sits CELL_BORE_CLR low.

    ⚠️ IT IS MODELLED SEATED AGAINST THE "+" PLATE, NOT FLOATING IN THE MIDDLE. The leaf pushes
    it that way and the longest cell is the one that has to fit, so both ends of the worst case
    are pinned by the same construction: +Y face on CELL_TIP_Y, body reaching back CELL_L_MAX.
    """
    return cyl_y(CELL_AXIS_X, CELL_AXIS_Z - CELL_BORE_CLR + dz, CELL_D_MAX,
                 CELL_TIP_Y - CELL_L_MAX + dy, CELL_TIP_Y + dy)


# spring_phantom() deleted with the coil. leaf_phantom() is defined up in section 5g, beside
# the kerf constants it depends on.


def driver_phantom():
    """The sealed-back module AS TAPED, diaphragm facing the grille.

    ⚠️ IT HANGS TAPE_T LOWER THAN THE MODEL USED TO SAY, and that only started mattering when
    the cover stopped sliding. The bond line is real hardware -- JP has already stuck the
    driver on -- and it was the one part of the assembly stack nobody had a number for. It
    changes nothing acoustically (check 7 differences VOLUMES, and the module's volume did not
    move) but it is the object the straight-down sweep has to miss, so the sweep gets the
    pessimistic position rather than the flattering one.
    """
    return rbox(DRV_CX - DRIVER_H/2, DRV_CX + DRIVER_H/2,
                DRV_CY - DRIVER_W/2, DRV_CY + DRIVER_W/2,
                BACK_Z - TAPE_T - DRIVER_T, BACK_Z - TAPE_T, DRIVER_R)


# ============================================================================
# 7. CHECKS.  Every one with a control that can fire.
# ============================================================================
def _lerr(depth, lh):
    """Distance from `depth` to the nearest whole multiple of `lh`. E's idiom, replicated
    here rather than imported because ember_case defines it inside _check_geometry()."""
    return abs(depth / lh - round(depth / lh)) * lh


def _rrect_area(w, h, r):
    return w * h - (4 - math.pi) * r * r


def _ink_half(paths):
    """(half-extent in u, half-extent in v) of a stroke glyph's INK, groove included.

    ⚠️ MARK_INK IS THE OVERALL EXTENT AND ONLY "+" IS SQUARE. Using MARK_INK/2 on both axes of
    a "-" claims 1.85mm of half-height for a glyph that is 0.45 -- which put its footprint
    1.40mm into the DOCKING BAND on paper and failed check 8i, and which would have made check
    15's own probe sweep 1.40mm of fresh air below COVER_Y0 and read the deboss as oversized.
    Exactly 8a's flare-height trap in another costume: the right number, on the wrong axis.
    """
    _us = [p[0] for path in paths for p in path]
    _vs = [p[1] for path in paths for p in path]
    return ((max(_us) - min(_us)) / 2 + E.LABEL_W / 2,
            (max(_vs) - min(_vs)) / 2 + E.LABEL_W / 2)


def _mark_face(which):
    """(plane, centre x, centre y, face) for a polarity marking. ONE derivation, read by BOTH
    the geometry and check 15, so a marking cannot drift off its face without the check
    following it there.

    `plane` is "y" for a deboss into a wall facing along Y (cut +Y from `cy`, centred at `cz`)
    or "z" for one into the cover's mating face (cut -Z from `cz`, centred at `cx, cy`).

    ⚠️ THEY SWAPPED ENDS WHEN THE POLARITY DID, and then the "-" ONE HAD TO LEAVE THE WALL
    ENTIRELY. The bay's polarity inverted with the leaf and the strip (§3b, §5f), so "-" became
    the low-Y end. Put on that end wall it is DEBOSSED CORRECTLY AND CANNOT BE SEEN: the folded
    leaf stands LEAF_FREE proud of exactly that face, directly over the mark, and you read a
    bay-end marking by looking down the bore from the other end. Check 15 measured its area and
    passed it -- area is not visibility, which is the #47 shape again (an invariant insensitive
    to the failure it names).
    
    # So "-" moves to the cover's own MATING FACE at BACK_Z, in the solid band between COVER_Y0
    # and BAY_Y0. Nothing can ever stand in front of a horizontal face that IS the opening:
    # with the cover off and the bay empty -- the moment the mark does its job -- you are
    # looking straight at it. "+" does NOT move, and the asymmetry is the point rather than an
    # oversight: the positive plate sits FLUSH in its kerf and projects nothing, so its wall
    # face is clear. Only the end with something standing in front of it had a problem.

    Both are still read at the moment the cell goes in, which is the whole job, and check 15
    now proves it with a sight line instead of assuming it.
    """
    if which == "+":
        return ("y", CELL_AXIS_X, CELL_TIP_Y, (CAV_Z0 + CONTACT_Z0) / 2)
    return ("z", CELL_AXIS_X, (COVER_Y0 + BAY_Y0) / 2, BACK_Z)


def _dirsign(wall):
    """+1 if the named side wall's material lies at increasing X from its inner face."""
    return 1.0 if wall == "hi" else -1.0


def _check_mobile(parts):
    print("\n--- MOBILE GEOMETRY CHECKS ---")

    # ---- 1. LAYER ALIGNMENT, every floor and recess against this part's own 0.20 ----
    for _d, _what in ((COV_WALL, "COV_WALL"), (LIP_DEPTH, "driver locating groove"),
                      (RIM_WALL, "rim wall"), (EV_FLOOR, "end-vent floor clearance"),
                      (CBORE_DEPTH, "cover counterbore"), (WGROOVE_Z, "lead groove"),
                      (TAB_D, "nickel tab slot"),
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

    # ---- 5. THE CELL BAY ACCEPTS THE WHOLE TOLERANCE BAND, ON A FOLD RATHER THAN A COIL ----
    
    # Same question as before, different mechanism, and the bounds are the two ends of one
    # manufacturing spread rather than two cell CLASSES: the SHORTEST cell must still be
    # preloaded, and the LONGEST must not close the fold. Both directions, both with controls,
    # because a single-bounded spring check passes on a spring that does nothing.
    for _nm, _L in (("shortest", CELL_L_MIN), ("longest", CELL_L_MAX)):
        _gap = BAY_L - _L                       # what the fold has to occupy
        assert _gap >= LEAF_SOLID, (
            f"the {_nm} cell at {_L} leaves the fold {_gap:.2f}mm -- under its {LEAF_SOLID:.2f} "
            f"closed height, so the cell physically will not go in")
        assert LEAF_FREE - _gap > 0.0, (
            f"the {_nm} cell at {_L} leaves a {_gap:.2f}mm gap against a {LEAF_FREE}mm free "
            f"fold -- the leaf is not compressed at all and the cell rattles with no contact")
    _travel = LEAF_FREE - LEAF_SOLID
    assert _travel >= (CELL_L_MAX - CELL_L_MIN), (
        f"fold travel {_travel:.2f} < the {CELL_L_MAX-CELL_L_MIN:.2f} cell-length spread -- one "
        f"end of the tolerance band cannot be accommodated")
    # CONTROL: a fold with too little travel must be rejected by the same arithmetic.
    _bad = LEAF_SOLID + 0.20
    assert not (_bad - LEAF_SOLID >= CELL_L_MAX - CELL_L_MIN), (
        "control failed: a fold with 0.20mm of travel reads as covering the cell spread")
    # >>> AND THE CONTROL THAT MATTERS MOST: THE DELETED COIL MUST NOT FIT THIS BAY. <<<
    # If it does, the bay never shrank, the brow was not the coil's fault, and the whole reason
    # this case is back on the desk profile is wrong.
    assert (BAY_L - CELL_L_MAX) < 2.50, (
        f"control failed: the deleted coil's 2.50 solid height still fits in the "
        f"{BAY_L-CELL_L_MAX:.2f}mm this bay leaves the longest cell, so removing it bought "
        f"nothing and MOB_OY1 = OY1 is a coincidence rather than a consequence")
    print(f"  [cell]    bay {BAY_L:.2f} on a folded leaf: shortest {CELL_L_MIN} -> fold at "
          f"{BAY_L-CELL_L_MIN:.2f} (preload {LEAF_FREE-(BAY_L-CELL_L_MIN):.2f}), longest "
          f"{CELL_L_MAX} -> {BAY_L-CELL_L_MAX:.2f} ({LEAF_MARGIN:.2f} off closed). BOTH FIT")
    print(f"             travel {_travel:.2f} vs {CELL_L_MAX-CELL_L_MIN:.2f} of cell spread; "
          f"LEAF_FREE {LEAF_FREE:.2f} is ⚠️ JP-TUNABLE -- he forms the fold by hand")
    print(f"             the deleted coil needed {2.50+1.00:.2f} of the same space and got it "
          f"by making the case {94.95-(MOB_OY1-OY0):.2f}mm longer. THAT WAS THE BROW.")

    # ---- 6. THE SEAL LANDS ON SOLID MATERIAL.  The two-parts-must-agree case. ----
    
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
    # CONTROL: the same measurement, on a patch of the SAME back face that is deliberately
    # perforated. If this reads solid, the probe cannot see a honeycomb and the 100.00% above
    # is silence rather than evidence.
    #
    # ⚠️ IT USED TO BE `Pos(0, -12.0, 0) * ring` AND THAT STOPPED WORKING THE MOMENT THE MOBILE
    # DROPPED ITS SECOND HEX ROW -- the ring slid onto floor that is now solid and read 98.40%,
    # failing as a control while the geometry it guards was perfectly fine. A control anchored
    # to an offset rather than to a FEATURE goes stale silently the first time the feature
    # moves. This one is anchored to the open strip the plateau does not reach: x < RIM_X0 -
    # PLATEAU_MARGIN is outside the refill by construction, and the field runs y 19..75.
    _ctl = bx(HEX_FIELD_X0 + 2.0, CELL_X1 - 1.0, 40.0, 60.0, BACK_Z, BACK_Z + _probe_t)
    _cfrac = (mf & _ctl).volume / _ctl.volume
    assert _cfrac < 0.98, (
        f"control failed: the seal probe reads {100*_cfrac:.2f}% solid over a patch of the back "
        f"face that IS the open hex vent field, so it cannot detect an unsealed rim")
    print(f"  [seal]    rim footprint {100*_frac:.2f}% solid; control on the open vent field "
          f"{100*_cfrac:.2f}% (must be < 98)")

    # ---- 6b. NO FASTENER MAY PIERCE THE SEAL.  In coordinates, as well as by boolean. ----
    
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

    _pierce = [(f"{_w} screw pilot", _s[0] - PILOT_D/2, _s[0] + PILOT_D/2,
                _s[1] - PILOT_D/2, _s[1] + PILOT_D/2)
               for _s, _w in ((SCREW_XY, "chin"), (TOP_SCREW_XY, "top"))]
    # The end-vent bores are cut in the same part and answer to the same rule -- they are not
    # in the BACK face, but a pocket that reached the rim's Y span from the +Y end would breach
    # the seal just as thoroughly, and stating it per feature is the point of this check.
    for _cx in EV_XS:
        _pierce.append((f"end vent x={_cx:.2f}",
                        _cx - MESH_AF/2, _cx + MESH_AF/2, EV_Y0, EV_Y1))
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
    assert _hits_ring(EV_XS[-1] - MESH_AF/2, EV_XS[-1] + MESH_AF/2,
                      RIM_Y1 - 1.00, EV_Y1), (
        "control failed: an end-vent bore run back down into the seal's Y span does not read "
        "as piercing, so nothing stops the next person lengthening one")
    assert not _hits_ring(RIM_X0 + 1.0, RIM_X0 + 3.0, RIM_Y0 + 1.0, RIM_Y0 + 3.0), (
        "control failed: a footprint wholly INSIDE the rim reads as piercing, so this test "
        "would reject the speaker relief and every legitimate feature in the cavity")
    print(f"  [seal 6b] {len(_pierce)} pockets in the midframe, all clear of the rim footprint; "
          f"retention strip y {BAY_Y0:.2f}..{RIM_Y0-RIM_WALL:.2f} makes room for the chin screw "
          f"and y>{RIM_Y1+RIM_WALL:.2f} for the top one ({TOP_SCREW_XY[1]-SCREW_BOSS_D/2:.2f} at "
          f"its boss's nearest reach)")

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
    print(f"             box-mode LIKE-FOR-LIKE vs the stand: {_sm:.0f} Hz / {_mm:.0f} Hz")
    print(f"             ⚠️ THAT IS A COMPARISON, NOT A DESCRIPTION. Both figures are closed-form "
          f"box modes, and this chamber is no longer a box: it is L-SHAPED with TWO open sides "
          f"(the low-Y wall and the -X divider, both on JP's call). The row is kept because "
          f"comparing the same wrong model on both parts is still informative; no honest "
          f"closed-form mode exists for the real volume and none is invented here.")

    # ---- 7b. THE SEALED CAVITY IS CLOSED ON ALL FOUR SIDES.  THE CHECK THAT WAS MISSING. ----
    #
    # >>> IT WAS PROPOSED THAT THE CHAMBER'S BOTTOM INNER WALL BE DELETED FOR CABLE ROOM,  <<<
    # >>> AND NOTHING IN THIS FILE WOULD HAVE STOPPED IT.                                  <<<
    #
    # Check 6 measures the MIDFRAME's back face over the rim's footprint. Check 7 measures the
    # air inside the envelope y RIM_Y0..RIM_Y1. The cover's own rim walls are at y < RIM_Y0 and
    # y > RIM_Y1 -- OUTSIDE BOTH. Delete one and the front cavity opens into the retention-strip
    # band, the cell bay's neighbourhood and the board cavity, and the build gates GREEN.
    #
    # ember_case.py:1689 is why it matters: the driver is a SEALED-BACK module, so "the chamber
    # volume barely matters -- what matters is the FRONT." A front cavity with a wall missing is
    # not a smaller cavity, it is not a cavity. And the one hole that IS in it, the SPK relief,
    # is closed by hand after wiring (check 9 prints the instruction); a missing WALL cannot be.
    #
    # Two of these four are not walls this file built -- the divider and the case's own side --
    # and they are probed anyway, because "it is obviously solid there" is the sentence every
    # other defect in this file started as.
    _cav_z = (CAV_Z0 + 0.20, BACK_Z - 0.20)
    for _nm, _w in (
            ("high-Y ", bx(RIM_X0 + 0.1, RIM_X1 - 0.1, RIM_Y1 + 0.1, RIM_Y1 + RIM_WALL - 0.1,
                           *_cav_z)),
            ("+X wall", bx(RIM_X1 + 0.1, OX1 - CHAMFER - 0.1, RIM_Y0 + 0.1, RIM_Y1 - 0.1,
                           *_cav_z))):
        _f = (cov & _w).volume / _w.volume
        assert _f > 0.98, (
            f"the sealed speaker cavity's {_nm} boundary is only {100*_f:.1f}% material -- the "
            f"front cavity is open to the rest of the case. The driver is a SEALED-BACK module, "
            f"so the front volume is the whole of its loading; a wall missing here is not a "
            f"bigger chamber, it is no chamber. If this is a deliberate cable pass, it belongs "
            f"in the cavity FLOOR or as a scallop in a wall's inboard face, not through it")
    # CONTROL: the same probe inside the cavity itself must read ~empty, or it cannot tell a
    # wall from air.
    _cav_ctl = bx(RIM_X0 + 4.0, RIM_X0 + 6.0, RIM_Y0 + 4.0, RIM_Y0 + 6.0, *_cav_z)
    _cav_cf = (cov & _cav_ctl).volume / _cav_ctl.volume
    assert _cav_cf < 0.10, (
        f"control failed: the cavity-closure probe reads {100*_cav_cf:.1f}% solid INSIDE the "
        f"cavity, so it cannot distinguish a wall from the air it encloses")
    # >>> BOTH OPENINGS ARE RASTERED OFF THE SOLID NOW, AND THAT IS THE SECOND FIX TO THE SAME <<<
    # >>> NUMBER. be95ed1 corrected this report for being wrong by 22x -- it printed the         <<<
    # >>> divider's CROSS-SECTION instead of the face it vacated. It was still a FORMULA over    <<<
    # >>> constants afterwards, so when r11 built the separator wall the check could not see it  <<<
    # >>> and cheerfully reported 869mm2 of opening into a part that has 417. A number computed  <<<
    # >>> from the constants a feature WOULD have had cannot notice the feature arriving. Both   <<<
    # >>> are measured with a thin slab through the plane in question, minus the built cover.    <<<
    def _open_in_plane(axis, at, a0, a1, b0, b1):
        """Open area in a thin slab through `axis` at `at`, over the (a,b) window. Measured."""
        _t = 0.10
        if axis == "x":
            _sl = bx(at - _t/2, at + _t/2, a0, a1, b0, b1)
        elif axis == "y":
            _sl = bx(a0, a1, at - _t/2, at + _t/2, b0, b1)
        else:
            _sl = bx(a0, a1, b0, b1, at - _t/2, at + _t/2)
        return (_sl - cov).volume / _t

    _open_area = _open_in_plane("y", (RIM_Y0 - RIM_WALL + RIM_Y0) / 2,
                                RIM_X0, RIM_X1, CAV_Z0, BACK_Z)
    # ⚠️ THE OPENING IS THE FACE THE WALL VACATED, NOT THE WALL'S CROSS-SECTION. The first
    # version of this line multiplied the divider's THICKNESS by its height -- 2.00 x 19.40 =
    # 39 mm2 -- and printed that as the opening. It is off by more than twentyfold: what is now
    # open between the chamber and the bay is the deleted wall's FACE, its Y span by its height.
    # A wrong area in a report is worse than no area, because it will be trusted; and this is
    # the number JP judges the acoustic trade by.
    _div_gone = _open_in_plane("x", (CELL_X1 + RIM_X0) / 2,
                               RIM_Y0, RIM_Y1, CAV_Z0, BACK_Z)
    _div_nominal = (RIM_Y1 - RIM_Y0) * (BACK_Z - CAV_Z0)        # what it was with NO wall at all
    _div_closed = _div_nominal - _div_gone
    assert _div_gone <= _div_nominal + 1e-6, (
        f"the measured -X opening {_div_gone:.0f} exceeds the {_div_nominal:.0f} the plane can "
        f"even hold -- the slab is sampling outside the chamber")
    # CONTROL: the same raster one wall-thickness further +X lands INSIDE the chamber, which is
    # all air, so it must read essentially fully open. If that came back partly solid the slab is
    # in the wrong place and every area on this row is fiction.
    _div_ctl = _open_in_plane("x", RIM_X0 + (RIM_X1 - RIM_X0) / 2,
                              RIM_Y0, RIM_Y1, CAV_Z0, BACK_Z)
    assert _div_ctl > 0.95 * _div_nominal, (
        f"control failed: a raster through the middle of the CHAMBER reads only "
        f"{_div_ctl:.0f} of {_div_nominal:.0f} mm2 open, but the chamber is air -- the "
        f"_open_in_plane slab is mis-placed and these opening areas mean nothing")
    print(f"  [chamber] closed on 2 sides (high-Y, case wall); control inside the cavity "
          f"{100*_cav_cf:.1f}%")
    print(f"             ⚠️ TWO SIDES ARE DELIBERATELY OPEN, BOTH ON JP'S INFORMED CALL: the "
          f"low-Y wall ({_open_area:.0f} mm2) and now the -X DIVIDER over the chamber's own span "
          f"({_div_gone:.0f} mm2). The chamber and the CELL BAY are ONE VOLUME over "
          f"y {RIM_Y0:.2f}..{RIM_Y1:.2f}.")
    print(f"             He was told the divider is the chamber's -X wall and reaffirmed the "
          f"architecture: the strip and its nickel lie beside the battery, in the space the "
          f"wall used to occupy (§5f-c). Recorded as a decision, not an oversight.")
    print(f"             SEPARATOR WALL (r11, JP's call): the stub lane x {CELL_X1:.2f}.."
          f"{RIM_X0:.2f} is {RIM_X0-CELL_X1:.2f} thick = {RIM_X0-CELL_X1-MIN_SOLID:+.2f} over "
          f"MIN_SOLID, so a wall CLOSES there. Built over the whole bay except the strip's own Y "
          f"span: closed {_div_closed:.0f} of {_div_nominal:.0f} mm2, {_div_gone:.0f} left "
          f"({100*_div_gone/_div_nominal:.0f}%). Control (raster inside the chamber) "
          f"{_div_ctl:.0f} mm2 open.")
    print(f"             ⚠️ PARTIAL, AND THE RESIDUAL WINDOW IS OVER THE BMS -- i.e. over exactly "
          f"what JP wanted out of the acoustic volume. It cannot be closed without giving up "
          f"STRAIGHT-DOWN assembly: the strip's {PROT_W:.2f} insertion column is PINNED by the "
          f"cell (0.28mm from the bore at the pocket's top Z), so no wall can share that lane.")
    print(f"             >>> FOR THE MORNING: that -X opening is BIGGER THAN THE GRILLE "
          f"({_div_gone:.0f} vs 562.7 mm2). The driver's front chamber now includes the cell "
          f"bay, and the cell and the BMS are inside the acoustic volume. r9 (40.60 deep, "
          f"chamber intact) is on the shelf if that sounds wrong in the hand. <<<")
    print(f"             ⚠️ THE LOW-Y SIDE IS DELIBERATELY OPEN -- JP's call, {_open_area:.0f} "
          f"mm2 against the grille's intended 562.7. It is a SECOND MOUTH, not a leak, and the "
          f"band behind it is empty now that the BMS body lives in the bay (§4c).")
    print(f"             ⚠️ THE BOTTOM INNER WALL IS LOAD-BEARING FOR THE ACOUSTICS and this "
          f"check is new: 6 and 7 both look past it (it sits at y < RIM_Y0). Cable room at that "
          f"end is {(BACK_Z-DRIVER_T-TAPE_T)-CAV_Z0:.2f}mm under the driver and "
          f"{(RIM_INNER_Y-DRIVER_W)/2:.2f}mm beside it -- the pigtail's exit, the SPK relief, "
          f"is INSIDE the rim, so the run never crosses this wall.")

    # ---- 7c. THE DRIVER'S WITNESS OUTLINE IS A RULER, SO IT GETS MEASURED LIKE ONE. ----

    # JP asked for the speaker outline on the backpack "so weknow how much tolrenece we have
    # there at a glance". That makes it an INSTRUMENT, and this file has already been burned once
    # by a marking that was present, correct by area, and unreadable (the "-" behind the leaf,
    # check 15). So: does it exist, does it land where a line can be READ, and does cutting it
    # cost the baffle anything.
    #
    # >>> AND IT IS A DIFFERENT RECTANGLE FROM THE MIDFRAME'S GROOVE, ON PURPOSE. <<<
    # The midframe's groove is driver + 2*DRIVER_CLR -- a LOCATING fit, it has to be loose or the
    # driver will not drop in. This ring is the driver's NOMINAL body -- a RULER, and a ruler with
    # clearance built into it is a lie. They differ by exactly DRIVER_CLR per side, which is why
    # the two lines look concentric in the viewer and why nobody should "harmonise" them later.
    _ring_out = rbox(DRV_CX - DRIVER_H/2, DRV_CX + DRIVER_H/2,
                     DRV_CY - DRIVER_W/2, DRV_CY + DRIVER_W/2,
                     CAV_Z0 - OUTLINE_DEPTH, CAV_Z0, DRIVER_R)
    _ring = _ring_out - rbox(
        DRV_CX - DRIVER_H/2 + LIP_WIDTH, DRV_CX + DRIVER_H/2 - LIP_WIDTH,
        DRV_CY - DRIVER_W/2 + LIP_WIDTH, DRV_CY + DRIVER_W/2 - LIP_WIDTH,
        CAV_Z0 - OUTLINE_DEPTH - 1, CAV_Z0 + 1, max(DRIVER_R - LIP_WIDTH, 0.5))
    _ring_cut = (_ring - cov).volume / _ring.volume
    assert _ring_cut >= 0.95, (
        f"the driver's witness outline only cut {100*_ring_cut:.0f}% of its own ring -- it is "
        f"being absorbed by the grille field or the chamber floor, and a partial ruler is worse "
        f"than none")

    # Is it a CONTINUOUS line or a dashed one? A witness mark drawn over a hex field is not
    # readable, and the solid baffle ring outside the field is only GRILLE_INSET wide while the
    # line is LIP_WIDTH wide -- so the fraction of it standing on solid is DERIVED, not chosen:
    # the straight runs give GRILLE_INSET/LIP_WIDTH and the corners can only add.
    # (Guessing this floor is exactly the 8a trap that rejected two sound fields this round.)
    def _ring_on_solid(inset):
        _r = (rbox(DRV_CX - DRIVER_H/2 + inset, DRV_CX + DRIVER_H/2 - inset,
                   DRV_CY - DRIVER_W/2 + inset, DRV_CY + DRIVER_W/2 - inset,
                   CAV_Z0 - OUTLINE_DEPTH, CAV_Z0, max(DRIVER_R - inset, 0.5))
              - rbox(DRV_CX - DRIVER_H/2 + inset + LIP_WIDTH,
                     DRV_CX + DRIVER_H/2 - inset - LIP_WIDTH,
                     DRV_CY - DRIVER_W/2 + inset + LIP_WIDTH,
                     DRV_CY + DRIVER_W/2 - inset - LIP_WIDTH,
                     CAV_Z0 - OUTLINE_DEPTH - 1, CAV_Z0 + 1,
                     max(DRIVER_R - inset - LIP_WIDTH, 0.5)))
        # the baffle that must survive UNDER the groove floor, over the ring's own footprint
        _u = _r.moved(Location((0, 0, -(CAV_Z0 - OUTLINE_DEPTH - COVER_Z0))))
        return 1.0 - (_u - cov).volume / _u.volume
    _ring_floor = GRILLE_INSET / LIP_WIDTH
    _ring_solid = _ring_on_solid(0.0)
    assert _ring_solid >= _ring_floor, (
        f"the witness outline stands on only {100*_ring_solid:.0f}% solid baffle against a "
        f"{100*_ring_floor:.0f}% floor derived from GRILLE_INSET/LIP_WIDTH -- the line crosses "
        f"grille openings and reads as dashes, which is unreadable at exactly the glance it "
        f"exists for")
    # CONTROL: slide the same ring inward past the baffle ring, fully onto the hex field. If a
    # line drawn over open grille still passes, this check cannot tell a ruler from a dashed one.
    _ring_ctl = _ring_on_solid(GRILLE_INSET + LIP_WIDTH)
    assert _ring_ctl < _ring_floor, (
        f"control failed: the same outline moved {GRILLE_INSET+LIP_WIDTH:.2f} inward, onto the "
        f"open grille field, still reads {100*_ring_ctl:.0f}% solid -- the readability lens is "
        f"blind and the assert above is decoration")
    print(f"  [outline] driver witness ring {_ring.volume/OUTLINE_DEPTH:.1f} mm2 cut "
          f"{100*_ring_cut:.0f}%, {OUTLINE_DEPTH:.2f} deep, on {100*_ring_solid:.0f}% solid baffle "
          f"(floor {100*_ring_floor:.0f}% = GRILLE_INSET/LIP_WIDTH); control over the open field "
          f"{100*_ring_ctl:.0f}%, REJECTED")
    print(f"             AT A GLANCE, and these are what the ruler is for: driver "
          f"{DRIVER_H:.2f} x {DRIVER_W:.2f} in a clear span of {RIM_X1-RIM_X0:.2f} x "
          f"{RIM_Y1-RIM_Y0:.2f} -> margins -X {DRV_CX-DRIVER_H/2-RIM_X0:.2f} "
          f"+X {RIM_X1-(DRV_CX+DRIVER_H/2):.2f} -Y {DRV_CY-DRIVER_W/2-RIM_Y0:.2f} "
          f"+Y {RIM_Y1-(DRV_CY+DRIVER_W/2):.2f}")
    print(f"             ⚠️ THE ONE TOLERANCE THIS MARK CANNOT SHOW IS DEPTH: a projection has "
          f"no Z. Driver {DRIVER_T:.2f} deep in a {BACK_Z-CAV_Z0:.2f} chamber leaves "
          f"{BACK_Z-CAV_Z0-DRIVER_T:.2f}mm over the magnet -- read that off check 6, not off "
          f"this line.")
    print(f"             the midframe's groove is driver+2x{DRIVER_CLR:.2f} "
          f"({DRIVER_H+2*DRIVER_CLR:.2f} x {DRIVER_W+2*DRIVER_CLR:.2f}, a LOCATING fit); this "
          f"ring is nominal ({DRIVER_H:.2f} x {DRIVER_W:.2f}, a RULER). Concentric, "
          f"{DRIVER_CLR:.2f} apart per side, and deliberately NOT the same number.")

    # ---- 7d. THE SIDE LABELS, AND THE DEBOSS DEPTH LEDGER (JP, r11) ----
    import strokefont as _SFm
    _lbl_rows = []
    for _nm, _face, _cy in SIDE_LBL_SITES:
        _iw, _ih = _SFm.ink_size(_nm, SIDE_LBL_H, SIDE_LBL_W, SIDE_LBL_GAP)
        _cz = (SIDE_LBL_Z0 + SIDE_LBL_Z1) / 2
        _x0 = OX0 if _face == "-X" else OX1 - SIDE_LBL_DEPTH
        _pr = bx(_x0 - 0.02, _x0 + SIDE_LBL_DEPTH + 0.02, _cy - _iw/2 - 0.3, _cy + _iw/2 + 0.3,
                 _cz - _ih/2 - 0.3, _cz + _ih/2 + 0.3)
        _cut = (_pr - mf).volume / SIDE_LBL_DEPTH
        assert _cut >= 0.40 * _iw * _ih, (
            f"side label {_nm!r} removed only {_cut:.2f} mm2 inside a {_iw*_ih:.2f} mm2 ink box "
            f"-- it is off its face, or the flank is not solid where it landed")
        # the wall it must NOT eat: MIN_SOLID immediately behind the groove floor
        _beh = (bx(_x0 + SIDE_LBL_DEPTH, _x0 + SIDE_LBL_DEPTH + MIN_SOLID,
                   _cy - _iw/2, _cy + _iw/2, _cz - _ih/2, _cz + _ih/2) if _face == "-X"
                else bx(_x0 - MIN_SOLID, _x0, _cy - _iw/2, _cy + _iw/2, _cz - _ih/2, _cz + _ih/2))
        _solid = 1.0 - (_beh - mf).volume / _beh.volume
        assert _solid > 0.999, (
            f"side label {_nm!r} leaves only {100*_solid:.1f}% of its {MIN_SOLID:.2f}mm backing "
            f"wall -- a {SIDE_LBL_DEPTH:.2f} groove in a {SIDE_WALL_T:.2f} flank must leave "
            f"{SIDE_WALL_T-SIDE_LBL_DEPTH:.2f}, so something else is cut into the same wall")
        _lbl_rows.append((_nm, _face, _cy, _iw, _cut, _solid))
    # CONTROL, and it is the label-into-air defect: the SAME label, dropped into the cable
    # channel band below PCB_BOT, is cut into a flank that is OPEN there -- an invisible label
    # on a part that has already shipped one. If that reads fully backed, this lens is blind.
    _cnm, _cface, _ccy = SIDE_LBL_SITES[0]
    _ciw, _cih = _SFm.ink_size(_cnm, SIDE_LBL_H, SIDE_LBL_W, SIDE_LBL_GAP)
    _ccz = (E.CAV_FLOOR + E.PCB_BOT) / 2
    _cx0 = OX0 if _cface == "-X" else OX1 - SIDE_LBL_DEPTH
    _cbeh = (bx(_cx0 + SIDE_LBL_DEPTH, _cx0 + SIDE_LBL_DEPTH + MIN_SOLID,
                _ccy - _ciw/2, _ccy + _ciw/2, _ccz - _cih/2, _ccz + _cih/2) if _cface == "-X"
             else bx(_cx0 - MIN_SOLID, _cx0, _ccy - _ciw/2, _ccy + _ciw/2,
                     _ccz - _cih/2, _ccz + _cih/2))
    _cfrac = 1.0 - (_cbeh - mf).volume / _cbeh.volume
    assert _cfrac < 0.999, (
        f"control failed: {_cnm!r} placed in the CABLE CHANNEL band reads {100*_cfrac:.1f}% "
        f"backed, but the flank is cut through there -- the backing lens cannot see a label "
        f"debossed into an opening")
    print(f"  [sidelbl] {len(_lbl_rows)} labels on the flanks, h {SIDE_LBL_H:.2f} / stroke "
          f"{SIDE_LBL_W:.2f} / depth {SIDE_LBL_DEPTH:.2f}, band z {SIDE_LBL_Z0:.2f}.."
          f"{SIDE_LBL_Z1:.2f} ({SIDE_LBL_BAND:.2f} tall)")
    for _nm, _face, _cy, _iw, _cut, _solid in _lbl_rows:
        print(f"             {_nm:5s} {_face} centred y {_cy:6.2f} on its own channel, ink "
              f"{_iw:5.2f} long, cut {_cut:6.2f} mm2, backing wall {100*_solid:.1f}% solid")
    print(f"             control (same label in the cable-channel band, where the flank is OPEN) "
          f"reads {100*_cfrac:.0f}% backed and is REJECTED")
    print(f"             SET DERIVED, NOT TYPED: served connectors minus SIDE_BLOCK's "
          f"{sorted(E.SIDE_BLOCK['mobile'])} plus the SD slit == JP's four. BAT and SPK have NO "
          f"OPENING on this variant, so they get NO LABEL -- the mic-label rule, generalised.")
    print(f"             ⚠️ SD IS NOT BUILT AND THAT IS THE ARITHMETIC, NOT AN OVERSIGHT: its S "
          f"needs ink {_SD_H_MIN + SIDE_LBL_W:.2f} tall at a {SIDE_LBL_W:.2f} stroke against a "
          f"{SIDE_LBL_BAND:.2f} band -> SHORT BY {SIDE_LBL_SD_SHORTFALL:.2f}mm. The font is "
          f"normalised and the stroke is not, so counters shrink and the groove does not.")
    print(f"             Buying it needs a sub-two-extrusion groove on a vertical wall (unproven, "
          f"and an invisible label is this file's own shipped defect) or a taller band, which is "
          f"bounded by a THROUGH-CUT channel below and the bezel SEAM above. NEEDS JP.")

    # ---- THE DEBOSS DEPTH LEDGER.  "as deep as we can", with what stops each one. ----
    # JP: "all debosses should be even deeper as deep as we can." Every depth in this file is now
    # derived, so this table is the audit: which BOUND is doing the work for each feature. Two
    # bounds compete -- the wall behind it, and the groove's own aspect (a groove deeper than it
    # is wide prints ragged and fills with dirt). Where ASPECT binds, more wall would not help.
    _ledger = (
        ("polarity '-'", "cover mating face (Z)", MARK_DEPTH, LH,
         BACK_Z - COVER_Z0, E.LABEL_W, "aspect"),
        ("polarity '+'", "bay +Y end wall (Y)", MARK_DEPTH_WALL, _EXTRUSION,
         MOB_OY1 - CELL_TIP_Y, E.LABEL_W, "aspect"),
        ("driver outline", "cover chamber floor (Z)", OUTLINE_DEPTH, LH,
         CAV_Z0 - COVER_Z0, LIP_WIDTH, "wall"),
        ("side labels", "midframe flank (X)", SIDE_LBL_DEPTH, _EXTRUSION,
         SIDE_WALL_T, SIDE_LBL_W, "aspect"),
        # >>> THE ONE FEATURE ALLOWED TO SIT EXACTLY ON MIN_SOLID, AND IT IS A DIFFERENT CASE. <<<
        # Behind the blind field is not incidental structure -- it is the MEMBRANE, a named
        # feature with its own check ([topmesh] measures it at 100% and 1.60mm every build). The
        # driver outline's 1.60 was leftover baffle that nothing was watching; this 1.60 is the
        # design's own intended thickness. So this row passes on_floor_ok, explicitly, with the
        # reason -- rather than arriving there because a float compared the way it happened to.
        ("blind top mesh", "cover +Y end face (Y)", TOPMESH_D, LH,
         MOB_OY1 - BAY_Y1, MESH_AF, "wall (membrane, on_floor_ok)"),
    )
    print(f"  [deboss]  every depth DERIVED (JP r11: as deep as we can). quantum = LAYER_H "
          f"{LH:.2f} on horizontal faces, EXTRUSION {_EXTRUSION:.2f} on vertical walls -- "
          f"ember_case.py:291, layer height does not govern a vertical wall.")
    for _nm, _cls, _d, _q, _wall, _stroke, _binds in _ledger:
        _wall_cap = _max_deboss(_wall, quantum=_q, on_floor_ok="membrane" in _binds)
        _asp_cap = int(_ASPECT_MAX * _stroke / _q) * _q
        assert _d <= _wall_cap + 1e-9, (
            f"{_nm} is {_d:.2f} deep but its {_wall:.2f} wall only allows {_wall_cap:.2f} "
            f"while keeping {MIN_SOLID:.2f}")
        print(f"             {_nm:15s} {_cls:24s} {_d:.2f} deep  "
              f"(wall {_wall:5.2f} allows {_wall_cap:.2f}, aspect allows {_asp_cap:.2f}) "
              f"-> {_binds.upper()} binds")
    print(f"             ⚠️ ONE FEATURE GOT SHALLOWER AND IT IS FLAGGED, NOT HIDDEN: the driver "
          f"outline goes {OUTLINE_DEPTH:.2f} (was 0.60). At 0.60 it left EXACTLY MIN_SOLID "
          f"{MIN_SOLID:.2f} of baffle -- on the constraint with no slack, which LABEL_DEBOSS's "
          f"own block rejects. {OUTLINE_DEPTH:.2f} leaves {CAV_Z0-COVER_Z0-OUTLINE_DEPTH:.2f}, "
          f"and it is the depth every desk label already prints at. The ring reads on its "
          f"{LIP_WIDTH:.2f} WIDTH, not on depth.")
    assert MARK_DEPTH > 3 * LH, (
        f"the polarity marks are {MARK_DEPTH:.2f}, no deeper than the 0.60 they were before "
        f"r11 -- JP asked for deeper everywhere, so a floor must have tightened. Say so, do "
        f"not regress quietly")

    # ---- 8. GRILLE THROAT, RASTERED.  Neither figure inherited from a comment. ----

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

    # ---- 8a. THE MACHINE'S OWN FLOOR.  THE LENS EVERY OTHER CHECK WAS MISSING. ----
    
    # >>> THIS CHECK EXISTS BECAUSE ROUND 2 PASSED EVERY OTHER ONE AND WAS STILL UNPRINTABLE. <<<
    
    # The skew rails were self-consistent, unbridged, >= 50 degrees everywhere, captured with
    # margin, and made of 0.60mm SOLID ribs on a machine documented to have collapsed 0.90mm
    # solid webs (#47). Not one assert here knew that, because they all measure the geometry
    # against ITSELF. This one measures it against THE PRINTER, and its control is #47's own
    # failure -- the only honest calibration point this project has.
    
    # ⚠️ THE TWO CALIBRATION NUMBERS ARE NOT INTERCHANGEABLE, and mixing them is what killed
    # round 2: SLOT_W's 0.60 is a proven VOID and #47's 0.90 is a failed SOLID. A void that
    # prints open says nothing about a rib that has to stand up.
    
    # ⚠️⚠️ AND THE CHECK'S FIRST RUN FAILED ON ITS AUTHOR'S OWN GEOMETRY, WHICH IS WHY THE
    # SCOPE IS NOW WRITTEN DOWN INSTEAD OF ASSUMED. It rejected DT_FLARE_H -- a vertical RISE,
    # not a section; through that whole rise the tongue ran 1.60 -> 3.20 and was never thinner
    # than the floor. Two HEIGHTS had been put in a list that may only hold SECTIONS.
    # ember_case.py records the identical trap from the other side: "over-strict is not safe --
    # it is just wrong in the other direction, AND IT GETS SWITCHED OFF." So both halves of the
    # scope are stated, and the exempt half is PRINTED rather than silently omitted:
    
    #   IN  -- free-standing sections: a rib, a boss annulus, a wall standing in a void, and
    #          the material left between two adjacent cut features.
    #   OUT -- heights, depths and rises (they are not sections at all), and MEMBRANES: a thin
    #          face backed by a full wall on every edge is not a rib.
    _ev_gap = min(abs(_x - SCREW_LANE_X) for _x in EV_XS) - MESH_R - PILOT_D/2
    for _v, _what in (((SCREW_BOSS_D - CBORE_D)/2, "screw boss annulus under the head"),
                      (SCREW_BOSS_D/2 - PILOT_D/2, "midframe boss wall around the pilot"),
                      (COV_WALL,    "the cover's outer wall (and the baffle)"),
                      (RIM_WALL,    "the seal rim's free-standing walls"),
                      (DIVIDER_W,   "the shared cell/cavity divider"),
                      (PROT_RIB_W,  "protection-strip locating rib"),
                      (_ev_gap,     "block between the end vent and the top screw's pilot"),
                      (EV_EDGE,     "block outboard of the end-vent row"),
                      (SEAM_Z - (EV_CZ + MESH_AF/2), "shell under the bezel seam over the vent"),
                      (E.PY1 - (TOP_SCREW_XY[1] - SCREW_BOSS_D/2)
                       + 0*SCREW_BOSS_D, "top boss reach into the pocket's +Y wall")):
        assert _v >= MIN_SOLID - 1e-9, (
            f"{_what} is {_v:.2f}mm against a {MIN_SOLID:.2f} floor ({MIN_SOLID/0.40:.0f} "
            f"extrusion widths). #47 collapsed 0.90mm SOLID webs on this machine; anything "
            f"under the floor needs a cited reason it beats that evidence, and 'SLOT_W prints "
            f"open' is NOT one -- SLOT_W is a void")
    assert 0.90 < MIN_SOLID, (
        "control failed: #47's 0.90mm web -- a MEASURED collapse on this machine -- passes the "
        "minimum-solid floor, so the floor is not defending against the thing it names")
    # >>> THE EXEMPTIONS, LOUD.  A carve-out nobody can see is a carve-out nobody re-examines. <<<
    _exempt = ((MESH_WEB_BORE, "the top fields' 1.25 web on HORIZONTAL bores -- clear of #47's "
                               "measured 0.90 collapse but still UNVALIDATED at this cell size; "
                               "JP: \"we have proven two that collapse and none that survives\""),
               (MESH_WEB_BLIND, "the blind deboss's 0.80 web -- the BACK GRILL's own, and that "
                                "field PRINTED on JP's r1. Proven, but only for VERTICAL prisms "
                                "in a bed face; it is exempt here because a 0.60 surface relief "
                                "has no rib to lose, not because 0.80 is safe in a bore."),
               (LAT_WEB, "the LED wire pass and the internal labyrinth vent still use the "
                         "4.75/1.25 lattice: both are functional apertures sized to pass a "
                         "3-wire pigtail and to collimate, not decorative fields."),
               (GLOW_MEMBRANE, "glow window membrane -- a face backed by wall on all four "
                               "edges, 2 extrusions by design, not a standing rib"),
               (VENT_SKIN, "vent labyrinth skin -- same class as the membrane"),
               (CONTACT_DETENT, "contact detent bar -- it is MEANT to deform past the plate"))
    assert any(_v < MIN_SOLID for _v, _ in _exempt), (
        "control failed: nothing in the exempt list is actually under the floor, so the "
        "exemption is decorative and the scope line above is not being tested by anything")
    print(f"  [minfeat] floor {MIN_SOLID:.2f} ({MIN_SOLID/0.40:.0f} extrusions); "
          f"{sum(1 for _ in range(10))} sections checked, worst is the "
          f"{MIN_SOLID:.2f} annulus/rib class. Control: #47's failed 0.90 web is REJECTED")
    for _v, _why in _exempt:
        print(f"  [exempt]  {_v:.2f}mm -- {_why}")

    # ---- 8b. NOTHING DROOPS.  The one flat roof in the new work is named and bounded. ----
    
    # Three layers, weakest first, and the last is measured on the mesh:
    #   (i)   the as-printed frame IS the model frame -- both parts export by a pure Z lift.
    #   (ii)  the analytic face angles, from the constants.
    #   (iii) THE ARTIFACT: sweep thin slabs up through the finished solid and watch how much
    #         MATERIAL each layer gains over the one below. 45 degrees gains LH per layer; a
    #         flat roof gains its whole width in one.
    assert PRINT_LIFT["ember-mobile-midframe"] == -BACK_Z and \
           PRINT_LIFT["ember-mobile-back"] == -COVER_Z0, (
        "PRINT_LIFT is no longer a pure Z translation of the model frame, so 'vertical in the "
        "model' no longer means 'vertical on the bed' and every angle below is meaningless")
    # The end-vent cell's shoulder: from its widest point (x = +/-MESH_R at z = EV_CZ) up to the
    # crown corner (+/-MESH_R/2, EV_CZ + MESH_AF/2).
    _a_shoulder = math.degrees(math.atan2(MESH_AF/2, MESH_R/2))
    assert _a_shoulder >= 50.0, (
        f"the end-vent cell's shoulder runs at {_a_shoulder:.1f} deg from horizontal against a "
        f"50 bar (45 is the print limit; this family holds 50 so tessellation cannot eat the "
        f"margin)")
    # >>> AND THE CONTROL IS A PART THIS PROJECT ACTUALLY PRINTED AND WATCHED FAIL. <<<
    # Turn the same cell vertex-up -- which is exactly the stand's grille, `rotation=30` through
    # `Rot(-90,0,0)` -- and its roof runs at 30 degrees. That is issue #28, the droop that
    # needed GRILLE_FLARE. If this bar ever stops rejecting it, the bar has stopped meaning
    # anything.
    _a_28 = math.degrees(math.atan2(MESH_R/2, MESH_AF/2))
    assert _a_28 < 50.0, (
        f"control failed: the vertex-up orientation -- issue #28's own drooping grille -- reads "
        f"{_a_28:.1f} deg and CLEARS the 50-degree bar, so this test cannot reject the "
        f"orientation the project has already watched fail")

    # ⚠️ THE METRIC IS MATERIAL GROWTH, NOT VOID CHANGE, and it is SPLIT AT THE CELL'S
    # CENTRELINE so each half has exactly ONE moving edge -- summing across a symmetric profile
    # lets the two edges cancel and hide a shallow face. Same lesson as the vent-throat and
    # polarity probes.
    def _mat_widths(part, y, z0, z1, xa, xb):
        out, _t, _dy = [], LH * 0.5, 0.40
        _z = z0 + LH / 2
        while _z <= z1:
            _pr = bx(xa, xb, y - _dy/2, y + _dy/2, _z - _t/2, _z + _t/2)
            out.append((part & _pr).volume / (_t * _dy))
            _z += LH
        return out

    def _worst_growth(ws):
        return max((b - a for a, b in zip(ws, ws[1:])), default=0.0)

    _step_max = LH * 1.15              # ONE edge at the 45 deg limit, plus 15% for the mesh
    _cx0 = EV_XS[0]
    _y_in = MOB_OY1 - 2.00             # a plane well inside the bore, not at either mouth
    _worst, _where = 0.0, "nothing"
    # sweep the SHOULDER only: from the cell's widest point up to one layer below the crown.
    for _xa, _xb in ((_cx0 - MESH_R - 0.60, _cx0), (_cx0, _cx0 + MESH_R + 0.60)):
        _st = _worst_growth(_mat_widths(mf, _y_in, EV_CZ, EV_CZ + MESH_AF/2 - LH, _xa, _xb))
        if _st > _worst:
            _worst, _where = _st, f"the end vent's shoulder at x {_xa:.2f}..{_xb:.2f}"
    assert _worst <= _step_max, (
        f"material grows {_worst:.2f}mm in one {LH} layer at {_where}, over the {_step_max:.2f} "
        f"a single 45-degree face can produce. Something is BRIDGED that should not be")
    # >>> THE ONE FLAT ROOF, DECLARED RATHER THAN DISCOVERED. <<<
    # The crown is a genuine bridge of one side length. It is allowed, and the bound is not a
    # taste: this same midframe already bridges CBORE_D flat, four times, in its own bed face,
    # and those counterbores print. Anything the crown could grow to beyond that would be a new
    # class for this part, not a bigger instance of an old one.
    assert EV_CROWN <= CBORE_D, (
        f"the end-vent crown bridges {EV_CROWN:.2f}mm flat, wider than the {CBORE_D}mm the four "
        f"counterbores in this part's bed face already bridge -- that is a new class of roof "
        f"and it needs its own evidence, not this comment")
    # ---- AND THE EASED BATTERY EDGE, WHICH IS THE ONLY REASON IT IS AN EASE AND NOT A ROUND ----
    #
    # JP asked for the -X back edge to feel rounded in the hand (§5i). A true round is the one
    # thing this part's print orientation forbids: outer-face-down means COVER_Z0 IS the bed,
    # and a round meets it tangent to horizontal. The profile is therefore an arc TRUNCATED at
    # a 45-degree tangent with a 45 run-out, and the check is that every facet of it earns that
    # claim -- measured on the profile the geometry actually uses, not on the intent.
    _ep = _ease_profile()[2:-1]                 # drop the two closure points, which are in air
    _worst_ease = min(math.degrees(math.atan2(abs(_b[1] - _a[1]), abs(_b[0] - _a[0])))
                      for _a, _b in zip(_ep, _ep[1:]) if abs(_b[0] - _a[0]) > 1e-9)
    assert _worst_ease >= 45.0 - 1e-6, (
        f"the eased battery edge has a facet at {_worst_ease:.1f} deg from horizontal. On a part "
        f"that prints outer-face-down that is an OUTWARD lean off the bed, not an overhang you "
        f"can support -- truncate the arc higher (EASE_TAN45 is where it stops being printable)")
    # CONTROL: the untruncated round -- what JP literally asked for -- must FAIL this bar, or
    # the truncation is decoration and the next person deletes it.
    _full = math.degrees(math.atan2(EASE_R - math.sqrt(EASE_R**2 - (EASE_R/EASE_FACETS)**2),
                                    EASE_R / EASE_FACETS))
    assert _full < 45.0, (
        f"control failed: the first facet of an UNtruncated round reads {_full:.1f} deg and "
        f"clears the 45 bar, so this test cannot reject the shape it exists to reject")
    # ...and it must stay out of the vent labyrinth's Z band, which is the constraint that made
    # this cheap: they do not share a wall, they share a part.
    assert COVER_Z0 + EASE_RISE < VENT_Z0 - 1.00, (
        f"the ease now reaches z {COVER_Z0+EASE_RISE:.2f} and the vent labyrinth starts at "
        f"{VENT_Z0:.2f} -- they share the -X wall and the labyrinth has placement priority, so "
        f"its folds have to be re-derived on the curve before this can grow further")
    print(f"  [ease]    battery edge R {EASE_R:.2f}: {EASE_BED:.2f} across the bed face, "
          f"{EASE_RISE:.2f} up the side, {EASE_WALL:.2f}mm of wall at the diagonal (floor "
          f"{MIN_SOLID:.2f}, ceiling R {(COV_WALL*math.sqrt(2)-MIN_SOLID)/(math.sqrt(2)-1):.2f})")
    print(f"             shallowest facet {_worst_ease:.1f} deg; control (an untruncated round, "
          f"which is what a literal wrap would be) reads {_full:.1f} deg and is REJECTED")
    print(f"             dies {VENT_Z0-(COVER_Z0+EASE_RISE):.2f} below the vent labyrinth and "
          f"{BACK_Z-(COVER_Z0+EASE_RISE):.2f} below the mating plane -- midframe UNTOUCHED")

    _blk = bx(OX0, OX0 + 12.0, 0.0, 12.0, BACK_Z, BACK_Z + 6.0)
    _blk -= bx(OX0 + 1.0, OX0 + 9.0, 2.0, 10.0, BACK_Z, BACK_Z + 1.40)      # the deleted hook
    _hw = _mat_widths(_blk, 6.0, BACK_Z, BACK_Z + 2.20, OX0, OX0 + 6.0)
    assert _worst_growth(_hw) > _step_max, (
        f"control failed: the deleted hook pocket -- an 8.00 x 1.40 flat-roofed void in the bed "
        f"face -- grows only {_worst_growth(_hw):.2f}mm per layer, inside the {_step_max:.2f} "
        f"budget. The sweep cannot detect a bridge")
    print(f"  [print]   as-printed frame = model frame (pure Z lift, both parts). End-vent "
          f"shoulder {_a_shoulder:.1f} deg from horizontal; control (#28's vertex-up grille) "
          f"{_a_28:.1f} deg, REJECTED")
    print(f"             shoulder material growth: worst {_worst:.3f}mm/{LH} layer, split at the "
          f"cell centreline (budget {_step_max:.2f})")
    print(f"             the one declared flat roof: {EV_CROWN:.2f}mm crown vs the {CBORE_D}mm "
          f"this part's own counterbores already bridge")
    print(f"             control: the deleted hook pocket grows {_worst_growth(_hw):.2f}mm in "
          f"one layer -- it fails the same sweep, which is why it is deleted")

    # ---- 8d. IT GOES TOGETHER STRAIGHT DOWN, OVER A DRIVER THAT IS ALREADY TAPED ON. ----
    
    # >>> THIS IS THE CHECK THAT KILLED THREE RETENTION DESIGNS, ONCE IT WAS ASKED PROPERLY. <<<
    
    # It began as a SLIDE sweep, because every scheme up to round 3 needed a slide. JP then
    # double-stick-taped the speaker to the printed midframe and said "the backpack can't
    # involve any sliding, it has to come straight down" -- and that sentence retired the whole
    # family of schemes, because the driver is now IN THE PATH and it is bonded. So the sweep
    # is inverted: the cover must be free through the entire -Z approach, and the assembly is
    # only legal if that number is a zero.
    
    # The driver is a PHANTOM -- it is in no STL -- so no part-vs-part boolean could ever have
    # seen it, exactly like the cell-vs-cradle interference at 13.1 mm3. Same for the cell and
    # the spring, which are loaded into the cover BEFORE it goes on and therefore ride the same
    # path.
    _drv = driver_phantom()
    assert (BACK_Z - TAPE_T - DRIVER_T) - CAV_Z0 >= 1.00, (
        f"with a {TAPE_T:.2f} bond line the driver hangs to z "
        f"{BACK_Z-TAPE_T-DRIVER_T:.2f}, leaving {(BACK_Z-TAPE_T-DRIVER_T)-CAV_Z0:.2f}mm over "
        f"the cavity floor at {CAV_Z0:.2f} -- the tape thickness has stopped being free")
    _path = [-_d for _d in (12.0, 8.0, 5.0, 3.0, 2.0, 1.0, 0.40, 0.0)]
    _fo_drv = max((Pos(0, 0, _dz) * cov & _drv).volume for _dz in _path)
    _fo_mf = max((Pos(0, 0, _dz) * cov & mf).volume for _dz in _path)
    assert _fo_drv < 0.5, (
        f"the cover passes {_fo_drv:.2f} mm3 through the TAPED driver somewhere on its way "
        f"straight down -- it will not go together, and the driver is bonded on first")
    assert _fo_mf < 0.5, (
        f"the cover passes {_fo_mf:.2f} mm3 through the midframe on its way down. With no "
        f"undercut anywhere in the joint this should be identically zero")
    _load = max(max((Pos(0, 0, _dz) * _ph & mf).volume for _dz in _path)
                for _ph in (cell_phantom(), leaf_phantom(LEAF_FREE)))
    assert _load < 0.5, (
        f"the cell or the spring passes {_load:.2f} mm3 through the midframe during the "
        f"descent -- the cover goes on with them already in it")
    # >>> CONTROL: THE SLIDE THAT IS NOW FORBIDDEN MUST STILL READ AS A COLLISION. <<<
    # Without this the 0.000 above is silence rather than evidence -- and it doubles as the
    # standing proof of WHY straight-down is not a preference. The rim's end walls clear the
    # driver by (RIM_INNER_Y - DRIVER_W)/2 in Y, so any Y travel past that shears the speaker.
    _gap_drv = (RIM_INNER_Y - DRIVER_W) / 2
    _fo_ctl = max((Pos(0, -_dy, 0.0) * cov & _drv).volume
                  for _dy in (0.8, 1.6, 2.4, 2.9, 3.6))
    assert _fo_ctl > 1.0, (
        f"control failed: sliding the seated cover in Y across the taped driver reads "
        f"{_fo_ctl:.2f} mm3, i.e. clear. The sweep cannot detect the failure that retired every "
        f"slide-based scheme this project tried")
    print(f"  [descent] straight down, {len(_path)} poses from {-_path[0]:.1f}mm out to seated: "
          f"vs the taped driver {_fo_drv:.3f} mm3, vs the midframe {_fo_mf:.3f} mm3, contents "
          f"(cell + spring) {_load:.3f} mm3")
    print(f"             driver taped at z {BACK_Z-TAPE_T:.2f} on a {TAPE_T:.2f} bond line "
          f"(⚠️ ALLOWANCE, not calipered); {(BACK_Z-TAPE_T-DRIVER_T)-CAV_Z0:.2f}mm over the "
          f"cavity floor")
    print(f"             control: a Y slide drives {_fo_ctl:.1f} mm3 of rim wall THROUGH the "
          f"driver ({_gap_drv:.2f}mm of clearance is all there is). NO SLIDE IS AVAILABLE.")
    # ---- AND THE TAPE PAD, IN COORDINATES, BECAUSE JP TAPED HIS BY EYE ----
    print(f"             >>> TAPE PAD for the physical build: x "
          f"{DRV_CX-(DRIVER_H+2*DRIVER_CLR)/2:.2f}..{DRV_CX+(DRIVER_H+2*DRIVER_CLR)/2:.2f}  y "
          f"{DRV_CY-(DRIVER_W+2*DRIVER_CLR)/2:.2f}..{DRV_CY+(DRIVER_W+2*DRIVER_CLR)/2:.2f}  "
          f"centre ({DRV_CX:.2f}, {DRV_CY:.2f}); the driver clears the rim by "
          f"{(RIM_X1-RIM_X0-DRIVER_H)/2:.2f} in X and {_gap_drv:.2f} in Y <<<")

    # ---- 8e. THE SCREWS.  Two, on the centreline, and a head may not stand proud. ----
    
    # The old form of this check asked whether the screw blocked a slide. There is no slide, so
    # the question changes to the two that are left: can the head be WRONG, and do the two
    # screws actually fix the cover in its plane.
    
    # ⚠️ A PROUD HEAD IS THE FAILURE THAT LOOKS LIKE SUCCESS FROM THE OTHER SIDE. CBORE_DEPTH
    # is exactly SCREW_HEAD_H so the head lands flush. Shallower and it stands proud -- on a
    # case that DOCKS IN A SLOT, a proud head is discovered at the stand, not at the bench.
    # Deeper and the tip drives further into the pilot, which is ember_case's own recorded
    # failure: M3x14 bottoms out at the pilot's 6.20 end and "the failure still looks like
    # success" -- you feel resistance, you stop, and the cover was never clamped.
    assert abs(CBORE_DEPTH - SCREW_HEAD_H) < 1e-9, (
        f"CBORE_DEPTH {CBORE_DEPTH} is not SCREW_HEAD_H {SCREW_HEAD_H}. Shallower leaves the "
        f"head proud of a face that has to seat in the stand's slot; deeper drives the tip "
        f"toward the end of the pilot, where clamping stops and resistance does not")
    # ...measured on the artifact, not on the constants: the counterbore's real floor depth.
    for _sxy, _who in ((SCREW_XY, "chin"), (TOP_SCREW_XY, "top ")):
        _pr = bx(_sxy[0] - 0.20, _sxy[0] + 0.20, _sxy[1] - 0.20, _sxy[1] + 0.20,
                 COVER_Z0 - 0.001, COVER_Z0 + CBORE_DEPTH + 4.0)
        _open = (_pr - cov).volume / (0.40 * 0.40)
        assert _open >= CBORE_DEPTH - 1e-6, (
            f"the {_who} counterbore measures {_open:.3f}mm deep on the finished solid against "
            f"a designed {CBORE_DEPTH} -- the head would stand {CBORE_DEPTH-_open:.3f} proud")
    # >>> AND THE PAIR FIXES THE COVER IN ITS PLANE.  Two points do; one does not. <<<
    # They are SCREW baseline apart on one lane, which is the longest baseline this part has:
    # the cell lane forbids any -X fastener at any y (round 4b), so the centreline is as far
    # from the +X edge as anything can get without giving the -X edge away.
    _seated = max((cyl(_s[0], _s[1], COVER_Z0 - 1, BACK_Z + 1, 3.00) & cov).volume
                  for _s in SCREWS)
    assert _seated < 0.02, (
        f"an M3 shank fouls the seated cover by {_seated:.3f} mm3 -- a clearance bore does not "
        f"line up with its pilot even when the cover is home")
    _shift = max((cyl(_s[0], _s[1], COVER_Z0 - 1, BACK_Z + 1, 3.00)
                  & (Pos(0.60, 0, 0) * cov)).volume for _s in SCREWS)
    assert _shift > 0.5, (
        f"control failed: a cover displaced 0.60mm in X still passes both shanks "
        f"({_shift:.2f} mm3 blocked) -- the screws are not locating it, they are only clamping "
        f"it, and nothing else on this part locates anything")
    _base = TOP_SCREW_XY[1] - SCREW_XY[1]
    print(f"  [screws]  2 x M3 x {MOB_SCREW_LEN:.0f} on x = {SCREW_LANE_X:.2f} (the case's own "
          f"centreline): chin y {SCREW_XY[1]:.2f}, top y {TOP_SCREW_XY[1]:.2f}, baseline "
          f"{_base:.2f}mm")
    print(f"             head FLUSH: CBORE_DEPTH {CBORE_DEPTH:.2f} = SCREW_HEAD_H "
          f"{SCREW_HEAD_H:.2f}, measured on the solid at both sites")
    print(f"             control: displaced 0.60 in X the pair blocks {_shift:.2f} mm3 of shank "
          f"-- they LOCATE, not just clamp")


    # ---- 8g. THE BAY HOLDS ITS METALWORK.  JP's question, answered in geometry. ----
    
    # >>> "we need features to hold the spring, and to hold the metal strips." <<<
    
    # The acceptance behaviour is JP's: cell OUT, case held OPEN-SIDE-DOWN, the metal stays put.
    # That is a CAPTIVITY question, and captivity is not an area or a depth -- it is "does the
    # part collide with the enclosure when you try to take it out the way gravity would". So it
    # is asked that way, with the escape direction and a control that must NOT collide.
    
    # There is no coil to ask about any more; the question moved to the LEAF, and it is the
    # same question because the leaf is retained the same way the plate is (§5g). Check 8h
    # measures the kerf and the detent at the "+" end; this measures the fold at the "-" end.
    _leaf_free = leaf_phantom(LEAF_FREE)
    _leaf_fit = (cov & _leaf_free).volume
    assert _leaf_fit < 0.5, (
        f"the leaf at its {LEAF_FREE} free height fouls the bay by {_leaf_fit:.2f} mm3 -- it "
        f"does not go in, never mind stay in")
    # THE CAPTIVITY TEST. Open-side-down is +Z out of the bay, so lift the leaf that way and
    # the detent bar over its root must be in the road. 2.00 is past any rattle and short of
    # clearing the kerf.
    _leaf_up = (cov & leaf_phantom(LEAF_FREE, dz=2.00)).volume
    # ⚠️ THE THRESHOLD IS THE BAR'S OWN VOLUME, NOT A ROUND NUMBER. The coil version asserted
    # "> 1.0 mm3" because a spring lifted into a d9.00 tunnel hits a lot of plastic. A detent
    # bar is CONTACT_DETENT x CONTACT_DET_H x LEAF_W = 0.60 mm3 in total, so 1.0 was a bar that
    # could never pass however well it worked -- a threshold with no relationship to the
    # feature is a threshold nobody can defend in either direction. Full engagement is the bar
    # entirely inside the lifted root; 60% of it is a real bite with room for mesh noise.
    _bar_vol = CONTACT_DETENT * CONTACT_DET_H * LEAF_W
    assert _leaf_up > 0.60 * _bar_vol, (
        f"lifting the leaf 2.00mm toward the bay's open side engages only {_leaf_up:.2f} mm3 of "
        f"the detent bar's {_bar_vol:.2f} mm3. Its root is not captured and it will fall out "
        f"when the cell comes out -- which is JP's stated acceptance behaviour, failed")
    # CONTROL: the same lift applied to a fold sitting OUT IN THE BAY, away from the kerf, must
    # be free. Without this, "captive" and "the probe collides with everything" read alike.
    _leaf_out = (cov & bx(CELL_AXIS_X - LEAF_W/2, CELL_AXIS_X + LEAF_W/2,
                          LEAF_SEAT_Y + 12.0, LEAF_SEAT_Y + 12.0 + LEAF_FREE,
                          CONTACT_Z0 + 2.00, CONTACT_Z1 + 2.00)).volume
    assert _leaf_out < 0.5, (
        f"control failed: a fold lifted 2.00mm well clear of the kerf still reads "
        f"{_leaf_out:.2f} mm3 of interference, so the captivity probe cannot tell the kerf from "
        f"the open bay")
    # THE END WALL IS THE OVER-TRAVEL STOP, AND IT IS A WHOLE WALL RATHER THAN AN ANNULAR LIP.
    # The coil needed the tunnel's mouth to stop it short of coil-bound; the fold cannot bind,
    # so what this asserts instead is that the wall behind it is real material and not the
    # cover's own outside.
    _wall = bx(CELL_AXIS_X - LEAF_W/2, CELL_AXIS_X + LEAF_W/2,
               COVER_Y0 + 0.20, LEAF_SEAT_Y - LEAF_KERF - 0.02, CAV_Z0 + 0.20, BACK_Z - 0.20)
    _wfrac3 = (cov & _wall).volume / _wall.volume
    assert _wfrac3 > 0.98, (
        f"the wall behind the leaf's kerf is only {100*_wfrac3:.1f}% material -- the fold has "
        f"nothing to bear against and the cell would push it out of the case")
    print(f"  [leaf]    folded nickel, root in a {LEAF_KERF:.2f} kerf at y {LEAF_SEAT_Y:.2f}, "
          f"free height {LEAF_FREE:.2f} (⚠️ JP-TUNABLE), closed {LEAF_SOLID:.2f}, travel "
          f"{LEAF_FREE-LEAF_SOLID:.2f}")
    print(f"             CAPTIVE: lifted 2.00 toward the open side it engages {_leaf_up:.2f} of "
          f"the detent bar's {_bar_vol:.2f} mm3; the same lift out in the open bay is free "
          f"({_leaf_out:.2f} mm3)")
    print(f"             backed by {100*_wfrac3:.1f}% solid end wall -- that wall IS the "
          f"over-travel stop, and a fold cannot coil-bind the way the deleted spring could")
    print(f"             ⚠️ NO PLA FLEXURE ANYWHERE IN THIS MECHANISM: PLA creeps under the "
          f"constant load a battery contact carries. Metal does the force, PLA the geometry.")

    # ---- 8h. THE "+" CONTACT KERF.  Bounded BOTH ways, because one bound is meaningless. ----
    
    # A slot too narrow does not take the strip; a slot too wide does not hold it. The same
    # probe answers both, measured on the finished solid at the plate's own mid-height.
    _kz = (CONTACT_Z0 + CONTACT_Z1) / 2
    _kpr = bx(CELL_AXIS_X - 0.20, CELL_AXIS_X + 0.20, CELL_TIP_Y, CELL_TIP_Y + 1.50,
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
    _dpr = bx(CELL_AXIS_X - 0.20, CELL_AXIS_X + 0.20, CELL_TIP_Y, CELL_TIP_Y + 1.50,
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
              CELL_TIP_Y + 0.05, CELL_TIP_Y + CONTACT_KERF - 0.05,
              BACK_Z - 3.0, BACK_Z - 2.6)
    _topen = (_tpr - cov).volume / _tpr.volume
    assert _topen > 0.90, (
        f"the tab lane is only {100*(1-_topen):.0f}% open where it meets the divider's wire "
        f"groove -- the +ve tab has no route to the protection strip")
    print(f"  [contact] kerf {_kw:.3f} measured (CONTACT_T {CONTACT_T} JP-confirmed material + "
          f"CONTACT_PLAY {CONTACT_PLAY} derived here); detent leaves {_dw:.3f} < {CONTACT_T}")
    print(f"             plate seat z {CONTACT_Z0:.2f}..{CONTACT_Z1:.2f}, throat open to "
          f"{BACK_Z:.2f}, tab lane to the divider {100*_topen:.0f}% open")

    # ---- 8i. IT STILL DOCKS.  The cross-part property that had no check at all. ----
    
    # >>> JP: "does the mobile case still dock in the desk stand with the backpack on?" <<<
    
    # The answer is yes BY DESIGN and that is precisely the problem: it is true because the
    # cover stops at COVER_Y0 and the docking band is the UNCHANGED 17.40 slab below it, and
    # nothing anywhere asserted either half. It has survived three redesigns of the retention
    # on the strength of everyone remembering that the step at y=18.00 exists. That is not a
    # property, it is a habit -- and habits do not survive the fourth redesign.
    
    # Two questions, and they are different: (a) does the SLAB still fit the slot, and (b) does
    # the BACKPACK -- 39.00 of body that rises behind the slot, including the rim notch cut for
    # cap access -- clear the stand's rear geometry once the case is laid back TILT degrees.
    # (a) is the desk's check 2f asked of the mobile stack; (b) has never been asked by anyone.
    
    # E.dock_pose is the SHARED transform, deliberately: transcribing it here is the drift that
    # 2f's own comment warns about, one indirection further away.
    _stand = E.desk_stand()
    _sbb = _stand.bounding_box()

    def _dock_hit(_dz=0.0):
        _tot = 0.0
        for _p in (E.front_bezel(), mf, cov):
            for _sd in (Pos(0, 0, _dz) * E.dock_pose(_p)).solids():
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

    _dock_i = _dock_hit()
    # >>> IT DOCKS.  IT DID NOT WHEN THIS CHECK FIRST RAN, AND THAT IS WORTH KEEPING. <<<
    #
    # 8i was written the round before and had NEVER RUN: that gate died upstream at check 8a's
    # false positive, so everything below 8a was written, committed, described as "gated-sound"
    # in a handoff, and never executed. Its first execution failed by 121.784 mm3. An invariant
    # nobody has watched fire is a comment, and this file has now paid for that twice.
    #
    # WHAT IT FOUND, and the fix is in ember_case because the CASE could not give it: the
    # cover's chin end swept the stand's rear top corner. In cover coordinates y 18.00..20.06,
    # z -26.44..-17.37, full width -- MID-HEIGHT on the end face, not the bed-face corner where
    # a bevel is cheap. The cover's bottom wall is COV_WALL 2.20 with the leaf's 0.35 kerf
    # behind it, so it cannot yield 2.06; raising COVER_Y0 grows the case past its start. The
    # stand was cut for a slab that predates the backpack, so DOCK_RELIEF_Y/Z put a 13.00 x
    # 4.40 bevel on its rear top edge and the number went to zero.
    #
    # ⚠️ HARD ZERO, NOT A BOUND. It was carried as a bounded known defect for exactly one
    # commit, to land a gate; there is no legitimate nonzero value for it and a tolerance left
    # behind is how the next one arrives unnoticed.
    assert _dock_i < 0.01, (
        f"the docked MOBILE stack intersects the stand by {_dock_i:.3f} mm3 -- the backpack "
        f"fouls it. The slab band below y={COVER_Y0:.2f} is what seats in the slot; anything "
        f"added to the long walls under that line, any growth of the {FRONT_Z-COVER_Z0:.2f} "
        f"body behind it, or any shrinking of ember_case's DOCK_RELIEF_Y/Z, does this")
    # CONTROL, exactly as its desk sibling carries: 0.000 is what a blind detector says too.
    _dock_self = _dock_hit(-2.0)
    assert _dock_self > 1.0, (
        f"[self-test] the docked mobile stack sunk 2mm reads {_dock_self:.3f} mm3 -- the "
        f"detector is blind, so the 0.000 above is silence, not evidence")
    # ---- AND THE DOCKING BAND ITSELF: no retention feature may reach below y = COVER_Y0. ----
    # Stated per feature rather than trusted, because "the cover starts at 18.00" is the kind of
    # sentence that stays in a comment while a lip creeps under it.
    for _nm, _y in (("cover bottom edge", COVER_Y0),
                    ("chin counterbore", SCREW_XY[1] - CBORE_D/2),
                    ("chin boss pad", COVER_Y0),
                    ("leaf kerf", LEAF_SEAT_Y - LEAF_KERF),
                    ("'-' marking", _mark_face("-")[2] - _ink_half(MARK_PATHS_N)[1]),
                    ("strip pocket", PROT_Y1 - PROT_W - PROT_CLR)):
        assert _y >= COVER_Y0 - 1e-9, (
            f"{_nm} reaches y={_y:.2f}, below the cover's own start at {COVER_Y0:.2f} -- it is "
            f"in the DOCKING BAND, where the slab profile must stay exactly the 17.40 the "
            f"stand's slot was cut for")
    print(f"  [dock]    MOBILE STACK (bezel + midframe + cover) vs the stand: {_dock_i:.3f} "
          f"mm3 CLEAR; control sunk 2mm -> {_dock_self:.1f} mm3, detector WORKS")
    print(f"             >>> IT DOCKS WITH THE BACKPACK ON. It did not when this check first "
          f"ran (121.784 mm3, the cover's chin end through the stand's rear top corner); "
          f"ember_case's DOCK_RELIEF {E.DOCK_RELIEF_Y:.2f} x {E.DOCK_RELIEF_Z:.2f} is the fix, "
          f"and this assert is a HARD ZERO now, not a bound.")
    print(f"             docking band is y < {COVER_Y0:.2f} at the unchanged "
          f"{FRONT_Z-BACK_Z:.2f} slab; the {FRONT_Z-COVER_Z0:.2f} backpack starts above it. "
          f"6 features checked, lowest is the leaf kerf at y {LEAF_SEAT_Y-LEAF_KERF:.2f}.")
    print(f"             ⚠️ AND THE ENVELOPE MOVED THIS ROUND: {MOB_OY1-OY0:.2f} long against "
          f"the desk case's {OY1-OY0:.2f} -- they are now THE SAME. The docked stack is the "
          f"desk stack plus depth, which is the strongest form this check has ever had.")

    # ---- 9. THE SPEAKER RELIEF IS INSIDE THE CAVITY, NOT STRADDLING ITS WALL ----
    
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

    # ---- 11. THE COVER SCREWS.  Engagement bounded BOTH ways, at both ends. ----
    _head_z = COVER_Z0 + CBORE_DEPTH
    _tip_z = _head_z + MOB_SCREW_LEN
    _eng = _tip_z - BACK_Z
    assert _eng >= 3.0, (
        f"only {_eng:.2f}mm of thread engagement with an M3x{MOB_SCREW_LEN:.0f} -- the cover "
        f"is not clamped")
    assert _eng <= MOB_PILOT_DEPTH - 0.5, (
        f"the screw tip reaches {_eng:.2f}mm into a {MOB_PILOT_DEPTH}mm pilot -- it bottoms out "
        f"on the end of the hole before it clamps, and that failure looks exactly like success")
    print(f"  [screw]   M3 x {MOB_SCREW_LEN:.0f} under-head at BOTH sites; head at z "
          f"{_head_z:.2f}, {_eng:.2f}mm engaged in an {MOB_PILOT_DEPTH:.1f}mm pilot")

    # ---- 11b. EACH COUNTERBORE IS A HOLE, NOT A NOTCH. ----
    
    # The widest circular feature at a fastener is the counterbore, and it must clear every
    # edge of the part it is sunk into or the head loses its annular seat on that side. This is
    # the check that was missing when the chin screw sat at y=19.20 and d5.80 hung 1.70mm off
    # the cover's bottom edge -- caught by looking at a slice, not by any number. The coordinate
    # form runs at module level (it has to -- the chamfer dies first); here it is measured on
    # the ARTIFACT, and now at both ends, because the top screw is new and untested by anything
    # else in this file.
    _ann = (SCREW_BOSS_D - CBORE_D) / 2
    assert _ann >= E.BOSS_MIN_ANN, (
        f"the head bears on only {_ann:.2f}mm of annulus, under ember_case's BOSS_MIN_ANN of "
        f"{E.BOSS_MIN_ANN}. CBORE_DEPTH {CBORE_DEPTH} exceeds COV_WALL {COV_WALL}, so the seat "
        f"is the boss and not the wall -- widen SCREW_BOSS_D, do not thin the counterbore")
    for _sxy, _who in ((SCREW_XY, "chin"), (TOP_SCREW_XY, "top ")):
        _fx, _fy = _sxy
        _seat = (cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH, COVER_Z0 + CBORE_DEPTH + 0.20,
                     SCREW_BOSS_D - 0.40)
                 - cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH - 1, COVER_Z0 + CBORE_DEPTH + 2, CBORE_D))
        _sfrac = (cov & _seat).volume / _seat.volume
        assert _sfrac > 0.98, (
            f"the {_who} counterbore's seat is only {100*_sfrac:.1f}% material -- the head has "
            f"no annular bearing on part of its circumference, which is what a bore that breaks "
            f"out looks like")
        # CONTROL: an annulus wider than the boss must NOT read solid, or the probe proves
        # nothing. Run per site, because the two sit in different neighbourhoods.
        _wide = (cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH, COVER_Z0 + CBORE_DEPTH + 0.20,
                     SCREW_BOSS_D + 6.0)
                 - cyl(_fx, _fy, COVER_Z0 + CBORE_DEPTH - 1, COVER_Z0 + CBORE_DEPTH + 2,
                       SCREW_BOSS_D + 1.0))
        _wfrac2 = (cov & _wide).volume / _wide.volume
        assert _wfrac2 < 0.98, (
            f"control failed: the {_who} seat probe reads {100*_wfrac2:.1f}% solid even outside "
            f"the boss, so it cannot distinguish a seated head from an unsupported one")
        print(f"  [cbore]   {_who} d{CBORE_D} at ({_fx:.2f}, {_fy:.2f}): annulus {_ann:.2f} "
              f"(min {E.BOSS_MIN_ANN}); seat {100*_sfrac:.1f}% solid, control outside the boss "
              f"{100*_wfrac2:.1f}%")

    # ---- 8f. THE RETENTION BUDGET, PER EDGE, AS NUMBERS RATHER THAN AS A CLAIM. ----
    
    # >>> EVERY ROUND OF THIS DESIGN RE-DISCOVERED THE SAME FACT AND NONE OF THEM WROTE IT   <<<
    # >>> DOWN AS A MEASUREMENT.  THE CELL LANE MAKES THE ENTIRE -X HALF UNFASTENABLE.       <<<
    
    # For x < CELL_X1 the bore owns y BAY_Y0..BAY_Y1; above that the SCREW_EDGE_MIN rule kills
    # it against MOB_OY1 and below it against COVER_Y0. There is no valid -X screw position at
    # any y, on any scheme, and there never will be while the cell is where it is. So the lane
    # at SCREW_LANE_X is not a compromise, it is the -X limit -- and this block prints the
    # consequence for both long edges instead of leaving it to be re-derived a fifth time.
    _screwable = [(_x, _y) for _x in (OX0 + 0.01, OX1 - 0.01) for _y in (COVER_Y0, MOB_OY1)]
    assert SCREW_LANE_X - CBORE_D/2 >= RIM_X0 - 1e-9, (
        f"the screw lane's d{CBORE_D} counterbore reaches x "
        f"{SCREW_LANE_X - CBORE_D/2:.2f}, past the compartment's -X wall at {RIM_X0:.2f} -- it "
        f"is eating the shared divider's base, which is the one thing that stopped it moving "
        f"further -X in the first place")
    # the worst unheld point on the part: max over the cover's outline of the distance to the
    # nearest fastener. Sampled on the perimeter, which is where a cover gaps.
    _worst_d, _worst_pt = 0.0, None
    for _k in range(0, 201):
        _t = _k / 200.0
        for _px, _py in ((OX0, COVER_Y0 + _t*(MOB_OY1-COVER_Y0)),
                         (OX1, COVER_Y0 + _t*(MOB_OY1-COVER_Y0)),
                         (OX0 + _t*(OX1-OX0), COVER_Y0),
                         (OX0 + _t*(OX1-OX0), MOB_OY1)):
            _d = min(math.hypot(_px-_s[0], _py-_s[1]) for _s in SCREWS)
            if _d > _worst_d:
                _worst_d, _worst_pt = _d, (_px, _py)
    _dx0 = SCREW_LANE_X - OX0
    _dx1 = OX1 - SCREW_LANE_X
    # ...and the two screws must stand on real material at both ends, which is the claim the
    # deleted tongue-root probe used to make about tongues.
    # ⚠️ THE PROBE IS THE ANNULUS, NOT THE DISC, AND THE FIRST VERSION WAS THE DISC. Just below
    # the compartment floor the counterbore is still open -- CBORE_DEPTH 3.00 runs from
    # COVER_Z0 to 0.80 ABOVE CAV_Z0 -- so a d9.00 square probe reads 67.4% solid on a perfectly
    # sound boss and calls it a floating column. It was measuring the fastener's own hole. The
    # question is whether the RING the boss stands on is material, which is what bears the head.
    for _sxy, _who in ((SCREW_XY, "chin"), (TOP_SCREW_XY, "top ")):
        _pr = (bx(_sxy[0] - SCREW_BOSS_D/2, _sxy[0] + SCREW_BOSS_D/2,
                  _sxy[1] - SCREW_BOSS_D/2, _sxy[1] + SCREW_BOSS_D/2,
                  CAV_Z0 - 0.40, CAV_Z0 - 0.05)
               - cyl(_sxy[0], _sxy[1], CAV_Z0 - 0.50, CAV_Z0, CBORE_D))
        _f = (cov & _pr).volume / _pr.volume
        assert _f > 0.95, (
            f"the {_who} screw's boss stands on only {100*_f:.1f}% material just below the "
            f"compartment floor -- it is growing out of open space and would print as a "
            f"floating column")
    # ---- AND EACH PILOT HAS A FULL COLLAR OF FLOOR AROUND IT.  MEASURED, NOT COUNTED. ----
    #
    # >>> THIS IS WHY THE MOBILE DROPS TWO HEX ROWS AND NOT ONE. <<<
    #
    # The chin pilot is bored through the SAME 2.60 floor the back hex field perforates, and
    # "the cells are somewhere else" is exactly the claim that survives a screw moving. Row 1's
    # cells at x 23.00 and 27.00 overlapped the bore outright; row 2's at x 25.00 left 0.80mm,
    # under the floor, at a thread-forming screw that expands material radially as it enters.
    # Neither was visible in any number -- the seal was 100%, the engagement was 3.40, the
    # boolean was clear. So the collar is measured on the artifact, all the way round.
    for _sxy, _who in ((SCREW_XY, "chin"), (TOP_SCREW_XY, "top ")):
        _collar = (cyl(_sxy[0], _sxy[1], BACK_Z + 1.00, BACK_Z + 1.40,
                       PILOT_D + 2*MIN_SOLID)
                   - cyl(_sxy[0], _sxy[1], BACK_Z + 0.50, BACK_Z + 1.90, PILOT_D))
        _cf = (mf & _collar).volume / _collar.volume
        assert _cf > 0.98, (
            f"the {_who} pilot has only {100*_cf:.1f}% of a {MIN_SOLID:.2f}mm collar of floor "
            f"around it -- a vent cell, a label or a pocket is inside the material this screw "
            f"forms its thread in. At 0.80mm (one hex row) this reads 92%")
    # CONTROL: the same collar over the middle of the surviving hex field must read LOW, or it
    # cannot tell a solid floor from a perforated one.
    # ...ANCHORED TO THE OPEN STRIP, NOT TO A COORDINATE. At (25, 50) it read 100% solid --
    # correctly, because that is inside the BOND PLATEAU, which refills the hexes under the
    # seal. Second control in this file to go stale by being pinned to a number instead of a
    # feature. The strip the plateau cannot reach is x < RIM_X0 - PLATEAU_MARGIN.
    _cc_x = (HEX_FIELD_X0 + CELL_X1) / 2
    _cc_ring = (cyl(_cc_x, 50.00, BACK_Z + 1.00, BACK_Z + 1.40, PILOT_D + 2*MIN_SOLID)
                - cyl(_cc_x, 50.00, BACK_Z + 0.50, BACK_Z + 1.90, PILOT_D))
    _ccf = (mf & _cc_ring).volume / _cc_ring.volume
    assert _ccf < 0.90, (
        f"control failed: the pilot-collar probe reads {100*_ccf:.1f}% solid in the MIDDLE of "
        f"the hex field, so it cannot see a perforation and the two asserts above are blind")
    print(f"  [collar]  both pilots have a full {MIN_SOLID:.2f}mm collar of floor; control in "
          f"the open hex field reads {100*_ccf:.0f}% and is REJECTED. The mobile drops TWO hex "
          f"rows for this -- row 2's cell at x=25.00 left 0.80mm at a thread-forming screw.")

    # CONTROL: the same probe over the OPEN cell bore must read ~empty.
    # ...ON THE CELL AXIS, not off to one side: at CELL_X0 + 1.0 the probe straddles the
    # cradle's lobe and read 36.4% solid, which is the cradle doing its job rather than the
    # probe failing. A control has to sit in unambiguous void.
    _cpr = bx(CELL_AXIS_X - 3.0, CELL_AXIS_X + 3.0, DRV_CY - 3.0, DRV_CY + 3.0,
              CAV_Z0 + 2.0, CAV_Z0 + 2.4)
    _croot = (cov & _cpr).volume / _cpr.volume
    assert _croot < 0.20, (
        f"control failed: the boss-root probe reads {100*_croot:.1f}% solid inside the OPEN "
        f"cell bore, so it cannot tell a column on a floor from a column on nothing")
    print(f"  [retention] 2 x M3 x {MOB_SCREW_LEN:.0f}, lane x {SCREW_LANE_X:.2f}, "
          f"y {SCREW_XY[1]:.2f} and {TOP_SCREW_XY[1]:.2f} ({TOP_SCREW_XY[1]-SCREW_XY[1]:.2f} "
          f"baseline). Both bosses stand on solid floor.")
    print(f"             BUDGET PER EDGE -- top: 1 screw {MOB_OY1-TOP_SCREW_XY[1]:.2f} from the "
          f"end. bottom: 1 screw {SCREW_XY[1]-COVER_Y0:.2f} from the end. "
          f"LONG EDGES: NOTHING, at either end or mid-span.")
    print(f"             -X edge {_dx0:.2f} from the lane, +X edge {_dx1:.2f}. Worst unheld "
          f"point on the whole outline: {_worst_d:.2f}mm from the nearest screw, at "
          f"({_worst_pt[0]:.2f}, {_worst_pt[1]:.2f}) -- mid-span of a long edge, as designed.")
    print(f"             ⚠️ AND -X CANNOT BE IMPROVED BY ANY FASTENER: the cell bore owns "
          f"x < {CELL_X1:.2f} for y {BAY_Y0:.2f}..{BAY_Y1:.2f}, and outside that band the "
          f"{SCREW_EDGE_MIN:.2f} edge rule owns it. The lane IS the -X limit.")
    print(f"             ⚠️ AND NOR BY A LOCATION LIP -- MEASURED, NOT ASSUMED. A non-undercut "
          f"lip needs lip {MIN_SOLID:.2f} + 2 x 0.35 clearance + 2 x {MIN_SOLID:.2f} skin = "
          f"{MIN_SOLID*3 + 0.70:.2f}mm of wall. The cover's long wall is {COV_WALL:.2f} and the "
          f"midframe's floor outboard of the board pocket is {E.PK0-OX0:.2f}. Short by "
          f"{MIN_SOLID*3 + 0.70 - COV_WALL:.2f}. Same arithmetic that killed the -X dovetail.")
    print(f"             So the long edges are carried by the cover's own box section: "
          f"{FRONT_Z-COVER_Z0:.2f} deep overall, {BACK_Z-COVER_Z0:.2f} of closed section on "
          f"the cover alone, {COV_WALL:.2f} walls. That is the whole answer and it is a number.")

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
    _free_y = (RIM_Y0 - RIM_WALL) - BAY_Y0      # the LOWER band, where it lives now
    assert _tpf > 1.0, (
        f"a TP4056 phantom now fits the compartment ({_tpf:.2f} mm3 of interference) -- the "
        f"design note and #44 say it does not. One of them is wrong")
    # ---- 13b. THE BODY LIES FLAT IN ITS POCKET AND CAN BE LAID IN FROM ABOVE. ----
    #
    # Rewritten for the bay pocket. The old pair asked about ribs under a PCB and iron access
    # over it; in the bay the questions are different and simpler, and the SECOND one is the
    # one JP's assembly order depends on: the strip goes in FIRST and the cell drops on it, so
    # the pocket has to be open from the bore side, not from the case's opening.
    _floor = bx(PROT_PKT_X0 + PROT_PKT_CLR, PROT_PKT_X0 + PROT_PKT_CLR + PROT_W,
                PROT_Y0, PROT_Y1, PROT_PKT_Z0 + 0.02, PROT_PKT_Z0 + PROT_T - 0.02)
    _fint = (cov & _floor).volume
    assert _fint < 0.5, (
        f"{_fint:.2f} mm3 of material stands inside the body's own footprint -- a guide channel "
        f"wall or the pocket's own corner is under the PCB and it will not sit flat")
    # OPEN FROM THE BORE SIDE: a column from the pocket's mouth up into the bay must be clear,
    # or the body cannot be laid in before the cell.
    _lay = bx(PROT_PKT_X0 + PROT_PKT_CLR, PROT_PKT_X1 - 0.10, PROT_Y0, PROT_Y1,
              PROT_PKT_Z1 + 0.05, CELL_AXIS_Z)
    _lint = (cov & _lay).volume
    assert _lint < 0.5, (
        f"{_lint:.2f} mm3 roofs the body pocket -- the strip cannot be dropped in from the "
        f"bore side, which is the whole reason the pocket is at the BOTTOM (§4c). Anything "
        f"here is also a bridge in the cover's print orientation")
    print(f"  [strip]   1S PCB {PROT_L:.2f} x {PROT_W:.2f} x {PROT_T:.2f} — ALL JP-MEASURED, "
          f"plus the {BMS_PACK_FLAT_L:.1f} flat assembly. No placeholders left in this section.")
    print(f"             pocket x {PROT_PKT_X0:.2f}..{PROT_PKT_X1:.2f} y {PROT_Y0:.2f}.."
          f"{PROT_Y1:.2f} z {PROT_PKT_Z0:.2f}..{PROT_PKT_Z1:.2f}, in the bay's bottom +X corner "
          f"solid; {PROT_PKT_Z0-COVER_Z0:.2f} of outer wall under it")
    print(f"             cell clears the seated body by "
          f"{((CELL_AXIS_Z-CELL_BORE_CLR)-PROT_PKT_Z1) - math.sqrt(max((CELL_D_MAX/2)**2-(PROT_PKT_X0-CELL_AXIS_X)**2,0)):.2f}"
          f"mm — BAY_EXTRA {BAY_EXTRA:.2f} is what bought that, and +1.20 missed by 0.01")
    print(f"             >>> INSTALL ORDER: lay the BMS body into the BOTTOM +X channel, runs "
          f"in their guides, fold both ends into their seats, solder the output wires and "
          f"thread them to the chin pass, THEN drop the bare cell in on top. <<<")

    # ---- 13c. THE 34.25 TABS REACH THEIR FOLD SEATS FROM WHERE THE BODY ACTUALLY SITS. ----
    #
    # JP measured the tabs EVEN: 34.25 each. With the body centred along the bay each tab
    # spends (bay - body)/2 getting to its end and folds whatever is left. This is the check
    # that says the metalwork he already owns fits the plastic being printed.
    _run_m = PROT_Y0 - BAY_Y0
    _run_p = CELL_TIP_Y - PROT_Y1
    _tab = (BMS_PACK_FLAT_L - PROT_L) / 2
    for _nm, _run in (("-Y", _run_m), ("+Y", _run_p)):
        _fold = _tab - _run
        assert _fold >= LEAF_FREE * 2.5, (
            f"the {_nm} tab runs {_run:.2f} to its seat and has {_fold:.2f} left to fold "
            f"against a {LEAF_FREE} free height -- under 2.5 limbs that is a bend, not a leaf "
            f"spring. Move the body along the bay or trim the other end")
    print(f"  [tabs]    {_tab:.2f} per side (JP: even). -Y run {_run_m:.2f} + fold "
          f"{_tab-_run_m:.2f}; +Y run {_run_p:.2f} + fold {_tab-_run_p:.2f}; "
          f"{(_tab-_run_m)/LEAF_FREE:.1f} and {(_tab-_run_p)/LEAF_FREE:.1f} limbs")
    print(f"             BOTH ends are folded-excess leaf springs now — the '+' plate is gone "
          f"and the one kerf construction serves both, which is what JP described.")

    # ---- 14. THE WS2812.  OCCLUDED, AND THE OCCLUSION IS PROVEN, NOT ASSUMED. ----
    
    # docs/enclosure.md:161 already states the general case: "WS2812 RGB LED (GPIO42) is on the
    # BACK, inboard, and fires backwards. A CLOSED BACK COVER HIDES IT COMPLETELY." So this is a
    # documented property of any back cover, not something this variant introduced. What IS
    # this variant's to answer is whether the geometry leaves a way out, and it does not:
    
    #   * the LED is inside the DRIVER's footprint, so the module's body is the first thing in
    #     front of it -- a window in the plateau would look straight at the back of the speaker;
    #   * and the driver CANNOT be moved off it. The sealed cavity must contain the SPK relief
    #     (the wire's only exit, check 9), the driver is DRIVER_W long, and clearing the LED
    #     would need the driver wholly above or wholly below it. Both overrun the cavity.
    
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
    # ⚠️ ALL the metalwork, not just the leaf. See plate_phantom(). The lens used to hold only
    # the -Y leaf, so the "+" mark was being cleared by the absence of a part that lives at the
    # other end of the bay. Both phantoms, both marks, and the numbers decide the placement.
    _leaf = leaf_phantom(LEAF_FREE)
    _plate = plate_phantom()
    _metal = _leaf + _plate
    for _nm, _ink in (("+", _ink_p), ("-", _ink_n)):
        _pl, _mx, _my, _mz = _mark_face(_nm)
        _hu, _hv = _ink_half(MARK_PATHS_P if _nm == "+" else MARK_PATHS_N)
        if _pl == "y":
            _pr = bx(_mx - _hu - 0.30, _mx + _hu + 0.30, _my, _my + MARK_DEPTH,
                     _mz - _hv - 0.30, _mz + _hv + 0.30)
            # the sight line: straight up out of the bay from just in front of the face
            _los = bx(_mx - _hu, _mx + _hu, _my - 0.60, _my, _mz + _hv, BACK_Z)
        else:
            _pr = bx(_mx - _hu - 0.30, _mx + _hu + 0.30, _my - _hv - 0.30, _my + _hv + 0.30,
                     _mz - MARK_DEPTH, _mz)
            _los = bx(_mx - _hu, _mx + _hu, _my - _hv, _my + _hv, _mz, _mz + 2.00)
        _cut = (_pr - cov).volume / MARK_DEPTH
        assert _cut >= 0.80 * _ink, (
            f"the '{_nm}' marking removed only {_cut:.2f} mm2 of face against {_ink:.2f} of ink "
            f"-- the deboss is missing, clipped by the end wall, or absorbed into the pocket")
        assert _cut <= 1.60 * _ink, (
            f"the '{_nm}' probe reads {_cut:.2f} mm2 against {_ink:.2f} of ink -- it is counting "
            f"the bore or the contact pocket, not the marking")
        # >>> AND THE LENS THIS CHECK DID NOT HAVE: CAN IT BE SEEN. <<<
        #
        # Area proves the groove was cut. It says nothing about whether anything STANDS IN
        # FRONT OF IT, and on a flat-top cell the markings are the ONLY reverse-insertion
        # measure there is -- so a mark that is present and hidden is the exact failure the
        # feature exists to prevent, passing the exact check written to prevent it. The bay is
        # loaded from +Z, so the test is a clear column from the mark out of the opening, and
        # it is run against the METALWORK as well as the plastic because the leaf is a phantom
        # and no part-vs-part boolean can see it.
        _free = (_los - cov - _metal).volume / _los.volume
        assert _free > 0.90, (
            f"the '{_nm}' marking is only {100*_free:.0f}% visible from the bay's open side -- "
            f"something stands in front of it. It is debossed, it measures correct, and nobody "
            f"can read it. Flat-top cells have NO mechanical keying, so this is the whole of "
            f"the reverse-insertion defence")
    # CONTROL, and it is the defect this lens was added for: the "-" mark's OLD home, on the
    # low-Y end wall, has the folded leaf standing directly over it. If that reads clear, the
    # lens is blind and the two asserts above are decoration.
    _ctl_los = bx(CELL_AXIS_X - MARK_INK/2, CELL_AXIS_X + MARK_INK/2, BAY_Y0, BAY_Y0 + 0.60,
                  (CAV_Z0 + CONTACT_Z0)/2 + MARK_INK/2, BACK_Z)
    _ctl_free = (_ctl_los - cov - _metal).volume / _ctl_los.volume
    assert _ctl_free < 0.90, (
        f"control failed: the '-' mark's old position on the low-Y end wall reads "
        f"{100*_ctl_free:.0f}% visible even with the leaf standing on that very face, so this "
        f"lens cannot detect an obscured marking")
    print(f"  [marks]   '+' on the +Y bulkhead's bay face (y {_mark_face('+')[2]:.2f}), '-' on "
          f"the cover's MATING FACE at BACK_Z (y {_mark_face('-')[2]:.2f}) -- see _mark_face")
    print(f"             VISIBILITY: both >90% clear to the bay's open side, measured against "
          f"the cover AND BOTH metal phantoms (leaf + plate); control (the '-' mark's old wall "
          f"position, behind the leaf) reads {100*_ctl_free:.0f}% and is REJECTED")
    # >>> THE ASYMMETRY, RE-EARNED BY MEASUREMENT RATHER THAN BY ITS OLD SENTENCE. <<<
    # The placement was justified by "a leaf at one end, a plate at the other", and that reason
    # was challenged as stale on the grounds that both ends are leaf seats now. THEY ARE NOT:
    # §5g's construction block is explicit -- ONE KERF DESIGN used at both ends, with a FOLDED
    # LEAF at -Y and a FLAT PLATE at +Y. What is shared is the seat, not the spring. So the old
    # sentence was right; but a sentence being right is not evidence, so the two projections
    # below are measured off the phantoms and printed every build. If a future round puts a
    # fold at +Y, this number moves and the "+" mark has to move with it.
    _proj_lo = LEAF_FREE - LEAF_KERF
    _proj_hi = 0.0
    print(f"             ASYMMETRY MEASURED, not argued: the -Y leaf projects "
          f"{_proj_lo:.2f}mm INTO the bore past its wall face; the +Y plate projects "
          f"{_proj_hi:.2f}mm (flush in a {CONTACT_KERF:.2f} kerf, body y "
          f"{CELL_TIP_Y:.2f}..{CELL_TIP_Y+CONTACT_KERF:.2f}, entirely behind the marked face).")
    print(f"             THAT is why '-' needs the mating face and '+' keeps its end wall. The "
          f"two ends share a SEAT design, not a spring -- see §5g.")
    print(f"             debossed {MARK_DEPTH:.2f}, {MARK_H:.2f} tall, {E.LABEL_W} groove; "
          f"area measured against ink both ways AND a sight line measured on the solid")
    print(f"             min_gap is VACUOUS on these glyphs (inf, 0 pairs) and is asserted to "
          f"STAY vacuous rather than used as a proof")
    print(f"             ⚠️ NO MECHANICAL KEYING IS POSSIBLE FOR FLAT-TOP CELLS -- both ends are "
          f"identical. Reverse-insertion protection is MARKINGS ONLY. Electrical, JP's call.")

    # ---- 16. THE FAILURE VENT: throat area, AND no line of sight. ----
    
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

    # ---- 19. THE RGB LED WIRE PASS, AND WHAT IT OPENS BETWEEN. ----
    #
    # JP wants an LED in the upper compartment, so the midframe gets one hex for its pigtail.
    # It is the first aperture ever cut between the board cavity and that compartment, so the
    # ingress picture is measured rather than asserted: WHICH volumes it joins, that it is
    # actually open end to end, and that it joins no volume that has a rule.
    _lp = hexp(LED_PASS_XY[0], LED_PASS_XY[1], LAT_R - 0.20, BACK_Z + 0.10, CAV_FLOOR - 0.10)
    _lp_open = (_lp - mf).volume / _lp.volume
    assert _lp_open > 0.98, (
        f"the LED wire pass is only {100*_lp_open:.0f}% open through the midframe's floor -- it "
        f"is a blind pocket, not an aperture, and from the back face the two look identical")
    # CONTROL: the same probe on solid floor must read shut.
    #
    # ⚠️ THIRD TIME IN THIS FILE, SO IT IS A RULE NOW: A CONTROL MUST BE ANCHORED TO A FEATURE
    # THAT GUARANTEES ITS PROPERTY, NEVER TO AN OFFSET. "8mm to the +X" landed on the MIC BORE
    # and read 40% open -- failing as a control while the aperture it guards was perfect. The
    # seal control did the same thing (slid onto floor a row deletion had just made solid) and
    # so did the pilot collar's (sat inside the bond plateau). The plateau is the right anchor
    # here for the opposite reason: it exists to be SOLID, by construction, so a probe at its
    # centre cannot go stale unless the plateau itself does.
    _pl_c = _plateau_region()
    _lp_ctl = hexp((_pl_c[0] + _pl_c[1]) / 2, (_pl_c[2] + _pl_c[3]) / 2, LAT_R - 0.20,
                   BACK_Z + 0.10, CAV_FLOOR - 0.10)
    _lp_cf = (_lp_ctl - mf).volume / _lp_ctl.volume
    assert _lp_cf < 0.20, (
        f"control failed: solid floor 8mm from the pass reads {100*_lp_cf:.0f}% open, so this "
        f"probe cannot tell an aperture from a plate")
    # IT MUST OPEN INTO THE CAVITY, NOT THE SOLID BLOCK: above PY1 the midframe is solid to
    # SEAM_Z and a hex there is a blind hole that looks the same from the back.
    assert LED_PASS_XY[1] + LAT_R <= E.PY1 - 1.00, (
        f"the wire pass reaches y {LED_PASS_XY[1]+LAT_R:.2f} against the board pocket's top at "
        f"{E.PY1:.2f} -- part of it is boring into the solid top block, where it opens onto "
        f"nothing")
    # ...and it joins NO volume that has a rule. The sealed cavity and the cell bay both do.
    assert LED_PASS_XY[1] - LAT_R > RIM_Y1 + RIM_WALL, (
        f"the wire pass reaches y {LED_PASS_XY[1]-LAT_R:.2f}, into the sealed cavity's footprint "
        f"which ends at {RIM_Y1+RIM_WALL:.2f}")
    assert LED_PASS_XY[0] - LAT_R > RIM_X0, (
        f"the wire pass reaches x {LED_PASS_XY[0]-LAT_R:.2f}, over the divider and the CELL BAY "
        f"-- the one volume in this design with a settled ingress rule (§5d's labyrinth)")
    assert LED_PASS_XY[1] - LAT_R > _plateau_region()[3], (
        f"the wire pass at y {LED_PASS_XY[1]-LAT_R:.2f} is inside the bond plateau (to "
        f"{_plateau_region()[3]:.2f}) -- it would be a hole in the surface the seal lands on")
    for _nm, _p, _r in (("mic bore", E.MIC, E.MIC_HOLE_D/2),
                        ("+X boss", (46.0, 82.0), E.BOSS_FLARE_D/2),
                        ("top pilot", TOP_SCREW_XY, PILOT_D/2)):
        _d = math.hypot(LED_PASS_XY[0] - _p[0], LED_PASS_XY[1] - _p[1]) - LAT_R - _r
        assert _d >= MIN_SOLID, (
            f"the wire pass leaves {_d:.2f}mm to the {_nm} at {_p}, under the {MIN_SOLID:.2f} "
            f"floor")
    print(f"  [ledwire] one {LAT_AF:.2f} hex at {LED_PASS_XY} through the midframe floor, "
          f"{100*_lp_open:.0f}% open (control on solid floor {100*_lp_cf:.0f}%), "
          f"{LED_PASS_BREAK:.2f} edge break at the cavity-side mouth")
    print(f"             IT JOINS: the board cavity <-> the upper compartment. Both already "
          f"open volumes -- the cavity has 4 flank channels and the back hex field, the "
          f"compartment is dry dead space above the seal rim.")
    print(f"             IT DOES NOT JOIN: the sealed speaker cavity (ends y "
          f"{RIM_Y1+RIM_WALL:.2f}, pass starts {LED_PASS_XY[1]-LAT_R:.2f}) or the CELL BAY "
          f"(ends x {RIM_X0:.2f}, pass starts {LED_PASS_XY[0]-LAT_R:.2f}). ⚠️ NO LED MOUNT — "
          f"JP asked for the wire pass only.")

    # ---- 19b. THE BLIND TOP MESH IS BLIND. ----
    # A deboss that has quietly become a window into the cell bay is the failure this feature
    # was redesigned to avoid, and it is invisible from the outside -- which is the whole
    # problem. Measured as a membrane, exactly like the glow window's.
    _tm_probe = bx(TOPMESH_X0, TOPMESH_X1, MOB_OY1 - COV_WALL, MOB_OY1 - TOPMESH_D,
                   TOPMESH_Z0, TOPMESH_Z1)
    _tm_frac = (cov & _tm_probe).volume / _tm_probe.volume
    assert _tm_frac > 0.98, (
        f"the blind top mesh's membrane is only {100*_tm_frac:.1f}% material -- the deboss has "
        f"become a through-hole on the battery side, i.e. a straight path into the 18650 bay. "
        f"That is what §5d's labyrinth exists to prevent")
    # CONTROL: the debossed band itself must read mostly OPEN, or the mesh was never cut.
    _tm_cut = bx(TOPMESH_X0, TOPMESH_X1, MOB_OY1 - TOPMESH_D, MOB_OY1, TOPMESH_Z0, TOPMESH_Z1)
    _tm_cf = (_tm_cut - cov).volume / _tm_cut.volume
    assert _tm_cf > 0.20, (
        f"control failed: the deboss band reads only {100*_tm_cf:.0f}% removed, so the mesh is "
        f"not there and the membrane check above is measuring a plain wall")
    print(f"  [topmesh] {TOPMESH_N} blind cells ({100*_tm_frac:.0f}% of the field), "
          f"{TOPMESH_D:.2f} deep in the +Y end face over "
          f"x {TOPMESH_X0:.2f}..{TOPMESH_X1:.2f}, z {TOPMESH_Z0:.2f}..{TOPMESH_Z1:.2f}; "
          f"{100*_tm_frac:.1f}% membrane behind it ({COV_WALL-TOPMESH_D:.2f}mm)")
    print(f"             ⚠️ BLIND ON PURPOSE. Behind this face on the battery side is the "
          f"cell-lane bulkhead and then the 18650. A through-vent here is a straight light and "
          f"dust path into a Li-ion bay; the +X side of the boss is where one could go.")

    # ---- 19c. THE LED-SIDE THROUGH FIELD, AND THE INTERNAL VENT'S NO-SIGHTLINE RULE. ----
    #
    # >>> JP took the alternative: "both, and there can be a hex vent between the battery <<<
    # >>> compartment and the led compartment."  Which makes the second one dangerous.      <<<
    #
    # With the +X field bored through, the upper compartment is OPEN TO THE SKY. A plain hex
    # through the divider would then put outside air one straight line from a Li-ion bay -- the
    # exact thing §5d's labyrinth refuses. It is not a hypothetical: a ray from a top cell at
    # x 30 to a divider hole at x 20.65 leaves the top bore at 41 degrees to its axis, and a
    # 2.20-long 4.75-wide bore only collimates to 65, so it goes straight through.
    #
    # So the internal vent is §5d's construction on a different axis, and this is where that
    # gets PROVEN rather than described: at the compartment-side notch's own Z, a straight
    # line across the divider must still find material.
    _iv_los = bx(CELL_X1, RIM_X0, IVENT_Y - 0.01, IVENT_Y + 0.01,
                 IVENT_CZ_O - LAT_AF/2 + 0.30, IVENT_CZ_O + LAT_AF/2 - 0.30)
    _iv_solid = (cov & _iv_los).volume / _iv_los.volume
    assert _iv_solid > 0.25, (
        f"a straight line across the divider at the compartment-side notch finds only "
        f"{100*_iv_solid:.0f}% material -- the internal vent has become a HOLE, and with the "
        f"+X field open above it that is a straight path from outside air into the 18650 bay")
    # CONTROL: drill the divider through at that Y and prove the probe can see it.
    _iv_drill = cov - bx(CELL_X1 - 1, RIM_X0 + 1, IVENT_Y - LAT_AF/2, IVENT_Y + LAT_AF/2,
                         IVENT_CZ_O - LAT_AF/2, IVENT_CZ_O + LAT_AF/2)
    _iv_cf = (_iv_drill & _iv_los).volume / _iv_los.volume
    assert _iv_cf < 0.05, (
        f"control failed: a divider deliberately drilled through still reads {100*_iv_cf:.0f}% "
        f"material, so this probe cannot detect the straight hole it exists to reject")
    # ...and the vent must actually PASS AIR: the band has to join the two notches.
    _iv_band = bx(RIM_X0 - IVENT_D + 0.05, RIM_X0 - IVENT_D + IVENT_BAND - 0.05,
                  IVENT_Y - 1.0, IVENT_Y + 1.0,
                  IVENT_CZ_O + LAT_AF/2 + 0.10, IVENT_CZ_I - LAT_AF/2 - 0.10)
    _iv_open = (_iv_band - cov).volume / _iv_band.volume
    assert _iv_open > 0.90, (
        f"the internal vent's connecting band is only {100*_iv_open:.0f}% open -- the two "
        f"notches do not meet and it is two blind pockets, which is what a vent looks like "
        f"when it has been drawn but not joined")
    print(f"  [ivent]   cell bay <-> LED compartment, {IVENT_D:.2f} from each face of a "
          f"{DIVIDER_W:.2f} divider, {IVENT_BAND:.2f} band; notches at z {IVENT_CZ_O:.2f} and "
          f"{IVENT_CZ_I:.2f}, both at y {IVENT_Y:.2f}")
    print(f"             NO SIGHTLINE: across the divider at the outer notch's Z it is still "
          f"{100*_iv_solid:.0f}% solid; control (drilled through) {100*_iv_cf:.0f}%. Band "
          f"{100*_iv_open:.0f}% open, so it is a vent and not two pockets.")
    print(f"             ⚠️ OFFSET IN Z, NOT Y: the divider's free Y window between the seal "
          f"rim and the top boss is {TOP_SCREW_XY[1]-SCREW_BOSS_D/2-(RIM_Y1+RIM_WALL):.2f}mm -- "
          f"one cell wide, not two. It is {BACK_Z-CAV_Z0:.2f} tall, so the pair stacks.")
    print(f"  [topvent] {TOPVENT_N} THROUGH cells on the LED side of the boss, x "
          f"{TOPVENT_X0:.2f}..{TOPVENT_X1:.2f} -- these are real bores into the upper "
          f"compartment, i.e. the LED's window as much as a vent")
    print(f"             INGRESS, STATED: atmosphere -> upper compartment (new, upward-facing) "
          f"-> board cavity via the LED wire pass. The compartment is EMPTY of electronics "
          f"since the 1S strip moved to the lower band; the cell bay is reached only through "
          f"the offset internal vent, which is why that one is a labyrinth.")

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
