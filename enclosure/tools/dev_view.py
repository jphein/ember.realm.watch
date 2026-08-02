#!/usr/bin/env python3
"""Live-edit loop for the ember models — build ONE part and show it in VS Code.

THE LOOP (JP, 2026-08-02):
  1. open enclosure/ in VS Code, open the OCP CAD Viewer panel (Ctrl+Shift+P →
     "OCP CAD Viewer: Open viewer")
  2. edit ember_case.py / ember_mobile_case.py (constants are at the top,
     features below — every tunable is named and commented)
  3. re-run this script → the changed part appears in the viewer in seconds-to-
     minutes (one part, NO export gates, NO full check suite)
  4. repeat until it looks right
  5. ⚠️ BEFORE ANY PRINT: run the full build (`cadenv/bin/python ember_mobile_case.py`)
     — the gated export IS the contract; this script deliberately skips it.

USAGE
  cadenv/bin/python tools/dev_view.py cover        # mobile back cover
  cadenv/bin/python tools/dev_view.py midframe     # mobile midframe
  cadenv/bin/python tools/dev_view.py bezel|shell|stand|base   # desk parts
  cadenv/bin/python tools/dev_view.py cover midframe           # several at once

The viewer talks to the VS Code extension on its default port (3939). If nothing
appears: the viewer panel isn't open yet — open it and re-run.
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ENC = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ENC)

PARTS = {
    # name -> (module, function)
    "bezel":    ("ember_case", "front_bezel"),
    "shell":    ("ember_case", "back_shell"),
    "stand":    ("ember_case", "desk_stand"),
    "base":     ("ember_case", "stand_base"),
    "midframe": ("ember_mobile_case", "midframe"),
    "cover":    ("ember_mobile_case", "back_cover"),
}
# back_shell() takes a variant argument; everything else takes none.
ARGS = {"shell": ("desk",)}


def main() -> int:
    names = [a for a in sys.argv[1:] if not a.startswith("-")] or ["cover"]
    bad = [n for n in names if n not in PARTS]
    if bad:
        sys.exit(f"unknown part(s) {bad} — choose from: {', '.join(PARTS)}")

    from ocp_vscode import show  # import late: fails fast with a clear message

    solids, labels = [], []
    for n in names:
        mod_name, fn_name = PARTS[n]
        t0 = time.time()
        print(f"[dev] building {n} ({mod_name}.{fn_name}) ...", flush=True)
        mod = __import__(mod_name)
        part = getattr(mod, fn_name)(*ARGS.get(n, ()))
        print(f"[dev]   done in {time.time()-t0:.0f}s", flush=True)
        solids.append(part)
        labels.append(n)

    show(*solids, names=labels)
    print(f"[dev] shown in OCP viewer: {', '.join(labels)}")
    print("[dev] ⚠️ preview only — run the full module before printing (gates!)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
