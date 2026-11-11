"""Evaluate all work roles on both foundations using schema 3, with consumer modules."""
import json

from nix_matrix import arguments, evaluate
from test_home import ROOT


def cases():
    import json
    from test_home import ROOT
    return json.loads((ROOT / "modules/ci/profiles/_cases.json").read_text())["legacy"]


def main():
    profiles = cases()
    args = arguments(profiles)
    for name, _, actual in evaluate("legacy-composition.nix", profiles, args.selected, args.batch_size):
        assert actual["homeManagerCliInstalled"] is True, name
        for field in ("bluefinAspectSelected", "preparationAttached", "stockFzfNotDuplicated",
                      "unmanagedFlatpaksPreserved", "flatpakServiceWrapped"):
            assert actual[field] is True, (name, field)
        print(f"All work roles and optional packages: {name} passed", flush=True)


if __name__ == "__main__":
    main()
