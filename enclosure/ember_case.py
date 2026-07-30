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
USB_X           = (20.53, 29.47)    # USB-C body, centred on 25.00
USB_Z           = (-4.85, -1.60)
# Rear-facing tact switches. WHICH IS WHICH — settled on the bench, 2026-07-30, because
# nothing in the model could say. The vendor STEP carries designators for plenty of parts
# (C10, SD_CARD1, MOLEX1.25-…, the WS2812 library part) but contains NO K1/K2 and no switch
# part at all — the same export suppression that hid the mic hole. Twice that file has been
# silent on exactly the feature we needed.
#
# JP pressed both on the bare board: the one that raises the volume overlay is on the
# microSD side. SD_PLATE spans x 33.68..44.83, i.e. high-x, so:
#
#   x = 36.58  ->  K2 / BOOT / GPIO0  -- the ONLY readable input. Short press = volume
#                  overlay + step, long press = power menu. Gets the BIG hex cap.
#   x = 13.45  ->  K1 / RESET         -- hardwired to CHIP_PU, unreadable by firmware,
#                  reboots the MCU *and* the LCD. Gets the SMALL hex cap.
#
# ⚠️ Holding BOOT low ACROSS a reset enters ROM download mode, which looks like a brick.
# With two pressable caps that is reachable by accident, so neither cap may be able to
# stick depressed, and one thumb must not span both.
BTN             = [(13.45,3.26),(36.58,3.26)]
BTN_RESET_X     = 13.45              # small cap
BTN_BOOT_X      = 36.58              # big cap, the only readable switch
#
# >>> NEVER SPECIFY THESE AS "LEFT" OR "RIGHT". USE THE COORDINATES. <<<
#
# The apparent side flips between three figures of this same part:
#   case-back.svg          eye behind the part -> board +X appears on the viewer's LEFT
#                          (confirmed from the render: the mic at (40, 81.5) lands
#                          upper-left and the x=46 countersinks are the left-hand pair)
#   case-print-layout.svg  shell open-side-up -> mirrored back again, +X on the RIGHT
#   case-hero.png          a front view entirely
#
# So "big cap on the left" is true in one figure, false in another and meaningless in the
# third. Spec from the wrong one and the generous thumb-sized cap lands over the HARDWARE
# RESET — a device that reboots when you reach for the volume. Same discipline as the
# hostname rule in CLAUDE.md: the literal is the thing that silently goes stale, and a
# coordinate cannot be mirrored by a camera.
BTN_TIP_Z       = -4.10             # plunger tip (2.50mm below PCB back face)
LED             = (29.00, 45.60)    # WS2812B 5x5, on the BACK, fires rearward
ANT             = (17.57, 32.21, 80.04, 85.70)  # PCB antenna -- KEEPOUT, no metal
CONN_R         = [(32.54,40.19),(44.84,54.99),(62.69,72.84)]  # X=50 edge connectors
CONN_L         = [(21.07,25.32),(29.91,40.06)]                # X=0  edge connectors
SD_PLATE       = (33.68,44.83,15.84,29.99)  # microSD, simplified in the STEP

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
BUTTON_PAD_W = 11.0   # pad width  (X)
PAD_Y0, PAD_Y1 = 0.80, 10.30   # pad spans +Y only: the switches sit just 3.26mm
                               # from the board edge, so a centred pad would cut
                               # through the shell's bottom wall. Hinge at PAD_Y1.
HINGE_T    = 0.90    # living-hinge thickness
SLOT_W     = 0.60    # printed-in-place slot around the button pads
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


def cyl(x,y,z0,z1,d):
    return Pos(x,y,z0) * Cylinder(d/2, z1-z0,
                                  align=(Align.CENTER,Align.CENTER,Align.MIN))

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
    return p

# ============================================================================
# 5. BACK SHELL
# ============================================================================
def back_shell():
    p  = rbox(OX0,OX1,OY0,OY1, BACK_Z, SEAM_Z, OUT_R)
    # board + glass pocket, and the back-component cavity, in one cut
    p -= rbox(PK0,PK1,PY0,PY1, CAV_FLOOR, SEAM_Z+1, POCK_R)
    # screw standoffs up to the PCB back face
    for (hx,hy) in HOLES:
        p += cyl(hx,hy, CAV_FLOOR, PCB_BOT, BOSS_D)
        p -= cyl(hx,hy, BACK_Z-0.01, PCB_BOT+0.01, SCREW_D)
        p -= cone(hx,hy, BACK_Z-0.01, BACK_Z+1.70, 6.40, SCREW_D)   # countersink
    # ---- USB-C opening + cable relief (bottom short edge) ----
    p -= bx(18.0,32.0, OY0-1, PY0+0.5, -6.60,-0.60)
    p -= bx(15.5,34.5, OY0-1, OY0+1.6, -8.20, 0.40)      # outside relief for overmould
    # ---- side channels: connectors + microSD.  Deliberately generous. ----
    for (a,b) in [(14.0,40.5),(44.0,56.0),(62.0,75.0)]:
        p -= bx(BW+FIT-0.01, OX1+1, a,b, CAV_FLOOR, PCB_BOT)
    for (a,b) in [(14.0,26.0),(29.0,42.0)]:
        p -= bx(OX0-1, PK0+0.01, a,b, CAV_FLOOR, PCB_BOT)
    # ---- mic BACK relief: works whichever way the port faces ----
    p -= cyl(MIC[0],MIC[1], BACK_Z-1, CAV_FLOOR+0.01, 3.00)
    # ---- NO LED WINDOW, NO DIFFUSER ----
    # There used to be a 12mm bore over the WS2812 plus a 16mm seat for a printed
    # translucent disc. Both are gone: the fine hex field below passes straight over the
    # LED, so its light leaves through ~30 small holes instead of one big one. That is a
    # better diffuser than the diffuser was — many small apertures scatter, one large one
    # just shows you the die — and it deletes a part, a seat, and a second filament.
    # ---- printed-in-place button pushers ----
    pw = BUTTON_PAD_W
    for (cx,cy) in BTN:
        x0,x1 = cx-pw/2, cx+pw/2
        y0,y1 = PAD_Y0, PAD_Y1
        # U-slot: free on -Y and both +/-X, hinge stays on the +Y side
        p -= bx(x0-SLOT_W, x1+SLOT_W, y0-SLOT_W, y0, BACK_Z-1, CAV_FLOOR+1)
        p -= bx(x0-SLOT_W, x0,        y0-SLOT_W, y1, BACK_Z-1, CAV_FLOOR+1)
        p -= bx(x1,        x1+SLOT_W, y0-SLOT_W, y1, BACK_Z-1, CAV_FLOOR+1)
        # thin the hinge from the inside
        p -= bx(x0-SLOT_W, x1+SLOT_W, y1-0.5, y1+0.5, BACK_Z+HINGE_T, CAV_FLOOR+1)
        # pip that reaches the switch plunger
        p += cyl(cx,cy, CAV_FLOOR, BTN_TIP_Z-0.15, 4.00)
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
    p -= _hex_panel(9.0, 41.0, 11.0, 75.0, BACK_Z-1, CAV_FLOOR+1, 3.2, 0.8)
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
SLOT_CLR = 0.40
ST_W, ST_D, ST_H = 64.0, 64.0, 40.0
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
# --- grille: lyra-artist's hearth-wyrm dorsal ridge, RE-DERIVED for this field.
#
# An earlier comment here deferred the motif and gave the wrong reason ("changing open
# area while validating fit would confound two variables"). Fit is validated by the bezel
# and shell against the board; the stand's grille pattern is independent of it. The real
# obstacle was arithmetic:
#
#   lyra's motif as delivered:  11 spines, 50 x 15 field, 190 mm2 open
#   this grille needs:          37 x 24 field, ~673 mm2 open
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
GRILLE_STYLE  = "hex"
HEX_R         = 3.75     # circumradius
HEX_WEB       = 0.90     # material between hexes; the print floor
WYRM_ON       = False    # solid wyrm island in the grille field
GRILLE_RAKE   = 24.0     # degrees back from vertical, from lyra's motif
GRILLE_N      = 9
GRILLE_W0     = 3.20     # widest slot, at the head
GRILLE_TAPER  = 0.78     # narrowest / widest, toward the tail
GRILLE_SLOT_W = 2.20
GRILLE_SLOT_W = 2.20
GRILLE_PITCH  = 3.40
# Slots are clipped to the driver's RADIATING AREA, inset 1.5mm from its outline so
# the grille never opens onto the frame — an open slot over the flange is a dust path
# into the chamber and vents the enclosure it is meant to seal.
GRILLE_INSET  = 1.5
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
GRILLE_FLARE  = 0.60

def _hex_panel(x0, x1, y0, y1, z0, z1, aflat, web):
    """Fine hex lattice filling a rectangular patch, extruded through Z.

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
            h = Pos(hx, hy, z0) * extrude(RegularPolygon(R, 6), z1 - z0)
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
                    extrude(RegularPolygon(R, 6), d))
            out = h if out is None else out + h
    return out


def desk_stand():
    # Deliberately NOT chamfered.  A first attempt shaved the top-front at 38deg;
    # the render showed it eating into the driver seat and the grille field, which
    # both live on the front wall.  Generous R10 corners + the leaning slab give
    # the form; the front wall stays solid and predictable from z=0 to z=ST_H.
    p = rbox(0,ST_W, 0,ST_D, 0,ST_H, 10.0)
    # slab slot, leaning back by TILT
    slot = Box(SLAB_W+2*SLOT_CLR, SLAB_T+2*SLOT_CLR, 70,
               align=(Align.CENTER,Align.CENTER,Align.MIN))
    p -= Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) * slot)
    # sealed speaker chamber, open at the bottom (closed by the base plate)
    cx0,cx1 = ST_WALL+1, ST_W-ST_WALL-1
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
    cy0 = ST_WALL
    cy1 = ST_WALL + FRONT_GAP + DRIVER_T + PAD_PROUD + 2.0
    assert cy1 <= 24.0, f"chamber rear {cy1} would foul the slab slot at ~24.9"

    # Ceiling raised 34.0 -> 37.0 for the rectangular driver. At 34 the chamber was
    # 30mm tall and a 27mm driver left 1.5mm a side — no room for a seat lip. At 37 it
    # is 33mm tall, the seat clears by ~2.5mm, and the sealed volume goes 27.5 -> 30cm3,
    # which helps the low end rather than hurting it. Still 3mm of wall above (ST_H=40),
    # and no conflict with the slab slot: that sits at y~34 while the chamber ends at 21.
    p -= bx(cx0,cx1, cy0,cy1, ST_WALL, 37.0)   # ceiling = 17mm bridge, no supports
    p -= bx(cx0,cx1, cy0,cy1, -1.0, ST_WALL)          # bottom access
    # driver seat on the INSIDE of the front wall + grille through it
    # Centred in the taller chamber: (ST_WALL + 37.0) / 2
    dz = 20.5
    # TAPE PAD on the chamber's rear wall, standing PAD_PROUD off it so the adhesive
    # meets one continuous flat plane and nothing — no fillet, no print artefact at the
    # wall/floor junction — interrupts the bond. Added, not subtracted: this is the one
    # feature in the stand that is material rather than a void.
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
        bars = _hex_field(dz) + _hex_field(dz, flare=GRILLE_FLARE,
                                           depth=GRILLE_RECESS + 2.4)
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
    # end reached z = -4.98 — straight THROUGH the 4mm floor, leaving a 1099mm2 hole in the
    # underside and a bearing footprint of only 2911 of 4010mm2. The stand was standing on a
    # ring. Nothing detected it: the boolean check compares parts to the BOARD, and a hole in
    # the floor intersects nothing at all.
    #
    # The plug never needed it. Measured clearance was "past 20.7mm" for every plug size, and
    # 20.7 IS the floor — (SLOT_FLOOR - ST_WALL)/cos(TILT). So ending the well exactly at the
    # inner floor surface costs nothing and closes the hole for free.
    _wellDepth = (SLOT_FLOOR - ST_WALL) / math.cos(math.radians(TILT))
    p -= Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT,0,0) *
             Box(22.0, _wellY, _wellDepth, align=(Align.CENTER, Align.CENTER, Align.MAX)))
    # cable route: slot floor -> out the back
    p -= bx(ST_W/2-8, ST_W/2+8, 29.0, ST_D+1, ST_WALL, 13.0)
    # SPEAKER WIRE PASS-THROUGH. Caught by JP: the chamber had no exit at all. Its only
    # opening was the bottom, closed by the base plate — which is correct for a SEALED
    # enclosure and leaves the driver's own wires with nowhere to go. The board's
    # speaker header is on a long edge, so the wire has to reach the slab slot.
    #
    # This channel runs from inside the chamber (y=19, chamber ends at 21) rearward to
    # y=30, meeting the board cable route that starts at 29. From there the wire follows
    # the same path up to the slot. 6 x 5mm: enough for a 2-core lead, small enough to
    # seal.
    #
    # >>> IT MUST BE SEALED AFTER WIRING — a dab of silicone, hot glue or putty. <<<
    # An unsealed hole turns the sealed box into a leaky one and costs exactly the low
    # end the chamber exists to produce. Sizing it for a bead of sealant rather than
    # trying to make it wire-tight is deliberate: a press-fit hole that has to be forced
    # abrades the insulation.
    p -= bx(ST_W/2-3, ST_W/2+3, 19.0, 30.0, 6.0, 11.0)
    return p

def stand_base():
    return bx(ST_WALL+1.3, ST_W-ST_WALL-1.3, ST_WALL+0.3, 20.7, 0.4, ST_WALL)

# ============================================================================
# 6. build + verify
# ============================================================================
if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))
    parts = {"ember-front-bezel": front_bezel(),
             "ember-back-shell":  back_shell(),
             }
    try:
        parts["ember-stand"] = desk_stand()
        parts["ember-stand-base"] = stand_base()
    except Exception as e:
        print("!! stand failed:", e)
    for n,p in parts.items():
        bb = p.bounding_box()
        print(f"{n:20s} vol={p.volume/1000:7.2f} cm^3   "
              f"bbox {bb.size.X:6.2f} x {bb.size.Y:6.2f} x {bb.size.Z:6.2f}")
        export_stl(p, os.path.join(out, n+".stl"))
    print("\n--- BOOLEAN CLEARANCE CHECK vs vendor STEP ---")
    # Also anchored to this file, not to cwd: with `out` derived from the working directory,
    # `../ES3C28P_3D/` resolved outside the repo and the clearance check silently skipped.
    _step = os.path.join(_HERE, "..", "ES3C28P_3D", "ES3C28P_3D.step")
    if not os.path.exists(_step):
        _step = os.path.join(_HERE, "ES3C28P_3D", "ES3C28P_3D.step")
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


# ─────────────────────────────────────────────────────────────────────────────
# GEOMETRY ASSERTS. These are cheap and they encode the two faults JP found by
# looking at a render — the kind a boolean clearance check cannot catch, because
# nothing intersects: the stand was simply in front of the screen.
# ─────────────────────────────────────────────────────────────────────────────
def _bearing_footprint():
    """Material area in the stand's bottom 0.4mm, i.e. what it actually rests on."""
    st = desk_stand()
    probe = Pos(ST_W/2, ST_D/2, 0.0) * Box(ST_W, ST_D, 0.4,
                                           align=(Align.CENTER, Align.CENTER, Align.MIN))
    return (st & probe).volume / 0.4


def _check_geometry():
    import math
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
    # 2b. THE STAND MUST NOT STAND ON A RING.
    #
    # The USB-C well once ran 30mm down the tilted axis, reaching z = -4.98 and cutting
    # straight through the 4mm floor — a 273mm2 hole, bearing footprint 2911 of 4010mm2.
    # Nothing caught it, and the reason is the pattern this project keeps hitting: the
    # boolean check compares each part to the BOARD, and a hole in the floor intersects
    # nothing whatsoever. An absence cannot collide.
    #
    # The one opening that is intentional is the speaker chamber's bottom access, 54 x 15.3
    # = 826mm2, closed by ember-stand-base. So the floor is correct at ~3184mm2 of bearing
    # material, and the threshold is set just under that.
    _foot = _bearing_footprint()
    assert _foot >= 3150.0, (
        f"stand bearing footprint {_foot:.0f}mm2 — something is piercing the floor beyond "
        f"the speaker chamber's intentional 826mm2 access")

    # 3. the slot must still hold it
    assert engagement >= 12.0, f"slot engagement {engagement:.1f}mm is too shallow to retain the slab"
    return engagement, va_start, below


if __name__ == "__main__":
    _e, _v, _b = _check_geometry()
    print(f"  [geometry] engagement {_e:.1f}mm | VA starts {_v:.1f}mm | {_b:.1f}mm under for USB-C  OK")
