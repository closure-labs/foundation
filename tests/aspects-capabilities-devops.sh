#!/usr/bin/env bash
set -euo pipefail

aspect_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
module="modules/capabilities/devops/_home.nix"
rootfs="modules/capabilities/devops/_assets/rootfs"

for file in .zshrc aliases.zsh bindings.zsh fzf.zsh prompt.zsh starship.toml LICENSE; do
	test -f "${rootfs}/usr/share/finite/zsh/${file}"
done
grep -qF 'paths = [pkgs.ghostty];' modules/apps/ghostty/_package.nix
grep -qF -- "--replace-fail 'DBusActivatable=true' 'DBusActivatable=false'" modules/apps/ghostty/_package.nix
grep -qF '"ghostty/config.ghostty".text' "${module}"
# shellcheck disable=SC2016 # Ghostty must start the Home Manager Zsh package.
grep -qF '"command = ${config.programs.zsh.package}/bin/zsh"' "${module}"
if grep -qF '"ghostty/config".source' "${module}"; then
	echo 'The devops aspect still deploys the superseded Ghostty config path' >&2
	exit 1
fi
grep -qF 'apps/openbao' modules/capabilities/devops/_feature.nix
grep -qF 'fzf --zsh' modules/hosts/os/bluefin/_home.nix
grep -qF 'src = pkgs.zsh-vi-mode' "${module}"
test ! -e "${rootfs}/usr/share/finite/zsh/plugins.zsh"
test ! -e "${aspect_root}/apply.sh"
shopt -s nullglob dotglob
manifests=("${aspect_root}"/manifests/*)
test "${#manifests[@]}" -eq 0
