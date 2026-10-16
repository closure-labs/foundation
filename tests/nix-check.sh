#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# A path flake includes new files in jj working copies as well as Git checkouts.
build_flags=()
case "${1:-}" in
  '') ;;
  --no-build) build_flags+=(--no-build) ;;
  *) printf 'Usage: bash tests/nix-check.sh [--no-build]\n' >&2; exit 2 ;;
esac
nix flake check --no-update-lock-file --print-build-logs "${build_flags[@]}" path:.

# Evaluate selectable modules too: the shipped profile has no roles enabled.
staged=$(mktemp -d)
trap 'rm -rf -- "$staged"' EXIT
cp -a flake.nix flake.lock profile.json finite-template.json customize.nix modules "$staged/"
for foundation in bluefin bluefin-dx; do
  jq --arg foundation "$foundation" \
    '.foundation = $foundation | .hardware = "dell-xps-9350-intel" |
     .roles = ["developer", "sales", "trainer", "support", "executive", "it"] |
     .packages = ["hack-font", "herdr", "jj", "opencode", "uv"]' \
    profile.json >"$staged/profile.json"
  username=$(jq -r '.identity.username' "$staged/profile.json")
  nix eval --no-update-lock-file --raw \
    "path:$staged#homeConfigurations.$username.activationPackage.drvPath"
  printf '\nEvaluated all roles and optional packages on %s with Dell hardware\n' "$foundation"
done
