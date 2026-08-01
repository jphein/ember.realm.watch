"""Line-art plumbing for the website figures: projection, plane sections, dimensions.

    import svg_util as S
    faces = S.section(part, "z", -15.0)
    polys = S.face_polys(faces, "z")
    S.write_svg(out, [(polys, "cover")], "mobile-bay", dims=[...])

WHY THIS FILE EXISTS. `make_renders.py` grew its own copy of the projection and SVG
writer inline, at module scope, in a script that BUILDS EVERY DESK FIGURE ON IMPORT --
so a second script cannot reuse one function from it without also rendering four
figures it did not ask for. That is not a criticism of that file; it was one script and
had no reason to be a library. It has one now. The plumbing here is lifted from it
verbatim where behaviour must match (`sample`, `project`, the stroke widths and the
hidden-line dash), so a figure written through either path looks like the same drawing.

⚠️ `make_renders.py` STILL CARRIES ITS OWN COPY. Migrating it is a mechanical change
behind a byte-identity check (regenerate into a temp dir, `cmp` against `site/renders/`)
and it was deliberately not bundled with the mobile figures, because a refactor of the
desk figures and an addition of new ones fail in different ways and should not land in
one commit. Whoever migrates it: delete the copies there, import these, and prove the
five committed SVGs come back byte-for-byte.

THE RULE THESE FIGURES OBEY, restated because it is the whole point: a figure carries no
hand-drawn geometry. Every outline here is sliced or projected out of the model, and
`dim()` MEASURES its own label off the two points it is given rather than accepting a
string. A number typed into a figure is a rumour about the part; a number measured from
it is a reading. The button outline on this project was once typed twice and the two
copies were free to disagree forever with nothing to notice -- they did.

SECTIONS RATHER THAN project_to_viewport, for the plane views. A section already lives
in a plane, so the orthographic map to the page is two of the three model coordinates
and nothing else -- which means an annotation point maps through the SAME two lines of
arithmetic as the geometry it annotates. Routing dimensions through the HLR projector
would leave no exact way to place a label, and a dimension line that lands a millimetre
off the feature it measures is worse than no dimension.
"""
from __future__ import annotations

import os

from build123d import *

# Which two model axes land on the page for each section normal, and which way is right.
#
# DERIVED, NOT PICKED, so the handedness of each view is a statement rather than a habit.
# For an eye on the +axis looking back down it with model +Z up (+Y up for the z view),
# the viewer's right is cross(view_direction, up):
#
#   z: d=(0,0,-1) up=(0,1,0) -> right=(1,0,0)   u=X  v=Y   (plan, from above)
#   x: d=(-1,0,0) up=(0,0,1) -> right=(0,1,0)   u=Y  v=Z   (from the +X side)
#   y: d=(0,1,0)  up=(0,0,1) -> right=(1,0,0)   u=X  v=Z   (transverse, from -Y)
#
# ⚠️ THE x VIEW IS THE ONE THAT WILL CATCH SOMEBODY. Model +Y runs to the viewer's RIGHT
# there, so a feature that is "further up the case" is further right on the page. No
# caption written against these figures may say left or right -- the coordinate cannot be
# mirrored but the apparent side flips with the view, exactly as it does between
# case-back.svg and case-print-layout.svg. Say +Y, or say "toward the brow".
_UV = {"z": (0, 1), "x": (1, 2), "y": (0, 2)}
_AX = {"x": 0, "y": 1, "z": 2}


def sample(edge, n):
    """n points along an edge, or [] if it has no parameterisation to walk."""
    try:
        return [(p.X, p.Y, p.Z) for p in (edge @ (i / (n - 1)) for i in range(n))]
    except Exception:
        return []


def _nseg(edge):
    """Sample by ARC LENGTH, not by a flat count.

    Verbatim from make_renders.py, including the reason: a flat 9 points made the M3
    countersinks read as visible OCTAGONS at figure scale -- a chamfer a reader could
    count the facets of. Bounding the chord error instead puts ~0.55mm per segment,
    well under a pixel-pair at the widths these are displayed at. Straight lines still
    cost two points, which is what keeps this cheap.
    """
    gt = str(edge.geom_type).upper()
    return 2 if "LINE" in gt else max(6, min(48, int(edge.length / 0.55) + 3))


def project(shape, eye, up=(0, 0, 1), target=(0, 0, 0), hidden=False):
    """Hidden-line projection -> (polys2d, kinds). For the 3D views only."""
    vis, hid = shape.project_to_viewport(viewport_origin=eye, viewport_up=up, look_at=target)
    edges = list(vis) + (list(hid) if hidden else [])
    polys, kinds = [], []
    for e in edges:
        p = [(x, y) for (x, y, _z) in sample(e, _nseg(e))]
        if len(p) >= 2:
            polys.append(p)
            kinds.append("hidden" if (hidden and e in hid) else "vis")
    return polys, kinds


def section(shape, axis, at, thickness=0.02):
    """The flat faces where `shape` crosses the plane `axis = at`.

    Slicing rather than shading, for the reason case-front.svg already records: a 0.80mm
    membrane or a 1.20mm rib is sub-pixel DEPTH at page scale, and a shaded view has only
    the recess side-walls to work with, so the feature reads as triangulation noise. A
    section cuts through the feature and nothing else, so the outlines ARE the feature.
    """
    k = _AX[axis]
    big, half = 400.0, 200.0
    size = [big, big, big]
    size[k] = thickness
    org = [-half, -half, -half]
    org[k] = at
    sl = shape & (Pos(*org) * Box(*size, align=(Align.MIN, Align.MIN, Align.MIN)))
    faces = [f for f in sl.faces()
             if abs(f.center().to_tuple()[k] - at) < max(thickness, 0.03)]
    if not faces:
        raise ValueError(f"no section geometry at {axis}={at} -- wrong plane?")
    return faces


def face_polys(faces, axis):
    """Section faces -> closed polylines on the page, outer wires and holes alike.

    Holes matter more than the outline in these figures: the vent slots, the hex windows
    and the tab reliefs are all INNER wires, so a drawing of outer wires only would show
    a solid block where every feature worth looking at is.
    """
    u, v = _UV[axis]
    out = []
    for f in faces:
        for w in [f.outer_wire()] + list(f.inner_wires()):
            poly = []
            for e in w.edges():
                pts = sample(e, _nseg(e))
                for p in pts:
                    q = (p[u], p[v])
                    if not poly or abs(q[0] - poly[-1][0]) > 1e-9 or abs(q[1] - poly[-1][1]) > 1e-9:
                        poly.append(q)
            if len(poly) >= 2:
                if poly[0] != poly[-1]:
                    poly.append(poly[0])
                out.append(poly)
    return out


def bbox_polys(shape, axis):
    """The part's silhouette in the section plane, as a light context rectangle."""
    b = shape.bounding_box()
    u, v = _UV[axis]
    lo = b.min.to_tuple()
    hi = b.max.to_tuple()
    x0, x1, y0, y1 = lo[u], hi[u], lo[v], hi[v]
    return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]]


# ------------------------------------------------------------------ dimensions
def dim(p0, p1, off=0.0, side="v", text=None, tick=1.1, places=2):
    """A dimension between two points ON THE PAGE, with the label MEASURED off them.

    `text=None` is the default and the intended use: the label is the distance between
    the two points actually drawn, so it cannot disagree with the line under it. Pass a
    string only for a label that is not a length (a count, a name, a units suffix), and
    understand that you have just typed a number into a figure.

    Returns (polys, labels) -- labels are (x, y, string, anchor) in page coordinates.
    """
    (x0, y0), (x1, y1) = p0, p1
    if side == "v":                      # dimension runs horizontally, offset in y
        y = y0 + off
        line = [[(x0, y), (x1, y)]]
        line += [[(x0, y - tick), (x0, y + tick)], [(x1, y - tick), (x1, y + tick)]]
        val = abs(x1 - x0)
        lab = ((x0 + x1) / 2, y, "middle")
    else:                                # dimension runs vertically, offset in x
        x = x0 + off
        line = [[(x, y0), (x, y1)]]
        line += [[(x - tick, y0), (x + tick, y0)], [(x - tick, y1), (x + tick, y1)]]
        val = abs(y1 - y0)
        # OFF the line, not on it. Centred on a vertical dimension the glyphs sit across
        # the very line they measure and both become harder to read than either alone.
        lab = (x - tick - 0.6, (y0 + y1) / 2, "end")
    s = text if text is not None else f"{val:.{places}f}"
    return line, [(lab[0], lab[1], s, lab[2])]


def leader(p, to, text):
    """A labelled leader line to a feature that is too small to dimension across."""
    return [[p, to]], [(to[0], to[1], text, "start")]


# ------------------------------------------------------------------- the writer
def write_svg(path, groups, prefix, dims=(), pad=6.0, target_w=1200,
              flip_v=True, label_px=27.0, swap=False):
    """groups: (polys, name) or (polys, kinds, name). One coordinate space throughout.

    Stroke is `currentColor` and nothing here sets a colour, which is why these are
    INLINED into the page rather than referenced as <img>: a raster or a hardcoded
    palette is locked to the theme it was made in -- dark line art vanishes on a dark
    page and light line art vanishes on a light one, and no single file satisfies both.
    CSS cannot cross an <img> boundary. currentColor inherits whatever the page uses, so
    one figure is correct in both themes.

    Group names become path ids (`mobile-bay-vent-vis`), so they are CSS handles the
    stylesheet uses to pick one feature out of a busy field. Named by IDENTITY, never by
    position -- a positional id silently re-points at a different feature the moment a
    group is inserted above it.

    `label_px` is in viewBox units and the default is sized for the page, not for the file:
    every figure here is written at a 1200-unit viewBox and the site renders it into a 74ch
    column (~660px), so the on-screen size is about 0.55x whatever is set. At the 15 this
    started on, the dimensions came out ~8px and were decoration rather than information.

    Labels are real <text>, deliberately, and it is a departure from the desk figures
    (which carry none). A dimension has to be read: <text> is selectable, searchable,
    reaches a screen reader, scales with the page, and costs a fraction of the same
    glyphs as stroked outlines. It stays self-contained because the family is a generic
    system stack -- no font is fetched, which is the invariant that actually matters.
    """
    # `swap` transposes the page axes. It exists for the vent figure: that section is
    # 2.20mm of wall against 25.60mm of labyrinth, so in its natural orientation the
    # drawing is a sliver two hundred pixels wide and two thousand tall, and the feature
    # is unreadable at any width a page will give it. Transposed, the gas path runs along
    # the long edge and the figure fits a text column.
    #
    # ⚠️ TRANSPOSING CHANGES WHICH MODEL AXIS IS "ACROSS", so the caption's handedness
    # claim changes with it. This is the same trap the desk figures carry between
    # case-back and case-print-layout: the coordinate cannot be mirrored, the apparent
    # side can. State the axis, never the side.
    def _t(p):
        return (p[1], p[0]) if swap else p

    norm = []
    for i, g in enumerate(groups):
        if len(g) == 3:
            norm.append(([[_t(q) for q in poly] for poly in g[0]], g[1], g[2]))
        else:
            norm.append(([[_t(q) for q in poly] for poly in g[0]],
                         ["vis"] * len(g[0]), g[1] if len(g) > 1 else f"g{i}"))

    dim_polys, dim_labels = [], []
    for d in dims:
        dim_polys += [[_t(q) for q in poly] for poly in d[0]]
        dim_labels += [(_t((lx, ly))[0], _t((lx, ly))[1], s, a)
                       for (lx, ly, s, a) in d[1]]

    allp = [pt for _p, _k, _n in norm for poly in _p for pt in poly]
    allp += [pt for poly in dim_polys for pt in poly]
    # Label anchors count toward the extent. They are not geometry, but a label pushed
    # outside the viewBox is simply invisible -- and an invisible dimension reads as a
    # figure that was never dimensioned rather than as a bug.
    allp += [(lx, ly) for (lx, ly, _s, _a) in dim_labels]
    if not allp:
        raise ValueError("nothing to draw")
    xs = [p[0] for p in allp]
    ys = [p[1] for p in allp]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    w, h = x1 - x0, y1 - y0
    s = target_w / w

    def X(px):
        return (px - x0) * s

    def Y(py):
        return (y1 - py) * s if flip_v else (py - y0) * s

    def path_of(poly):
        d = f"M{X(poly[0][0]):.0f} {Y(poly[0][1]):.0f}"
        last = None
        for px, py in poly[1:]:
            q = (round(X(px)), round(Y(py)))
            if q != last:
                d += f"L{q[0]} {q[1]}"
            last = q
        return d

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w*s:.1f} {h*s:.1f}" '
           f'width="{w*s:.0f}" height="{h*s:.0f}" fill="none" stroke="currentColor" '
           f'stroke-linecap="round" stroke-linejoin="round" role="img">']
    for polys, kinds, name in norm:
        hid = [p for p, k in zip(polys, kinds) if k == "hidden"]
        vis = [p for p, k in zip(polys, kinds) if k == "vis"]
        if hid:
            out.append(f'<path id="{prefix}-{name}-hidden" '
                       f'd="{" ".join(path_of(p) for p in hid)}" stroke-width="0.7" '
                       f'stroke-opacity="0.35" stroke-dasharray="4 3" '
                       f'vector-effect="non-scaling-stroke"/>')
        if vis:
            out.append(f'<path id="{prefix}-{name}-vis" '
                       f'd="{" ".join(path_of(p) for p in vis)}" stroke-width="1.4" '
                       f'vector-effect="non-scaling-stroke"/>')
    if dim_polys:
        out.append(f'<path id="{prefix}-dim" '
                   f'd="{" ".join(path_of(p) for p in dim_polys)}" stroke-width="0.9" '
                   f'stroke-opacity="0.55" vector-effect="non-scaling-stroke"/>')
    for lx, ly, txt, anchor in dim_labels:
        out.append(f'<text x="{X(lx):.0f}" y="{Y(ly)-3:.0f}" fill="currentColor" '
                   f'stroke="none" font-size="{label_px:.0f}" text-anchor="{anchor}" '
                   f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
                   f'opacity="0.75">{txt}</text>')
    out.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(out))
    print(f"  {os.path.basename(path):28s} {os.path.getsize(path)/1024:6.1f} KB   "
          f"ratio {w/h:.2f}:1   {len(dim_labels)} labels")
    return os.path.getsize(path) / 1024


def tri_of(shape, tmpdir, tol=0.06):
    """Tessellate via an STL round-trip.

    shape.tessellate() raises on some boolean results -- a face comes back with no
    triangulation -- and export_stl never does.
    """
    import numpy as np
    f = os.path.join(tmpdir, "_svgutil_tmp.stl")
    export_stl(shape, f, tolerance=tol, angular_tolerance=0.3)
    n = int.from_bytes(open(f, "rb").read(84)[80:84], "little")
    d = np.fromfile(f, dtype=np.uint8, offset=84)
    rec = 50
    n = min(n, len(d) // rec)
    T = np.frombuffer(d[:n * rec].reshape(n, rec)[:, 12:48].tobytes(),
                      dtype="<f4").reshape(n, 3, 3).astype(float)
    os.remove(f)
    return T
