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

# --dir is the Pages root. build.sh writes version.json there and, if the HTML
# exists, injects/updates the meta tag. It skips the injection gracefully when
# the page is not present yet, so this is safe to run before the site lands.
"$SIGIL" \
  --name ember \
  --description "Local-first voice assistant satellite with a hearth for a face" \
  --realm forge \
  --repo https://github.com/jphein/ember.realm.watch \
  --html index.html \
  --dir docs
