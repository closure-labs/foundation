#!/usr/bin/env python3
"""Advance the stable pair from its owners, regenerating artifacts as one change."""
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request


NIXPKGS_OWNER = "modules/providers/nixpkgs/default.nix"
HOME_MANAGER_OWNER = "modules/home/construction/default.nix"
TRANSACTION_PATHS = (
    NIXPKGS_OWNER,
    HOME_MANAGER_OWNER,
    "flake.nix",
    "flake.lock",
    "modules/ci/_graph.json",
    "docs/ARCHITECTURE.md",
)


def stable_pair(root):
    """Read the declarations, never infer an input owner from generated flake.nix."""
    nixpkgs = (root / NIXPKGS_OWNER).read_text()
    home_manager = (root / HOME_MANAGER_OWNER).read_text()
    versions = re.findall(r'https://flakehub\.com/f/DeterminateSystems/nixpkgs-(\d{2})\.(05|11)-chilled/0\.1"', nixpkgs)
    homes = re.findall(r'https://flakehub\.com/f/nix-community/home-manager/0\.(\d{2})(05|11)"', home_manager)
    if len(versions) != 1 or len(homes) != 1:
        raise ValueError("Expected one stable input declaration in each owning module")
    if versions[0] != homes[0]:
        raise ValueError("Stable Nixpkgs and Home Manager owner declarations must use the same series")
    return ".".join(versions[0])


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

    # Keep user edits and generated artifacts intact if any generation/update fails.
    before = {relative: (root / relative).read_bytes() for relative in TRANSACTION_PATHS}
    try:
        for relative, old, new in (
            (NIXPKGS_OWNER, f"nixpkgs-{current}-chilled", f"nixpkgs-{candidate}-chilled"),
            (HOME_MANAGER_OWNER, "home-manager/0." + current.replace(".", ""), "home-manager/0." + candidate.replace(".", "")),
        ):
            path = root / relative
            path.write_text(path.read_text().replace(old, new))
        subprocess.run(["nix", "run", "--no-update-lock-file", "path:.#write-flake"], cwd=root, check=True)
        subprocess.run(["nix", "flake", "update", "nixpkgs", "home-manager"], cwd=root, check=True)
        subprocess.run(["nix", "run", "--no-update-lock-file", "path:.#write-ci-graph"], cwd=root, check=True)
    except BaseException:
        for relative, contents in before.items():
            (root / relative).write_bytes(contents)
        raise
    print(f"Advanced stable owner declarations and generated artifacts from {current} to {candidate}")
    return True


if __name__ == "__main__":
    advance(Path(__file__).resolve().parents[1])
