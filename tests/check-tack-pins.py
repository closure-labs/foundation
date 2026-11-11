"""Check the files needed to load Foundation's Tack resolver."""
import json
from pathlib import Path
import sys
import tomllib

flake_lock, declarations, tack_lock = map(Path, sys.argv[1:])
native = json.loads(flake_lock.read_text())
assert native["nodes"] == {native["root"]: {}}, "Foundation has native dependency pins"

groups = tomllib.loads(declarations.read_text())["inputs"]
assert {"password-managers", "office", "browser", "ai"} <= groups.keys()
pins = {name: pin["url"] for group in groups.values() for name, pin in group.items()}
locked = json.loads(tack_lock.read_text())
assert pins == locked.pop("$declared"), "Run Tack to lock the declared URLs"
assert pins.keys() == locked.keys(), "Tack pin declarations and lock entries differ"
assert all(pin.get("narHash") for pin in locked.values()), "Tack sources must be hash-pinned"
assert all(pin["type"] != "path" for pin in locked.values()), "Local path pin in Tack lock"
