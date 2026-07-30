"""Website renders for the Ember enclosure.
SVG technical views  -> currentColor line art, themeable, namespaced ids, no text.
PNG hero            -> shaded, coal background, 16:9.
"""
from build123d import *
import ember_case as E
import numpy as np, os, math
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
os.makedirs(OUT, exist_ok=True)

bezel, shell = E.front_bezel(), E.back_shell()
stand, base  = E.desk_stand(), E.stand_base()
diff         = E.diffuser()
_raw  = Pos(52.750,-6.000,0.0) * import_step("../ES3C28P_3D/ES3C28P_3D.step")
board = _raw                                     # full 1238-solid assembly
# For line art, the full board projects ~thousands of edges (87 KB of SVG for one
# view).  A reader needs the PCB + LCD + glass silhouette, not every 0402.  Pick
# the four structural solids by volume.
_bs   = sorted(_raw.solids(), key=lambda s: -s.volume)[:4]
board_lite = Compound(children=_bs)

def to_stand(part):
    """board coords -> assembled position inside the tilted stand slot"""
    loc = Pos(-25,-1,2.95) * (Rot(90,0,0) * part)
    return Pos(E.ST_W/2, E.SLOT_CY, E.SLOT_FLOOR) * (Rot(-E.TILT,0,0) * loc)

# ---------------------------------------------------------------- SVG plumbing
def sample(edge, n):
    try:
        return [(p.X, p.Y) for p in (edge @ (i/(n-1)) for i in range(n))]
    except Exception:
        return []

def project(shape, eye, up=(0,0,1), target=(0,0,0), hidden=False):
    vis, hid = shape.project_to_viewport(viewport_origin=eye, viewport_up=up, look_at=target)
    edges = list(vis) + (list(hid) if hidden else [])
    polys, kinds = [], []
    for e in edges:
        gt = str(e.geom_type).upper()
        n = 2 if "LINE" in gt else 9
        p = sample(e, n)
        if len(p) >= 2:
            polys.append(p); kinds.append("hidden" if (hidden and e in hid) else "vis")
    return polys, kinds

def write_svg(path, groups, prefix, pad=6.0, target_w=1200, hidden_dash=True):
    """groups: list of (polys, kinds). All share one coordinate space."""
    allp = [pt for g,_ in groups for poly in g for pt in poly]
    xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
    x0,x1,y0,y1 = min(xs)-pad, max(xs)+pad, min(ys)-pad, max(ys)+pad
    w,h = x1-x0, y1-y0
    s = target_w/w
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w*s:.1f} {h*s:.1f}" '
           f'width="{w*s:.0f}" height="{h*s:.0f}" fill="none" stroke="currentColor" '
           f'stroke-linecap="round" stroke-linejoin="round" role="img">']
    def path_of(poly):
        d = f"M{(poly[0][0]-x0)*s:.0f} {(y1-poly[0][1])*s:.0f}"
        last = None
        for px,py in poly[1:]:
            q = (round((px-x0)*s), round((y1-py)*s))
            if q != last: d += f"L{q[0]} {q[1]}"
            last = q
        return d
    for gi,(polys,kinds) in enumerate(groups):
        vis = [p for p,k in zip(polys,kinds) if k=="vis"]
        hid = [p for p,k in zip(polys,kinds) if k=="hidden"]
        if hid:
            d = " ".join(path_of(p) for p in hid)
            out.append(f'<path id="{prefix}-g{gi}-hidden" d="{d}" stroke-width="0.7" '
                       f'stroke-opacity="0.35" stroke-dasharray="4 3" '
                       f'vector-effect="non-scaling-stroke"/>')
        if vis:
            d = " ".join(path_of(p) for p in vis)
            out.append(f'<path id="{prefix}-g{gi}-vis" d="{d}" stroke-width="1.4" '
                       f'vector-effect="non-scaling-stroke"/>')
    out.append("</svg>")
    open(path,"w").write("\n".join(out))
    kb = os.path.getsize(path)/1024
    print(f"  {os.path.basename(path):26s} {kb:6.1f} KB   ratio {w/h:.2f}:1")
    return kb

_tmp = 0
def tri_of(shape, tol=0.06):
    """Tessellate via an STL round-trip. shape.tessellate() raises on some boolean
    results (a face comes back with no triangulation); export_stl never does."""
    global _tmp
    _tmp += 1
    f = os.path.join(OUT, f"_t{_tmp}.stl")
    export_stl(shape, f, tolerance=tol, angular_tolerance=0.3)
    n = int.from_bytes(open(f,'rb').read(84)[80:84],'little')
    d = np.fromfile(f, dtype=np.uint8, offset=84); rec=50; n=min(n, len(d)//rec)
    T = np.frombuffer(d[:n*rec].reshape(n,rec)[:,12:48].tobytes(),
                      dtype='<f4').reshape(n,3,3).astype(float)
    os.remove(f)
    return T

# ============================== 1. EXPLODED (svg, fans horizontally) =========
print("exploded:")
# explode along the true assembly axis (board Z); the eye is placed so that axis
# projects HORIZONTALLY -> wide landscape figure, per luna's height budget.
EX = [(Pos(0,0, 92)*bezel, "bezel"), (Pos(0,0, 34)*board_lite, "board"),
      (Pos(0,0,-26)*shell, "shell"),
      (Pos(0,0,-86)*diff, "diffuser")]
# CAMERA CORRECTED. The previous eye was (1500,-150,120) with up=(0,1,0) — almost
# pure +X, chosen so the Z explode-axis would project HORIZONTALLY and give luna the
# wide figure she asked for. But every part in this stack is FLAT IN XY, so an eye on
# the X axis sees them edge-on: the rendered figure was four vertical slivers, and a
# reader could not tell a bezel from a shell. The aspect ratio was right and the
# picture was useless.
#
# A three-quarter eye reads the parts at the cost of a squarer figure. That is the
# correct trade for the one image whose whole job is to show what the parts ARE and
# the order they stack in — an unreadable landscape strip is worse than a readable
# square. Explosion stays on the true assembly axis (board Z), so the figure remains
# a true statement about assembly rather than a pleasing arrangement.
eye, tgt = (760, -1020, 560), (25, 43, -5)
groups=[]
for s,_ in EX:
    # up is +Z now, not +Y: the camera moved off the X axis (see above), so world-up
    # is the natural up and the parts read as plates rather than as edges.
    p,k = project(s, eye, up=(0,0,1), target=tgt); groups.append((p,k))
write_svg(os.path.join(OUT,"case-exploded.svg"), groups, "case-exploded")

# ============================== 2. SECTION (svg) =============================
print("section:")
SEC_X = 47.0            # stand coords; == board x=40, the mic-port axis
asm = [to_stand(bezel), to_stand(shell), to_stand(board_lite), stand, base]
knife = E.bx(SEC_X-0.5, SEC_X+0.5, -20, 120, -20, 130)
groups=[]
for s in asm:
    try:
        cut = s & knife
        if cut.volume < 0.01: continue
        p,k = project(cut, (600, 30, 30), up=(0,0,1), target=(47,32,25))
        if p: groups.append((p,k))
    except Exception as e: print("   skip:", e)
write_svg(os.path.join(OUT,"case-section.svg"), groups, "case-section")

# ============================== 3. PRINT LAYOUT (svg) ========================
print("print layout:")
# Hand-placed offsets overlapped: the bezel was flipped with Rot(180,0,0), which puts it
# at NEGATIVE y and z instead of on the bed, so it collided with its neighbours in the
# projection. Pack from measured bounding boxes instead, and assert the result — a layout
# figure whose parts overlap teaches the wrong assembly.
_parts = [("bezel", Rot(180,0,0)*bezel), ("shell", shell), ("stand", stand),
          ("base", base), ("diffuser", diff)]
GAP = 14.0
LAY = []; _boxes = []; _x = 0.0
for _name, _p in _parts:
    _b = _p.bounding_box()
    # drop each part onto z=0 and butt it against the running x cursor
    _q = Pos(_x - _b.min.X, -_b.min.Y, -_b.min.Z) * _p
    _nb = _q.bounding_box()
    for _on, _ob in _boxes:
        if not (_nb.min.X > _ob.max.X or _nb.max.X < _ob.min.X or
                _nb.min.Y > _ob.max.Y or _nb.max.Y < _ob.min.Y):
            raise AssertionError(f"print layout: {_name} overlaps {_on}")
    _boxes.append((_name, _nb)); LAY.append(_q)
    _x = _nb.max.X + GAP
print(f"  packed {len(LAY)} parts across {_x-GAP:.0f}mm, no overlaps")
groups=[]
for s_ in LAY:
    p,k = project(s_, (60,-150,300), up=(0,1,0), target=((_x-GAP)/2,45,0)); groups.append((p,k))
write_svg(os.path.join(OUT,"case-print-layout.svg"), groups, "case-print")

# ============================== 4. HERO (png) ================================
print("hero:")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
COAL="#0A0604"
pieces=[(to_stand(bezel),(0.30,0.29,0.28)),(to_stand(shell),(0.22,0.21,0.20)),
        (stand,(0.26,0.25,0.24)),(base,(0.20,0.19,0.18)),
        (to_stand(board_lite),(0.05,0.06,0.08))]
fig=plt.figure(figsize=(14,7.875),facecolor=COAL)   # 16:9
ax=fig.add_subplot(111,projection='3d',facecolor=COAL)
# >>> WHY EVERY PART GOES INTO ONE COLLECTION <<<
# This previously called add_collection3d() once PER PART. matplotlib's 3D painter
# sorts triangles WITHIN a collection and does not sort BETWEEN collections — they are
# drawn in the order added. `stand` was third in the list and the slab first and
# second, so the stand painted straight over the slab and the case appeared to float
# BEHIND its own stand. Nothing was wrong with the geometry: a numeric check confirms
# the glass faces forward and the slab sits in the slot. It was a draw-order artefact
# that looked exactly like a modelling error, which is why it survived review.
#
# Merging everything into a single Poly3DCollection lets one painter sort see all the
# triangles at once. It is still a painter's algorithm — no true occlusion — but with
# convex-ish parts at this scale it resolves correctly.
key=np.array([0.45,-0.80,0.42]); key/=np.linalg.norm(key)
fill=np.array([-0.55,-0.35,0.75]); fill/=np.linalg.norm(fill)
allT=[]; allC=[]
for sh,base_col in pieces:
    T=tri_of(sh)
    n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); L=np.linalg.norm(n,axis=1); L[L==0]=1; n/=L[:,None]
    kd=np.clip(n@key,0,1); fd=np.clip(n@fill,0,1)
    amb=0.16
    r=np.clip(base_col[0]*(amb+0.62*kd)+0.95*kd**14+0.10*fd,0,1)
    g=np.clip(base_col[1]*(amb+0.62*kd)+0.55*kd**14+0.09*fd,0,1)
    b=np.clip(base_col[2]*(amb+0.62*kd)+0.22*kd**14+0.11*fd,0,1)
    allT.append(T); allC.append(np.stack([r,g,b],1))
T=np.concatenate(allT); C=np.concatenate(allC)
pc=Poly3DCollection(T,facecolors=C,edgecolors='none',shade=False)
pc.set_zsort('average')     # explicit: sort by mean depth, not by insertion order
ax.add_collection3d(pc)
V=T.reshape(-1,3); c=V.mean(0); rad=(V.max(0)-V.min(0)).max()/2*0.80
ax.set_xlim(c[0]-rad,c[0]+rad); ax.set_ylim(c[1]-rad,c[1]+rad); ax.set_zlim(c[2]-rad,c[2]+rad)
# FRONT three-quarter. The old azim=-72 looked at the BACK, so the hero showed vents
# and the LED window — informative, but not what "what does it look like on my desk"
# means. azim=-118 swings round to the screen side and keeps enough angle to read the
# stand's depth and the grille.
ax.set_box_aspect((1,1,1)); ax.view_init(elev=12,azim=-118); ax.set_axis_off()
fig.subplots_adjust(0,0,1,1)
fig.savefig(os.path.join(OUT,"case-hero.png"),dpi=100,facecolor=COAL)
plt.close(fig)
print("  case-hero.png", round(os.path.getsize(os.path.join(OUT,'case-hero.png'))/1024,1),"KB")
