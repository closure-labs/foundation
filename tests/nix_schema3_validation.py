"""Evaluate actual schema-3 composition in bounded batches; never activate."""

from nix_matrix import arguments, evaluate
from test_profile_validation import profile


def cases():
    base = {**profile(), "schema": 3, "roles": [], "packages": []}
    cases = {
        "minimal": {},
        "family": {"roles": ["family"]},
        "media": {"roles": ["media"]},
        "creative": {"roles": ["creative"]},
        "gaming": {"roles": ["gaming"]},
        "capabilities": {"capabilities": ["devops", "support-tools", "trainer-links", "executive-links", "chromium"], "packages": ["jj"]},
        "dell-mixed": {"foundation": "bluefin-dx", "hardware": "dell-xps-9350-intel", "roles": ["developer", "creative"]},
        "all": {"roles": ["developer", "sales", "trainer", "support", "executive", "it", "family", "media", "creative", "gaming"],
                "capabilities": ["team-chat", "file-sync", "notes", "chromium", "camera-controls", "web-apps", "desktop-comforts", "pdf-tools", "painting", "video-editing", "modeling", "recording", "jellyfin", "audio-player", "steam", "heroic", "lutris"],
                "packages": ["hack-font", "herdr", "jj", "opencode", "uv"]},
    }
    return {name: {**base, **changes} for name, changes in cases.items()}


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
