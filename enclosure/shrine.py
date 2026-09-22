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
# 3. PENDING — THE MFRC522.  NOTHING HERE IS GUESSED.
# ============================================================================
# JP is measuring the actual board with calipers. Until those land, the reader pocket, the coil
# keepout and the ribbon exit are UNKNOWN, and this file refuses to export a printable part.
# A guessed pocket is worse than no pocket: it looks finished and is wrong by an unknown amount.
READER_L      = None   # board outline length, mm
READER_W      = None   # board outline width, mm
READER_T      = None   # board thickness over its tallest component on the pad side, mm
COIL_L        = None   # coil ACTIVE area, which is not the board outline
COIL_W        = None
RIBBON_SIDE   = None   # "left" | "right" | "rear" — sets which way the ribbon leaves the pocket
READER_MOUNT  = None   # "screws" | "clips" | "pocket+lid"
_PENDING = {k: v for k, v in list(globals().items())
            if k.startswith(("READER_", "COIL_", "RIBBON_")) and v is None}

# The skin over the coil: materials.md says 1.5-2 mm of PLA/wood/resin, nothing conductive.
SKIN_T = 1.75                             # mid-band; the pad floor IS this skin where the coil sits
assert 1.5 <= SKIN_T <= 2.0, "materials.md fixes the RF skin at 1.5-2.0 mm"

# ============================================================================
# 4. THE APRON PLAN
# ============================================================================
WALL      = 2.4                           # outer wall / lip wall around the pad
LED_GAP   = 3.0                           # solid between pad wall and LED channel
LED_W     = 6.0                           # channel width — sized for a 5 mm WS2812 strip. PROVISIONAL:
LED_D     = 5.0                           # confirm the strip before printing; it is a later fit (0005)
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
APRON_T   = 12.0
assert APRON_T >= FLOOR_T + TUCK_D + CH_CEIL, "apron too thin to carry the cable groove"
assert APRON_T >= SKIN_T + LIP_H + 2.0, "apron too thin to carry the pad skin"

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
CABLE_SIDE = +1                           # +1 = exits +x, -1 = exits -x. PENDING the ribbon exit:
                                          # the two should leave on opposite sides.
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
APRON_D    = REAR_BAND + PAD_D + FRONT_MG                    # 97.00
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


def _pad_pocket(z0, z1, grow=0.0):
    """The card-shaped prism, as a pocket or as a keepout probe."""
    sk = RectangleRounded(PAD_W + 2 * grow, PAD_D + 2 * grow, PAD_R + grow)
    return Pos(ST_W / 2, PAD_CY, z0) * extrude(sk, z1 - z0)


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


def apron():
    """The shrine apron. Reader pocket omitted while the MFRC522 is unmeasured — see _PENDING."""
    p = E.rbox(APRON_X0, APRON_X1, APRON_Y0, APRON_Y1, DESK_Z, TOP_Z, APRON_R)

    # the card pad
    p -= _pad_pocket(PAD_FLOOR, TOP_Z + 1.0)

    # the finger scallop, cut from the pad's front wall so a thumb arrives along the desk
    p -= E.cyl(ST_W / 2, PAD_CY - PAD_D / 2, TOP_Z - SCALLOP_DZ, TOP_Z + 1.0, SCALLOP_D)

    # the LED ring channel, a later fit (0005): a groove following the pad, open at the top
    ring_o = RectangleRounded(PAD_W + 2 * (WALL + LED_GAP + LED_W), PAD_D + 2 * (WALL + LED_GAP + LED_W), PAD_R + WALL + LED_GAP + LED_W)
    ring_i = RectangleRounded(PAD_W + 2 * (WALL + LED_GAP), PAD_D + 2 * (WALL + LED_GAP), PAD_R + WALL + LED_GAP)
    p -= Pos(ST_W / 2, PAD_CY, TOP_Z - LED_D) * extrude(ring_o - ring_i, LED_D + 1.0)

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

    # 3b. the arms must actually embrace the stand — a clearance that grew until the arms miss
    #     the sides entirely would satisfy check 3 perfectly, which is the point of asserting it.
    span = 2 * ARM_CLR
    assert span <= 1.0, f"arm clearance {span:.2f} mm total — the apron would wander on the stand"
    ok.append(f"[fit] arms embrace the plinth, {ARM_CLR:.2f} mm/side slide fit, {ARM_L:.0f} mm long")

    # 4. exactly one solid. An apron that severs at the hooks is two parts on the bed and the
    #    dimension checks above would all still pass — ember's own back-shell lesson.
    n = len(p.solids())
    assert n == 1, f"apron is {n} solids, must be exactly 1"
    ok.append("[mesh] exactly 1 solid")

    # 5. the RF skin, once the reader lands, must still be 1.5-2.0 mm under the card
    ok.append(f"[rf] pad skin budget {SKIN_T:.2f} mm (reader pocket pending)")

    # 6. the scallop must stay inside the apron. A dish that breaches the front face is a notch
    #    in the rim, and nothing above can see it: it collides with nothing and fits everything.
    reach = PAD_CY - PAD_D / 2 - SCALLOP_D / 2
    assert reach >= APRON_Y0 + 1e-9, (
        f"finger scallop reaches y={reach:.2f}, past the apron's front face at {APRON_Y0:.2f}")
    ok.append(f"[hand] scallop contained, {reach - APRON_Y0:.2f} mm of rim in front of it")

    # 7. the cable must be able to LEAVE. The groove is cut toward the side face, but "cut toward"
    #    is not "opens onto" — a margin change could leave it buried with every other check green.
    face = E.bx(APRON_X1 - 0.5, APRON_X1, APRON_Y0 - 1, APRON_Y1 + 1, DESK_Z - 1, TOP_Z + 1)
    ap = (_cable_groove(DESK_Z - 1.0, DESK_Z + CH_D) & face).volume
    assert ap > 0.5 * CH_W * CH_D * 0.5, f"cable groove does not open onto the side face ({ap:.2f} mm^3)"
    ok.append(f"[cable] groove opens onto the {'+x' if CABLE_SIDE > 0 else '-x'} face, "
              f"{CH_W:.1f} x {CH_D:.1f} mm, turning inside the {REAR_BAND:.0f} mm rear band")
    return ok


if __name__ == "__main__":
    part = apron()
    bb = part.bounding_box()
    print(f"shrine apron  {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, "
          f"{part.volume / 1000:.1f} cm^3")
    for line in _check_geometry(part):
        print("  " + line)

    if _PENDING:
        print("\n⛔ NOT EXPORTED — the MFRC522 is unmeasured, so the reader pocket does not exist.")
        print("   Pending: " + ", ".join(sorted(_PENDING)))
        print("   This part is the apron BLANK: envelope, pad, lip, scallop, LED channel, cable")
        print("   groove and hooks. It is reviewable and previewable; it is not printable.")
        sys.exit(0)

    raise SystemExit("export path not written yet — see the PENDING gate above")
