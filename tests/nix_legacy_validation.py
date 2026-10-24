"""Evaluate all work roles on both foundations and schemas, with consumer modules."""
import json

from nix_matrix import arguments, evaluate
from test_home import ROOT


def cases():
    base = json.loads((ROOT / "profile.json").read_text())
    base.pop("host", None)
    base.update(hardware="dell-xps-9350-intel",
                roles=["developer", "sales", "trainer", "support", "executive", "it"],
                packages=["hack-font", "herdr", "jj", "opencode", "uv"])
    result = {}
    for schema in (2, 3):
        for foundation in ("bluefin", "bluefin-dx"):
            value = {**base, "schema": schema, "foundation": foundation}
            if schema == 2:
                value.pop("capabilities", None)
            result[f"schema{schema}-{foundation}"] = value
    return result


def main():
    profiles = cases()
    args = arguments(profiles)
    for name, _, actual in evaluate("legacy-composition.nix", profiles, args.selected, args.batch_size):
        assert actual["homeManagerCliInstalled"] is True, name
        print(f"All work roles and optional packages: {name} passed", flush=True)


if __name__ == "__main__":
    main()
