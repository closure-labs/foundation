#!/usr/bin/env python3
"""Advance the stable package/Home Manager pair only when both mirrors exist."""
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

root = Path(__file__).resolve().parents[1]
path = root / "flake.nix"
text = path.read_text()
current = re.search(r"nixpkgs-(\d{2})\.(05|11)-chilled", text)
if current is None:
    raise ValueError("Cannot identify the stable package series")
year, month = map(int, current.groups())
year, month = (year, 11) if month == 5 else (year + 1, 5)
candidate = f"{year:02d}.{month:02d}"
for repository, branch in (("NixOS/nixpkgs", "nixos-" + candidate), ("nix-community/home-manager", "release-" + candidate)):
    result = subprocess.run(["git", "ls-remote", "--exit-code", "--heads", "https://github.com/" + repository + ".git", "refs/heads/" + branch], timeout=30, capture_output=True)
    if result.returncode == 2:
        print("The next stable pair is not available")
        raise SystemExit(0)
    result.check_returncode()
for url in (f"https://flakehub.com/f/DeterminateSystems/nixpkgs-{candidate}-chilled/0.1", f"https://flakehub.com/f/nix-community/home-manager/0.{year:02d}{month:02d}"):
    try:
        with urllib.request.urlopen(url, timeout=30):
            pass
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("The next stable mirrors are not available")
            raise SystemExit(0)
        raise
old = f"{current[1]}.{current[2]}"
text = text.replace(f"nixpkgs-{old}-chilled", f"nixpkgs-{candidate}-chilled")
text = text.replace("home-manager/0." + old.replace(".", ""), "home-manager/0." + candidate.replace(".", ""))
path.write_text(text)
subprocess.run(["nix", "flake", "update", "nixpkgs", "home-manager"], cwd=root, check=True)
