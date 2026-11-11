#!/usr/bin/env python3
"""Advance the stable pair in Tack as one change."""
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request
import tomllib


PINS = ".tack/pins.toml"
LOCK = ".tack/pins.lock.json"
STABLE_PINS = ("nixpkgs", "home-manager", "office-stable", "passwords-stable")


def stable_pair(root):
    """Read the core series and validate the other stable declarations."""
    groups = tomllib.loads((root / PINS).read_text())["inputs"]
    pkgs = re.fullmatch(
        r"https://flakehub\.com/f/DeterminateSystems/nixpkgs-(\d{2})\.(05|11)-chilled/0\.1",
        groups["core"]["nixpkgs"]["url"],
    )
    if pkgs is None:
        raise ValueError("Expected a stable Nixpkgs URL")
    version = ".".join(pkgs.groups())
    home = "https://flakehub.com/f/nix-community/home-manager/0." + version.replace(".", "")
    if groups["core"]["home-manager"]["url"] != home:
        raise ValueError("Stable Nixpkgs and Home Manager pins must use the same series")
    for group, pin in (("office", "office-stable"), ("password-managers", "passwords-stable")):
        if groups[group][pin]["url"] != pkgs[0]:
            raise ValueError(f"{pin} must track the stable Nixpkgs series")
    return version


def next_series(current):
    year, month = map(int, current.split("."))
    year, month = (year, 11) if month == 5 else (year + 1, 5)
    return f"{year:02d}.{month:02d}"


def available(candidate):
    for repository, branch in (("NixOS/nixpkgs", "nixos-" + candidate), ("nix-community/home-manager", "release-" + candidate)):
        result = subprocess.run(["git", "ls-remote", "--exit-code", "--heads", "https://github.com/" + repository + ".git", "refs/heads/" + branch], timeout=30, capture_output=True)
        if result.returncode == 2:
            print("The next stable pair is not available")
            return False
        result.check_returncode()
    for url in (f"https://flakehub.com/f/DeterminateSystems/nixpkgs-{candidate}-chilled/0.1", f"https://flakehub.com/f/nix-community/home-manager/0.{candidate.replace('.', '')}"):
        try:
            with urllib.request.urlopen(url, timeout=30):
                pass
        except urllib.error.HTTPError as error:
            if error.code == 404:
                print("The next stable mirrors are not available")
                return False
            raise
    return True


def advance(root):
    current = stable_pair(root)
    candidate = next_series(current)
    if not available(candidate):
        return False

    pins, lock = root / PINS, root / LOCK
    before = {path: path.read_bytes() for path in (pins, lock)}
    try:
        text = pins.read_text()
        text = text.replace(f"nixpkgs-{current}-chilled", f"nixpkgs-{candidate}-chilled")
        text = text.replace("home-manager/0." + current.replace(".", ""), "home-manager/0." + candidate.replace(".", ""))
        pins.write_text(text)
        subprocess.run(
            ["nix", "run", "--no-update-lock-file", "path:.#tack", "--", "update", *STABLE_PINS],
            cwd=root, check=True,
        )
    except BaseException:
        for path, contents in before.items():
            path.write_bytes(contents)
        raise
    print(f"Advanced the stable Tack pins from {current} to {candidate}")
    return True


if __name__ == "__main__":
    advance(Path(__file__).resolve().parents[1])
