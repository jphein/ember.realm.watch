#!/usr/bin/env python3
"""Render what the printer will ACTUALLY do, from the gcode itself.

Not the STL. The STL is the design; the gcode is the instruction set, and the two
can disagree — wrong profile, wrong scale, off-bed placement, a --center that
landed somewhere unintended. This parses extrusion moves only (G1 with E
increasing) so what you see is deposited plastic, nothing else.

WHERE THIS SITS IN THE PRE-PRINT SEQUENCE (standing rule, JP 2026-08-01):
queue file -> make_3d_viewer.py -> THIS, on the sliced gcode -> JP looks ->
"go" -> print. The viewer answers "is this the right geometry"; this answers
"is that geometry what the machine was told" — placement on the real bed
outline, island count, per-island height. First used 2026-08-06 on the
three-part plate (bezel r3 / midframe r12 / cover r15), where it confirmed
three islands at three heights before ~7h of filament went down.

⚠️ A NAIVE FOOTPRINT MIN/MAX OVERSTATES. The first cut of this script reported
a 146mm footprint for a 56mm part — the min/max swept up the skirt and one
travel-adjacent artefact. That is why the plan view draws the FIRST LAYER only
and why island analysis belongs in per-layer bands, not whole-file bounds.
Cross-check a surprising number per layer before believing it.

USAGE
  python3 tools/gcode_preview.py <file.gcode> <out.png>
  xdg-open <out.png>

Left panel: first layer on the 235x235 bed outline (skirt included — that IS
what the machine draws first). Right: every extrusion move, coloured by height,
downsampled only past ~26k segments and saying so in the title.
"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.collections import LineCollection

GC = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
BED = 235.0

x = y = z = 0.0
e = 0.0
abs_e = True
segs = []          # (x0,y0,z0,x1,y1,z1)
first_layer = []   # (x0,y0),(x1,y1)
zs = set()

for line in GC.read_text(errors="ignore").splitlines():
    s = line.strip()
    if not s or s.startswith(";"):
        continue
    cmd = s.split(";", 1)[0].strip()
    if cmd.startswith("M82"):
        abs_e = True
        continue
    if cmd.startswith("M83"):
        abs_e = False
        continue
    if cmd.startswith("G92"):
        for tok in cmd.split()[1:]:
            if tok[0] == "E":
                e = float(tok[1:])
        continue
    if not (cmd.startswith("G1") or cmd.startswith("G0")):
        continue
    nx, ny, nz, ne = x, y, z, None
    for tok in cmd.split()[1:]:
        try:
            v = float(tok[1:])
        except ValueError:
            continue
        if tok[0] == "X":
            nx = v
        elif tok[0] == "Y":
            ny = v
        elif tok[0] == "Z":
            nz = v
        elif tok[0] == "E":
            ne = v
    extruding = False
    if ne is not None:
        delta = (ne - e) if abs_e else ne
        extruding = delta > 1e-6
        e = ne if abs_e else e + ne
    if extruding and (nx != x or ny != y):
        segs.append((x, y, z, nx, ny, nz))
        zs.add(round(nz, 2))
        if nz <= 0.21:
            first_layer.append(((x, y), (nx, ny)))
    x, y, z = nx, ny, nz

print(f"extrusion segments: {len(segs)}")
print(f"layers: {len(zs)}   z range: {min(zs):.2f} .. {max(zs):.2f}")
xsall = [p for s in segs for p in (s[0], s[3])]
ysall = [p for s in segs for p in (s[1], s[4])]
print(f"bed footprint X {min(xsall):.1f}..{max(xsall):.1f}   Y {min(ysall):.1f}..{max(ysall):.1f}")

fig = plt.figure(figsize=(15, 7.2), facecolor="#12100e")

# ---- left: plan view of the FIRST LAYER on the real bed outline ----
ax = fig.add_subplot(1, 2, 1)
ax.set_facecolor("#12100e")
ax.add_collection(LineCollection(first_layer, colors="#FFA81E", linewidths=0.45))
ax.plot([0, BED, BED, 0, 0], [0, 0, BED, BED, 0], color="#6A5240", lw=1.4)
ax.plot([BED / 2], [BED / 2], marker="+", color="#6A5240", ms=10)
ax.set_xlim(-10, BED + 10)
ax.set_ylim(-10, BED + 10)
ax.set_aspect("equal")
ax.set_title(f"first layer on the 235x235 bed  —  {len(first_layer)} moves",
             color="#F2DCB8", fontsize=11)
ax.tick_params(colors="#6A5240", labelsize=8)
for sp in ax.spines.values():
    sp.set_color("#3A322C")

# ---- right: the whole toolpath in 3D, coloured by height ----
ax2 = fig.add_subplot(1, 2, 2, projection="3d")
ax2.set_facecolor("#12100e")
step = max(1, len(segs) // 26000)          # keep the render honest but drawable
sub = segs[::step]
lines = [[(s[0], s[1], s[2]), (s[3], s[4], s[5])] for s in sub]
zmax = max(zs) or 1.0
cols = [(1.0, 0.35 + 0.55 * (s[2] / zmax), 0.10 + 0.60 * (s[2] / zmax), 0.85) for s in sub]
ax2.add_collection3d(Line3DCollection(lines, colors=cols, linewidths=0.35))
ax2.set_xlim(min(xsall) - 4, max(xsall) + 4)
ax2.set_ylim(min(ysall) - 4, max(ysall) + 4)
ax2.set_zlim(0, zmax + 2)
try:
    ax2.set_box_aspect((max(xsall) - min(xsall), max(ysall) - min(ysall), zmax))
except Exception:
    pass
ax2.view_init(elev=26, azim=-52)
ax2.set_title(f"all extrusion moves  —  {len(segs)} segments, {len(zs)} layers"
              + (f"  (1/{step} shown)" if step > 1 else ""),
              color="#F2DCB8", fontsize=11)
for a in (ax2.xaxis, ax2.yaxis, ax2.zaxis):
    a.set_pane_color((0.07, 0.06, 0.05, 1.0))
    a.line.set_color("#3A322C")
ax2.tick_params(colors="#6A5240", labelsize=7)

fig.suptitle(GC.name, color="#FFA81E", fontsize=13)
fig.tight_layout()
fig.savefig(OUT, dpi=115, facecolor="#12100e")
print(f"wrote {OUT}")
