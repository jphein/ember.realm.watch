#!/usr/bin/env bash
# deploy-ha.sh — push Ember's Home Assistant packages from this repo to the HA VM.
#
# This repo is the SOURCE OF TRUTH. HA loads /homeassistant/packages/*.yaml via
# `homeassistant: packages: !include_dir_named packages`, so deploying is: copy the
# file in, validate, then reload only the domains that changed. No restart needed
# for anything this repo ships (see the caveat on template sensors below).
#
# Usage:
#   ./deploy-ha.sh                 # deploy every package + reload changed domains
#   ./deploy-ha.sh --check         # validate only, change nothing
#   ./deploy-ha.sh --dry-run       # show what would be copied, and WHICH WAY
#   ./deploy-ha.sh ember_persona   # deploy one package by stem (prefer this)
#   ./deploy-ha.sh --force         # overwrite even a VM copy that is newer
#
# ⚠️ THE VM IS OFTEN AHEAD OF THIS REPO. Packages get edited live on the HA host,
# so "the files differ" does NOT mean "the repo is ahead". This script now
# compares timestamps and REFUSES to overwrite a VM copy newer than what the repo
# has authored, exiting 2. Reconcile repo <- VM, re-apply your change on that
# base, then deploy. --force discards the VM copy and is almost never what you
# want. See docs/verification.md §33 for the run that made this necessary.
#
# Auth: env HA_TOKEN -> ~/.cache/ha-token-tmp -> `bw get password ha-llat`.
set -euo pipefail

# ---------------------------------------------------------------- host names
# ⚠ THE SSH HOST AND THE API HOST ARE USUALLY NOT THE SAME MACHINE, and getting it
# wrong fails silently in the worst way. If your Home Assistant is behind a reverse
# proxy, the public name resolves to the PROXY. SSH to it succeeds, `sudo tee` writes
# these packages onto the proxy's filesystem, the script reports success, and nothing
# whatsoever changes in Home Assistant. Confirmed the hard way by running `hostname`
# after such an SSH and finding the wrong box.
#
#   HA_SSH_HOST -> the machine actually running Home Assistant (file copies)
#   HA_API      -> whatever fronts the HTTP/WebSocket API (validation + reloads)
#
# Set both for your install; they are deliberately separate and must stay so:
#   export HA_SSH_HOST="jp@ha.lan" HA_API="https://ha.example.com:8123"
# Defaults are THIS homelab's real endpoints (fixed 2026-07-31 — the
# homeassistant.local defaults resolved from nowhere on katana, so every run
# needed manual overrides):
#   SSH  -> the HAOS VM itself by IP. ha.jphe.in is the Caddy edge (see the
#           warning above) and there is no mDNS on this LAN's VLANs.
#   API  -> ha.jphe.in:8123, HA core's own TLS listener (valid LE cert), the
#           same base every ~/Projects/ha tool uses.
HA_SSH_HOST="${HA_SSH_HOST:-jp@10.0.6.108}"
HA_API="${HA_API:-https://ha.jphe.in:8123}"
# Overridable so the copy path can be exercised against a scratch directory without
# touching the live config, and for instances whose config dir isn't the default.
PKG_DIR="${PKG_DIR:-/homeassistant/packages}"

# Derived from this script's own location rather than from a repo-root path, so the
# HA tree can be called `homeassistant/`, `ha/`, or anything else without an edit.
# Only requirement: packages/ and tools/ are siblings.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")/packages"

# ⚠️ THIS LIST IS THE DRIFT MECHANISM. A package that is not named here is not
# deployed, not compared, and not reported by --dry-run — so it can be edited on
# the VM and never come back to the repo, and nothing complains. That is exactly
# what happened to ember_slack and ember_wake_backend, which lived only on the VM
# from 2026-08-03 until the second board's bring-up went looking for them.
# ADD NEW PACKAGES HERE IN THE SAME COMMIT THAT CREATES THEM.
PACKAGES=(ember_backend_health ember_persona ember_announce ember_laundry_herald ember_driveway_watch ember_toolkit ember_print_context ember_slack ember_wake_backend ember_house_watch ember_intercom ember_battery_watch)

# Which reload service each package needs. A package that declares several
# domains needs each of them reloaded.
declare -A RELOADS=(
  [ember_backend_health]="rest template"
  [ember_persona]="input_text"
  [ember_announce]="script"
  [ember_laundry_herald]="automation"
  [ember_driveway_watch]="automation"
  # ember_toolkit carries the credential-bearing data plane behind Ember's
  # tools: a `rest:` sensor (OctoPrint) and `rest_command:` entries (MemPalace,
  # Spyglass). Both reload live; neither needs a restart.
  [ember_toolkit]="rest rest_command"
  [ember_print_context]="automation"
  # ember_slack owns script.ember_broadcast — the hook point every herald now
  # calls, which decides spoken-vs-Slack before ember_announce ever runs.
  [ember_slack]="script"
  [ember_wake_backend]="script automation"
  # ember_intercom is the horn's relay: event entity press -> ask_question ->
  # announce on the peer hearth.
  [ember_intercom]="automation"
  # ember_battery_watch: the mobile cell's critical alarm (speak + broadcast).
  # The 20% chime is firmware-side; only the 8% escalation lives in HA.
  [ember_battery_watch]="automation"
  # ⚠️ `template` here, and mind the caveat printed at the end of a run: on this
  # instance a NEW template entity appears on reload, but EDITS to an existing
  # one have historically needed a full restart. Changing the Jinja in
  # ember_house_watch and seeing a stale value is that, not a broken template.
  [ember_house_watch]="template"
)

DRY=0; CHECK_ONLY=0; ONLY=""; FORCE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --check)   CHECK_ONLY=1 ;;
    --force)   FORCE=1 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *)         ONLY="$arg" ;;
  esac
done

# ─────────────────────── WHICH SIDE IS NEWER ───────────────────────
# THE BUG THIS EXISTS TO KILL: this script's only report about a divergent file
# used to be "remote differs or absent". That is SYMMETRIC language for an
# ASYMMETRIC action — it overwrites the VM — and a reader naturally completes it
# as "my repo is ahead". On 2026-08-03 the VM was ahead: it held a wake-on-LAN
# retry in ember_announce added that morning, plus two packages this repo did
# not have at all, and a routine deploy would have reverted the lot. Nothing in
# the output hinted at the direction.
#
# So the script now answers the question it was silently begging, and REFUSES to
# overwrite a VM copy that looks newer than what this repo has authored.
#
# repo_authored_at() deliberately does NOT use the working file's mtime as its
# first choice: mtime is reset by every checkout, branch switch and clone, so a
# fresh clone would claim every file was authored seconds ago and this guard
# would never fire. The last COMMIT that touched the file is when its content
# was actually authored. The exception is a file with uncommitted local edits,
# where mtime IS a real authoring time and the commit date is stale — so dirty
# files fall back to mtime, which also means "I just edited this" correctly wins
# over an older VM copy.
repo_authored_at() {  # repo_authored_at <path> -> unix seconds
  local f="$1"
  if ! git -C "$(dirname "$f")" diff --quiet -- "$f" 2>/dev/null; then
    stat -c %Y "$f"; return          # locally modified: mtime is genuine
  fi
  local t
  t="$(git -C "$(dirname "$f")" log -1 --format=%ct -- "$f" 2>/dev/null || true)"
  [ -n "$t" ] && printf '%s' "$t" || stat -c %Y "$f"
}

token() {
  [ -n "${HA_TOKEN:-}" ] && { printf '%s' "$HA_TOKEN"; return; }
  local c="$HOME/.cache/ha-token-tmp"
  [ -s "$c" ] && { cat "$c"; return; }
  bw get password ha-llat
}
TOKEN="$(token)"

api() {  # api <method> <path> [json]
  curl -fsS -X "$1" "$HA_API$2" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    ${3+-d "$3"}
}

check_config() {
  local out
  out="$(api POST /api/config/core/check_config)"
  if [ "$(printf '%s' "$out" | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"])')" != "valid" ]; then
    echo "!! check_config FAILED — not reloading. HA is still running the old config:" >&2
    printf '%s\n' "$out" >&2
    return 1
  fi
  echo "   check_config: valid"
}

# --check talks only to the HTTP API, so it must not require SSH to be set up.
if [ "$CHECK_ONLY" = 1 ]; then check_config; exit 0; fi

# Fail early and legibly if known_hosts has the IP form but not the hostname.
if ! ssh -o BatchMode=yes -o ConnectTimeout=6 "$HA_SSH_HOST" true 2>/dev/null; then
  cat >&2 <<EOF
!! Cannot SSH to $HA_SSH_HOST.
   If this is "Host key verification failed", known_hosts likely has the IP form
   only. Accept the hostname once:
       ssh-keyscan -H ha.lan >> ~/.ssh/known_hosts
   Then re-run. (Do NOT switch to ha.jphe.in — that is the Caddy edge, not the VM.)
   To target a different host for one run: HA_SSH_HOST=jp@... ./deploy-ha.sh
EOF
  exit 1
fi

echo "==> repo   $SRC_DIR"
echo "==> target $HA_SSH_HOST:$PKG_DIR"

changed=()
for p in "${PACKAGES[@]}"; do
  [ -n "$ONLY" ] && [ "$ONLY" != "$p" ] && continue
  src="$SRC_DIR/$p.yaml"
  [ -f "$src" ] || { echo "!! missing $src" >&2; exit 1; }

  # Skip the copy when the remote file is already byte-identical, so a no-op
  # deploy doesn't trigger pointless reloads.
  local_sum="$(sha256sum "$src" | cut -d' ' -f1)"
  remote_sum="$(ssh "$HA_SSH_HOST" "sha256sum $PKG_DIR/$p.yaml 2>/dev/null | cut -d' ' -f1" || true)"
  if [ "$local_sum" = "$remote_sum" ]; then
    echo "==  $p.yaml unchanged"
    continue
  fi

  # They differ. Say WHICH WAY, because the old message did not and that is how a
  # deploy nearly reverted a morning's work. An absent remote is unambiguous —
  # nothing to lose — so it is reported as new rather than as a conflict.
  if [ -z "$remote_sum" ]; then
    if [ "$DRY" = 1 ]; then echo "++  would create $p.yaml (absent on VM)"; continue; fi
  else
    remote_mtime="$(ssh "$HA_SSH_HOST" "stat -c %Y $PKG_DIR/$p.yaml 2>/dev/null" || echo 0)"
    repo_mtime="$(repo_authored_at "$src")"
    if [ "${remote_mtime:-0}" -gt "${repo_mtime:-0}" ]; then
      echo "!!  $p.yaml — THE VM COPY IS NEWER. Not overwriting."
      echo "      VM   modified $(date -d "@$remote_mtime" '+%Y-%m-%d %H:%M:%S')"
      echo "      repo authored $(date -d "@$repo_mtime" '+%Y-%m-%d %H:%M:%S')"
      echo "      The VM may hold work this repo has never seen. Diff it first:"
      echo "        ssh $HA_SSH_HOST \"cat $PKG_DIR/$p.yaml\" | diff - $src"
      echo "      Then reconcile repo <- VM, re-apply your change on that base, and"
      echo "      deploy again. Use --force ONLY if you mean to discard the VM copy."
      if [ "$FORCE" != 1 ]; then BLOCKED=$((${BLOCKED:-0} + 1)); continue; fi
      echo "      --force given: overwriting anyway."
    elif [ "$DRY" = 1 ]; then
      echo "++  would copy $p.yaml (repo is newer)"
      continue
    fi
  fi

  if [ "$DRY" = 1 ]; then
    echo "++  would copy $p.yaml"
    continue
  fi

  # Timestamped backup with the suffix AFTER .yaml — `!include_dir_named` loads
  # every *.yaml in the directory, so a `.bak.yaml` would be parsed as a second
  # copy of the package and collide on every entity id.
  ssh "$HA_SSH_HOST" "[ -f $PKG_DIR/$p.yaml ] && sudo cp $PKG_DIR/$p.yaml $PKG_DIR/$p.yaml.bak-\$(date +%Y%m%d-%H%M%S) || true"
  ssh "$HA_SSH_HOST" "sudo tee $PKG_DIR/$p.yaml >/dev/null" < "$src"
  echo "->  copied $p.yaml"
  changed+=("$p")
done

# A skipped VM-newer file is a FAILURE, not a note. Exiting 0 here would let a
# caller (or a person skimming) read a run that deployed nothing as a success,
# which is the same class of mistake as the symmetric "differs" message: the
# output has to make the dangerous case impossible to miss.
if [ "${BLOCKED:-0}" -gt 0 ]; then
  echo
  echo "!! ${BLOCKED} package(s) NOT deployed because the VM copy is newer (see above)."
  echo "   Nothing was reloaded. Reconcile first; --force discards the VM copy."
  exit 2
fi

[ "$DRY" = 1 ] && exit 0
[ "${#changed[@]}" -eq 0 ] && { echo "nothing changed; skipping reload"; exit 0; }

# Validate the MERGED config before reloading anything. If a package is
# malformed, HA keeps running the old config and this stops here.
check_config

seen=""
for p in "${changed[@]}"; do
  for domain in ${RELOADS[$p]:-}; do
    case " $seen " in *" $domain "*) continue ;; esac
    seen="$seen $domain"
    api POST "/api/services/$domain/reload" '{}' >/dev/null
    echo "   reloaded: $domain"
  done
done

cat <<'EOF'

Done. Caveat worth knowing (recorded project behaviour, ha skill gotcha 5):
`template.reload` picks up NEW template entities, but EDITS to an existing
template sensor's definition have historically needed a full HA restart on this
instance. If you changed an existing template sensor and it still reads stale,
budget one restart rather than hunting the template.
EOF
