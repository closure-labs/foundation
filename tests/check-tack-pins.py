"""Check the files needed to load Foundation's Tack resolver."""
import json
from pathlib import Path
import sys
import tomllib

flake_lock, declarations, tack_lock = map(Path, sys.argv[1:])
native = json.loads(flake_lock.read_text())
assert native["nodes"] == {native["root"]: {}}, "Foundation has native dependency pins"

configuration = tomllib.loads(declarations.read_text())
groups = configuration["inputs"]
assert {"core", "development", "ai", "tooling"} <= groups.keys()
pins = {name: pin["url"] for group in groups.values() for name, pin in group.items()}
locked = json.loads(tack_lock.read_text())
assert pins == locked.pop("$declared"), "Run Tack to lock the declared URLs"
follow_targets = {
    target if isinstance(target, str) else name
    for name, target in configuration.get("all_follow", {}).items()
}
automatic_pins = {target for target in follow_targets - pins.keys() if "/" not in target}
assert pins.keys() | automatic_pins == locked.keys(), "Tack declarations and lock entries differ"
assert all(pin.get("narHash") for pin in locked.values()), "Tack sources must be hash-pinned"
assert all(pin["type"] != "path" for pin in locked.values()), "Local path pin in Tack lock"

channels = {"nixpkgs", "nixpkgs-weekly", "nixpkgs-unstable"}
assert channels <= pins.keys(), "The three shared Nixpkgs channels are required"
assert all(
    name in channels or url not in {pins[channel] for channel in channels}
    for name, url in pins.items()
), "Reuse shared Nixpkgs channels instead of pinning a second copy"
