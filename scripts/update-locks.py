#!/usr/bin/env python3
"""Refresh Tack sources and keep gen paired with the selected Den."""
import json
from pathlib import Path
import re
import subprocess


def update(root):
    pins = root / ".tack/pins.toml"
    lock = root / ".tack/pins.lock.json"
    before = {path: path.read_bytes() for path in (pins, lock)}
    tack = ["nix", "run", "--no-update-lock-file", "path:.#tack", "--"]
    try:
        subprocess.run([*tack, "update", "--exclude", "gen,tooling"], cwd=root, check=True)
        expression = (
            'let pins = import (builtins.toPath ' + json.dumps(str(root / ".tack"))
            + ') {}; in (builtins.fromJSON (builtins.readFile '
            '(pins.den.outPath + "/templates/ci/flake.lock"))).nodes.gen.locked.rev'
        )
        rev = subprocess.check_output(
            ["nix", "eval", "--impure", "--raw", "--expr", expression], cwd=root, text=True
        ).strip()
        if not re.fullmatch(r"[a-f0-9]{40}", rev):
            raise ValueError("Den does not advertise a valid tested gen revision")
        text, count = re.subn(
            r'(?m)^url = "github:sini/gen/[a-f0-9]{40}"$',
            f'url = "github:sini/gen/{rev}"', pins.read_text(),
        )
        if count != 1:
            raise ValueError("Expected one explicit gen pin")
        if text.encode() != before[pins]:
            pins.write_text(text)
            subprocess.run([*tack, "update", "gen"], cwd=root, check=True)
    except BaseException:
        for path, contents in before.items():
            path.write_bytes(contents)
        raise


if __name__ == "__main__":
    update(Path(__file__).resolve().parents[1])
