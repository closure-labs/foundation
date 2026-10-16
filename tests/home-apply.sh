#!/usr/bin/env bash
set -euo pipefail

repo=$(pwd)
test_root=$(mktemp -d)
trap 'rm -rf -- "$test_root"' EXIT
export XDG_CONFIG_HOME="$test_root/config"
export FINITE_HOME_FLAKE_ROOT="$test_root/checkout"
export FINITE_NIX_COMMAND="$test_root/nix"
export FINITE_BREW_BOOTSTRAP_COMMAND="$test_root/brew-bootstrap"
export FINITO_TEST_ROOT="$test_root"
mkdir -p "$XDG_CONFIG_HOME" "$FINITE_HOME_FLAKE_ROOT" "$test_root/activation"
cp -a flake.nix flake.lock finite-template.json profile.json customize.nix modules "$FINITE_HOME_FLAKE_ROOT/"
mkdir -p "$FINITE_HOME_FLAKE_ROOT"/{.git,.jj,.direnv,result}
touch "$FINITE_HOME_FLAKE_ROOT/.git/sentinel" "$FINITE_HOME_FLAKE_ROOT/.jj/sentinel"
printf 'personal source\n' >"$FINITE_HOME_FLAKE_ROOT/personal.txt"
account=$(id -un)
account_home=$(getent passwd "$account" | cut -d: -f6)
jq --arg username "$account" --arg home "$account_home" \
  '.identity = {username: $username, homeDirectory: $home} | .packages = ["jj"]' \
  profile.json >"$FINITE_HOME_FLAKE_ROOT/profile.json"
cp "$FINITE_HOME_FLAKE_ROOT/profile.json" "$test_root/original-profile.json"

{
  printf '#!%s\n' "$BASH"
  cat <<'EOF'
set -euo pipefail
[[ " $* " == *' --no-update-lock-file '* ]]
for argument in "$@"; do
  if [[ "$argument" == path:*#homeConfigurations.*.activationPackage ]]; then
    staged=${argument#path:}
    staged=${staged%%#*}
  fi
done
test -n "${staged:-}"
for excluded in .git .jj .direnv result; do
  test ! -e "$staged/$excluded"
done
cmp "$FINITE_HOME_FLAKE_ROOT/personal.txt" "$staged/personal.txt"
cmp "$FINITE_HOME_FLAKE_ROOT/flake.lock" "$staged/flake.lock"
test -f "$staged/modules/aspects/capabilities/devops/rootfs/usr/share/finite/zsh/.zshrc"
cp "$staged/profile.json" "$FINITO_TEST_ROOT/built-profile.json"
[[ "${FINITO_TEST_BUILD_FAIL:-false}" == false ]]
printf '%s\n' "$FINITO_TEST_ROOT/activation"
EOF
} >"$FINITE_NIX_COMMAND"
{
  printf '#!%s\n' "$BASH"
  # shellcheck disable=SC2016
  printf 'touch "$FINITO_TEST_ROOT/activated"\n'
} >"$test_root/activation/activate"
cat >"$FINITE_BREW_BOOTSTRAP_COMMAND" <<'EOF'
set -euo pipefail
[[ "${FINITO_TEST_BREW_FAIL:-false}" == false ]]
touch "$FINITO_TEST_ROOT/brew-provisioned"
EOF
chmod +x "$FINITE_NIX_COMMAND" "$test_root/activation/activate"
apply="$repo/modules/finite-home-apply"

bash "$apply" --roles support,developer --check >/dev/null
jq -e '.roles == ["developer", "support"] and .packages == ["jj"]' "$test_root/built-profile.json" >/dev/null
cmp "$test_root/original-profile.json" "$FINITE_HOME_FLAKE_ROOT/profile.json"
test ! -e "$test_root/activated"
test ! -e "$test_root/brew-provisioned"

for failure in build brew; do
  if env "FINITO_TEST_${failure^^}_FAIL=true" bash "$apply" --roles it >/dev/null 2>&1; then
    echo "Failed $failure was accepted" >&2
    exit 1
  fi
  cmp "$test_root/original-profile.json" "$FINITE_HOME_FLAKE_ROOT/profile.json"
  test ! -e "$test_root/activated"
done

for roles in developer,developer unknown; do
  if bash "$apply" --roles "$roles" --check >/dev/null 2>&1; then
    echo "Invalid roles accepted: $roles" >&2
    exit 1
  fi
done

bash "$apply" --roles support,developer --packages uv,herdr >/dev/null
jq -e '.roles == ["developer", "support"] and .packages == ["herdr", "uv"]' "$FINITE_HOME_FLAKE_ROOT/profile.json" >/dev/null
cmp "$FINITE_HOME_FLAKE_ROOT/profile.json" "$XDG_CONFIG_HOME/finite/profile.json"
cmp flake.lock "$FINITE_HOME_FLAKE_ROOT/flake.lock"
test -e "$test_root/brew-provisioned"
test -e "$test_root/activated"
test -e "$FINITE_HOME_FLAKE_ROOT/.jj/sentinel"
printf 'Home Manager apply contracts passed\n'
