#!/usr/bin/env python3
"""The print queue: ONE file per part, revision in the filename, refreshed by the build.

WHY THIS EXISTS (2026-07-31)

JP nearly printed the wrong bezel. The correct STL and the superseded one were both named
`ember-front-bezel.stl` — one in `enclosure/`, one in the frozen `print-ready/` set — and
the only thing distinguishing them was a sha256, which no slicer shows. A filename that
does not carry its version cannot be told apart from its own stale twin at the moment of
use, and the moment of use is a slicer's file picker, not a terminal.

THE SCHEME

  enclosure/print/ember-front-bezel_r2_5f3fc539.stl
                                    ^^  ^^^^^^^^
                                    rev  sha256[:8] of the file itself

  * `enclosure/print/` holds exactly ONE file per part — the current one. History lives
    in git and in `printed/` archives, never here. If two revisions of a part are ever in
    this directory, that is a bug, and `refresh()` enforces it by deleting strays.
  * The rev is ordinal so "which is newer" is readable in a slicer's recent-files list;
    the sha8 ties the file to its exact bytes so a claim like "I printed r2" is auditable.
  * The manifest also records which rev was PHYSICALLY PRINTED, so "what needs a
    reprint" is `status`, not a dig through issue history.

WHY REFRESH IS CALLED BY THE BUILD AND NOT BY A HUMAN

  A queue someone must remember to update is a stale copy waiting to happen — the exact
  class this repo keeps paying for (six stale-copy firmware bugs in one session; the
  bezel near-miss above). `ember_case.py` calls `refresh` in its commit step, AFTER the
  gated os.replace promotion, so the queue is exactly as current as the canonical STLs
  and there is no second thing to keep in sync by discipline.

  Deleting a stale rev file is safe by the same gating: the canonical STL a queue entry
  mirrors only changes when every geometry check has passed.

STATES `status` CAN REPORT

  ⛔ REPRINT   printed rev < current rev — the part in hand is superseded
  🖨  UNPRINTED  never printed at any rev
  ✅ CURRENT   printed rev == current rev

RUN
  python3 enclosure/tools/print_queue.py status
  python3 enclosure/tools/print_queue.py refresh            # what the build calls
  python3 enclosure/tools/print_queue.py printed <part>     # record: current rev is on the bed and done
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ENC = os.path.normpath(os.path.join(HERE, ".."))
QUEUE = os.path.join(ENC, "print")
MANIFEST = os.path.join(QUEUE, "manifest.json")

PARTS = ["ember-front-bezel", "ember-back-shell", "ember-stand", "ember-stand-base",
         # the mobile variant (#44) — same queue, same rules
         "ember-mobile-midframe", "ember-mobile-back"]


def sha8(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


def load() -> dict:
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {}


def save(m: dict) -> None:
    os.makedirs(QUEUE, exist_ok=True)
    tmp = MANIFEST + ".tmp"
    with open(tmp, "w") as f:
        json.dump(m, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, MANIFEST)


def qname(part: str, rev: int, s8: str) -> str:
    return f"{part}_r{rev}_{s8}.stl"


def refresh() -> int:
    """Mirror the canonical STLs into the queue, bumping rev on any byte change."""
    m = load()
    changed = []
    for part in PARTS:
        src = os.path.join(ENC, part + ".stl")
        if not os.path.exists(src):
            # Loud, not fatal: a build that produced only some parts (stand failed etc.)
            # should still queue the ones it made — but silence here would read as
            # "queue is current" for a part it never saw.
            print(f"  [print-queue] !! {part}.stl missing — its queue entry is UNTOUCHED")
            continue
        s8 = sha8(src)
        e = m.get(part, {"rev": 0, "sha8": None, "printed_rev": 0, "printed_at": None})
        if s8 != e["sha8"]:
            e["rev"] += 1
            e["sha8"] = s8
            e["updated"] = datetime.now().isoformat(timespec="minutes")
            changed.append(f"{part} -> r{e['rev']}")
        m[part] = e
        want = qname(part, e["rev"], s8)
        # one file per part: remove anything else answering to this part's name
        os.makedirs(QUEUE, exist_ok=True)
        for f in os.listdir(QUEUE):
            if f.startswith(part + "_r") and f.endswith(".stl") and f != want:
                os.remove(os.path.join(QUEUE, f))
        dst = os.path.join(QUEUE, want)
        if not os.path.exists(dst) or sha8(dst) != s8:
            tmp = dst + ".tmp"
            with open(src, "rb") as a, open(tmp, "wb") as b:
                b.write(a.read())
            os.replace(tmp, dst)
    save(m)
    print(f"  [print-queue] {'bumped: ' + ', '.join(changed) if changed else 'current'}"
          f" — slice from enclosure/print/")
    return 0


def status() -> int:
    m = load()
    if not m:
        print("no manifest — run `refresh` first")
        return 1
    print(f"{'part':<20} {'queue file':<42} printed")
    worst = 0
    for part in PARTS:
        e = m.get(part)
        if not e:
            print(f"{part:<20} — never refreshed")
            worst = 1
            continue
        f = qname(part, e["rev"], e["sha8"])
        if e["printed_rev"] == e["rev"]:
            mark = f"✅ CURRENT (r{e['rev']}, {e['printed_at']})"
        elif e["printed_rev"] == 0:
            mark, worst = "🖨  UNPRINTED", 1
        else:
            mark, worst = f"⛔ REPRINT — you have r{e['printed_rev']}", 1
        print(f"{part:<20} {f:<42} {mark}")
    return worst


def printed(part: str) -> int:
    m = load()
    if part not in m:
        sys.exit(f"unknown part {part!r} — expected one of {PARTS}")
    e = m[part]
    e["printed_rev"] = e["rev"]
    e["printed_at"] = datetime.now().date().isoformat()
    save(m)
    print(f"{part}: r{e['rev']} recorded as printed {e['printed_at']}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "refresh":
        raise SystemExit(refresh())
    if cmd == "printed":
        if len(sys.argv) != 3:
            sys.exit("usage: print_queue.py printed <part>")
        raise SystemExit(printed(sys.argv[2]))
    raise SystemExit(status())
