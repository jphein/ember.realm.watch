#!/usr/bin/env python3
"""
ember-satellite — the hearth-wyrm.

Generates the dragon silhouette for the ESPHome display lambda in
scratch/ember-satellite.yaml (flame band, y188..263).

This is NOT an ESPHome `image:`. It emits per-row RUN-LENGTH SPANS as C tables,
because:

  * the flame band is rendered ROW-MAJOR and must tile every row exactly once
    (auto_clear_enabled: false — see the YAML header). An `it.image()` blit is a
    second write over pixels the fire already wrote; spans composite into the
    existing run-length classifier and preserve write-once.
  * spans carry no colour, so the dragon is shaded at render time from the live
    fire-temperature palette — it rides the ember->amber->gold->white-hot ramp,
    honours the daylight theme, and brightens with state. A baked image cannot.
  * the animation is procedural (head lift, glow, travelling rim light), so it
    never visibly loops the way frame-cycled art does.

Outputs (all into this directory):
  dragon_spans.inc      C tables to paste into the display lambda
  dragon_sheet.png      8x preview of every piece, flat
  dragon_states.png     8x preview of the five states, shaded, over a fire
  dragon_wing.png       8x preview of the winged variant (not shipped)

Reproduce:  python3 dragon.py
Deterministic — no RNG anywhere.
"""

import numpy as np
from PIL import Image

# ---------------------------------------------------------------- geometry ----
# Dragon-local coordinates. (0,0) is the top-left of the bounding box.
#
# WHY LONG AND LOW: the flame band is 240x76. A coiled, doughnut-shaped dragon
# fights that aspect ratio — it needs height the band does not have, and at 7px
# tube radius it reads as a blob with a hole in it (see git history of this
# file). A slender serpentine wyrm, couchant, agrees with the band the same way
# the fire does: wide, low, resting on the grate. It also occludes far less of
# the fire — a 5px tube hides ~25% of the band's area where a coil hid ~55%.
DW, DH = 120, 50          # bbox, px
SS = 8                    # supersample factor for the rasteriser

# Placement inside the flame band (band-local rows, 0..75).
DGN_X, DGN_Y = 60, 22     # -> screen x 60..179, y 210..259

# Head sprite, its own little bbox. Faces LEFT.
HW, HH = 28, 19
# Where the neck attaches, in head-local coords (back-bottom of the cranium).
HEAD_ATTACH = (21, 13)
# Eye centre, head-local.
HEAD_EYE = (8, 7)
# Nostril / muzzle tip, head-local — where breath leaves.
HEAD_MUZZLE = (1, 9)

# Head placement, dragon-local, as a function of wakefulness k in [0,1].
#   k=0 asleep: nose tucked down against the chest, resting on the forelimb
#   k=1 alert : head raised, neck extended
HEAD_POS_SLEEP = (4, 30)
HEAD_POS_ALERT = (0, 0)

# Where the neck leaves the body.
SHOULDER = (29, 28)


def _grid():
    return np.zeros((DH * SS, DW * SS), dtype=np.float32)


def _disc(a, cx, cy, r):
    """Stamp a filled disc into a supersampled buffer."""
    cx, cy, r = cx * SS, cy * SS, r * SS
    y0, y1 = max(0, int(cy - r - 2)), min(a.shape[0], int(cy + r + 3))
    x0, x1 = max(0, int(cx - r - 2)), min(a.shape[1], int(cx + r + 3))
    if y0 >= y1 or x0 >= x1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    a[y0:y1, x0:x1] = np.maximum(
        a[y0:y1, x0:x1],
        ((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= r * r).astype(np.float32),
    )


def _catmull(pts, n):
    """Catmull-Rom through pts (list of (x, y, r)); returns n samples."""
    p = np.array(pts, dtype=np.float64)
    p = np.vstack([p[0] + (p[0] - p[1]), p, p[-1] + (p[-1] - p[-2])])
    out = []
    segs = len(p) - 3
    for i in range(n):
        u = i / (n - 1) * segs
        s = min(int(u), segs - 1)
        t = u - s
        p0, p1, p2, p3 = p[s], p[s + 1], p[s + 2], p[s + 3]
        t2, t3 = t * t, t * t * t
        out.append(
            0.5 * ((2 * p1) + (-p0 + p2) * t
                   + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                   + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
        )
    return out


def _tube(a, pts, n=260):
    """Sweep a varying-radius disc along a Catmull-Rom spline."""
    for x, y, r in _catmull(pts, n):
        _disc(a, x, y, max(r, 0.4))


def _poly(a, pts):
    """Stamp a filled convex-ish polygon (even-odd scanline)."""
    p = [(x * SS, y * SS) for x, y in pts]
    ys = [q[1] for q in p]
    for row in range(max(0, int(min(ys))), min(a.shape[0], int(max(ys)) + 1)):
        yc = row + 0.5
        xs = []
        for i in range(len(p)):
            (x0, y0), (x1, y1) = p[i], p[(i + 1) % len(p)]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            lo, hi = int(round(xs[i])), int(round(xs[i + 1]))
            if hi > lo:
                a[row, max(0, lo):min(a.shape[1], hi)] = 1.0


def _resolve(a):
    """Downsample the supersampled buffer to a 1-bit mask."""
    h, w = DH, DW
    blocks = a.reshape(h, SS, w, SS).mean(axis=(1, 3))
    return blocks >= 0.42


# ------------------------------------------------------------------- shapes ---

def body_mask(with_wing=False):
    """
    Couchant hearth-wyrm, facing LEFT. Shoulder -> chest -> belly resting on the
    coals -> haunch -> hip, and then the TAIL rises to the right and curls up
    into the flames, so the tail-flourish on the right balances the raised head
    on the left. Two verticals framing one low body: the same composition the
    hearth already has.

    NO WINGS by default. At 50px tall a folded membrane either reads as a bird or
    competes with the dorsal ridge for the same silhouette; the long neck, the
    ridge and the rising tail carry the draconic signal without it. Pass
    with_wing=True to render the rejected variant for comparison.
    """
    a = _grid()

    # --- the spine: one tapered tube, shoulder to tail-tip. ---
    # The belly is deliberately held ~7px CLEAR of the feet. Two reasons: the
    # legs only read as legs if there is daylight under the body, and the coals
    # keep glowing underneath — which is what makes it look like the thing is
    # lying IN the fire rather than on top of a picture of one.
    _tube(a, [
        (27.0, 26.5, 4.8),    # shoulder  (the neck leaves here)
        (33.0, 31.0, 5.0),    # chest
        (45.0, 34.4, 5.0),
        (58.0, 35.8, 4.9),    # belly, lowest
        (72.0, 34.4, 5.0),
        (85.0, 31.0, 5.2),    # haunch
        (95.0, 26.5, 4.3),    # hip / tail base
        (104.0, 20.0, 3.3),   # the tail rises
        (110.5, 13.5, 2.3),
        (113.0, 7.0, 1.4),
        (112.5, 2.8, 0.9),    # tail tip, up among the flames
    ])

    # --- foreleg, planted forward. Toes, not a boot. ---
    _tube(a, [(31.0, 31.5, 2.9), (27.0, 39.0, 2.3), (25.5, 45.0, 2.0)])
    _tube(a, [(20.5, 46.4, 1.5), (24.5, 46.6, 1.8), (28.0, 46.0, 1.7)])

    # --- hind leg, folded under the haunch. ---
    _disc(a, 86.0, 32.5, 5.9)
    _tube(a, [(87.5, 35.5, 2.9), (90.5, 41.0, 2.4), (89.5, 45.0, 2.1)])
    _tube(a, [(84.5, 46.4, 1.5), (88.5, 46.6, 1.8), (92.0, 46.0, 1.7)])

    # --- dorsal ridge: triangles along the back, tallest over the shoulders.
    # This is the whole draconic signal, so it runs the full length of the spine
    # and tapers into the tail rather than stopping. The heights are deliberately
    # NOT a smooth curve — a perfectly graded sawtooth reads as a machined comb.
    ridge = [(30.0, 22.8, 4.8), (37.5, 26.0, 5.4), (45.5, 29.0, 4.8),
             (54.0, 31.0, 5.2), (63.0, 31.4, 4.6), (72.0, 30.0, 4.9),
             (81.0, 27.4, 4.0), (89.5, 23.6, 3.6), (97.0, 19.4, 2.8),
             (104.5, 13.6, 2.2), (109.5, 8.2, 1.6)]
    for cx, cy, h in ridge:
        _poly(a, [(cx - h * 0.46, cy + 1.6), (cx + h * 0.46, cy + 1.6),
                  (cx + h * 0.18, cy - h)])

    if with_wing:
        # The rejected variant: a folded membrane over the shoulders.
        _poly(a, [(36, 25), (50, 6), (66, 9), (78, 25), (68, 30), (42, 29)])
        _poly(a, [(50, 6), (56, 1), (58, 9)])

    return _resolve(a)


def head_mask(jaw_drop):
    """
    Head, facing LEFT, in its own HW x HH box.

      jaw_drop = 0  mouth shut
               = 2  ajar
               = 4  open  (the throat shows — see maw_mask)

    Three discrete mouth shapes is the classic limited-animation vocabulary and
    it reads as speech at 18fps far better than a continuous morph would.
    """
    a = _grid()

    # upper skull: a long tapered wedge, muzzle tip to jaw hinge. The muzzle is
    # deliberately LONG — a short one reads as a lizard, and at 28px the
    # difference between reptile and dragon is almost entirely snout length.
    _tube(a, [
        (0.9, 8.8, 1.2),      # muzzle tip
        (3.0, 8.4, 1.8),
        (6.0, 7.9, 2.4),
        (9.5, 7.4, 3.0),      # brow / eye socket
        (13.5, 7.6, 3.6),
        (17.5, 8.8, 4.0),     # cranium
        (21.0, 11.0, 3.2),    # jaw hinge / neck attach
    ])

    # brow ridge — gives the eye a socket and the profile some authority
    _poly(a, [(6.4, 5.4), (11.0, 3.2), (15.5, 4.2), (12.5, 6.4)])

    # two horns, swept back over the neck
    _poly(a, [(14.0, 3.8), (17.0, 2.6), (27.4, 0.0), (19.5, 4.8)])
    _poly(a, [(15.5, 6.6), (18.5, 5.8), (27.6, 5.2), (20.0, 8.4)])

    # cheek frill, so the head is not a smooth cone
    _poly(a, [(17.5, 9.2), (23.0, 8.2), (24.0, 12.0), (19.0, 13.4)])

    # lower jaw — hinged at the back, so the drop is a rotation, not a slide
    j = jaw_drop
    _tube(a, [
        (1.3, 10.0 + j * 1.00, 1.0),
        (4.5, 10.4 + j * 0.82, 1.4),
        (8.5, 10.9 + j * 0.58, 1.8),
        (13.5, 11.4 + j * 0.30, 2.1),
        (18.5, 11.8, 2.4),        # hinge: does not move
    ])
    return _resolve(a)


def maw_mask(jaw_drop):
    """The lit throat between the jaws. Empty when the mouth is shut."""
    a = _grid()
    if jaw_drop <= 0:
        return _resolve(a)
    j = jaw_drop
    _poly(a, [
        (1.6, 9.4),
        (17.5, 11.2),
        (17.5, 11.8),
        (1.6, 10.0 + j * 1.00),
    ])
    return _resolve(a)


# -------------------------------------------------------------------- tables ---

def dilate(m):
    """1px 8-connected dilation — the shadow gap that lifts the silhouette off
    the fire behind it."""
    out = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    out[0, :] |= m[1, :] if DH > 1 else False
    return out


def spans(mask):
    """Per-row [x0, x1) runs."""
    rows = []
    for r in range(mask.shape[0]):
        row, cur, out = mask[r], None, []
        for x in range(mask.shape[1]):
            if row[x] and cur is None:
                cur = x
            elif not row[x] and cur is not None:
                out.append((cur, x))
                cur = None
        if cur is not None:
            out.append((cur, mask.shape[1]))
        rows.append(out)
    return rows


def topy(mask):
    """Topmost set row per column, or 255."""
    out = []
    for x in range(mask.shape[1]):
        col = np.nonzero(mask[:, x])[0]
        out.append(int(col[0]) if len(col) else 255)
    return out


def boty(mask):
    """Bottom-most set row per column, or 0.

    This is what the belly furnace is shaded from. Keying the interior colour off
    the ABSOLUTE row makes the underside one flat gold bar the length of the
    animal — it reads as a glowing plank, not a body. Keying it off the distance
    up from each column's own lowest pixel makes the light follow the form, and
    it costs the same single array lookup because topy is already being read for
    the rim test."""
    out = []
    for x in range(mask.shape[1]):
        col = np.nonzero(mask[:, x])[0]
        out.append(int(col[-1]) if len(col) else 0)
    return out


def emit_spans(name, rows, comment):
    """Fixed-stride span table. Stride is the measured worst case, so the table
    self-sizes when the anatomy is retuned — a hardcoded stride silently
    truncates a limb and the failure looks like a rendering bug."""
    nmax = max(1, max(len(o) for o in rows))
    flat = []
    for out in rows:
        for i in range(nmax):
            flat += list(out[i]) if i < len(out) else [0, 0]
    lines = [f"      // {comment}",
             f"      //   {len(rows)} rows x {nmax} spans, stride {nmax * 2}",
             f"      static const uint8_t {name}[] = {{"]
    per = nmax * 2
    for r, out in enumerate(rows):
        vals = flat[r * per:(r + 1) * per]
        lines.append("        " + ",".join(f"{v:3d}" for v in vals) + f",   // r{r:02d}")
    lines.append("      };")
    lines.append(f"      static const int {name}_N = {nmax};   // spans per row")
    return "\n".join(lines), len(flat)


def emit_bytes(name, vals, comment):
    lines = [f"      // {comment}", f"      static const uint8_t {name}[] = {{"]
    for i in range(0, len(vals), 20):
        lines.append("        " + ",".join(f"{v:3d}" for v in vals[i:i + 20]) + ",")
    lines.append("      };")
    return "\n".join(lines), len(vals)


# ------------------------------------------------------------------ previews ---

PAL = {
    "bg": (0x0A, 0x06, 0x04), "ash": (0x3A, 0x32, 0x2C),
    "bed": (0x4A, 0x10, 0x02), "ember": (0x8E, 0x22, 0x06),
    "amber": (0xE0, 0x5A, 0x08), "gold": (0xFF, 0xA8, 0x1E),
    "tip": (0xFF, 0xE8, 0xB4), "alarm": (0xFF, 0x3C, 0x18),
    "dim": (0x6A, 0x52, 0x40),
}


def shade(canvas, ox, oy, body, halo, tp, k_rim, k_in_rows, eye=None,
          maw=None, maw_c="gold"):
    """Approximate the renderer's shading model, for eyeballing only."""
    for r in range(body.shape[0]):
        for x in range(body.shape[1]):
            cx, cy = ox + x, oy + r
            if not (0 <= cx < canvas.shape[1] and 0 <= cy < canvas.shape[0]):
                continue
            if body[r, x]:
                d = r - tp[x] if tp[x] != 255 else 99
                c = k_rim[x] if d < 2 else k_in_rows[r]
                canvas[cy, cx] = PAL[c]
            elif halo[r, x]:
                canvas[cy, cx] = PAL["bg"]
    if maw is not None:
        for r in range(maw.shape[0]):
            for x in range(maw.shape[1]):
                if maw[r, x]:
                    cy, cx = oy + r, ox + x
                    if 0 <= cx < canvas.shape[1] and 0 <= cy < canvas.shape[0]:
                        canvas[cy, cx] = PAL[maw_c]
    if eye:
        ex, ey, ec, form = eye
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cx, cy = ox + ex + dx, oy + ey + dy
                if not (0 <= cx < canvas.shape[1] and 0 <= cy < canvas.shape[0]):
                    continue
                if form == "closed":
                    if dy == 0 and dx <= 1:
                        canvas[cy, cx] = PAL["bg"]        # a shut lid
                elif form == "slit":
                    if dy == 0 and dx <= 1:
                        canvas[cy, cx] = PAL[ec]
                else:
                    if dy >= 0 and dx <= 1:
                        canvas[cy, cx] = PAL[ec]          # 2x2, the awake eye


def synth_fire(h, w, level, seed_phase):
    """A stand-in for the real fire, purely so separation can be judged."""
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[:, :] = PAL["bg"]
    base = h - 3
    for col in range(w // 4):
        fx = col
        f = level * (0.5 + 0.5 * np.sin(0.27 * fx - seed_phase)) \
            * (0.5 + 0.5 * np.sin(0.11 * fx + seed_phase * 0.6 + 1.7))
        f = 0.18 + 0.7 * f
        hgt = int(f * (h - 8))
        for r in range(base - hgt, base):
            up = base - r
            c = "ember" if up <= hgt * 0.5 else ("amber" if up <= hgt * 0.82 else
                                                ("tip" if f > 0.72 else "gold"))
            out[r, col * 4:col * 4 + 4] = PAL[c]
    out[base:, :] = PAL["ash"]
    return out


def scale(img, n):
    return Image.fromarray(img).resize((img.shape[1] * n, img.shape[0] * n),
                                       Image.NEAREST)


def neck_spans(hx, hy, sx=SHOULDER[0], sy=SHOULDER[1]):
    """Same maths the lambda uses: a tapered capsule chain, shoulder -> head."""
    ax, ay = hx + HEAD_ATTACH[0], hy + HEAD_ATTACH[1]
    # control point bulges the neck forward-left so it reads as an S, not a stick
    cxp, cyp = sx - 5.5, (sy + ay) * 0.5 - 2.0
    lo = [DW] * DH
    hi = [-1] * DH
    tp = [255] * DW
    N = 26
    for i in range(N):
        t = i / (N - 1)
        u = 1 - t
        cx = u * u * sx + 2 * u * t * cxp + t * t * ax
        cy = u * u * sy + 2 * u * t * cyp + t * t * ay
        r = 4.6 * u + 2.9 * t
        for row in range(int(cy - r), int(cy + r) + 1):
            if not (0 <= row < DH):
                continue
            dyv = row + 0.5 - cy
            if abs(dyv) > r:
                continue
            hw = (r * r - dyv * dyv) ** 0.5
            x0, x1 = int(cx - hw), int(cx + hw) + 1
            lo[row] = min(lo[row], max(0, x0))
            hi[row] = max(hi[row], min(DW, x1))
        for x in range(max(0, int(cx - r)), min(DW, int(cx + r) + 1)):
            dxv = x + 0.5 - cx
            if abs(dxv) <= r:
                t0 = int(cy - (r * r - dxv * dxv) ** 0.5)
                tp[x] = min(tp[x], max(0, t0))
    return lo, hi, tp


def main():
    body = body_mask()
    # NOTE: the second table is the DILATED mask, not the 1px ring. Dilation
    # MERGES spans (the ring splits them: 10 spans/row vs 4), and the renderer
    # wants the cheap early-out — "not in the dilated mask" rejects a fire pixel
    # in one or two compares.
    bdil = dilate(body)
    halo = bdil & ~body
    b_top = topy(body)
    b_bot = boty(body)

    heads = [head_mask(0), head_mask(2), head_mask(4)]
    hdil = [dilate(h) for h in heads]
    hhalo = [hdil[i] & ~heads[i] for i in range(3)]
    h_top = [topy(h) for h in heads]
    h_bot = [boty(h) for h in heads]
    maws = [maw_mask(0), maw_mask(2), maw_mask(4)]

    bsp, dsp = spans(body), spans(bdil)
    print("spans/row  body:", max(len(s_) for s_ in bsp),
          " dilated:", max(len(s_) for s_ in dsp),
          " (ring would be", max(len(s_) for s_ in spans(halo)), ")")
    for i, h in enumerate(heads):
        print(f"  head[{i}] body:", max(len(s_) for s_ in spans(h)),
              " dilated:", max(len(s_) for s_ in spans(hdil[i])),
              " maw:", max(len(s_) for s_ in spans(maws[i])))

    # ------------------------------------------------------------- the .inc ---
    chunks, total = [], 0
    for nm, rows, cm in [
        ("DGN_B", bsp, f"hearth-wyrm body: per-row [x0,x1) runs in dragon-local x"),
        ("DGN_D", dsp, f"same, dilated 1px — the shadow gap that lifts it off the fire"),
    ]:
        t, n_ = emit_spans(nm, rows, cm)
        chunks.append(t)
        total += n_
    for nm, vals, cm in [
        ("DGN_TOPY", b_top, "topmost body row per column (255 = none) -> rim light"),
        ("DGN_BOTY", b_bot, "bottom-most body row per column (0 = none) -> belly furnace"),
    ]:
        t, n_ = emit_bytes(nm, vals, cm)
        chunks.append(t)
        total += n_

    for i in range(3):
        for nm, m, cm in [
            (f"HED_B{i}", heads[i], f"head silhouette, jaw drop {i * 2}px"),
            (f"HED_D{i}", hdil[i], f"head dilated 1px, jaw drop {i * 2}px"),
            (f"HED_M{i}", maws[i], f"lit maw (empty when shut), jaw drop {i * 2}px"),
        ]:
            t, n_ = emit_spans(nm, spans(m), cm)
            chunks.append(t)
            total += n_
        for nm, vals, cm in [
            (f"HED_T{i}", h_top[i], f"head topmost row per column, jaw drop {i * 2}px"),
            (f"HED_Y{i}", h_bot[i], f"head bottom row per column, jaw drop {i * 2}px"),
        ]:
            t, n_ = emit_bytes(nm, vals, cm)
            chunks.append(t)
            total += n_

    hdr = (
        "      // ===== generated by esphome/art/dragon.py - DO NOT HAND-EDIT =====\n"
        f"      // hearth-wyrm {DW}x{DH} at flame-band ({DGN_X},{DGN_Y}); head {HW}x{HH}\n"
        f"      // neck attaches at head-local {HEAD_ATTACH}, eye at {HEAD_EYE},\n"
        f"      // muzzle at {HEAD_MUZZLE}; shoulder at dragon-local {SHOULDER}\n"
        f"      // head pos: asleep {HEAD_POS_SLEEP} -> alert {HEAD_POS_ALERT}\n"
        f"      // total table bytes: {total}\n"
    )
    with open("dragon_spans.inc", "w") as f:
        f.write(hdr + "\n" + "\n\n".join(chunks) + "\n")
    print("table bytes:", total)

    # -------------------------------------------------------------- sheet ----
    sheet = np.zeros((DH + 4, DW + HW * 3 + 16, 3), dtype=np.uint8)
    sheet[:, :] = PAL["bg"]
    for r in range(DH):
        for x in range(DW):
            if body[r, x]:
                sheet[r + 2, x + 2] = PAL["ember"] if (r - b_top[x] if b_top[x] != 255 else 9) >= 2 else PAL["gold"]
            elif halo[r, x]:
                sheet[r + 2, x + 2] = PAL["dim"]
    for i, h in enumerate(heads):
        ox = DW + 6 + i * (HW + 3)
        for r in range(DH):
            for x in range(HW):
                if r < HH and h[r, x]:
                    sheet[r + 2, ox + x] = PAL["ember"] if (r - h_top[i][x] if h_top[i][x] != 255 else 9) >= 2 else PAL["gold"]
                elif r < HH and maws[i][r, x]:
                    sheet[r + 2, ox + x] = PAL["tip"]
    scale(sheet, 8).save("dragon_sheet.png")

    # ------------------------------------------------------------- states ----
    # Mimic the lambda per state so the shading model can be judged, over fire.
    BAND_H, BAND_W = 76, 240
    states = [
        ("0 idle / asleep",   0.00, 0, "closed", 0.34, 0.35),
        ("1 listening",       1.00, 0, "open",   0.90, 0.95),
        ("2 thinking",        0.62, 0, "slit",   1.05, 0.50),
        ("3 speaking",        0.92, 2, "open",   1.15, 1.00),
        ("4 error / guttered", 0.05, 0, "dark",  0.00, 0.10),
    ]
    tiles = []
    for label, k, jaw, eyeform, glow, rim in states:
        canvas = synth_fire(BAND_H, BAND_W,
                            0.16 if label.startswith("0") else
                            (0.10 if label.startswith("4") else 0.75),
                            {"0": 0.4, "1": 1.1, "2": 2.0, "3": 3.1, "4": 0.0}[label[0]])
        err = label.startswith("4")

        # interior colour per row: belly glow rises from the bottom
        k_in = []
        for r in range(DH):
            v = (r - 22) / 24.0
            g = glow * max(0.0, min(1.0, v)) ** 1.1
            k_in.append("ash" if err else
                        ("gold" if g > 0.80 else "amber" if g > 0.52 else
                         "ember" if g > 0.24 else "bed"))
        rim_c = ["ash" if err else
                 ("gold" if rim > 0.55 else "ember")] * DW
        if not err and rim > 0.9:
            # the travelling swallow: white-hot only where the light is passing
            for x in range(DW):
                if abs(x - int(rim * 96)) < 9:
                    rim_c[x] = "tip"

        # neck
        hx, hy = (HEAD_POS_SLEEP[0] + (HEAD_POS_ALERT[0] - HEAD_POS_SLEEP[0]) * k,
                  HEAD_POS_SLEEP[1] + (HEAD_POS_ALERT[1] - HEAD_POS_SLEEP[1]) * k)
        hx, hy = int(round(hx)), int(round(hy))
        nlo, nhi, ntop = neck_spans(hx, hy)
        nmask = np.zeros((DH, DW), dtype=bool)
        for r in range(DH):
            if nhi[r] > nlo[r]:
                nmask[r, nlo[r]:nhi[r]] = True
        nhalo = dilate(nmask) & ~nmask

        comb_top = [min(b_top[x], ntop[x]) for x in range(DW)]
        shade(canvas, DGN_X, DGN_Y, nmask, nhalo, ntop, rim_c, k_in)
        shade(canvas, DGN_X, DGN_Y, body, halo, comb_top, rim_c, k_in)

        hb, hh_, ht, hm = heads[jaw], hhalo[jaw], h_top[jaw], maws[jaw]
        # The head's rim runs ONE ramp step hotter than the body's. Without it the
        # sleeping head — which necessarily overlaps the shoulder, there being only
        # 22px of clear space in front of it — has no line separating the two and
        # reads as a lump. Costs one array, no per-pixel work.
        hot = {"ember": "amber", "amber": "gold", "gold": "tip", "tip": "tip",
               "ash": "dim"}
        rim_h = [hot[c] for c in rim_c]
        eye = (HEAD_EYE[0], HEAD_EYE[1],
               "tip" if eyeform == "open" else "gold" if eyeform == "slit" else "alarm",
               "closed" if eyeform == "closed" else eyeform)
        shade(canvas, DGN_X + hx, DGN_Y + hy, hb, hh_, ht, rim_h, k_in,
              eye=eye, maw=hm, maw_c="tip")

        tile = np.zeros((BAND_H + 14, BAND_W, 3), dtype=np.uint8)
        tile[:, :] = (0, 0, 0)
        tile[12:12 + BAND_H] = canvas
        tiles.append((label, tile))

    out = np.vstack([t for _, t in tiles])
    img = scale(out, 4)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for i, (label, t) in enumerate(tiles):
        d.text((6, i * t.shape[0] * 4 + 2), label, fill=(200, 200, 200))
    img.save("dragon_states.png")

    # ------------------------------------------------- ACTUAL SIZE check ----
    # The 4x previews flatter everything. On the panel the wyrm is 120x50px,
    # which at the ILI9341's ~0.18mm pitch is about 21 x 9 mm — smaller than a
    # thumbnail. If a feature does not survive here it does not exist.
    real = np.vstack([tiles[i][1][12:12 + BAND_H] for i in (0, 1, 3)])
    Image.fromarray(real).save("dragon_actual_size.png")
    scale(real, 2).save("dragon_2x.png")

    # ------------------------------------------------------------ the wing ---
    wb = body_mask(with_wing=True)
    wh = dilate(wb) & ~wb
    wt = topy(wb)
    canvas = synth_fire(76, 240, 0.75, 1.1)
    k_in = ["amber" if r > 36 else "ember" if r > 28 else "bed" for r in range(DH)]
    shade(canvas, DGN_X, DGN_Y, wb, wh, wt, ["gold"] * DW, k_in)
    scale(canvas, 4).save("dragon_wing.png")

    print("wrote dragon_spans.inc, dragon_sheet.png, dragon_states.png, dragon_wing.png")


if __name__ == "__main__":
    main()
