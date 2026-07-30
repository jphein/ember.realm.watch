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
