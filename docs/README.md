# docs/ — the GitHub Pages root

GitHub's free plan can publish only from the repo root or `/docs`, so this
directory *is* the site. `.nojekyll` keeps the tree served untouched by Jekyll.

| File | |
|---|---|
| `index.html` | **Generated.** Built by `../site/build.py` from `../site/index.src.html`. Do not hand-edit — the next build silently overwrites it. |
| `assets/` | Six chimes as real files (fetched on click rather than inlined — the rationale is at the top of `build.py`) plus the social preview card. |
| `home-assistant.md` | The full Home Assistant guide: prerequisites, deploy, verify, pipeline internals, troubleshooting. |
| `audio-pop.md` | The ES8311/FM8002E pop analysis, verbatim from the original repo. |
| `version.json` | realm-sigil stamp, written by `../build-sigil.sh`. |

## Rebuilding

```bash
python3 site/build.py    # regenerate index.html + assets/
./build-sigil.sh         # refresh version.json + the <meta name="realm-version"> tag
```

Run them in that order. The sigil step injects its tag into the *built* HTML, so
rebuilding afterwards would drop it.

The markdown files here are served raw rather than rendered. That's deliberate —
they're also the natural place to read them on GitHub, and with `.nojekyll` nothing
stands between the file and either reader.
