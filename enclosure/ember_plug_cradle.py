"""
Ember desk-stand CAPTIVE USB-C PLUG CRADLE (#49) — one-handed dock insertion
============================================================================
Parametric source.  Run:  ./cadenv/bin/python ember_plug_cradle.py
Outputs ONE small STL (ember-plug-cradle.stl) through the same gated commit as the
other parts: nothing lands on disk unless every check below passes first.

WHAT THIS IS. The stand's USB-C well was sized for a plug a HAND holds; this insert
press-fits into that well and holds the plug itself, connector-up, at exactly the height
where lowering the slab into the slot mates USB-C blind. The slot supplies lateral
alignment (its own clearance is inside USB-C's lead-in capture — asserted below, not
assumed); this part supplies height and grip. Docking becomes one-handed.

WHY A SEPARATE PART AND NOT A RESHAPED WELL — the issue (#49) already argues it: plug
heads vary per cable, so the geometry that grips one is per-cable geometry. The stand is
a 5.4 h print; this is a ~15 min one. Iterate here, never there.

>>> ⚠️ FOUR NUMBERS BELOW ARE ASSUMED, NOT MEASURED — DO NOT PRINT BEFORE CALIPERS. <<<
PLUG_W / PLUG_T / PLUG_L / TIP_TO_FACE describe JP's actual cable's overmold and are
typed from "a typical chunky USB-C lead", exactly the standing CABLE_OD already has in
ember_case.py. Every derived height in this file moves with them. The asserts turn a
wrong measurement into a failed build rather than a wrong part — but only measurement
makes the part RIGHT. BOOT_D / BOOT_L have the same standing.

THE EXTRACTION-FORCE PROBLEM, STATED HONESTLY (issue #49 item 2). USB-C extraction is
~8–20 N and ~170 g of stand is ~1.7 N. This v1 ships posture (a): grip LIGHT, so
one-handed *insertion* (the actual ask) works and *removal* is two-handed — steady the
stand, lift the slab. The grip knob is GRIP_PROUD; raising it toward posture (c) is a
measurement decision (JP's, with a spring scale), not a vibes decision. The cradle
cannot out-pull the connector AND stay a cradle unless the stand is also held down —
(b) mass in the base — so the knob alone never "solves" undocking.

COORDINATES: the part is modelled in the WELL'S OWN FRAME, printed exactly as modelled:
z = 0 is the well's inner floor (the part stands on the 2 mm rim the tail corridor
leaves), +z runs UP the tilt axis toward the slot, x spans the stand's width, +y is
REARWARD along the slab thickness — the same local frame ember_case.py cuts the well
in, so every constant imported from there drops in without a sign flip.

Y DATUM IS THE WELL'S REAR WALL. The body is 2·FIT_CLR narrower than the well; two
front-face ribs press it rear-flush, so the pocket is modelled FIT_CLR forward of where
it must land (PC_B below) and lands on the port axis when seated. The plug then floats
REARWARD only (rear of pocket is open — see LOADING), and that float is asserted inside
USB-C's own capture so the receptacle centres the plug on the way down. Float is the
self-alignment, not slop.

LOADING. The pocket and the boot channel are open through the REAR face, full height:
the plug slides in sideways with its cable already hanging below (a top-down drop is
impossible — the far end of the cable is a wall wart). Feed the cable's free end down
the well and out the front egress arch first, exactly as today; then plug into insert,
insert into well, press home. The well's rear wall closes the pocket when seated.
"""
from build123d import *
import math, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import ember_case as E

# ============================================================================
# 1. WHAT IS IMPORTED — the dependency as a list, not a grep (ember_mobile's rule)
# ============================================================================
WELL_W, WELL_Y, WELL_DEPTH = E.WELL_W, E.WELL_Y, E.WELL_DEPTH   # 22.0 / 12.0 / 20.706
PORT_PC, PORT_ZFACE = E.PORT_PC, E.PORT_ZFACE                   # +2.225 / 2.582
TILT, ST_W, SLOT_CY, SLOT_FLOOR = E.TILT, E.ST_W, E.SLOT_CY, E.SLOT_FLOOR
TAIL_W, TAIL_Y = E.TAIL_W, E.TAIL_Y                             # 18.0 / 8.0
CABLE_OD, CABLE_RIGID = E.CABLE_OD, E.CABLE_RIGID               # 4.5 (⚠️ assumed) / 40.0
USBC_W, USBC_H = E.USBC_W, E.USBC_H                             # 10.54 / 4.85 case opening

# ============================================================================
# 2. THE PLUG — ⚠️ EVERY NUMBER IN THIS BLOCK NEEDS JP'S CALIPERS (#49 item 3)
# ============================================================================
PLUG_W      = 10.5   # ⚠️ ASSUMED — overmold width, across the stand's x
PLUG_T      = 5.5    # ⚠️ ASSUMED — overmold thickness, along the slab's thickness
PLUG_L      = 16.0   # ⚠️ ASSUMED — overmold length, connector face -> boot neck
TIP_TO_FACE = 10.0   # ⚠️ ASSUMED — shell tip -> overmold face. Sets the SEAT HEIGHT
                     #   directly: 1 mm of error here is 1 mm of mating error. The
                     #   receptacle is recessed PORT_ZFACE (2.58) behind the case edge,
                     #   so any cable that fully mates this board has TIP_TO_FACE >~ 9.1
                     #   — asserted below, a shorter head can't reach today by hand either.
BOOT_D      = 6.5    # ⚠️ ASSUMED — strain-relief boot OD at the overmold
BOOT_L      = 8.0    # ⚠️ ASSUMED — boot length below the overmold
# The USB-C plug SHELL is spec, not per-cable, and it is only a phantom here:
SHELL_W, SHELL_T = 8.4, 2.6
MATE_DEPTH   = 6.5   # spec-nominal shell engagement when fully seated
MATE_BACKOFF = 0.30  # deliberate UNDER-mating: the slab must bottom on the slot floor,
                     # never hang on the connector — a slab held proud rocks, and USB-C
                     # has wipe to spare. Docked engagement is MATE_DEPTH - this.

# ============================================================================
# 3. THE PART'S OWN KNOBS
# ============================================================================
FIT_CLR    = 0.15    # per-side body-to-well clearance; the ribs, not the body, do the fit
TOP_RECESS = 0.30    # top face below the slot-floor plane, so the docking slab can never
                     # rest on the insert instead of the slot floor
POCKET_CLR = 0.15    # per-side pocket-to-overmold clearance
GRIP_PROUD = POCKET_CLR + 0.10   # grip ribs reach 0.10/side INTO the overmold: posture (a),
                     # light. THE EXTRACTION KNOB — raise only with a spring scale in hand.
BOOT_W     = 7.0     # boot channel width; must beat BOOT_D, and the seat ledges are what
                     # remains of the pocket floor either side of it
RIB_R      = 0.5
RIB_PROUD_X     = 0.25              # 0.10/side crush against the well's x walls
RIB_PROUD_FRONT = 2*FIT_CLR + 0.10  # 0.40: takes up the whole y clearance + 0.10 crush,
                                    # pressing the body rear-flush = the y datum

BODY_W = WELL_W - 2*FIT_CLR         # 21.70
BODY_Y = WELL_Y - 2*FIT_CLR         # 11.70
INS_H  = WELL_DEPTH - TOP_RECESS    # 20.41
YSHIFT = FIT_CLR                    # body centre -> well centre once pressed rear-flush
PC_B   = PORT_PC - YSHIFT           # 2.075 — the port axis in the BODY's frame

# ============================================================================
# 4. THE SEAT HEIGHT — the whole point of the part, derived, never typed
# ============================================================================
# Distances run ALONG the tilt axis, measured DOWN from the well mouth plane (where the
# docked slab's bottom edge lands — dock_pose maps board OY0 exactly there):
#     receptacle mouth sits PORT_ZFACE ABOVE the mouth plane
#     mated shell tip   sits MATE_DEPTH - MATE_BACKOFF above the receptacle mouth
#     overmold face     = tip - TIP_TO_FACE            (below the mouth plane: s_face)
#     overmold bottom   = face + PLUG_L  ->  THE SEAT
# Full mating therefore completes exactly as the slab bottoms on the slot floor (less the
# deliberate backoff) — that identity is the design, and check [mate] below proves it on
# solids rather than trusting this prose.
_mate_eff = MATE_DEPTH - MATE_BACKOFF                     # 6.20
s_face = TIP_TO_FACE - _mate_eff - PORT_ZFACE             # 1.218 below the mouth plane
SEAT_Z = WELL_DEPTH - (s_face + PLUG_L)                   # 3.488 above the well floor
TIP_Z  = WELL_DEPTH + PORT_ZFACE + _mate_eff              # 29.49 — mated tip, well frame

# ---- the asserts that make a wrong caliper number a FAILED BUILD, not a wrong part ----
assert TIP_TO_FACE >= PORT_ZFACE + 5.0, (
    f"TIP_TO_FACE={TIP_TO_FACE} cannot reach a receptacle recessed {PORT_ZFACE:.2f} behind "
    f"the case edge with >=5mm engagement — this cable cannot mate this board by hand either; "
    f"re-measure before blaming the cradle")
assert s_face >= TOP_RECESS + 0.20, (
    f"the overmold face sits {s_face:.2f} below the mouth plane — above the insert's top "
    f"face. The docking slab would land ON THE OVERMOLD instead of the slot floor")
assert SEAT_Z >= 1.0, (
    f"seat lands {SEAT_Z:.2f} above the well floor — this overmold ({PLUG_L}) is too long "
    f"for an in-well seat and needs a spigot down the tail corridor: a DIFFERENT PART. "
    f"Measure first, then redesign; do not shave this assert")
assert PORT_PC + PLUG_T/2 + POCKET_CLR <= WELL_Y/2, (
    f"an overmold {PLUG_T} thick on an axis {PORT_PC:.2f} rearward does not fit the well's "
    f"{WELL_Y} — that is a STAND change (well reshape, 5.4h reprint), JP's call, not a knob")
# rear float: pocket rear is open, so the plug can drift rearward to the well wall. The
# receptacle centres it on the way down ONLY if that drift stays inside USB-C capture.
_float_rear = WELL_Y/2 - (PORT_PC + PLUG_T/2)             # 1.025
_capture_y  = (USBC_H - SHELL_T)/2                        # 1.125 — case-opening capture
assert _float_rear <= _capture_y, (
    f"plug can float {_float_rear:.2f} rearward but the case opening only captures "
    f"{_capture_y:.2f} — blind mating would jam on the case face. Close the gap with a "
    f"thicker-overmold measurement or a rear tongue, with calipers in hand")
assert BOOT_W >= BOOT_D + 0.4, f"boot channel {BOOT_W} pinches a {BOOT_D} boot"
_ledge = (PLUG_W + 2*POCKET_CLR - BOOT_W)/2               # 1.90
assert _ledge >= 1.2, (
    f"seat ledges are {_ledge:.2f} — under 1.2 they are fins carrying the full 5-20N "
    f"docking push. Narrow BOOT_W or re-measure PLUG_W")
assert (BODY_W - (PLUG_W + 2*POCKET_CLR))/2 >= 2.0, "pocket side walls under 2mm"
_pocket_y0 = PC_B - PLUG_T/2 - POCKET_CLR                 # -0.825, pocket front face
assert _pocket_y0 - (-BODY_Y/2) >= 2.0, "pocket front wall under 2mm"
_chan_y0 = PC_B - BOOT_D/2 - 1.8    # boot channel front: BOOT clearance + 1.8mm of forward
                                    # deflection room — below the well floor the corridor's
                                    # rear wall (TAIL_Y/2 < the boot's rear reach) pushes the
                                    # flexible boot FORWARD, and it needs somewhere to go
assert _chan_y0 - (-BODY_Y/2) >= 2.0, "channel front wall under 2mm"


def plug_cradle():
    """The insert, in the well frame described above, z0 = the well's inner floor."""
    pocket_w = PLUG_W + 2*POCKET_CLR
    body = extrude(RectangleRounded(BODY_W, BODY_Y, 0.8), INS_H)
    # bottom chamfer: elephant's foot on a press-fit part IS the press fit failing — the
    # flare would wedge against the well walls before the body reaches its floor datum.
    body = chamfer(body.edges().group_by(Axis.Z)[0], 0.3)
    # top chamfer: the edge a fingertip (and the sliding plug) meets first
    body = chamfer(body.edges().group_by(Axis.Z)[-1], 0.5)
    # THE POCKET — open through the rear face (LOADING, above). +1 overshoots so the cut
    # face never coincides with the body face (coincident faces are the bezel's 3
    # non-manifold edges all over again).
    body -= Pos(0, _pocket_y0, SEAT_Z) * Box(
        pocket_w, (BODY_Y/2 - _pocket_y0) + 1.0, (INS_H - SEAT_Z) + 1.0,
        align=(Align.CENTER, Align.MIN, Align.MIN))
    # THE BOOT CHANNEL — under the seat, also rear-open, wider FORWARD than the pocket so
    # the boot can deflect forward where the tail corridor's rear wall will push it.
    body -= Pos(0, _chan_y0, -1.0) * Box(
        BOOT_W, (BODY_Y/2 - _chan_y0) + 1.0, SEAT_Z + 1.0,
        align=(Align.CENTER, Align.MIN, Align.MIN))
    return body


def _grip_ribs():
    """Vertical ribs on the pocket's x walls, bearing GRIP_PROUD - POCKET_CLR into the
    overmold's flanks. Round, so the side-loaded plug cams over them instead of catching.
    SEPARATE from the bare body for the same reason the outer ribs are: they are the one
    interior feature DESIGNED to interfere with the plug, and the checks below measure
    that bite as its own number instead of letting it pollute the pocket's zero."""
    pocket_w = PLUG_W + 2*POCKET_CLR
    gx = pocket_w/2 - GRIP_PROUD + RIB_R          # embeds 2R-GRIP_PROUD into the wall
    ribs = None
    for sx in (-1, 1):
        for gy in (PC_B - 1.5, PC_B + 1.5):
            r = Pos(sx*gx, gy, SEAT_Z) * Cylinder(
                RIB_R, INS_H - SEAT_Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
            ribs = r if ribs is None else ribs + r
    return ribs


def _outer_ribs():
    """Press-fit ribs, SEPARATE from the body on purpose: the boolean checks below prove
    the body proper clears the well exactly, and the ribs — the one thing DESIGNED to
    interfere — are measured as their own number instead of polluting that zero.
    Each rib is a cone-tipped cylinder: the cone is the lead-in that lets the part start
    into the well before the crush begins (the insert enters bottom-first)."""
    ribs = None
    def rib(ax, ay):
        c = (Pos(ax, ay, 1.0) * Cone(0.1, RIB_R, 0.9,
                                     align=(Align.CENTER, Align.CENTER, Align.MIN)) +
             Pos(ax, ay, 1.9) * Cylinder(RIB_R, INS_H - 0.8 - 1.9,
                                         align=(Align.CENTER, Align.CENTER, Align.MIN)))
        return c
    for sx in (-1, 1):                                    # x walls: centring crush
        for ry in (-3.0, 3.0):
            r = rib(sx*(BODY_W/2 - RIB_R + RIB_PROUD_X), ry)
            ribs = r if ribs is None else ribs + r
    for rx in (-3.0, 3.0):                                # front wall: the rear-flush datum
        ribs += rib(rx, -(BODY_Y/2) + RIB_R - RIB_PROUD_FRONT)
    return ribs


def plug_phantom_rigid():
    """Shell + overmold at the MATED position, well frame. RIGID: must clear everything
    (except the grip ribs, whose bite is measured separately)."""
    return (Pos(0, PORT_PC, SEAT_Z + PLUG_L) * Box(
                SHELL_W, SHELL_T, TIP_Z - (SEAT_Z + PLUG_L),
                align=(Align.CENTER, Align.CENTER, Align.MIN)) +
            Pos(0, PORT_PC, SEAT_Z) * Box(
                PLUG_W, PLUG_T, PLUG_L,
                align=(Align.CENTER, Align.CENTER, Align.MIN)))


def plug_phantom_flex():
    """Boot + the rest of the measured 40mm rigid run. FLEXIBLE members: their
    interference with the stand below the well floor is reported, not asserted — the
    boot deflects forward off the tail corridor's rear wall, exactly as a hand-inserted
    plug's does today. A number here is information for JP's calipers, not a defect."""
    z_boot = SEAT_Z - BOOT_L
    z_end  = TIP_Z - CABLE_RIGID
    return (Pos(0, PORT_PC, z_boot) * Cone(CABLE_OD/2, BOOT_D/2, BOOT_L,
                align=(Align.CENTER, Align.CENTER, Align.MIN)) +
            Pos(0, PORT_PC, z_end) * Cylinder(CABLE_OD/2, z_boot - z_end,
                align=(Align.CENTER, Align.CENTER, Align.MIN)))


def place_in_stand(part, yshift=0.0, axial=0.0):
    """Well frame -> stand (cradle) frame. `yshift` is the assembled rear-flush offset
    (YSHIFT for the insert, 0 for phantoms, which are modelled on the true axis);
    `axial` displaces along the tilt axis — the checks' controls push through it."""
    return Pos(ST_W/2, SLOT_CY, SLOT_FLOOR) * (Rot(-TILT, 0, 0) *
           (Pos(0, yshift, -WELL_DEPTH + axial) * part))


if __name__ == "__main__":
    assert E._selftest_export_gate()
    out = _HERE
    _committed = False
    name = "ember-plug-cradle"

    print(f"seat derivation: face {s_face:.3f} below mouth | seat {SEAT_Z:.3f} above well "
          f"floor | mated tip {TIP_Z - WELL_DEPTH:.2f} above mouth | engagement {_mate_eff:.2f}")

    bare = plug_cradle()
    body = bare + _grip_ribs()
    insert = body + _outer_ribs()
    assert len(insert.solids()) == 1, (
        f"insert is {len(insert.solids())} solids — a rib failed to fuse and would rattle "
        f"loose on the bed (the back shell's severed-hinge lesson, same instrument)")

    import atexit
    atexit.register(lambda: None if _committed else (
        E._discard_partials(out, [name]),
        print("\n!! BUILD DID NOT PASS — nothing committed, no debris. The .stl on disk "
              "is the previous good one, untouched.")))

    bb = insert.bounding_box()
    print(f"{name:20s} vol={insert.volume/1000:7.2f} cm^3   "
          f"bbox {bb.size.X:6.2f} x {bb.size.Y:6.2f} x {bb.size.Z:6.2f}")
    assert abs(bb.min.Z) < 1e-6, f"exports with min Z = {bb.min.Z:.4f}, not on the bed"
    export_stl(insert, os.path.join(out, name + E.STL_TMP))

    print("\n--- MESH CHECK (the STL itself, not the solid) ---")
    _t, _b, _nm, _dd = E._check_manifold(os.path.join(out, name + E.STL_TMP))
    print(f"  {name:20s} {_t:6d} tris   boundary {_b:2d}   non-manifold {_nm:2d}   "
          f"{'watertight' if (_b == 0 and _nm == 0) else 'REGRESSION'}")
    assert _b == 0 and _nm == 0, "open or non-manifold edges in a brand-new simple prism"

    print("\n--- BOOLEAN CHECKS vs the stand, the docked slab, and the plug ---")
    # The board STEP never comes near this part (everything of the board's is PORT_ZFACE
    # above the mouth plane; the insert stops TOP_RECESS below it) — a board boolean here
    # would be the check that cannot fail. The mates that CAN collide are the stand, the
    # docked slab, and the plug itself, so those are what get measured.
    stand = E.desk_stand()
    slab = E.dock_pose(Pos(E.OX0, E.OY0, E.BACK_Z) *
                       Box(E.OX1 - E.OX0, E.OY1 - E.OY0, E.FRONT_Z - E.BACK_Z,
                           align=(Align.MIN, Align.MIN, Align.MIN)))
    rigid, flex = plug_phantom_rigid(), plug_phantom_flex()

    def vol(a, b):
        try: return (a & b).volume
        except Exception: return 0.0

    _v = vol(place_in_stand(body, YSHIFT), stand)
    print(f"  body vs stand           {_v:9.3f} mm^3   {'CLEAR' if _v < 0.01 else '*** COLLISION ***'}")
    assert _v < 0.01, f"the body proper must clear the well exactly; only ribs may bite ({_v:.3f})"
    _vr = vol(place_in_stand(insert, YSHIFT), stand)
    print(f"  ribs' designed bite     {_vr:9.3f} mm^3   (the press fit, as a number)")
    assert 0.2 < _vr < 10.0, (
        f"rib bite {_vr:.3f} mm^3 out of range — under 0.2 the part rattles, over 10 it "
        f"shaves or cracks the well walls going in")
    _vs = vol(place_in_stand(insert, YSHIFT), slab)
    print(f"  insert vs docked slab   {_vs:9.3f} mm^3   {'CLEAR' if _vs < 0.01 else '*** COLLISION ***'}")
    assert _vs < 0.01, "the docking slab lands on the insert, not the slot floor"
    _vp = vol(place_in_stand(rigid, 0.0), place_in_stand(bare, YSHIFT))
    print(f"  rigid plug vs bare body {_vp:9.3f} mm^3   {'CLEAR' if _vp < 0.01 else '*** COLLISION ***'}")
    assert _vp < 0.01, "the pocket does not clear the overmold it exists to hold"
    _vg = vol(place_in_stand(rigid, 0.0), place_in_stand(insert, YSHIFT)) - _vp
    print(f"  grip ribs' bite         {_vg:9.3f} mm^3   (posture (a): light, the knob is GRIP_PROUD)")
    assert 0.02 < _vg < 5.0, f"grip bite {_vg:.3f} mm^3 — the plug is either loose or hammered in"
    _vrs = vol(place_in_stand(rigid, 0.0), stand)
    print(f"  rigid plug vs stand     {_vrs:9.3f} mm^3   {'CLEAR' if _vrs < 0.01 else '*** COLLISION ***'}")
    assert _vrs < 0.01, "the mated overmold/shell fouls the stand itself"
    _vf = vol(place_in_stand(flex, 0.0), stand) + vol(place_in_stand(flex, 0.0),
                                                      place_in_stand(insert, YSHIFT))
    print(f"  flex boot/cable bite    {_vf:9.3f} mm^3   (INFO — flexible members deflect "
          f"forward off the corridor wall, as today's hand-inserted plug does)")

    # [mate] the derivation, proved on solids: the mated shell must penetrate the slab
    # envelope by exactly its above-mouth run x its cross-section.
    _vm = vol(place_in_stand(rigid, 0.0), slab)
    _expect = SHELL_W * SHELL_T * (PORT_ZFACE + _mate_eff)
    print(f"  [mate] shell into slab  {_vm:9.3f} mm^3   expected {_expect:9.3f}")
    assert abs(_vm - _expect) < 2.0, (
        f"the mated shell penetrates the slab envelope by {_vm:.2f} mm^3, expected "
        f"{_expect:.2f} — the seat height derivation and the solids disagree")

    # ---- CONTROLS, because 0.000 is also what a broken detector returns ----
    _c1 = vol(place_in_stand(body, YSHIFT + 1.0), stand)      # rearward, into the well wall
    _c2 = vol(place_in_stand(insert, YSHIFT, 2.0), slab)      # up the axis, into the slab
    _c3 = vol(place_in_stand(rigid, 0.0, 3.0), place_in_stand(body, YSHIFT))
    print(f"  [self-test] body +1.0y -> {_c1:8.3f}   insert +2.0ax -> {_c2:8.3f}   "
          f"plug +3.0ax -> {_c3:8.3f}")
    for _c, _w in ((_c1, "stand"), (_c2, "slab"), (_c3, "pocket")):
        assert _c > 1.0, f"!!! DETECTOR BLIND on {_w} — a displaced part reads as clear !!!"

    os.replace(os.path.join(out, name + E.STL_TMP), os.path.join(out, name + ".stl"))
    _committed = True
    print(f"\n[export] committed {name}.stl — all checks passed first")

    import subprocess as _sp
    _pq = _sp.run([sys.executable, os.path.join(out, "tools", "print_queue.py"), "refresh"])
    if _pq.returncode != 0:
        raise RuntimeError("print_queue refresh FAILED — enclosure/print/ may be stale")
