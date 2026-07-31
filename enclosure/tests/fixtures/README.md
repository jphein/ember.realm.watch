# `back-shell-wordgap-0.80.stl` — the control that must fail

This is a **real build**, not a synthesised mesh, and that distinction is the whole reason it
is in the repo.

## What it is

`ember_case.py` built with one line changed:

```python
LABEL_WORD_GAP = LABEL_MARGIN        # 0.80, instead of 2 * (LABEL_GAP - LABEL_W) = 2.00
```

That reproduces the **original `SPKI2C` / `BATUARTSD` defect** through the real pipeline —
`text_paths() → mirror → placement → boolean cut → STL export` — rather than by arranging
numbers in a test.

⚠️ **The build exits 0.** Every assert in `ember_case.py` passes at 0.80, including the two
that mention `LABEL_WORD_GAP` by name — because they compare placement against the constant,
and the constant is what moved. That is not a flaw in those asserts; it is the exact reason a
mesh-level check has to exist alongside them, and this fixture is the evidence.

## Why it is cropped

The full build is 1.77 MB. Only the triangles crossing the two slice planes can affect the
result, so it is reduced to the z band `zmin-0.01 .. zmin+0.60` → **1.13 MB, 22 528 of 35 388
triangles**. The reduction was verified rather than assumed: `glyph_boxes()` returns the
**identical** 20 glyph boxes at the identical 6.40 mm ink height from the cropped and full
meshes.

It is **not** cropped in XY, deliberately. The hex field, counterbores and speaker relief are
what the depth-difference has to discriminate against; an XY crop to the label strips would
delete the discrimination the check is being tested on and leave a control that proves less
than it appears to.

## Regenerating it

```bash
# in a worktree, never the main tree — a build rewrites all four STLs where it runs
sed -i 's/^LABEL_WORD_GAP = .*/LABEL_WORD_GAP = LABEL_MARGIN/' ember_case.py
cadenv/bin/python ember_case.py          # ~9 min; the STEP-import step at the end may fail
                                         # on a missing vendor asset, AFTER the STLs are written
python3 tools/../<crop script> ember-back-shell.stl tests/fixtures/back-shell-wordgap-0.80.stl
git restore --source=HEAD -- ember-back-shell.stl ember_case.py
```

## What it must do

`python3 tools/label_export_check.py --selftest` must report this fixture **FAIL** (ratio
0.56) and the shipped shell **PASS** (ratio 1.39). If the fixture ever passes, the check has
stopped being able to see the defect it exists for, and the check is wrong — not the fixture.
