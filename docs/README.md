# docs/ — the GitHub Pages root

GitHub's free plan can publish only from the repo root or `/docs`, so this
directory *is* the site. `.nojekyll` keeps the tree served untouched by Jekyll.

| File | Written by |
|---|---|
| `index.html` | **Generated** by `../site/build.py` from `../site/index.src.html`. Never hand-edit — the next build overwrites it silently. |
| `assets/` | `../site/build.py`. Six chimes as real files (fetched on click rather than inlined — rationale at the top of `build.py`) plus the social preview card. |
| `home-assistant.md` | The full Home Assistant guide: prerequisites, deploy, verify, pipeline internals, troubleshooting. |
| `audio-pop.md` | The ES8311/FM8002E pop analysis, verbatim from the original repo, plus a coda on how it was resolved. |
| `enclosure.md` | Verified board geometry, the vendor STEP model, and the case survey. |
| `version.json` | realm-sigil stamp, written by `../build-sigil.sh`. |

## ⚠️ Outstanding: `assets/og-card.png` is a placeholder

It exists so the `og:image` tag never points at a 404 — a broken `og:image` degrades
to *no link preview at all*, not to a plain link, so a placeholder genuinely beats
nothing.

When the real 1200×630 card lands, **swap the file *and* update `og:image:alt` in
`site/index.src.html`**, then rebuild. The alt text currently describes the
placeholder. This is the one follow-up nothing local will flag: the page renders
perfectly with a stale alt, and the only place it surfaces is a screen reader or a
social preview.

## Rebuilding — one writer per file, no ordering to remember

```bash
python3 site/build.py    # owns index.html + assets/
./build-sigil.sh         # owns version.json — and touches nothing else
```

**Order no longer matters, and that is the point.** These two commands write disjoint
files, so neither can undo the other and there is no sequence to get wrong.

It briefly wasn't so. `build-sigil.sh` used to pass sigil's `--html` flag, which
injected a `<meta name="realm-version">` tag into the *built* `index.html` — so the
site build would silently drop the tag, the sigil run would silently re-add it, and
**whichever ran last looked correct.** That is the same shape as every other failure
this project has hit: a stale artifact that renders perfectly. `--html` is now
deliberately not passed, with the reasoning recorded in `build-sigil.sh` itself.

### If the page should carry the stamp in a meta tag

The site build is the only thing that may write `index.html`, so it should emit the
tag — reading the stamp that `build-sigil.sh` already produced:

```python
# in site/build.py, after the {{ASSET:…}} substitutions
import json
v = json.loads((DOCS / "version.json").read_text())
tag = f'<meta name="realm-version" content=\'{json.dumps(v)}\'>'
html = html.replace("</head>", f"  {tag}\n</head>")
```

That keeps one writer per file and makes the tag survive a rebuild. Run
`./build-sigil.sh` first so `version.json` exists; a missing file should be a
skipped tag, not a crash, so the site still builds on a fresh clone.

## Why the markdown is served raw

Not rendered, deliberately — these files are also the natural place to read the
documentation on GitHub, and with `.nojekyll` nothing stands between the file and
either reader.
