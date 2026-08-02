# Editing the ember models by hand

The models are **code** (`ember_case.py` desk, `ember_mobile_case.py` mobile) —
[build123d](https://build123d.readthedocs.io) Python. The `.py` file is the part;
STLs are output. There is no GUI file to edit — and that's the feature: every
dimension is a named constant with the reasoning next to it.

## The loop

1. `code ~/Projects/ember.realm.watch/enclosure` (VS Code, OCP CAD Viewer
   extension installed)
2. `Ctrl+Shift+P` → **OCP CAD Viewer: Open viewer** (3D panel opens)
3. Edit constants/features in the model file
4. ```bash
   ./cadenv/bin/python tools/dev_view.py cover     # or midframe/bezel/shell/stand/base
   ```
   → the part appears in the viewer (one part, no gates, seconds-to-minutes)
5. Repeat 3–4 until right.

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
