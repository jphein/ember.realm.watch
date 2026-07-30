#!/usr/bin/env bash
# Stamp the project site with a realm-sigil version.
#
# Ember is firmware plus a static site — there is no server process, so there is
# no `/api/version` endpoint to serve. The static sigil path is the right one:
# it writes `docs/version.json` and injects a `<meta name="realm-version">` tag
# into the page, both derived from the current git hash.
#
# Realm is `forge` — Molten / Smoldering / Kiln / Ironheart. It is a hearth.
#
# Run after any commit that changes the site, and before publishing Pages:
#   ./build-sigil.sh
#
# Requires ~/Projects/realm-sigil checked out beside this repo.
set -euo pipefail

SIGIL="${REALM_SIGIL_DIR:-$HOME/Projects/realm-sigil}/static/build.sh"

if [[ ! -x "$SIGIL" ]]; then
  echo "realm-sigil static/build.sh not found at: $SIGIL" >&2
  echo "Clone https://github.com/jphein/realm-sigil, or set REALM_SIGIL_DIR." >&2
  exit 1
fi

cd "$(dirname "$0")"

# --dir is the Pages root. This writes docs/version.json and NOTHING ELSE.
#
# ⚠️ `--html` is deliberately NOT passed, even though sigil supports it and it would
# inject a <meta name="realm-version"> tag into the page. `docs/index.html` is owned by
# the site build (site/build.py) and regenerated from site/index.src.html. Passing
# --html here would make two tools write one file in opposite directions: this script
# would inject a tag, and the next site build would silently drop it. Whichever ran
# last would look correct, which is the failure mode this project keeps meeting.
#
# So: one writer per file. This script owns version.json; the site build owns the HTML.
# If the page wants the stamp in a meta tag, the site build should read version.json
# and emit it — see docs/README.md.
"$SIGIL" \
  --name ember \
  --description "Local-first voice assistant satellite with a hearth for a face" \
  --realm forge \
  --repo https://github.com/jphein/ember.realm.watch \
  --dir docs

# ---------------------------------------------------------------- dirty, corrected
# Sigil derives `dirty` from `git diff --quiet`, which has a bootstrapping paradox
# here: docs/version.json is TRACKED, so the previous run's output leaves the tree
# modified, and the next run then reports dirty:true purely because of its own
# artifact. The published stamp ends up claiming the build came from a modified tree
# when the only modification was the stamp.
#
# So recompute it ignoring version.json — the one file whose churn is self-inflicted —
# and correct the field. Any OTHER modification still reports dirty:true, which is the
# signal worth keeping.
python3 - <<'PY'
import json, pathlib, subprocess
vj = pathlib.Path("docs/version.json")
changed = subprocess.run(
    ["git", "status", "--porcelain", "--untracked-files=no"],
    capture_output=True, text=True).stdout.splitlines()
real = [l for l in changed if l[3:].strip() not in ("docs/version.json",)]
d = json.loads(vj.read_text())
was, d["dirty"] = d["dirty"], bool(real)
vj.write_text(json.dumps(d, indent=2) + "\n")
if was != d["dirty"]:
    print(f"  \033[2;37m✓ dirty corrected {was} -> {d['dirty']} "
          f"(version.json's own churn ignored)\033[0m")
if real:
    print("  \033[2;37m! tree has other uncommitted changes; stamp says dirty\033[0m")
PY
