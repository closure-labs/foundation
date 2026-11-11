#!/usr/bin/env bash
set -euo pipefail

aspect_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module="modules/profiles/composition/_home.nix"

# shellcheck disable=SC2016 # Match the literal Nix interpolation.
grep -qF '(map (role: "FINITE_ROLE_${lib.toUpper role}") foundationComposition.profile.roles) (_: "1")' "${module}"
test ! -e "${aspect_root}/apply.sh"
shopt -s nullglob dotglob
manifests=("${aspect_root}"/manifests/*)
test "${#manifests[@]}" -eq 0
