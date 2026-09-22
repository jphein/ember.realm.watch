"""
Tapstone shrine apron  --  the card pad that grows in front of the ember desk stand
===================================================================================
Parametric source.  Run:  ./cadenv/bin/python shrine.py

Tapstone decision 0005 (+ its 2026-09-21 amendment) and 0018; RF rules from tapstone
`docs/design/materials.md`.

WHAT THIS IS: a separate, non-bearing shelf that butts against the ember stand's plinth and
carries one CR80 card pad over the MFRC522 coil.  It is NOT fused to the stand — `ember_case.py`
is imported read-only and never edited, so `ember-front-bezel.stl` and `ember-back-shell.stl`
are byte-identical by construction rather than by care.

COORDINATE SYSTEM = ember's model frame, so imported parts compose with no transform:
    x  0 .. ST_W     the stand's width; the apron is centred on the same axis and is wider
    y  0 .. ST_D     the stand.  y = 0 IS THE STAND'S FRONT FACE, so the apron lives at y < 0
    z                desk at -PLINTH_H (the plinth is modelled below the cradle's z origin
                     and lifted at export — see PRINT-SHEET "The plinth").  PRINT_LIFT does
                     the same job for this part.
"""
from build123d import *
import os, sys, math

# Resolve imports against THIS FILE, never the working directory — ember_case.py's own lesson.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# READ-ONLY IMPORT. ember_case keeps every export and check inside `if __name__ == "__main__"`,
# so importing it builds nothing and writes nothing (verified: 2.9 s, no file touched). Every
# stand number below is READ from it — none is re-typed, which is the duplicate-constant trap
# that cost ember its base plate (PRINT-SHEET, "plate kept its private copy of the old number").
import ember_case as E

# ============================================================================
# 1. WHAT WE INHERIT FROM THE STAND  (read, never typed)
# ============================================================================
ST_W, ST_D      = E.ST_W, E.ST_D          # 64.0 x 64.0 footprint
ST_R            = E.ST_R                  # 10.0 corner radius
PLINTH_H        = E.PLINTH_H              # 16.0 — the apron's whole vertical budget
DESK_Z          = -PLINTH_H               # the desk plane in this frame
EGRESS_W        = E.EGRESS_W              # 14.0 — the cable arch in the plinth's front face
EGRESS_H        = E.EGRESS_H              # 10.0
EGRESS_CX       = ST_W / 2                # 32.0, centred
CABLE_OD        = E.CABLE_OD              # 4.5 (ASSUMED upstream — inherits that standing)
TUCK_W, TUCK_D  = E.TUCK_W, E.TUCK_D      # 7.00 / 5.00 — ember's solved "a cord must LIE in it"
CHAMFER         = E.CHAMFER               # 0.80, so the shrine reads as the same family
FRONT_FLAT      = ST_W - 2 * ST_R         # 44.0 — the flat span the hooks key into

# ============================================================================
# 2. THE CARD AND ITS PAD
# ============================================================================
# ISO 7810 ID-1. The card itself is a standard, not a measurement, so these are exact.
CR80_W, CR80_D, CR80_T = 85.6, 54.0, 0.76

# >>> LIP CLEARANCE: 0.50 PER SIDE, AND IT IS A LOCATING FEATURE, NOT A FIXTURE. <<<
# ID-1 permits ~85.47..85.72 on its own; an Ender 3 wall lands within roughly +/-0.2 with
# elephant's foot pulling the first layers inward. 0.50 leaves 1.0 mm of slack per axis: the
# card drops in one-handed and still cannot rattle enough to read as loose. 0.35 binds against
# a slightly fat wall and wants a file; 0.80+ reads as a tray. The coil does not care.
PAD_CLR = 0.50
PAD_W   = CR80_W + 2 * PAD_CLR            # 86.60
PAD_D   = CR80_D + 2 * PAD_CLR            # 55.00
PAD_R   = 3.18                            # ID-1's own corner radius, so the pocket matches the card

# >>> LIP HEIGHT 0.60, WHICH IS *BELOW* THE CARD'S 0.76 THICKNESS ON PURPOSE. <<<
# The amendment says "lip ~0.9 mm"; that number came from my own bad arithmetic, and 0.9 against
# a 0.76 card leaves the card 0.14 mm BELOW the lip — recessed, not proud, and a card you cannot
# pinch. 0.60 engages 79% of the card's thickness (plenty to locate a card nobody is aiming) and
# leaves 0.16 mm proud to get a nail under, with the scallop below doing the real work.
LIP_H = 0.60
assert LIP_H < CR80_T, "the lip must be shallower than the card or the card cannot be picked up"

# The finger scallop: a dish in the pad's front wall. Without it a flush card is unpickable, and
# 0.16 mm of proud card is not a handle. Cut from the front edge so a thumb arrives along the desk.
SCALLOP_D  = 22.0                         # wide enough for a thumb, not so wide the lip stops locating
SCALLOP_DZ = LIP_H + 1.2                  # through the lip and into the pad floor, so the nail passes under

# ============================================================================
# 3. THE MFRC522 — MEASURED OUT OF THE PRINTED CASE JP ALREADY USES
# ============================================================================
# >>> SOURCE: ~/Projects/labels/RFID+Bottom.stl (+ RFID+Lid.stl), the case printed and verified
#     on JP's unit 2026-09-01 (tapstone CLAUDE.md, MakerWorld 2524848). Measured out of the mesh.
#
# WHAT IS MEASURED vs WHAT IS INFERRED, because a case is not a board:
#   MEASURED  pocket interior            40.50 x 60.50 mm   <- board PLUS its fit clearance
#   MEASURED  floor under the board       2.00 mm           <- a PROVEN RF skin, see SKIN_T
#   MEASURED  internal height             7.00 mm  (pocket floor z=2.0 to the lid's inner face)
#   MEASURED  four support posts 2.30 mm square, tops z=6.00, at (+/-17.15, -14.65) and
#             (+/-12.40, +22.95) — an asymmetric 4-point pattern, so it is the board's own
#   MEASURED  centre boss 16.00 x 6.00, top z=3.50
#   MEASURED  wire notch ~25 mm wide in one SHORT (-Y) wall, open from z~7 to the rim at z=9
#   INFERRED  the board outline is the pocket MINUS clearance, so <= 60.50 x 40.50
#   INFERRED  the connector bundle leaves by the short edge the notch is in
# The pocket envelope is used as-is: it already contains the slack a board needs, and taking the
# looser reading is the safe direction for a hole (unlike the skin, where tighter is safe).
READER_POCKET_L = 60.50   # x — the board's long axis (see the orientation note below)
READER_POCKET_W = 40.50   # y
READER_POCKET_D = 7.00    # the proven case's full internal height, so whatever rides on the
                          # board clears too. The pocket opens downward; the desk closes it.

# >>> THE COIL'S POSITION IS NOT RECOVERABLE FROM A CASE — AND IS NOT NEEDED. <<<
# A pocket says where the board sits, never where the antenna sits on it. Rather than infer it,
# the pad carries a UNIFORM skin over the WHOLE board footprint and the RF keepout covers the
# whole footprint too. The coil is necessarily inside the board outline, so a rule that holds
# everywhere on the board holds wherever the coil actually is. The printed case does exactly
# this — one flat 2 mm floor under the entire board — and it reads.
# The gate stays SHUT on this one value alone (lead's call, and it is the right failure): six of
# seven numbers landing is progress; a guessed coil area is the single error that yields a part
# which reads cards badly and looks perfectly finished.
COIL_L = None             # coil ACTIVE area — NOT recoverable from a case, see above
COIL_W = None
# The argument for opening it, for the record, is that the coil position may not be NEEDED: the
# pad carries a uniform skin over the WHOLE board footprint and the RF keepout covers the whole
# footprint, so a rule that holds everywhere on the board holds wherever the coil is — which is
# exactly what the printed case does with one flat 2 mm floor. That is a proposal, not a licence;
# the gate stays shut until someone decides it.

# Orientation is forced, not chosen: the card is 85.6 x 54.0 and the board is 60.5 x 40.5, so
# the board's long axis must run along the card's long axis. Across it, 60.5 > 54.0 — the board
# would be longer than the card it reads.
assert READER_POCKET_L <= CR80_W and READER_POCKET_W <= CR80_D, "reader does not fit under the card"

# >>> IT IS NOT A RIBBON. <<< Seven individual female dupont jumpers pushed onto a straight
# 8-pin 2.54 header standing PERPENDICULAR to the board (JP's photo). The clearance that needs
# is a connector STACK plus a loose bundle — a different shape and a much greater height than a
# flat connector bundle — so the name is wrong in a way that would mislead the next reader.
#
# VERIFIED IN THE MESH, both bodies: the relief is in a SHORT edge, not a long one. The case
# body's wire notch and the lid's notch are both in the min-Y wall, and the pocket runs
# 40.50 (x) x 60.50 (y), so that wall spans the board's 40.50 mm SHORT edge. The lid's notch
# measures ~24.5 mm wide — an 8-pin 2.54 header is 20.3 mm — and it is open through the lid's
# EDGE, which is how the case accommodates a stack taller than its 7.00 mm interior: the header
# is not enclosed, it protrudes through the edge.
CONN_SIDE = -1            # -1 = the connector leaves the -x face. The board's short edge.
CONN_CH_W = 22.0          # clears the 20.3 mm header with room; the case's own notch is ~24.5

# >>> BLOCKING UNKNOWN: how tall is the header + dupont socket stack above the PCB? <<<
# The case sidesteps it by letting the stack out through a notch rather than housing it. This
# apron cannot copy that without knowing the height: the board lies under a 2.00 mm skin with
# the pocket only READER_POCKET_D deep, so a vertical stack has nowhere to go in either
# orientation — pointing up it hits the skin and the card pad, pointing down it hits the desk.
# Measuring this off a photograph is exactly the substitution that is not allowed, so it is
# PENDING and the export gate is shut on it.
CONN_STACK_H = None       # mm above the PCB, header + pushed-on dupont socket housings

# The skin over the coil: materials.md says 1.5-2 mm of PLA/wood/resin, nothing conductive.
# 2.00 is not the mid-band guess it started as — it is what the printed case above uses under
# the whole board, and that case demonstrably reads. Taking the proven number beats splitting
# a range, and it is the stiffest option materials.md allows over a 60 x 40 opening.
SKIN_T = 2.00
assert 1.5 <= SKIN_T <= 2.0, "materials.md fixes the RF skin at 1.5-2.0 mm"
# COIL_L/COIL_W are deliberately NOT pending: the uniform skin over the whole board footprint
# makes the coil's position unnecessary rather than unknown-and-needed (lead's ruling). The gate
# is shut on the connector stack instead, which is a real dimension with nowhere to go.
_PENDING = {k: v for k, v in list(globals().items()) if k.startswith("CONN_STACK") and v is None}

# ============================================================================
# 4. THE APRON PLAN
# ============================================================================
WALL      = 2.4                           # outer wall / lip wall around the pad
LED_GAP   = 3.0                           # solid between pad wall and LED channel
LED_W     = 6.0                           # channel width — sized for a 5 mm WS2812 strip. PROVISIONAL:
                                          # confirm the strip before printing; it is a later fit (0005)
# >>> DEPTH IS BOUNDED BY WHAT PASSES UNDERNEATH, NOT BY THE STRIP. <<<
# At 5.0 the channel floor dropped below POCKET_TOP and the connector relief and cable groove
# punched clean through it — a continuous void from the desk to the top face, which is a light
# leak, a dust path and the wiring visible from above. Kept above POCKET_TOP by construction.
LED_D     = 2.4
APRON_W   = PAD_W + 2 * (WALL + LED_GAP + LED_W + WALL)      # 114.20
# >>> THE FRONT MARGIN IS THE SCALLOP'S RADIUS PLUS A RIM, NOT A ROUND NUMBER. <<<
# It was 9.0, against a scallop of radius 11.0 — so the dish cut straight through the apron's
# front face and left a notch in the rim. Every assert passed; the RENDER showed it, which is
# this repo's own five-for-five lesson about defects invisible in correct-looking source.
FRONT_RIM = 3.0                           # solid left in front of the scallop
FRONT_MG  = SCALLOP_D / 2 + FRONT_RIM     # 14.00
APRON_X0  = ST_W / 2 - APRON_W / 2        # centred on the stand's axis
APRON_X1  = APRON_X0 + APRON_W
APRON_Y1  = 0.0                           # butts the plinth's front face
APRON_R   = 6.0                           # plan corner radius; smaller than the stand's R10 so the
                                          # apron reads as a shelf the stand sits behind, not a second box

# Thickness. Two independent requirements; the part takes the larger, and the reader may raise it
# again once measured (asserted in _check_geometry once READER_T exists).
FLOOR_T   = 1.6                           # under the cable groove: 4 x 0.4 mm walls
CH_CEIL   = 2.0                           # material over the groove — a 7 mm bridge, trivial for FDM
# Derived from the two stacks that have to fit, rather than rounded to a nice number: the pad
# stack (lip + skin + the reader pocket, which opens to the desk) and the cable stack.
APRON_T   = max(LIP_H + SKIN_T + READER_POCKET_D, FLOOR_T + TUCK_D + CH_CEIL)   # 9.60

TOP_Z     = DESK_Z + APRON_T              # the apron's top face
PAD_FLOOR = TOP_Z - LIP_H                 # the card rests here

# ---- the cable groove: OPEN TO THE DESK, AND IT TURNS OUT THE SIDE ----
# >>> THE CABLE MUST NOT PASS UNDER THE PAD. <<<
# materials.md: any conductor in the coil's field kills the read, and a USB lead's braided
# shield is exactly that. Carrying the egress straight forward is the obvious route and it is
# the wrong one. The groove therefore turns inside REAR_BAND and leaves through a side face,
# putting every millimetre of copper outside the pad footprint. _check_geometry asserts it.
# Open to the underside rather than enclosed: the desk closes it, nothing bridges over copper,
# and the cable can be laid in after the fact rather than threaded.
# >>> DERIVED, NOT PICKED: the cable leaves opposite the connector bundle. <<<
# They must not fight for the same corner, and the connector bundle's side is fixed by the reader, so this
# one is not a free choice. Flipping CONN_SIDE flips this with it.
CABLE_SIDE = -CONN_SIDE
CH_W       = TUCK_W                       # 7.00 — ember's own solve for a cord that must lie in it
CH_D       = TUCK_D                       # 5.00 — must EXCEED the cord, not merely admit it
CH_SWEEP   = 18.0                         # a 4.5 mm USB-C lead wants ~R18; the corner is opened out
                                          # to that so the turn is a sweep rather than a kink

RF_KEEPOUT = 6.0                          # how far the groove must stay from the pad footprint

# >>> THE REAR BAND IS SOLVED, NOT CHOSEN. <<<
# The pad's rear edge always lands at y = -REAR_BAND (the pad is placed from the apron's front),
# so the band is exactly the room the turn needs to finish before the keepout starts: half the
# sweep, plus the keepout, plus a margin, on each side of the turn centreline. Typing 24 here is
# what put the groove 3 mm inside the pad on the first build — the assert caught it, and the fix
# is to derive the number so the two cannot drift apart again.
RF_MARGIN  = 1.5
REAR_BAND  = 2 * (RF_KEEPOUT + CH_SWEEP / 2 + RF_MARGIN)     # 33.00
APRON_D    = REAR_BAND + PAD_D + FRONT_MG                    # 102.00
APRON_Y0   = -APRON_D
PAD_CY     = APRON_Y0 + FRONT_MG + PAD_D / 2                 # pad centre in y
CH_Y       = -REAR_BAND / 2                                  # the turn's centreline

# >>> THE APRON KEYS TO THE OUTSIDE OF THE PLINTH, BECAUSE THE INSIDE IS NOT OURS. <<<
# The first attempt put two tongues against the plinth's flat front span — and they occupied the
# stand's own volume, which the interference assert caught at 568 mm^3. There is nothing to key
# INTO: the only opening in that face is the cable arch, and a plug in it would sit exactly where
# the cable flattens (#29/#30). So the apron reaches back ALONGSIDE the stand instead. Two arms
# run up the plinth's flat side faces (flat for y = R..ST_D-R), locating x and y by embrace; the
# desk and the apron's own weight do z. The stand is untouched and can still be lifted straight out.
ARM_CLR = 0.30                            # per side: a slide fit, not a press fit
ARM_T   = 3.0                             # arm wall
ARM_H   = 6.0                             # from the desk up; stays under the cradle's overhang
ARM_L   = 26.0                            # reaches y = 26, inside the side face's flat span
assert ARM_L <= ST_D - ST_R, "arm would run past the stand's flat side into the rear corner radius"

# >>> NO RETAINING LIP, AND THAT IS MEASURED RATHER THAN ASSUMED. <<<
# The arms resist sliding and rotation in plan; they do nothing against vertical lift, and
# _check_geometry reports what that costs (~0.6 N at the front edge). The obvious hedge is a lip
# tucking under an overhang on the plinth — so the stand was measured for one, and it has none:
# desk_stand() is a constant 64.00 x 64.00 cross-section from z = -14 to well above the plinth.
# The only relief anywhere near the desk is the base chamfer, and it is 0.15 mm of inset half a
# millimetre up — too small to hook and the wrong shape (a 45 deg ramp sheds a lip rather than
# catching it). Inventing a ledge would mean modifying a validated part we may not touch, so the
# apron stays a shelf that lifts at ~60 g. Acceptable for playtest one, whose point is the game;
# if it annoys anyone on a table, rubber feet are the fix that needs no new geometry.


def _pad_pocket(z0, z1, grow=0.0):
    """The card-shaped prism, as a pocket or as a keepout probe."""
    sk = RectangleRounded(PAD_W + 2 * grow, PAD_D + 2 * grow, PAD_R + grow)
    return Pos(ST_W / 2, PAD_CY, z0) * extrude(sk, z1 - z0)


POCKET_TOP = PAD_FLOOR - SKIN_T           # the pocket's ceiling IS the underside of the skin

# >>> PRINT ORIENTATION: UNDERSIDE DOWN, NO SUPPORTS. DECIDED, NOT DEFAULTED. <<<
# The two candidates both cost something and this one costs less. Underside-down puts the whole
# footprint and both keying arms flat on the bed — nothing overhangs — at the price of one 40.5 mm
# bridge: the skin's underside spanning the reader pocket. Top-face-down would print the skin
# solid on the bed, but the pad recess becomes an 86.6 mm bridge 0.6 mm off the plate and the arms
# become unsupported cantilevers on a 3.0 x 6.0 mm face, so it trades one bridge for a bigger one
# plus supports. The bridge here sags on the POCKET side, where a tenth of a millimetre costs
# nothing; the card face is ten layers above it and prints clean. PRINT_LIFT puts the desk plane
# on z = 0 in the exported file, the same trick and the same reason as ember-stand's plinth.
PRINT_LIFT = PLINTH_H


# >>> THE BOARD SITS BEHIND THE SCALLOP'S REACH, AND THAT IS SOLVED. <<<
# Centring the board under the card put its front edge 7.25 mm behind the pad's front edge while
# the scallop reaches 11.0 mm past it, so the scallop — which cuts 1.2 mm INTO the pad floor, and
# the pad floor IS the skin — left 0.80 mm of skin over ~43 mm^2 of the board. That is worse than
# a thin spot: it re-creates the coil dependency this design claims to have removed, because
# "uniform skin over the whole footprint" was the entire argument for not needing the antenna's
# position. The pocket is therefore placed from the scallop's reach, not centred, so the two
# cannot drift apart again. There is slack at both ends to absorb it.
POCKET_CLR = 0.50                          # solid between the scallop's arc and the board's edge
POCKET_CY = (PAD_CY - PAD_D / 2) + SCALLOP_D / 2 + POCKET_CLR + READER_POCKET_W / 2


def _reader_pocket(z0, z1, grow=0.0):
    """The MFRC522's envelope, set back from the card's front edge — see POCKET_CY."""
    return E.bx(ST_W / 2 - READER_POCKET_L / 2 - grow, ST_W / 2 + READER_POCKET_L / 2 + grow,
                POCKET_CY - READER_POCKET_W / 2 - grow, POCKET_CY + READER_POCKET_W / 2 + grow,
                z0, z1)


def _cable_groove(z0, z1, grow=0.0):
    """The L: in from the stand's egress, then out through a side face. Open to the desk."""
    w = CH_W + 2 * grow
    # leg 1 — straight in from the plinth face, on the egress centreline
    leg_in = E.bx(EGRESS_CX - w / 2, EGRESS_CX + w / 2, CH_Y - w / 2, APRON_Y1 + 1.0, z0, z1)
    # the sweep: a generous pocket at the corner so an R18 cable turns instead of kinking
    corner = E.cyl(EGRESS_CX, CH_Y, z0, z1, CH_SWEEP + 2 * grow)
    # leg 2 — out to the side face
    x_out = (APRON_X1 + 1.0) if CABLE_SIDE > 0 else (APRON_X0 - 1.0)
    leg_out = E.bx(min(EGRESS_CX, x_out), max(EGRESS_CX, x_out),
                   CH_Y - w / 2, CH_Y + w / 2, z0, z1)
    return leg_in + corner + leg_out


def _cuts():
    """Every subtractive feature, named, so checks can probe ALL of them rather than the one
    somebody remembered. The scallop reached the skin because only the cable groove was ever
    tested against the keepouts."""
    x_out = (APRON_X1 + 1.0) if CONN_SIDE > 0 else (APRON_X0 - 1.0)
    return [
        ("pad pocket", _pad_pocket(PAD_FLOOR, TOP_Z + 1.0)),
        ("finger scallop", E.cyl(ST_W / 2, PAD_CY - PAD_D / 2, TOP_Z - SCALLOP_DZ, TOP_Z + 1.0, SCALLOP_D)),
        ("LED channel", _led_channel()),
        ("reader pocket", _reader_pocket(DESK_Z - 1.0, POCKET_TOP)),
        ("connector relief", E.bx(min(ST_W / 2, x_out), max(ST_W / 2, x_out),
                                  POCKET_CY - CONN_CH_W / 2, POCKET_CY + CONN_CH_W / 2,
                                  DESK_Z - 1.0, POCKET_TOP)),
        ("cable groove", _cable_groove(DESK_Z - 1.0, DESK_Z + CH_D)),
    ]


def _led_channel():
    ring_o = RectangleRounded(PAD_W + 2 * (WALL + LED_GAP + LED_W),
                              PAD_D + 2 * (WALL + LED_GAP + LED_W), PAD_R + WALL + LED_GAP + LED_W)
    ring_i = RectangleRounded(PAD_W + 2 * (WALL + LED_GAP),
                              PAD_D + 2 * (WALL + LED_GAP), PAD_R + WALL + LED_GAP)
    ring = Pos(ST_W / 2, PAD_CY, TOP_Z - LED_D) * extrude(ring_o - ring_i, LED_D + 1.0)
    front_cut = E.bx(APRON_X0 - 1, APRON_X1 + 1, APRON_Y0 - 1,
                     PAD_CY - PAD_D / 2 - WALL, TOP_Z - LED_D - 1, TOP_Z + 2)
    return ring - front_cut


def apron():
    """The shrine apron: envelope, card pad, LED channel, reader pocket, connector relief,
    cable groove and the arms that embrace the plinth."""
    p = E.rbox(APRON_X0, APRON_X1, APRON_Y0, APRON_Y1, DESK_Z, TOP_Z, APRON_R)

    # the card pad
    p -= _pad_pocket(PAD_FLOOR, TOP_Z + 1.0)

    # the finger scallop, cut from the pad's front wall so a thumb arrives along the desk
    p -= E.cyl(ST_W / 2, PAD_CY - PAD_D / 2, TOP_Z - SCALLOP_DZ, TOP_Z + 1.0, SCALLOP_D)

    # The LED channel, a later fit (0005). THREE-SIDED, not a ring: the finger scallop reaches
    # 11 mm past the pad's front edge and the channel runs 5.4 mm outside it, so a front run would
    # be severed by the scallop wherever it sat. A continuous ring and a front scallop are not
    # both possible on this face — LED_W/LED_D are provisional, so this is a decision to take with
    # the strip, not a defect to fix here. The rear and both sides are continuous.
    ring_o = RectangleRounded(PAD_W + 2 * (WALL + LED_GAP + LED_W),
                              PAD_D + 2 * (WALL + LED_GAP + LED_W), PAD_R + WALL + LED_GAP + LED_W)
    ring_i = RectangleRounded(PAD_W + 2 * (WALL + LED_GAP),
                              PAD_D + 2 * (WALL + LED_GAP), PAD_R + WALL + LED_GAP)
    ring = Pos(ST_W / 2, PAD_CY, TOP_Z - LED_D) * extrude(ring_o - ring_i, LED_D + 1.0)
    front_cut = E.bx(APRON_X0 - 1, APRON_X1 + 1, APRON_Y0 - 1,
                     PAD_CY - PAD_D / 2 - WALL, TOP_Z - LED_D - 1, TOP_Z + 2)
    p -= ring - front_cut

    # the reader pocket and its connector bundle channel, both open to the desk. The board is pushed UP
    # against the skin — the shortest coil-to-card distance the design allows — and the desk
    # closes the pocket. Playtest one is bare printed parts (materials.md), so retention is a
    # foam pad between board and desk rather than a part.
    p -= _reader_pocket(DESK_Z - 1.0, POCKET_TOP)
    x_out = (APRON_X1 + 1.0) if CONN_SIDE > 0 else (APRON_X0 - 1.0)
    p -= E.bx(min(ST_W / 2, x_out), max(ST_W / 2, x_out),
              POCKET_CY - CONN_CH_W / 2, POCKET_CY + CONN_CH_W / 2, DESK_Z - 1.0, POCKET_TOP)

    # the cable groove, open to the desk
    p -= _cable_groove(DESK_Z - 1.0, DESK_Z + CH_D)

    # keying arms, up the OUTSIDE of the plinth's side faces (see the note at ARM_CLR)
    for x_in, x_out in ((0.0 - ARM_CLR, 0.0 - ARM_CLR - ARM_T),
                        (ST_W + ARM_CLR, ST_W + ARM_CLR + ARM_T)):
        p += E.bx(min(x_in, x_out), max(x_in, x_out), 0.0, ARM_L, DESK_Z, DESK_Z + ARM_H)

    return E.chamfer_outline(p, TOP_Z, CHAMFER, "shrine apron top")


def _check_geometry(part=None):
    p = part if part is not None else apron()
    ok = []

    # 1. THE RF RULE, AS GEOMETRY. materials.md forbids a conductor in the coil's field; the
    #    cable groove is where the only conductor in this part lives. Nothing else here can
    #    catch this — a groove under the pad collides with nothing and looks perfectly fine.
    probe = _pad_pocket(DESK_Z - 2.0, TOP_Z + 2.0, grow=RF_KEEPOUT)
    bad = (_cable_groove(DESK_Z - 1.0, DESK_Z + CH_D) & probe).volume
    assert bad < 1e-6, (
        f"cable groove intrudes {bad:.3f} mm^3 into the pad footprint + {RF_KEEPOUT} mm keepout. "
        f"A USB lead's braided shield under the coil is the read failure materials.md names.")
    ok.append(f"[rf] cable groove clear of the pad footprint by >= {RF_KEEPOUT} mm")

    # 2. the card actually fits, derived rather than re-typed
    assert PAD_W - CR80_W == 2 * PAD_CLR and PAD_D - CR80_D == 2 * PAD_CLR
    ok.append(f"[card] pocket {PAD_W:.2f} x {PAD_D:.2f} for an {CR80_W} x {CR80_D} card "
              f"({PAD_CLR:.2f}/side, lip {LIP_H:.2f}, card proud {CR80_T - LIP_H:.2f})")

    # 3. the apron must not touch the stand it butts against — it is a separate part, and a
    #    part that overlaps its neighbour is a part that does not seat.
    inter = (p & E.desk_stand()).volume
    assert inter < 1e-6, f"apron interferes with the stand by {inter:.3f} mm^3"
    ok.append("[fit] no interference with desk_stand()")

    # 3b. MEASURED ENGAGEMENT, not the constant. The old check asserted 2*ARM_CLR <= 1.0, which
    #     is true with ARM_L = 0 — it would have passed a part with no arms at all. What matters
    #     is how much arm actually runs alongside a FLAT face: the plinth's side is flat only for
    #     y >= ST_R, so the first 10 mm of every arm faces the corner radius and grips nothing.
    flat = E.bx(APRON_X0 - 1, APRON_X1 + 1, ST_R, APRON_Y1 + ARM_L, DESK_Z, DESK_Z + ARM_H)
    engaged = (p & flat).volume / (ARM_T * ARM_H) / 2.0
    assert engaged >= 12.0, f"arms engage only {engaged:.1f} mm of flat plinth face"
    ok.append(f"[fit] arms engage {engaged:.0f} mm of FLAT plinth face each "
              f"({ARM_L:.0f} mm long, first {ST_R:.0f} faces the corner radius), "
              f"{ARM_CLR:.2f} mm/side slide fit")

    # 4. exactly one solid. An apron that severs at the hooks is two parts on the bed and the
    #    dimension checks above would all still pass — ember's own back-shell lesson.
    n = len(p.solids())
    assert n == 1, f"apron is {n} solids, must be exactly 1"
    ok.append("[mesh] exactly 1 solid")

    # 5. the RF skin, once the reader lands, must still be 1.5-2.0 mm under the card
    # 5. THE SKIN, MEASURED ON THE BUILT PART. The check this replaces was algebra: it computed
    #    PAD_FLOOR - POCKET_TOP and asserted it equalled SKIN_T, which are the two constants that
    #    DEFINE each other. It could not see geometry, so it printed a confident 2.00 while the
    #    finger scallop left 0.80 mm over 43 mm^2 of the board. Weigh the slab instead.
    nominal = READER_POCKET_L * READER_POCKET_W * SKIN_T
    slab = _reader_pocket(POCKET_TOP, PAD_FLOOR)
    actual = (p & slab).volume
    if abs(actual - nominal) >= 1e-6:
        culprit = [n for n, c in _cuts() if (c & slab).volume > 1e-6]
        raise AssertionError(
            f"skin over the board is {actual:.1f} mm^3 of a nominal {nominal:.1f} — "
            f"{nominal - actual:.1f} mm^3 removed by: {', '.join(culprit) or 'unknown'}")
    ok.append(f"[rf] skin over the board measured {actual:.0f} mm^3 = a full {SKIN_T:.2f} mm "
              f"everywhere on {READER_POCKET_L:.1f} x {READER_POCKET_W:.1f} (nominal {nominal:.0f})")

    # 5b. the reader must sit under the card, not merely under the apron
    pad_probe = _pad_pocket(POCKET_TOP - READER_POCKET_D, POCKET_TOP)
    out = (_reader_pocket(POCKET_TOP - READER_POCKET_D, POCKET_TOP) - pad_probe).volume
    assert out < 1e-6, f"{out:.1f} mm^3 of the reader pocket lies outside the card footprint"
    ok.append("[rf] reader pocket entirely under the card")

    # 5d. THE SKIN IS THE ONE STRUCTURAL RISK: 2.00 mm spanning a 60.5 x 40.5 hole, with a card
    #     pressed onto it. Asserted as a span/thickness relationship rather than left implied.
    #     It may use SKIN_T only because check 5 has just PROVEN the built part carries a full
    #     SKIN_T everywhere over the board — before that, this ratio inherited a blind constant
    #     and read 20.2 while the real figure at the scallop was 40.5/0.80 = 50.6.
    span = min(READER_POCKET_L, READER_POCKET_W)      # the short span governs a plate
    assert span / SKIN_T <= 21.0, (
        f"skin spans {span:.1f} mm at {SKIN_T:.2f} mm thick (ratio {span/SKIN_T:.1f}) — too slender")
    ok.append(f"[skin] span/thickness {span/SKIN_T:.1f} over the short span, on a skin measured "
              f"rather than assumed (the printed case runs {60.5/2.0:.1f} and holds)")

    # 5e. EVERY subtractive feature against the skin slab, not just the cable groove. The scallop
    #     got through because checks 1 and 5e only ever probed the groove; a feature nobody probes
    #     is a feature nobody checks, and the part still prints a reassuring line about it.
    for name, cut in _cuts():
        if name == "reader pocket":
            continue                        # it IS the void under the skin
        v = (cut & slab).volume
        assert v < 1e-6, f"{name} removes {v:.2f} mm^3 from the skin over the board"
    ok.append(f"[rf] all {len(_cuts()) - 1} other cuts probed against the skin slab: none enters it")

    # 5f. NOTHING MAY PUNCTURE THE LED CHANNEL. At LED_D = 5.0 its floor sat below POCKET_TOP and
    #     the connector relief (317 mm^3) and cable groove (16 mm^3) opened a continuous void from
    #     the desk to the top face — a light leak, a dust path, and the wiring on show from above.
    assert TOP_Z - LED_D > POCKET_TOP, (
        f"LED channel floor {TOP_Z - LED_D:.2f} is at or below the pocket ceiling {POCKET_TOP:.2f}")
    led = _led_channel()
    for name, cut in _cuts():
        if name == "LED channel":
            continue
        v = (cut & led).volume
        assert v < 1e-6, f"{name} punctures the LED channel ({v:.2f} mm^3)"
    ok.append(f"[led] channel floor {TOP_Z - LED_D - POCKET_TOP:.2f} mm above the pocket ceiling; "
              f"nothing punctures it (three-sided: a closed ring and a front scallop are exclusive)")

    # 5c. connector bundle and cable must not fight for the same corner
    assert CONN_SIDE == -CABLE_SIDE, "connector bundle and power cable leave on the same side"
    ok.append(f"[cable] connector leaves {'+x' if CONN_SIDE > 0 else '-x'} (the board's short "
              f"edge), power {'+x' if CABLE_SIDE > 0 else '-x'} — opposite faces")

    # 6. the scallop must stay inside the apron. A dish that breaches the front face is a notch
    #    in the rim, and nothing above can see it: it collides with nothing and fits everything.
    #    Measured through SOLID: the old line subtracted two numbers and reported the gap, which
    #    says nothing about whether material actually occupies it.
    reach = PAD_CY - PAD_D / 2 - SCALLOP_D / 2
    rim = E.bx(ST_W / 2 - 2, ST_W / 2 + 2, APRON_Y0, reach, TOP_Z - SCALLOP_DZ, TOP_Z)
    rim_v = (p & rim).volume
    assert rim_v > 0.9 * 4 * (reach - APRON_Y0) * SCALLOP_DZ, (
        f"the rim in front of the scallop is not solid ({rim_v:.1f} mm^3)")
    ok.append(f"[hand] scallop contained, {reach - APRON_Y0:.2f} mm of SOLID rim in front of it")

    # 7. the cable must be able to LEAVE. The groove is cut toward the side face, but "cut toward"
    #    is not "opens onto" — a margin change could leave it buried with every other check green.
    fx = APRON_X1 if CABLE_SIDE > 0 else APRON_X0
    face = E.bx(min(fx, fx + 0.5 * -CABLE_SIDE), max(fx, fx + 0.5 * -CABLE_SIDE),
                APRON_Y0 - 1, APRON_Y1 + 1, DESK_Z - 1, TOP_Z + 1)
    ap = (_cable_groove(DESK_Z - 1.0, DESK_Z + CH_D) & face).volume
    assert ap > 0.5 * CH_W * CH_D * 0.5, f"cable groove does not open onto the side face ({ap:.2f} mm^3)"
    ok.append(f"[cable] groove opens onto the {'+x' if CABLE_SIDE > 0 else '-x'} face, "
              f"{CH_W:.1f} x {CH_D:.1f} mm, turning inside the {REAR_BAND:.0f} mm rear band")

    # 8. TIPPING. The apron is non-bearing and only embraced, never hooked, so the question is
    #    not "does it hold the stand up" but "does normal handling move it". Downward force
    #    anywhere inside the footprint cannot tip it; the exposed case is lifting the front.
    try:
        com = p.center(CenterOf.MASS)
    except Exception:
        bb = p.bounding_box(); com = bb.center()
    mass_g = p.volume * 1.24e-3          # PLA ~1.24 g/cm^3, and volume is mm^3
    W = mass_g * 9.81e-3                 # newtons
    pivot_y = APRON_Y1 + ARM_L           # rearmost desk contact: the arm tips
    scallop_y = PAD_CY - PAD_D / 2
    lift_N = W * (pivot_y - com.Y) / (pivot_y - scallop_y)
    ok.append(f"[tip] {mass_g:.0f} g, CoM y={com.Y:.1f}; a downward press anywhere inside the "
              f"footprint cannot tip it; lifting the front edge takes {lift_N:.2f} N ({lift_N/9.81e-3:.0f} g)")
    return ok


if __name__ == "__main__":
    part = apron()
    bb = part.bounding_box()
    print(f"shrine apron  {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, "
          f"{part.volume / 1000:.1f} cm^3")
    for line in _check_geometry(part):
        print("  " + line)

    if _PENDING:
        print("\n⛔ NOT EXPORTED, and nothing is staged in the print queue.")
        print("   Pending: " + ", ".join(sorted(_PENDING)) + " — the header + dupont stack height.")
        print("   Everything else is measured and checked. The board's outline, depth, skin and")
        print("   connector edge come off the printed case; the coil's position is not needed")
        print("   because the skin is uniform over the whole board footprint. What is missing is")
        print("   how far a VERTICAL header with sockets on it stands above the PCB: pointing up")
        print("   it hits the 2.00 mm skin and the card, pointing down it hits the desk, and the")
        print("   printed case dodges the question by letting the stack out through a notch.")
        sys.exit(3)   # not success: this run produced no part

    raise SystemExit("export path not written yet — see the PENDING gate above")
