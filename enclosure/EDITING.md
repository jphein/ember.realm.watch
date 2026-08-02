# Editing the ember models by hand

The models are **code** (`ember_case.py` desk, `ember_mobile_case.py` mobile) —
[build123d](https://build123d.readthedocs.io) Python. The `.py` file is the part;
STLs are output. There is no GUI file to edit — and that's the feature: every
dimension is a named constant with the reasoning next to it.

## The loop

1. Start the viewer once per session (browser-based, no extension needed):
   ```bash
   ./cadenv/bin/python -m ocp_vscode &     # serves http://127.0.0.1:3939/viewer
   ```
   and open that URL in Brave. (The VS Code "OCP CAD Viewer" extension is the
   same thing embedded in the editor — its marketplace install was flaky here,
   so the browser viewer is the supported path; both listen on :3939.)
2. Edit constants/features in the model file — any editor: VS Code, nano, whatever.
3. ```bash
   ./cadenv/bin/python tools/dev_view.py cover     # or midframe/bezel/shell/stand/base
   ```
   → the part appears in the viewer tab (one part, no gates, seconds-to-minutes)
4. Repeat 2–3 until right.

## Where things are

- **Constants live at the top of each file**, grouped and commented — cell bay,
  strip/leaf (`LEAF_*`, `CONTACT_*`, `BMS_*`), hex fields, ease, labels. The desk
  tunables table is in `PRINT-SHEET.md` (§Tunables).
- Features are functions below (`back_cover()`, `midframe()`, …). Checks live in
  `_check_geometry` — **leave them on**; they're the reason bad parts don't reach
  the printer.

## The two rules

1. **Preview ≠ gate.** `dev_view.py` skips every check and export. Before
   anything prints: `./cadenv/bin/python ember_mobile_case.py` (or `ember_case.py`)
   must run green — the gated export writes the STLs and the queue picks them up
   (`tools/print_queue.py refresh`).
2. **Don't delete an assert to make a change fit** — the assert is usually
   remembering a printed failure (#26/#28/#34/#47…). If one blocks you, it's
   telling you the price of the change; read its message.

## Pre-print (unchanged)

`tools/make_3d_viewer.py <part>` → Brave preview → bed clear → print via
OctoPrint (`serialhub`).
