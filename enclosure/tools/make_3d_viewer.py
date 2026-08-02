#!/usr/bin/env python3
"""Build a self-contained 3D viewer for queue STLs and open it in the browser.

WHY THIS EXISTS (2026-08-01)

JP inspects parts BEFORE they print — that inspection caught the hook-retention
printability failure and the strip-seat mismatch before they cost filament. PrusaSlicer
froze doing this job; this replaces it with a single self-contained HTML file: both/all
parts embedded base64, three.js orbit controls, per-part visibility toggles, the rev+sha
from each queue filename shown in the HUD so there is never doubt about WHICH geometry
is on screen.

STANDING RULE (JP, 2026-08-01): renders are shown to JP THIS WAY before every print.
The pre-print sequence is: queue file → this viewer → JP looks → JP says "bed clear,
go" → print. See memory feedback-preprint-3d-preview.

USAGE
  python3 tools/make_3d_viewer.py                 # all mobile parts from the queue
  python3 tools/make_3d_viewer.py ember-stand     # any queue part name prefixes
  python3 tools/make_3d_viewer.py --all           # every part in the queue
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
#hud{position:fixed;top:10px;left:12px;z-index:2;background:rgba(0,0,0,.25);padding:8px 12px;border-radius:8px}
#hud b{font-size:16px} label{display:block;margin-top:6px;cursor:pointer;user-select:none}
label small{opacity:.6}
#hint{position:fixed;bottom:10px;left:12px;opacity:.6;z-index:2}
canvas{display:block}
</style></head><body>
<div id="hud"><b>&#128293; pre-print check</b><span id="boxes"></span></div>
<div id="hint">drag = orbit &middot; scroll = zoom &middot; right-drag = pan &middot; parts sit in PRINT orientation</div>
<script type="importmap">{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
const PARTS=[__BLOBS__];
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,1,3000);
const ren=new THREE.WebGLRenderer({antialias:true,alpha:true});
ren.setSize(innerWidth,innerHeight);document.body.appendChild(ren.domElement);
scene.add(new THREE.HemisphereLight(0xfff2dd,0x332211,1.1));
const d1=new THREE.DirectionalLight(0xffffff,1.4);d1.position.set(1,1,2);scene.add(d1);
const d2=new THREE.DirectionalLight(0xe8b25a,.5);d2.position.set(-2,-1,-1);scene.add(d2);
const loader=new STLLoader();const colors=[0xd9c9a8,0x9a7b4f,0xb0a284,0x7d6a4a];
const group=new THREE.Group();scene.add(group);
let off=0;
PARTS.forEach((p,i)=>{
  const buf=Uint8Array.from(atob(p.b64),c=>c.charCodeAt(0)).buffer;
  const g=loader.parse(buf);g.computeVertexNormals();g.computeBoundingBox();
  const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:colors[i%4],metalness:.05,roughness:.65}));
  const w=g.boundingBox.max.x-g.boundingBox.min.x;
  m.position.x=off-g.boundingBox.min.x; off+=w+14;
  group.add(m);
  const l=document.createElement('label');
  const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;
  cb.onchange=e=>m.visible=e.target.checked;
  const sm=document.createElement('small');sm.textContent=p.tag;
  // flip 180 about X: shows the BED FACE (underside) without wrestling the orbit.
  const fb=document.createElement('button');fb.textContent='\u27F2 flip';
  fb.style.cssText='margin-left:8px;font:12px system-ui;cursor:pointer;background:none;border:1px solid currentColor;border-radius:4px;color:inherit;padding:1px 6px';
  const cz=(g.boundingBox.min.z+g.boundingBox.max.z)/2;
  fb.onclick=e=>{e.preventDefault();m.rotation.x=m.rotation.x?0:Math.PI;
    m.position.z=m.rotation.x?2*cz:0;};
  l.appendChild(cb);l.appendChild(document.createTextNode(' '+p.name+' '));l.appendChild(sm);l.appendChild(fb);
  document.getElementById('boxes').appendChild(l);
});
const bb=new THREE.Box3().setFromObject(group),c=bb.getCenter(new THREE.Vector3()),s=bb.getSize(new THREE.Vector3());
group.position.sub(c);
cam.position.set(s.x*.8,-Math.max(s.length()*.9,120),s.z*1.2);cam.up.set(0,0,1);
const ctl=new OrbitControls(cam,ren.domElement);ctl.enableDamping=true;
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();ren.setSize(innerWidth,innerHeight)});
(function anim(){requestAnimationFrame(anim);ctl.update();ren.render(scene,cam)})();
</script></body></html>"""


def pick_files(argv: list[str]) -> list[str]:
    stls = sorted(glob.glob(os.path.join(QUEUE, "*.stl")))
    if "--all" in argv:
        return stls
    prefixes = [a for a in argv if not a.startswith("-")]
    if prefixes:
        chosen = [f for f in stls if any(os.path.basename(f).startswith(p) for p in prefixes)]
        if not chosen:
            sys.exit(f"no queue STL matches {prefixes} — queue has: "
                     + ", ".join(os.path.basename(f) for f in stls))
        return chosen
    return [f for f in stls if "mobile" in os.path.basename(f)] or stls


def main() -> int:
    files = pick_files(sys.argv[1:])
    blobs = []
    for f in files:
        base = os.path.basename(f)[:-4]
        part = base.split("_r")[0]
        tag = base[len(part) + 1:]                       # e.g. r4_44f36abb
        b64 = base64.b64encode(open(f, "rb").read()).decode()
        blobs.append(f'{{name:"{part}", tag:"{tag}", b64:"{b64}"}}')
    html = TEMPLATE.replace("__BLOBS__", ",\n".join(blobs))
    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"preview: {OUT}  ({os.path.getsize(OUT)//1024} KB, {len(files)} part(s))")
    for f in files:
        print(f"  {os.path.basename(f)}")
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
