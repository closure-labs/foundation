#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# A path flake includes new files in jj working copies as well as Git checkouts.
export PYTHONDONTWRITEBYTECODE=1
exec python3 tests/nix_checks.py "$@"
