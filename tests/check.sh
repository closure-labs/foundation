#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

while IFS= read -r -d '' file; do
  nix-instantiate --parse "$file" >/dev/null
done < <(find . -path ./.git -prune -o -path ./.jj -prune -o -name '*.nix' -type f -print0)

for file in modules/finite-* modules/aspects/hardware/dell-xps-9350-intel/dell-xps-9350-panel-policy tests/*.sh; do
  bash -n "$file"
done

python3 - <<'PY'
import json
from pathlib import Path

lock = json.loads(Path('flake.lock').read_text())
assert all(node.get('locked', {}).get('type') != 'path' for node in lock['nodes'].values()), 'Local path pin in flake.lock'
assert 'finite' not in lock['nodes'][lock['root']]['inputs'], 'Flake depends on Finite'
for file in ('profile.json', 'finite-template.json', 'modules/aspects/base/brew-packages.json'):
    json.loads(Path(file).read_text())
PY

bash tests/brew-providers.sh
bash tests/dell-panel-policy.sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_home.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_profile_classification.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_profile_validation.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_profile_capabilities.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_profile_drafts.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_profile_editor.py
for aspect in tests/aspects-*.sh; do bash "$aspect"; done
printf 'Foundation checks passed\n'
