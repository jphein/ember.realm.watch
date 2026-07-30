#!/usr/bin/env bash
# deploy-ha.sh — push Ember's Home Assistant packages from this repo to the HA VM.
#
# This repo is the SOURCE OF TRUTH. HA loads /homeassistant/packages/*.yaml via
# `homeassistant: packages: !include_dir_named packages`, so deploying is: copy the
# file in, validate, then reload only the domains that changed. No restart needed
# for anything this repo ships (see the caveat on template sensors below).
#
# Usage:
#   ./deploy-ha.sh                 # deploy all three packages + reload
#   ./deploy-ha.sh --check         # validate only, change nothing
#   ./deploy-ha.sh --dry-run       # show what would be copied
#   ./deploy-ha.sh ember_persona   # deploy one package by stem
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
HA_SSH_HOST="${HA_SSH_HOST:-jp@homeassistant.local}"
HA_API="${HA_API:-https://homeassistant.local:8123}"
# Overridable so the copy path can be exercised against a scratch directory without
# touching the live config, and for instances whose config dir isn't the default.
PKG_DIR="${PKG_DIR:-/homeassistant/packages}"

# Derived from this script's own location rather than from a repo-root path, so the
# HA tree can be called `homeassistant/`, `ha/`, or anything else without an edit.
# Only requirement: packages/ and tools/ are siblings.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")/packages"

PACKAGES=(ember_backend_health ember_persona ember_announce)

# Which reload service each package needs. A package that declares several
# domains needs each of them reloaded.
declare -A RELOADS=(
  [ember_backend_health]="rest template"
  [ember_persona]="input_text"
  [ember_announce]="script"
)

DRY=0; CHECK_ONLY=0; ONLY=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --check)   CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *)         ONLY="$arg" ;;
  esac
done

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

  if [ "$DRY" = 1 ]; then
    echo "++  would copy $p.yaml (remote differs or absent)"
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

[ "$DRY" = 1 ] && exit 0
[ "${#changed[@]}" -eq 0 ] && { echo "nothing changed; skipping reload"; exit 0; }

# Validate the MERGED config before reloading anything. If a package is
# malformed, HA keeps running the old config and this stops here.
check_config

seen=""
for p in "${changed[@]}"; do
  for domain in ${RELOADS[$p]}; do
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
