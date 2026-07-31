#!/usr/bin/env python3
"""Is what a VISITOR downloads the current thing?

TWO TRAPS, BOTH OF WHICH PRODUCED FALSE STALEs BEFORE THEY WERE UNDERSTOOD.

⚠️ 1. THE REFERENCE MUST BE origin/main, NOT THE WORKING TREE. An earlier version compared
served bytes against local files and reported three false STALEs, purely because a teammate
had committed locally without pushing. "Served differs from my disk" is not the bug;
"served differs from what the remote would produce" is.

⚠️ 2. RUN IMMEDIATELY AFTER A PUSH, THIS MEASURES THE EDGE, NOT THE PUSH. Observed: the
fixed stand STL was pushed and the raw link kept serving the OLD blob for about a minute
(t+25s stale, t+50s match). For that window the page said "fixed" over a download that
was not — the exact state a commit-ordering hold was meant to prevent, arriving by a
route ordering cannot reach.

    Both surfaces are ordinary Fastly/Varnish edge caches, measured repeatedly:

      GitHub Pages : cache-control: max-age=600, via: 1.1 varnish, and an `age:` header.
      raw.github.. : cache-control: max-age=300, via: 1.1 varnish. `age:` is usually
                     absent because x-served-by changes on nearly every request — a
                     fleet of edge nodes, so requests keep landing on cold ones.

    ⚠️ AN EARLIER VERSION OF THIS DOCSTRING SAID raw SENDS `no-cache` AND IS THEREFORE
    "NOT AN HTTP CACHE AT ALL, BUT REPLICATION LAG WITH NO HEADER TO BOUND IT". THAT WAS
    WRONG, AND THE WAY IT WAS WRONG IS THE POINT. It was measured with

        curl -sI https://github.com/<o>/<r>/raw/main/<path>          # no -L

    which is a 302 to raw.githubusercontent.com. `curl -I` without `-L` reports the
    headers of the REDIRECT, and github.com sends `cache-control: no-cache` on that hop.
    So the reading was accurate about an object nobody downloads. Follow the redirect,
    or address raw.githubusercontent.com directly, and it is max-age=300 every time.

    (The page links visitors at the github.com/raw form, so a real visitor takes both
    hops: an uncached 302, then a 300s-cached object.)

    THE FIX DID NOT CHANGE, AND THAT IS WHY IT SURVIVED THE CORRECTION. Re-read and
    report only what persists is correct against an edge cache and against replication
    lag alike, and needs no header to work. A wrong stated reason attached to a correct
    fix is worse than no reason, because it licenses the wrong change later — so the
    reason is now the measured one.

This is the same family as the two above: an instrument whose correctness depends on a
condition it does not check. The reference point was the first one; timing is the second.
"""
import hashlib, os, subprocess, sys, urllib.request
BASE = "https://jphein.github.io/ember.realm.watch"
RAW  = "https://github.com/jphein/ember.realm.watch/raw/main"
REPO = "/home/jp/Projects/ember.realm.watch"

def git(*a):
    r = subprocess.run(["git","-C",REPO,*a], capture_output=True)
    return r.stdout if r.returncode == 0 else None
def sha(b): return hashlib.sha256(b).hexdigest()[:16] if b is not None else "-"
def fetch(u, with_meta=False):
    try:
        with urllib.request.urlopen(u, timeout=60) as r:
            body = r.read()
            if with_meta:
                h = r.headers
                return body, {"age": h.get("age"), "cc": h.get("cache-control"),
                              "by": h.get("x-served-by")}
            return body
    except Exception:
        return (None, {}) if with_meta else None

git("fetch","-q")
REF = "origin/main"
rows = []
def check(label, url, path, note=""):
    served, src = fetch(url), git("show", f"{REF}:{path}")
    if served is None: rows.append((label,"FETCH-FAIL","",note,url,path)); return
    if src is None:    rows.append((label,"NOT-ON-REMOTE",path,note,url,path)); return
    ok = sha(served) == sha(src)
    rows.append((label, "match" if ok else "*** STALE ***",
                 f"{sha(served)} vs {sha(src)}  {len(served)}b", note, url, path))

# controls, run against the same machinery the real checks use
ctl_a = fetch(f"{BASE}/index.html"); ctl_b = git(f"show", f"{REF}:docs/index.html")
print("negative control (served index.html vs remote docs/index.html):",
      "PASS" if sha(ctl_a)==sha(ctl_b) else "FAIL/pending — Pages may still be building")
ctl_c = git("show", f"{REF}:enclosure/PRINT-SHEET.md")
print("positive control (served index.html vs remote PRINT-SHEET.md):",
      "PASS" if sha(ctl_a)!=sha(ctl_c) else "FAIL — method is blind")
print()

check("index.html",       f"{BASE}/index.html",       "docs/index.html")
check("print-sheet.html", f"{BASE}/print-sheet.html", "docs/print-sheet.html")
for a in ("case-hero.png","og-card.png","dragon_sheet.png","wyrm_startle_shipped.png",
          "favicon.svg","wyrm-states.svg"):
    check(f"assets/{a}", f"{BASE}/assets/{a}", f"docs/assets/{a}")
for w in ("announce","done","error","listening","thinking","touch"):
    check(f"assets/chime_{w}.wav", f"{BASE}/assets/chime_{w}.wav", f"docs/assets/chime_{w}.wav")
for m in ("enclosure.md","home-assistant.md","verification.md","audio-pop.md","README.md"):
    check(f"docs/{m}", f"{BASE}/{m}", f"docs/{m}")
for s in ("ember-front-bezel","ember-back-shell","ember-stand","ember-stand-base"):
    check(f"STL {s}", f"{RAW}/enclosure/{s}.stl", f"enclosure/{s}.stl", "linked from the page")
check("ember_case.py", f"{RAW}/enclosure/ember_case.py", "enclosure/ember_case.py", "linked from the page")

if "--prove-confirm" in sys.argv:
    # positive control for the confirm path: compare a real served file against the WRONG
    # source, so it must mismatch on both reads and be reported as genuinely stale.
    check("PROBE (must stay stale)", f"{BASE}/print-sheet.html", "docs/index.html", "control")

# --- CONFIRM: never report a mismatch on one observation (see trap 2) ---
CONFIRM = "--no-confirm" not in sys.argv
mismatched = [r for r in rows if r[1] == "*** STALE ***"]
if mismatched and CONFIRM:
    import time
    wait = int(os.environ.get("SERVED_CONFIRM_WAIT", "60"))
    print(f"\n{len(mismatched)} apparent mismatch(es). NOT reporting yet — re-reading in "
          f"{wait}s, because a single read cannot tell a stale artifact from a stale edge.")
    for r in mismatched:
        _, meta = fetch(r[4] if len(r) > 4 else "", with_meta=True)
    time.sleep(wait)
    still = []
    for i, r in enumerate(rows):
        if r[1] != "*** STALE ***":
            continue
        url, path = r[4], r[5]
        served, meta = fetch(url, with_meta=True)
        src = git("show", f"{REF}:{path}")
        agree = sha(served) == sha(src)
        rows[i] = (r[0], "match (edge caught up)" if agree else "*** STALE ***",
                   f"{sha(served)} vs {sha(src)}"
                   + (f"  [age={meta.get('age')} cc={meta.get('cc')}]" if meta else ""),
                   r[3], url, path)
        if not agree:
            still.append(r[0])
    print(f"after re-read: {len(still)} genuinely stale "
          f"({', '.join(still) if still else 'none — all were edge lag'})\n")

w = max(len(r[0]) for r in rows)
for r in rows: print(f"{r[0]:{w}s}  {r[1]:22s} {r[2]}  {r[3]}")
bad = [r for r in rows if not r[1].startswith("match")]
print(f"\n{len(bad)} of {len(rows)} not matching")
for r in bad: print("   ", r[0], r[1], r[2], r[3])

# separately: is the LOCAL tree ahead of / behind the remote? different question, not a defect
ahead = git("rev-list","--count",f"{REF}..HEAD"); behind = git("rev-list","--count",f"HEAD..{REF}")
dirty = git("status","--porcelain")
print(f"\n[local vs remote — NOT a served-surface defect] ahead {ahead.decode().strip()}, "
      f"behind {behind.decode().strip()}, dirty files {len(dirty.decode().splitlines())}")
