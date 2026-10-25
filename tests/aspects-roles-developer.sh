#!/usr/bin/env bash
set -euo pipefail

aspect_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module="modules/roles/developer/_home.nix"

# shellcheck disable=SC2016 # Match the literal Nix interpolation.
grep -qF 'home.sessionVariables.FINITE_ROLE_DEVELOPER = "1"' "${module}"
test ! -e "${aspect_root}/apply.sh"
shopt -s nullglob dotglob
manifests=("${aspect_root}"/manifests/*)
test "${#manifests[@]}" -eq 0
