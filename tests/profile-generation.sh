#!/usr/bin/env bash
set -euo pipefail
generator="${1:?generator required}"
catalog="${2:?catalog required}"
export FINITE_SKIP_FOUNDATION_CHECK=true
export FINITE_HOME_FLAKE_PATH="$PWD/untouched-consumer"
export FINITE_FOUNDATION_SOURCE=/invalid-caller-source
export FINITE_FOUNDATION_CATALOG=/invalid-caller-catalog
"$generator" --foundation bluefin-dx --roles creative,developer --capabilities recording,office \
  --form-factor desktop --cpu intel --gpus amd-discrete,intel-integrated --format json > profile.json
"$generator" --foundation bluefin-dx --roles creative,developer --capabilities recording,office \
  --form-factor desktop --cpu intel --gpus amd-discrete,intel-integrated > profile.yaml
yq -o=json . profile.yaml > roundtrip.json
jq -S . profile.json > canonical.json
jq -S . roundtrip.json > canonical-roundtrip.json
cmp canonical.json canonical-roundtrip.json
jq -e '.schema == 3 and .roles == ["developer", "creative"] and .capabilities == ["office", "recording"] and
  .host.formFactor == "desktop" and .host.cpu == "intel" and .host.gpus == ["intel-integrated", "amd-discrete"]' profile.json
jq -e '.profileSchema == 3 and .profileCapabilities.writeSchema == 3 and (.roles | length) == 10 and
  .classifications.personal.roles == ["family", "media", "creative", "gaming"]' "$catalog"
"$generator" --foundation bluefin-dx --hardware dell-xps-9350-intel --fingerprint --no-camera --format json > dell.json
jq -e '.host.fingerprint and (.host.camera | not) and .host.model == "dell-xps-9350"' dell.json
if "$generator" --foundation bluefin --roles family,family --format json > invalid.json; then
  echo 'Generator accepted duplicate roles' >&2
  exit 1
fi
test ! -s invalid.json
test ! -e "$FINITE_HOME_FLAKE_PATH"
printf 'Packaged schema-3 generation and catalog round trips passed\n'
