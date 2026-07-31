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

def whose(path, digest, depth=12):
    """Which recent commit's blob do these served bytes match?

    This is the decisive test for "stale artifact vs stale edge", and it is strictly better
    than re-reading. Three identical reads inside one 300s cache window prove nothing — they
    are one observation taken three times. But if the served bytes ARE a recent ancestor's
    version, the edge is simply behind and will catch up; if they match nothing in history,
    something is actually wrong and no amount of waiting fixes it.
    """
    out = git("log", "--format=%h", f"-{depth}")
    if not out: return None
    for c in out.decode().split():
        blob = git("show", f"{c}:{path}")
        if blob is not None and sha(blob) == digest:
            behind = git("rev-list", "--count", f"{c}..{REF}")
            return c, int(behind.decode().strip()) if behind else -1
    return None
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
    if sha(served) == sha(src):
        rows.append((label, "match", f"{sha(served)} vs {sha(src)}  {len(served)}b",
                     note, url, path)); return
    # IDENTIFY BEFORE WAITING. Asking which commit the served bytes match is free and
    # decisive; re-reading costs a cache TTL and, inside one window, only repeats a single
    # observation. If the bytes are a recent ancestor's, the edge is behind and will catch
    # up. If they match nothing in history, waiting will not help and something is wrong.
    w = whose(path, sha(served))
    if w:
        rows.append((label, f"edge behind ({w[1]})",
                     f"{sha(served)} vs {sha(src)}  -> serving {w[0]}, {w[1]} commit(s) behind",
                     note, url, path))
    else:
        rows.append((label, "*** STALE ***",
                     f"{sha(served)} vs {sha(src)}  -> matches NO recent commit",
                     note, url, path))

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
mismatched = [r for r in rows if r[1] == "*** STALE ***"]  # unexplained only
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
        detail = f"{sha(served)} vs {sha(src)}"
        if meta: detail += f"  [age={meta.get('age')} cc={meta.get('cc')}]"
        verdict = "match (edge caught up)"
        if not agree:
            w = whose(path, sha(served))
            if w:
                verdict = f"edge behind ({w[1]})"
                detail += f"  -> serving {w[0]}, {w[1]} commit(s) behind"
            else:
                verdict = "*** STALE ***"
                detail += "  -> matches NO recent commit — investigate"
                still.append(r[0])
        rows[i] = (r[0], verdict, detail, r[3], url, path)
    print(f"after re-read: {len(still)} genuinely stale "
          f"({', '.join(still) if still else 'none — all were edge lag'})\n")

w = max(len(r[0]) for r in rows)
for r in rows: print(f"{r[0]:{w}s}  {r[1]:22s} {r[2]}  {r[3]}")
bad = [r for r in rows if not (r[1].startswith("match") or r[1].startswith("edge behind"))]
behind = [r for r in rows if r[1].startswith("edge behind")]
if behind:
    n = max(int(r[1].split("(")[1].rstrip(")")) for r in behind)
    print(f"\n{len(behind)} artifact(s) served from an OLDER COMMIT — the edge is up to {n} "
          f"commit(s) behind. Expected for a few minutes after a push (raw is max-age=300, "
          f"Pages 600).\n⚠️  If this persists well past the TTL it stops being lag: re-run, and "
          f"if it holds, treat it as a real failure to publish.")
    for r in behind: print(f"    {r[0]}: {r[2].split('->')[-1].strip()}")
print(f"\n{len(bad)} of {len(rows)} not matching")
for r in bad: print("   ", r[0], r[1], r[2], r[3])

# separately: is the LOCAL tree ahead of / behind the remote? different question, not a defect
ahead = git("rev-list","--count",f"{REF}..HEAD"); behind = git("rev-list","--count",f"HEAD..{REF}")
dirty = git("status","--porcelain")
print(f"\n[local vs remote — NOT a served-surface defect] ahead {ahead.decode().strip()}, "
      f"behind {behind.decode().strip()}, dirty files {len(dirty.decode().splitlines())}")
