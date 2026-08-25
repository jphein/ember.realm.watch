#!/usr/bin/env bash
# remote_build.sh — compile (and optionally OTA) ember firmware ON FAMILIAR.
#
# WHY (JP, 2026-08-24): parallel agent work on katana + ESPHome's compiler
# fleet is a bad marriage — one full build pegs every core for minutes. The
# familiar host has 24 mostly-idle cores and sits on the same LAN as the
# hearths, so builds AND OTA pushes run there. This script is the ONE seam:
# agents and humans alike call it instead of bare `esphome compile/upload`.
#
#   esphome/tools/remote_build.sh ember-mobile compile
#   esphome/tools/remote_build.sh ember-mobile flash        # compile + OTA
#   esphome/tools/remote_build.sh ember-satellite flash abc1234   # sigil override
#
# Sigil defaults to the CURRENT katana HEAD (short) + "-dirty" if the tree is
# dirty — same convention the sessions have used all along. The remote build
# dir persists (~/ember-build) so PlatformIO caches survive between runs;
# secrets ride the rsync (familiar is trusted; the dir is chmod 700).
set -euo pipefail

DEV="${1:?usage: remote_build.sh <device> compile|flash [sigil]}"
ACT="${2:?usage: remote_build.sh <device> compile|flash [sigil]}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"          # the esphome/ dir
SIGIL="${3:-$(git -C "$HERE" rev-parse --short HEAD)$(git -C "$HERE" diff --quiet HEAD -- . 2>/dev/null || echo -dirty)}"
R=familiar
RDIR="ember-build"

ssh "$R" "mkdir -p $RDIR/esphome"
# secrets.yaml is gitignored, so a WORKTREE checkout doesn't have it — and
# --delete would then remove familiar's standing copy and break every !secret
# lookup (found by PR #91's ultrareview). Excluded from the sync wholesale;
# pushed explicitly only when the caller actually has one.
rsync -a --delete \
      --exclude '.esphome/build' --exclude '.esphome/storage' \
      --exclude '__pycache__' --exclude 'secrets.yaml' \
      "$HERE/" "$R:$RDIR/esphome/"
if [ -f "$HERE/secrets.yaml" ]; then
  rsync -a "$HERE/secrets.yaml" "$R:$RDIR/esphome/secrets.yaml"
fi
# Exit codes must SURVIVE the log-trimming: a remote `esphome | tail` reports
# tail's success, not the compile's (same ultrareview). Capture, then trim.
ssh "$R" "chmod 700 $RDIR; cd $RDIR/esphome && \
  { ~/esphome-venv/bin/esphome -s sigil_version '$SIGIL' compile '$DEV.yaml' \
      > /tmp/ember-build.log 2>&1; rc=\$?; tail -3 /tmp/ember-build.log; exit \$rc; }"

if [ "$ACT" = flash ]; then
  ssh "$R" "cd $RDIR/esphome && \
    { ~/esphome-venv/bin/esphome upload '$DEV.yaml' --device '$DEV.local' \
        > /tmp/ember-flash.log 2>&1; rc=\$?; tail -2 /tmp/ember-flash.log; exit \$rc; }"
fi
echo "remote_build: $DEV $ACT done (sigil $SIGIL, host $R)"
