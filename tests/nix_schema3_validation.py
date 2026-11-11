"""Evaluate actual schema-3 composition in bounded batches; never activate."""

from nix_matrix import arguments, evaluate
from test_profile_validation import profile


def cases():
    import json
    from test_home import ROOT
    return json.loads((ROOT / "modules/ci/profiles/_cases.json").read_text())["schema3"]


def main():
    profiles = cases()
    args = arguments(profiles)
    for name, value, actual in evaluate("schema3-composition.nix", profiles, args.selected, args.batch_size):
        assert actual["homeManagerCliInstalled"] is True, (name, "Home Manager CLI missing from installed packages")
        assert actual["gpu"] is False and actual["nixgl"] is True and actual["vulkan"] is False
        assert actual["firefoxWrapped"] is True
        assert actual["firefoxRecipePreserved"] is True
        assert all(all(checks.values()) for checks in actual["packages"].values()), (name, actual["packages"])
        assert "LD_LIBRARY_PATH" not in actual["environment"]
        assert ("espanso" in actual["services"]) == (name in ("capabilities", "all"))
        assert actual["ghosttyConfigured"] == (name in ("capabilities", "dell-mixed", "all"))
        assert ("finite-grist" in actual["desktopEntries"]) == (name in ("capabilities", "all"))
        assert ("finite-vates-notes" in actual["desktopEntries"]) == (name in ("capabilities", "all"))
        assert ("camera-controls" in actual["packages"]) == (name in ("dell-mixed", "all"))
        assert ("chromium" in actual["packages"]) == (name in ("capabilities", "all"))
        for role in value["roles"]:
            assert actual["environment"]["FINITE_ROLE_" + role.upper()] == "1"
        if name == "capabilities":
            assert not any(key.startswith("FINITE_ROLE_") for key in actual["environment"])
        print(f"Schema-3 {name}: actual membership, wrapping, services and backend passed", flush=True)


if __name__ == "__main__":
    main()
