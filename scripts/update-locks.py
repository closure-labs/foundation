#!/usr/bin/env python3
"""Refresh dependencies and synchronize gen with the selected Den's test lock."""
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
subprocess.run(["nix", "flake", "update"], cwd=root, check=True)
expression = 'let f = builtins.getFlake ' + json.dumps("path:" + str(root)) + '; in (builtins.fromJSON (builtins.readFile (f.inputs.den.outPath + "/templates/ci/flake.lock"))).nodes.gen.locked.rev'
rev = subprocess.run(["nix", "eval", "--impure", "--raw", "--no-update-lock-file", "--expr", expression], check=True, text=True, capture_output=True).stdout.strip()
if not re.fullmatch(r"[a-f0-9]{40}", rev):
    raise ValueError("Den does not advertise a valid tested gen revision")
path = root / "modules/flake/framework/default.nix"
text, count = re.subn(r'gen.url = "github:sini/gen/[a-f0-9]{40}";', f'gen.url = "github:sini/gen/{rev}";', path.read_text())
if count != 1:
    raise ValueError("Expected one explicit gen input")
path.write_text(text)
subprocess.run(["nix", "run", "path:.#write-flake"], cwd=root, check=True)
subprocess.run(["nix", "flake", "update", "gen"], cwd=root, check=True)

subprocess.run(["nix", "run", "path:.#write-ci-graph"], cwd=root, check=True)
