#!/usr/bin/env python3
"""Build a self-contained 3D viewer for queue STLs and open it in the browser.

WHY THIS EXISTS (2026-08-01)

JP inspects parts BEFORE they print — that inspection caught the hook-retention
printability failure and the strip-seat mismatch before they cost filament. PrusaSlicer
froze doing this job; this replaces it with a single self-contained HTML file: parts
embedded base64, three.js orbit controls, per-part visibility toggles, the rev+sha
from each queue filename shown in the HUD so there is never doubt about WHICH geometry
is on screen.

STANDING RULE (JP, 2026-08-01): renders are shown to JP THIS WAY before every print.
The pre-print sequence is: queue file → this viewer → JP looks → JP says "bed clear,
go" → print. See memory feedback-preprint-3d-preview.

TABS (JP, 2026-08-02): "the preprint check should have tabs with the constructed ones."
The viewer now carries two tabs — 🖨 Print (queue STLs, bed orientation, flippable) and
🧩 Constructed (the mated slabs + docked tableaus from tools/make_assembly_view.py).
The Constructed tab appears whenever print/assembly/*.stl exists; rebuild those with
make_assembly_view.py after any geometry merge or they show the previous design.

USAGE
  python3 tools/make_3d_viewer.py                 # mobile queue parts + constructed tab
  python3 tools/make_3d_viewer.py ember-stand     # queue part name prefixes + constructed
  python3 tools/make_3d_viewer.py --all           # every queue part + constructed
  python3 tools/make_3d_viewer.py --assembly      # constructed scenes only
  python3 tools/make_3d_viewer.py --no-open       # write the file, don't launch

Output: enclosure/print/preview.html (gitignored — derived artifact, rebuilt at will).
Opens in Brave when available, else the default browser via xdg-open.
"""
from __future__ import annotations

import base64
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.normpath(os.path.join(HERE, "..", "print"))
OUT = os.path.join(QUEUE, "preview.html")

TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ember — pre-print 3D</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#128293;</text></svg>">
<style>
:root{color-scheme:dark light}
body{margin:0;font:14px system-ui;background:#14110f;color:#e8b25a;overflow:hidden}
@media(prefers-color-scheme:light){body{background:#f5efe6;color:#7a4a12}}
#hud{position:fixed;top:10px;left:12px;z-index:2;background:rgba(0,0,0,.25);padding:8px 12px;border-radius:8px;max-height:85vh;overflow-y:auto}
#hud b{font-size:16px} label{display:block;margin-top:6px;cursor:pointer;user-select:none}
label small{opacity:.6}
#tabs{margin:8px 0 2px 0;display:flex;gap:6px}
#tabs button{font:13px system-ui;cursor:pointer;background:none;border:1px solid currentColor;border-radius:6px;color:inherit;padding:3px 10px;opacity:.55}
#tabs button.on{opacity:1;font-weight:600}
#hint{position:fixed;bottom:10px;left:12px;opacity:.6;z-index:2}
canvas{display:block}
</style></head><body>
<div id="hud"><b>&#128293; pre-print check</b><div id="tabs"></div><span id="boxes"></span></div>
<div id="hint">drag = orbit &middot; scroll = zoom &middot; right-drag = pan</div>
<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
const PARTS=[__BLOBS__];
const TAB_NAME={print:'\\u{1F5A8} Print', built:'\\u{1F9E9} Constructed'};
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,1,5000);
const ren=new THREE.WebGLRenderer({antialias:true,alpha:true});
ren.setSize(innerWidth,innerHeight);document.body.appendChild(ren.domElement);
scene.add(new THREE.HemisphereLight(0xfff2dd,0x332211,1.1));
const d1=new THREE.DirectionalLight(0xffffff,1.4);d1.position.set(1,1,2);scene.add(d1);
const d2=new THREE.DirectionalLight(0xe8b25a,.5);d2.position.set(-2,-1,-1);scene.add(d2);
const loader=new STLLoader();const colors=[0xd9c9a8,0x9a7b4f,0xb0a284,0x7d6a4a];
const groups={};const offs={};
PARTS.forEach((p,i)=>{
  if(!groups[p.tab]){const g=new THREE.Group();groups[p.tab]=g;scene.add(g);offs[p.tab]=0;}
  const buf=Uint8Array.from(atob(p.b64),c=>c.charCodeAt(0)).buffer;
  const g=loader.parse(buf);g.computeVertexNormals();g.computeBoundingBox();
  // DoubleSide: walls stay opaque from inside too. Single-sided culling made interior
  // views into a glass box — the far flank's labels showed through a vanished near wall,
  // MIRRORED, and twice read as "the labels are backwards". The part was always correct.
  const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:colors[i%4],metalness:.05,roughness:.65,side:THREE.DoubleSide}));
  if(p.tab==='print'){const w=g.boundingBox.max.x-g.boundingBox.min.x;
    m.position.x=offs.print-g.boundingBox.min.x; offs.print+=w+14;}
  groups[p.tab].add(m);
  const l=document.createElement('label');l.dataset.tab=p.tab;
  const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;
  cb.onchange=e=>m.visible=e.target.checked;
  const sm=document.createElement('small');sm.textContent=p.tag;
  l.appendChild(cb);l.appendChild(document.createTextNode(' '+p.name+' '));l.appendChild(sm);
  if(p.tab==='print'){
    // flip 180 about X: shows the BED FACE (underside) without wrestling the orbit.
    const fb=document.createElement('button');fb.textContent='\\u27F2 flip';
    fb.style.cssText='margin-left:8px;font:12px system-ui;cursor:pointer;background:none;border:1px solid currentColor;border-radius:4px;color:inherit;padding:1px 6px';
    const cz=(g.boundingBox.min.z+g.boundingBox.max.z)/2;
    fb.onclick=e=>{e.preventDefault();m.rotation.x=m.rotation.x?0:Math.PI;
      m.position.z=m.rotation.x?2*cz:0;};
    l.appendChild(fb);
  }
  document.getElementById('boxes').appendChild(l);
});
const ctl=new OrbitControls(cam,ren.domElement);ctl.enableDamping=true;cam.up.set(0,0,1);
function fit(tab){
  const bb=new THREE.Box3().setFromObject(groups[tab]);
  const c=bb.getCenter(new THREE.Vector3()),s=bb.getSize(new THREE.Vector3());
  ctl.target.copy(c);
  cam.position.set(c.x+s.x*.4,c.y-Math.max(s.length()*.8,120),c.z+Math.max(s.z*1.5,60));
}
const tabs=Object.keys(groups);
let active=tabs[0];
const bar=document.getElementById('tabs');
tabs.forEach(t=>{
  const b=document.createElement('button');b.textContent=TAB_NAME[t]||t;b.id='tab-'+t;
  b.onclick=()=>setTab(t);bar.appendChild(b);
});
function setTab(t){
  active=t;
  tabs.forEach(x=>{
    groups[x].visible=(x===t);
    document.getElementById('tab-'+x).classList.toggle('on',x===t);
  });
  document.querySelectorAll('#boxes label').forEach(l=>{
    l.style.display=(l.dataset.tab===t)?'block':'none';
  });
  fit(t);
}
setTab(active);
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();ren.setSize(innerWidth,innerHeight)});
(function anim(){requestAnimationFrame(anim);ctl.update();ren.render(scene,cam)})();
</script></body></html>"""


def pick_files(argv: list[str]) -> list[tuple[str, str]]:
    """Return [(path, tab)] — tab is 'print' or 'built'."""
    built = sorted(glob.glob(os.path.join(QUEUE, "assembly", "*.stl")))
    if "--assembly" in argv:
        if not built:
            sys.exit("no assembly STLs — run tools/make_assembly_view.py first")
        return [(f, "built") for f in built]
    stls = sorted(glob.glob(os.path.join(QUEUE, "*.stl")))
    if "--all" in argv:
        chosen = stls
    else:
        prefixes = [a for a in argv if not a.startswith("-")]
        if prefixes:
            chosen = [f for f in stls if any(os.path.basename(f).startswith(p) for p in prefixes)]
            if not chosen:
                sys.exit(f"no queue STL matches {prefixes} — queue has: "
                         + ", ".join(os.path.basename(f) for f in stls))
        else:
            chosen = [f for f in stls if "mobile" in os.path.basename(f)] or stls
    return [(f, "print") for f in chosen] + [(f, "built") for f in built]


def main() -> int:
    files = pick_files(sys.argv[1:])
    blobs = []
    for f, tab in files:
        base = os.path.basename(f)[:-4]
        part = base.split("_r")[0]
        tag = base[len(part) + 1:] if "_r" in base else "constructed"
        b64 = base64.b64encode(open(f, "rb").read()).decode()
        blobs.append(f'{{name:"{part}", tag:"{tag}", b64:"{b64}", tab:"{tab}"}}')
    html = TEMPLATE.replace("__BLOBS__", ",\n".join(blobs))
    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"preview: {OUT}  ({os.path.getsize(OUT)//1024} KB, {len(files)} part(s))")
    for f, tab in files:
        print(f"  [{tab}] {os.path.basename(f)}")
    if "--no-open" not in sys.argv:
        # Brave when present (JP's ask), else the desktop default.
        for cand in ("brave-browser", "brave"):
            if shutil.which(cand):
                subprocess.Popen([cand, OUT], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                break
        else:
            if subprocess.run(["flatpak", "info", "com.brave.Browser"],
                              capture_output=True).returncode == 0:
                subprocess.Popen(["flatpak", "run", "com.brave.Browser", OUT],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["xdg-open", OUT], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
