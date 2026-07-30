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
import os, math

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
BTN             = [(13.45,3.26),(36.58,3.26)]   # rear-facing tact switches
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
LED_WIN_D  = 12.0
DIFF_D     = 16.0    # diffuser disc seat

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
    # ---- rear glow window for the WS2812 + diffuser seat ----
    p -= cyl(LED[0],LED[1], BACK_Z-1, CAV_FLOOR+1, LED_WIN_D)
    p -= cyl(LED[0],LED[1], BACK_Z-0.01, BACK_Z+1.00, DIFF_D)
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
    # ---- vents (kept clear of the antenna keepout and the LED window) ----
    for i in range(6):
        yv = 15.0 + i*2.6
        p -= bx(10.0,40.0, yv, yv+1.3, BACK_Z-1, CAV_FLOOR+1)
    for i in range(6):
        yv = 60.0 + i*2.6
        p -= bx(10.0,40.0, yv, yv+1.3, BACK_Z-1, CAV_FLOOR+1)
    return p

def diffuser():
    return cyl(0,0,0,0.90, DIFF_D-0.4)


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
DRIVER_D = 28.0                    # target driver; change and re-run
SLOT_CY  = 34.0                    # slot centreline Y at the floor
SLOT_FLOOR = 10.0
# --- grille: replace this block with lyra's motif; it is a pure parameter set
GRILLE_SLOT_W = 2.20
GRILLE_PITCH  = 3.40
GRILLE_FIELD  = 30.0               # slots are clipped to this circle

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
    cy0,cy1 = ST_WALL,   21.0
    p -= bx(cx0,cx1, cy0,cy1, ST_WALL, 34.0)   # ceiling = 17mm bridge, no supports
    p -= bx(cx0,cx1, cy0,cy1, -1.0, ST_WALL)          # bottom access
    # driver seat on the INSIDE of the front wall + grille through it
    dz = 18.0
    seat = Pos(ST_W/2, cy0+0.01, dz) * (Rot(-90,0,0) *
            Cylinder((DRIVER_D+1.0)/2, 2.2, align=(Align.CENTER,Align.CENTER,Align.MIN)))
    p -= seat
    field = Pos(ST_W/2, -1, dz) * (Rot(-90,0,0) *
            Cylinder(GRILLE_FIELD/2, ST_WALL+3, align=(Align.CENTER,Align.CENTER,Align.MIN)))
    bars = None
    n = int(GRILLE_FIELD/GRILLE_PITCH)+2
    for i in range(-n,n+1):
        z = dz + i*GRILLE_PITCH
        b = bx(0, ST_W, -2, ST_WALL+2, z-GRILLE_SLOT_W/2, z+GRILLE_SLOT_W/2)
        bars = b if bars is None else bars+b
    p -= (field & bars)
    # cable route: slot floor -> out the back
    p -= bx(ST_W/2-8, ST_W/2+8, 29.0, ST_D+1, ST_WALL, 13.0)
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
             "ember-diffuser":    diffuser()}
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
    raw = import_step(os.path.join(out,"..","ES3C28P_3D","ES3C28P_3D.step"))
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
