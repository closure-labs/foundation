#!/usr/bin/env bash
set -euo pipefail
cli="${1:?foundation executable required}"
"$cli" --help
"$cli" home --help
for action in check apply update init profile configure migrate status; do
  "$cli" home "$action" --help >/dev/null
done
for args in '' 'home' 'unknown' 'home unknown' 'update'; do
  read -r -a words <<< "$args"
  set +e
  "$cli" "${words[@]}" >invalid-command.log 2>&1
  status=$?
  set -e
  [[ "$status" == 2 ]] || { cat invalid-command.log; exit 1; }
done
export FINITE_SKIP_FOUNDATION_CHECK=true
export FINITE_HOME_FLAKE_PATH="$PWD/untouched-consumer"
"$cli" home profile --foundation bluefin --roles family --format json > cli-profile.json
jq -e '.schema == 3 and .roles == ["family"]' cli-profile.json
[[ ! -e "$FINITE_HOME_FLAKE_PATH" ]]
# Invalid input to check must fail before any consumer can be created or activated.
if "$cli" home check --unknown-option; then exit 1; fi
[[ ! -e "$FINITE_HOME_FLAKE_PATH" ]]
