# Label-spacing control fixtures

Both are **real builds**, not synthesised meshes, and that distinction is the whole reason
they are in the repo: a control that never crosses the slice→loop front end proves only that
the arithmetic works.

| fixture | geometry | must |
|---|---|---|
| `back-shell-chamfered-wordgap-0.80.stl` | **post-#35, what ships today** | FAIL |
| `back-shell-wordgap-0.80.stl` | pre-#35, no exterior chamfer | FAIL |

The must-**pass** control is not a fixture: it is `../../ember-back-shell.stl`, the shipped
shell itself, so it tracks whatever is actually being printed rather than a snapshot that
can go stale. Which is exactly how the tool went blind — see below.

## What they are

`ember_case.py` built with one line changed:

```python
LABEL_WORD_GAP = LABEL_MARGIN        # 0.80, instead of 2 * (LABEL_GAP - LABEL_W) = 2.00
```

That reproduces the **original `SPKI2C` / `BATUARTSD` defect** through the real pipeline —
`text_paths() → mirror → placement → boolean cut → STL export`. Sliced at z −9.50 and looked
at, the left strip reads `BATUARTSD` as one continuous string, against `BAT` `UART` `SD` on
the shipped part.

⚠️ **Both builds exit 0.** Every assert in `ember_case.py` passes at 0.80, including the two
that mention `LABEL_WORD_GAP` by name — they compare placement against the constant, and the
constant is what moved. That is not a flaw in those asserts; it is the reason a mesh-level
check has to exist alongside them.

## Why there are two, and why the pre-chamfer one stays

`#35`'s exterior chamfer broke the check within minutes of it landing. The depth difference
had assumed the part outline is the same shape at both slice planes; a chamfer makes it a
function of z — measured, 54.700 mm wide at `z_in` against 55.300 mm at `z_below` — so the
perimeter stopped matching itself, survived the difference, and **swallowed the entire text**
(every glyph is nested inside the outline, so the counter-dropping step discarded all
twenty). The tool reported `BLIND` rather than a false pass, which is the one thing that
went right.

The fix is `drop_silhouette()`, which removes loops **reaching an extreme of the part's own
silhouette** — not loops that are *big*. Sizing would be the wrong test and a dangerous one:
a merged `BATUARTSD` run is also large, and a rule that discarded the biggest loop would
discard the defect. The pre-chamfer fixture stays so that fix is pinned against both
geometries at once.

## Why they are cropped

Full builds are ~1.79 MB. Only triangles crossing the two slice planes can affect the result,
so each is reduced to the z band `zmin-0.01 .. zmin+0.60` → ~1.13 MB. The reduction is
**verified, not assumed**: `glyph_boxes()` returns the identical 20 glyph boxes at the
identical 6.40 mm ink height from cropped and full meshes.

Not cropped in XY, deliberately — the hex field, counterbores and speaker relief are what the
depth difference has to discriminate against, and an XY crop to the label strips would delete
the discrimination the check is being tested on.

## Regenerating

```bash
# in a worktree, NEVER the main tree — a build rewrites all four STLs where it runs
sed -i 's/^LABEL_WORD_GAP = .*/LABEL_WORD_GAP = LABEL_MARGIN/' ember_case.py
cadenv/bin/python ember_case.py     # ~9 min. The STEP-import step at the end fails on a
                                    # missing vendor asset, AFTER the STLs are written.
<crop to the z band>  ember-back-shell.stl  tests/fixtures/<name>.stl
git restore --source=HEAD -- ember-back-shell.stl ember_case.py
```

## What they must do

`python3 tools/label_export_check.py --selftest` must report the shipped shell **PASS**
(ratio 1.39) and both fixtures **FAIL** (ratio 0.56) — and **all three must recover exactly
20 glyphs**. That glyph count is not decoration: the chamfer failure looked precisely like
"fewer loops than expected", so it is what stops a future filter tweak from quietly eating
text and leaving a check that still says OK.

If a fixture ever passes, the check has stopped seeing the defect it exists for, and the
check is wrong — not the fixture.
