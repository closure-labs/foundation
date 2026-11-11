#!/usr/bin/env bash
set -euo pipefail

aspect_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module="modules/apps/espanso/_settings.nix"

grep -qF 'espanso = pkgs.espanso-wayland' "${module}"
if grep -qF 'espanso = pkgs.espanso;' "${module}"; then
	echo 'Wayland-only Finite profiles must not install X11 Espanso' >&2
	exit 1
fi
grep -qF "ExecStart = \"\${espanso}/bin/espanso launcher\"" "${module}"
test ! -e "${aspect_root}/apply.sh"
shopt -s nullglob dotglob
manifests=("${aspect_root}"/manifests/*)
test "${#manifests[@]}" -eq 0

