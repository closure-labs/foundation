"""Prove helper source isolation without losing complete release provenance."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from test_home import ROOT, home


def evaluate(source, checks=True):
    expression = 'let f = builtins.getFlake ' + home.nix_value("path:" + str(source)) + '; in { '
    expression += 'helper = toString (import (f.outPath + "/lib/helper-source.nix") f.outPath); '
    if checks:
        expression += 'checks = builtins.mapAttrs (_: d: d.drvPath) f.checks.x86_64-linux; '
        expression += 'metadata = f.lib.sourceInfo; narHash = f.narHash; init = f.packages.x86_64-linux.home-init.drvPath; '
    expression += '}'
    return json.loads(subprocess.check_output(["nix", "eval", "--impure", "--json", "--no-update-lock-file", "--expr", expression], text=True))


def main():
    with tempfile.TemporaryDirectory(prefix="foundation-helper-source-") as temporary:
        source = Path(temporary)
        for directory in ("lib", "scripts", "modules", "templates", "tests", "docs"):
            shutil.copytree(ROOT / directory, source / directory, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in ("flake.nix", "flake.lock", "VERSION", "foundation.json", "profile.json", "customize.nix",
                     "finite-template.json", "legacy-managed.json", "LICENSE", "NOTICE", "ORIGIN.md", "README.md"):
            shutil.copy2(ROOT / name, source / name)
        before = evaluate(source)
        helper = Path(before["helper"])
        for name in ("scripts/home.py", "lib/generate-profile.nix", "lib/profile-capabilities.json", "lib/profile-drafts/contract.nix",
                     "flake.lock", "profile.json", "customize.nix", "modules/local.nix", "legacy-managed.json", "VERSION",
                     "foundation.json", "LICENSE", "NOTICE", "ORIGIN.md"):
            assert (helper / name).is_file(), name
        for name in ("flake.nix", "README.md", "tests", "templates", "scripts/ci_plan.py", "modules/ci"):
            assert not (helper / name).exists(), name
        source.joinpath("README.md").write_text("Documentation-only change.\n")
        flake = source / "flake.nix"
        flake.write_text(flake.read_text() + "\n# Description/comment-only edit.\n")
        source.joinpath("scripts/ci_plan.py").write_text("# CI-only change.\n")
        after = evaluate(source)
        assert after["helper"] == before["helper"]
        assert {k:v for k,v in after["checks"].items() if k not in ("check-flake-file", "ci-graph", "consumer-template")} == {k:v for k,v in before["checks"].items() if k not in ("check-flake-file", "ci-graph", "consumer-template")}, (before["checks"], after["checks"])
        assert before["metadata"]["narHash"] == before["narHash"]
        assert after["metadata"]["narHash"] == after["narHash"]
        assert before["narHash"] != after["narHash"]
        assert before["init"] != after["init"], "Published initializer must retain exact full-source provenance"
        settings = source / "modules/apps/espanso/_settings.nix"
        settings.write_text(settings.read_text() + "\n# Unselected home settings.\n")
        assert evaluate(source, checks=False)["helper"] == after["helper"]
        script = source / "scripts/home.py"
        script.write_text(script.read_text() + "\n# Runtime helper change.\n")
        assert evaluate(source, checks=False)["helper"] != after["helper"]
        print("Helper bundle: five check derivations ignore docs/flake comments/CI-only files; runtime changes invalidate it; full-source provenance retained", flush=True)


if __name__ == "__main__":
    main()
