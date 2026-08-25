#!/usr/bin/env bash
# remote_cad.sh — run the enclosure builds ON FAMILIAR, artifacts synced back.
#
# WHY (JP, 2026-08-25: "you should be building on familiar"): a CAD build
# balloons to gigabytes and pegs cores for ~10 minutes; on a katana deep in
# swap the builds were being reaped before their first log line (killer never
# conclusively named — no oomd/kernel OOM record visible even with sudo — but
# the cure is the same as the firmware seam's: familiar has 24 mostly-idle
# cores and the RAM to spare). This is the ONE seam: humans and agents call
# this instead of bare `cadenv/bin/python ember_case.py` on katana.
#
#   enclosure/tools/remote_cad.sh desk      # ember_case.py
#   enclosure/tools/remote_cad.sh mobile    # ember_mobile_case.py
#   enclosure/tools/remote_cad.sh all       # desk + mobile + renders + site
#
# First run bootstraps ~/ember-cad/cadenv on familiar from tools/
# requirements.txt (python 3.12.3 there). Repo syncs TO familiar minus .git
# and katana's own cadenv; artifacts (STLs, print queue, renders, generated
# site pages) sync BACK. Exit codes survive the trims (capture-then-tail,
# same lesson as remote_build.sh).
set -euo pipefail

WHAT="${1:?usage: remote_cad.sh desk|mobile|all}"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"        # repo root
R=familiar
RDIR="ember-cad"

ssh "$R" "mkdir -p $RDIR"
# --copy-unsafe-links: symlinks pointing OUTSIDE the tree are materialized as
# files instead of shipped as dangling links. Found the hard way: the vendor
# STEP was a symlink into a dead session's scratch dir (now materialized in
# the repo, 2026-08-25), and the first remote build chased it into nothing.
rsync -a --delete --copy-unsafe-links \
      --exclude '.git' --exclude '.esphome' --exclude 'enclosure/cadenv' \
      --exclude 'esphome/secrets.yaml' --exclude '__pycache__' \
      "$HERE/" "$R:$RDIR/repo/"

ssh "$R" "set -e; cd $RDIR
  if [ ! -x cadenv/bin/python ]; then
    python3 -m venv cadenv
    cadenv/bin/pip install -q -r repo/enclosure/tools/requirements.txt
  fi"

run_remote() {
  ssh "$R" "cd $RDIR/repo/enclosure && \
    { ../../cadenv/bin/python $1 > /tmp/ember-cad.log 2>&1; rc=\$?; \
      tail -4 /tmp/ember-cad.log; exit \$rc; }"
}

case "$WHAT" in
  desk)   run_remote ember_case.py ;;
  mobile) run_remote ember_mobile_case.py ;;
  all)
    run_remote ember_case.py
    run_remote ember_mobile_case.py
    run_remote tools/make_mobile_renders.py
    ssh "$R" "cd $RDIR/repo/site && \
      { python3 build.py > /tmp/ember-site.log 2>&1 && \
        python3 build_print_sheet.py >> /tmp/ember-site.log 2>&1; rc=\$?; \
        tail -2 /tmp/ember-site.log; exit \$rc; }"
    ;;
  *) echo "unknown target: $WHAT" >&2; exit 22 ;;
esac

# Artifacts home. --existing on docs/ so only generated pages update.
rsync -a "$R:$RDIR/repo/enclosure/" "$HERE/enclosure/" \
      --include 'ember-*.stl' --include 'print/***' --include 'preview-*.png' \
      --exclude 'cadenv' --exclude '*.py' --exclude '*'
rsync -a "$R:$RDIR/repo/site/renders/" "$HERE/site/renders/"
rsync -a --existing "$R:$RDIR/repo/docs/" "$HERE/docs/"
echo "remote_cad: $WHAT done on $R, artifacts synced back"
