#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

bash tests/check.sh
actionlint
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/release.py --check
