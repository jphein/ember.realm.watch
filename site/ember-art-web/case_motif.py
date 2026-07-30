#!/usr/bin/env python3
"""
The dorsal ridge, extracted as a repeat for the printed case shell.

nebula-stl asked whether a motif from the wyrm should carry onto the enclosure.
It should, and the useful thing is not a picture — it is the RHYTHM, with real
numbers, at a scale FDM can actually hold.

The device ridge is 11 spines over 120 dragon units ~= 21.5 mm, so each spine is
about 0.86 mm tall: below the 0.4 mm feature floor in any meaningful way, and
invisible. So the shell must QUOTE the proportions, not copy the geometry.

Emits case-motif.svg (1:1 mm, for import as a sketch) and prints the numbers.
"""
import math

# the ridge, verbatim from dragon.py's body_mask(): (cx, cy, h) in dragon units
RIDGE = [(30.0, 22.8, 4.8), (37.5, 26.0, 5.4), (45.5, 29.0, 4.8),
         (54.0, 31.0, 5.2), (63.0, 31.4, 4.6), (72.0, 30.0, 4.9),
         (81.0, 27.4, 4.0), (89.5, 23.6, 3.6), (97.0, 19.4, 2.8),
         (104.5, 13.6, 2.2), (109.5, 8.2, 1.6)]
BASE_HALF, APEX_LEAN, BASE_DROP = 0.46, 0.18, 1.6

pitches = [RIDGE[i + 1][0] - RIDGE[i][0] for i in range(len(RIDGE) - 1)]
heights = [h for _, _, h in RIDGE]
lean_deg = [math.degrees(math.atan2(APEX_LEAN * h, h + BASE_DROP)) for h in heights]

print("dorsal ridge, as measured from the shipped creature")
print("  spines          %d" % len(RIDGE))
print("  pitch           %.1f-%.1f units (mean %.1f)"
      % (min(pitches), max(pitches), sum(pitches) / len(pitches)))
print("  height          %.1f -> %.1f  (taper %.1f:1 head to tail)"
      % (heights[0], heights[-1], max(heights) / min(heights)))
print("  pitch : height  %.2f : 1" % ((sum(pitches) / len(pitches)) / (sum(heights) / len(heights))))
print("  base width      %.2f x height" % (BASE_HALF * 2))
print("  apex LEANS BACK %.0f-%.0f deg (toward the tail)"
      % (min(lean_deg), max(lean_deg)))
print()
print("  at device scale one unit is ~0.18 mm, so a spine is ~%.2f mm."
      % (heights[0] * 0.18))
print("  -> quote the proportions, do not copy the size.")

# --- the grille: same rhythm, scaled to a 44 mm run, as slots ---
RUN_MM, SLOT_W, DEPTH_MAX, LEAN = 44.0, 1.8, 13.0, 24.0
n = len(RIDGE)
span = RIDGE[-1][0] - RIDGE[0][0]
slots, area = [], 0.0
for cx, cy, h in RIDGE:
    x = (cx - RIDGE[0][0]) / span * RUN_MM
    L = DEPTH_MAX * (h / max(heights))
    area += SLOT_W * L
    slots.append((x, L))
print()
print("speaker grille, same rhythm at %.0f mm:" % RUN_MM)
print("  %d slots, %.1f mm wide, %.1f -> %.1f mm long, leaning back %.0f deg"
      % (n, SLOT_W, slots[0][1], slots[-1][1], LEAN))
print("  open area %.0f mm^2   (target was 100-200)" % area)

t = math.tan(math.radians(LEAN))
body = []
for x, L in slots:
    body.append('<path d="M%.2f 0 l%.2f %.2f a%.2f %.2f 0 0 0 %.2f 0 l%.2f %.2f '
                'a%.2f %.2f 0 0 0 %.2f 0 Z" fill="#E05A08"/>'
                % (x, L * t, L, SLOT_W / 2, SLOT_W / 2, SLOT_W,
                   -L * t, -L, SLOT_W / 2, SLOT_W / 2, -SLOT_W))
open("case-motif.svg", "w").write(
    '<svg xmlns="http://www.w3.org/2000/svg" width="%.1fmm" height="%.1fmm" '
    'viewBox="-3 -3 %.1f %.1f">\n'
    '<!-- 1:1 in mm. Slots lean BACK toward the tail, which is also the cheap\n'
    '     direction for FDM: a back-leaning ridge is self-supporting. -->\n'
    '<rect x="-3" y="-3" width="%.1f" height="%.1f" fill="#0A0604"/>\n%s\n</svg>\n'
    % (RUN_MM + 12, DEPTH_MAX + 8, RUN_MM + 12, DEPTH_MAX + 8,
       RUN_MM + 12, DEPTH_MAX + 8, "\n".join(body)))
print("  wrote case-motif.svg (1:1 mm)")
