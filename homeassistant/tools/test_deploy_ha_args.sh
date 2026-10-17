#!/usr/bin/env bash
# test_deploy_ha_args.sh [deploy-ha.sh] — argument handling of deploy-ha.sh, using ONLY --dry-run (never writes
# to the VM). Born 2026-10-17: with two stems the script silently deployed only the LAST one.
set -uo pipefail
D="${1:-$(dirname "$0")/deploy-ha.sh}"
fail=0
ok() { echo "PASS $1"; }; bad() { echo "FAIL $1"; fail=1; }
pkgs_in() { grep -oE '(unchanged|would copy|would create|copied) [a-z_]+\.yaml|^==  [a-z_]+\.yaml' <<<"$1" | grep -oE '[a-z_]+\.yaml' | sort -u | tr '\n' ' '; }

out=$(bash "$D" --dry-run ember_slack ember_driveway_watch 2>&1); rc=$?
got=$(pkgs_in "$out")
[ $rc -eq 0 ] && [ "$got" = "ember_driveway_watch.yaml ember_slack.yaml " ] && ok "two stems → both handled" || bad "two stems → both handled (rc=$rc got: $got)"

out=$(bash "$D" --dry-run ember_slack 2>&1); rc=$?
got=$(pkgs_in "$out")
[ $rc -eq 0 ] && [ "$got" = "ember_slack.yaml " ] && ok "one stem → only that one" || bad "one stem → only that one (rc=$rc got: $got)"

out=$(bash "$D" --dry-run ember_slak 2>&1); rc=$?
[ $rc -eq 2 ] && grep -q "unknown package stem: ember_slak" <<<"$out" && ok "typo stem → exit 2, named" || bad "typo stem → exit 2 (rc=$rc)"

out=$(bash "$D" --dry-run --frce ember_slack 2>&1); rc=$?
[ $rc -eq 2 ] && grep -q "unknown option: --frce" <<<"$out" && ok "unknown option → exit 2" || bad "unknown option → exit 2 (rc=$rc)"

out=$(bash "$D" --help 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "several stems" <<<"$out" && ok "--help documents multi-stem" || bad "--help documents multi-stem (rc=$rc)"
exit $fail
