#!/usr/bin/env bash
set -euo pipefail
activation="${1:?installPackages script is required}"
profile_directory="${2:?profile directory is required}"
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/bin" "$work/profile"
export TEST_COMMAND_LOG="$work/commands"
printf '#!%s\n' "$BASH" >"$work/bin/nix"
cat >>"$work/bin/nix" <<'NIX'
set -euo pipefail
if [[ "$(basename "$0")" == nix-env ]]; then
  printf 'nix-env %s\n' "$*" >>"$TEST_COMMAND_LOG"
elif [[ "$*" == 'profile add --help' ]]; then
  [[ "$TEST_NIX_HAS_ADD" == true ]]
elif [[ "$1 $2" == 'profile add' || "$1 $2" == 'profile install' ]]; then
  printf '%s\n' "$*" >>"$TEST_COMMAND_LOG"
else
  printf 'Unexpected Nix command: %s\n' "$*" >&2
  exit 80
fi
NIX
chmod +x "$work/bin/nix"
ln -s nix "$work/bin/nix-env"
export PATH="$work/bin:$PATH"
activation_text=$(<"$activation")
printf '%s\n' "${activation_text//"$profile_directory"/"$work/profile"}" >"$work/activate"
run() { "$@"; }
nixProfileRemove() { printf 'remove %s\n' "$*" >>"$TEST_COMMAND_LOG"; }
_iError() { printf '%s\n' "$*" >&2; }
for mode in modern older legacy; do
  : >"$TEST_COMMAND_LOG"
  rm -f "$work/profile/manifest.json"
  export TEST_NIX_HAS_ADD=false
  if [[ "$mode" != legacy ]]; then
    touch "$work/profile/manifest.json"
  fi
  if [[ "$mode" == modern ]]; then
    export TEST_NIX_HAS_ADD=true
  fi
  # Exercise Home Manager's actual merged activation block with a fake Nix.
  # shellcheck source=/dev/null
  source "$work/activate"
  case "$mode" in
    modern|older)
      [[ "$(head -n 1 "$TEST_COMMAND_LOG")" == 'remove home-manager-path' ]]
      [[ "$(wc -l <"$TEST_COMMAND_LOG")" -eq 2 ]]
      subcommand=install
      [[ "$mode" != modern ]] || subcommand=add
      [[ "$(tail -n 1 "$TEST_COMMAND_LOG")" == "profile $subcommand /nix/store/"*'-home-manager-path' ]]
      ;;
    legacy)
      [[ "$(wc -l <"$TEST_COMMAND_LOG")" -eq 1 ]]
      [[ "$(<"$TEST_COMMAND_LOG")" == 'nix-env -i /nix/store/'*'-home-manager-path' ]]
      ;;
  esac
  [[ ! -v foundationNixProfileCommand ]]
done
printf 'Modern, older and legacy Nix profile activation passed\n'
