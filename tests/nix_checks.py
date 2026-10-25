"""Run full or affected Nix validation; Nix reuses unchanged check outputs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ci_plan import make_plan, validate_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--ci", action="store_true", help="Require the explicit CI_PLAN supplied by the fixture job")
    parser.add_argument("--batch-size", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    plan = validate_plan(json.loads(os.environ["CI_PLAN"])) if args.ci else make_plan(None)
    if plan["mode"] == "docs":
        parser.error("The Nix job must be skipped for a documentation plan")
    os.chdir(ROOT)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    def run(command):
        subprocess.run(command, check=True, env=environment)

    def matrix(script, names):
        if names:
            run([sys.executable, f"tests/{script}", "--batch-size", str(args.batch_size),
                 *[arg for name in names for arg in ("--case", name)]])

    print(f"Nix validation plan: {plan['mode']}", flush=True)
    if plan["contracts"]:
        for script in ("nix_feature_validation.py", "nix_profile_validation.py", "nix_editor_validation.py", "nix_helper_source_validation.py"):
            run([sys.executable, "tests/" + script])
    matrix("nix_schema3_validation.py", plan["schema3"])
    matrix("nix_host_validation.py", plan["hosts"])
    if plan["mode"] == "full":
        run(["nix", "flake", "check", "--no-update-lock-file", "--print-build-logs",
             *(["--no-build"] if args.no_build else []), "path:."])
    elif args.no_build:
        for check in plan["checks"]:
            run(["nix", "eval", "--raw", "--no-update-lock-file", f"path:.#checks.x86_64-linux.{check}.drvPath"])
    elif plan["checks"]:
        run(["nix", "build", "--no-link", "--no-update-lock-file", "--print-build-logs",
             *[f"path:.#checks.x86_64-linux.{check}" for check in plan["checks"]]])
    matrix("nix_legacy_validation.py", plan["legacy"])
    print("All planned Nix checks passed", flush=True)


if __name__ == "__main__":
    main()
