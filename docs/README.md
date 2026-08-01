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
| `enclosure-mobile.md` | The battery variant (#44): BOM, assembly order, wiring, print notes, the full measured table, and every soft number flagged. |
| `vendor/` | The archived ES3C28P schematic, plus a README of what it settles — the charger, the power path, and the *absence* of any protection IC. |
| `print-sheet.html` | **Generated** by `../site/build_print_sheet.py` (which `build.py` calls) from `../enclosure/PRINT-SHEET.md`. Never hand-edit. See the exception below. |
| `verification.md` | The running log of claims that outran their evidence. Read it before trusting a green check. |
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

### The meta tag, and how it is done now

This section used to propose a fix. **It has been implemented** — `site/build.py` reads the
stamp that `build-sigil.sh` already produced and injects
`<meta name="realm-version" content="…">` before `</head>`. One writer per file, the tag
survives a rebuild, and a **missing `version.json` is a skipped tag rather than a crash**, so
a fresh clone with no sigil output still builds. Run `./build-sigil.sh` first if you want the
stamp; the build prints which it did.

*(Left in place rather than deleted because the reasoning is the useful part — but stated as
what the code does, not as what someone should do. A proposal that has quietly become the
implementation is one of the easier things to leave lying around, and it reads as work
outstanding.)*

## The markdown files are NOT browsable from the site

Stated plainly so nobody files it as a bug. `.nojekyll` turns Jekyll off, which is
required so Pages serves `index.html` and the assets exactly as built — but it also
means **every `.md` file here is served as plain text**, not rendered HTML. Opening
`…/audio-pop.md` on the Pages domain gives you the raw source.

**GitHub's blob view is the intended reading surface** for all of them, and links from
the site point there for that reason. Accepted rather than fixed: rendering them would
mean either letting Jekyll process the whole tree — including a 113 KB hand-built
`index.html` it has no business touching — or maintaining a second Markdown→HTML build
for documents whose natural home is the repo anyway.

The trade is deliberate, but it is a trade. If these ever need to be readable on the
site itself, the cheapest honest fix is a link out, not a build step.
