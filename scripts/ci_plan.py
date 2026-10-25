#!/usr/bin/env python3
"""Plan affected Nix checks and validate the required CI gate. Unknowns run full."""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.request


SCHEMA3 = ["minimal", "family", "media", "creative", "gaming", "capabilities", "dell-mixed", "all"]
HOSTS = ["generic", "amd-laptop", "intel-laptop", "intel-desktop-amd-discrete",
         "amd-desktop-intel-discrete", "amd-integrated-and-discrete", "intel-integrated-and-discrete",
         "dell-camera-disabled", "workstation"]
LEGACY = [f"schema{schema}-{foundation}" for schema in (2, 3) for foundation in ("bluefin", "bluefin-dx")]
ROLES = {"developer", "sales", "trainer", "support", "executive", "it"}
RECIPE_CASES = {
    "lib/ghostty-package.nix": ["capabilities", "dell-mixed", "all"],
    "lib/without-icon-build-files.nix": ["all"],
}


def documentation(path):
    return (path in {"README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md"}
            or (path.startswith("docs/") and path.endswith((".md", ".txt", ".json")))
            or (path.startswith(".great_cto/") and path.endswith(".md")))


def make_plan(paths, full=False, baseline=None):
    if paths is not None:
        if (not isinstance(paths, list) or any(not isinstance(p, str) or not p
                or PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts for p in paths)):
            raise ValueError("Invalid changed paths")
        paths = sorted(set(paths))
    plan = {"schema": 1, "mode": "full", "paths": paths, "schema3": list(SCHEMA3),
            "hosts": list(HOSTS), "legacy": list(LEGACY), "contracts": True, "baseline": None}
    if full or not paths:
        return plan
    schema3, hosts, legacy = set(), set(), set()
    for path in paths:
        if documentation(path):
            continue
        parts = PurePosixPath(path).parts
        if (len(parts) >= 5 and parts[:3] == ("modules", "aspects", "roles") and parts[3] in ROLES):
            schema3.add("all")
            if parts[3] == "developer":
                schema3.add("dell-mixed")
        elif path.startswith("modules/_legacy/aspects/capabilities/devops/"):
            schema3.update(["capabilities", "dell-mixed", "all"])
        elif path.startswith("modules/_legacy/aspects/hardware/dell-xps-9350-intel/"):
            schema3.update(["minimal", "dell-mixed"])
            hosts.update(["generic", "dell-camera-disabled"])
        elif path in RECIPE_CASES:
            schema3.update(RECIPE_CASES[path])
        else:
            return plan
        # Exercise legacy module selection on both foundations and the real
        # schema-3 workstation, including their interactions with shared policy.
        legacy.update(LEGACY[:2])
        hosts.add("workstation")
    plan.update(mode="focused" if schema3 or hosts or legacy else "docs", contracts=False, baseline=baseline,
                schema3=[name for name in SCHEMA3 if name in schema3],
                hosts=[name for name in HOSTS if name in hosts],
                legacy=[name for name in LEGACY if name in legacy])
    return plan


def validate_plan(plan):
    if (not isinstance(plan, dict) or type(plan.get("schema")) is not int or plan.get("schema") != 1
            or type(plan.get("contracts")) is not bool or not isinstance(plan.get("mode"), str)
            or plan.get("mode") not in {"docs", "focused", "full"}):
        raise ValueError("Missing or unsupported CI plan")
    if plan["mode"] != "full" and (not isinstance(plan.get("baseline"), str)
                                  or not re.fullmatch(r"[a-f0-9]{40}", plan["baseline"])):
        raise ValueError("A shortened plan needs a verified green base commit")
    expected = make_plan(plan.get("paths"), full=plan["mode"] == "full", baseline=plan.get("baseline"))
    # Recompute every selection: an omitted case, empty focused plan, extra key
    # or mismatched mode must never authorize a skipped check.
    if plan != expected:
        raise ValueError("CI plan does not match its changed paths")
    return plan


def requires_full(event, ref, requested=False):
    return requested or not (event == "pull_request" or (event == "push" and ref == "refs/heads/main"))


def changed_paths(base, head, cwd=None):
    if (not all(isinstance(sha, str) and re.fullmatch(r"[a-f0-9]{40}", sha) and sha != "0" * 40
                for sha in (base, head))):
        return None
    try:
        # Disable rename detection so moving a module to/from docs cannot hide
        # either path. An unavailable/shallow base selects the full suite.
        data = subprocess.check_output(["git", "diff", "--no-renames", "--name-only", "-z", base, head, "--"], stderr=subprocess.PIPE, cwd=cwd)
        return [p.decode("utf-8") for p in data.split(b"\0") if p]
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        return None


def baseline_green(repository, sha, token=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repository or "") or not re.fullmatch(r"[a-f0-9]{40}", sha or ""):
        return False
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Foundation-CI-plan"}
    if token:
        headers["Authorization"] = "Bearer " + token
    url = f"https://api.github.com/repos/{repository}/commits/{sha}/check-runs?check_name=CI%20gate&per_page=100"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as response:
            checks = json.load(response)["check_runs"]
        if not isinstance(checks, list):
            return False
        return any(isinstance(c, dict) and c.get("name") == "CI gate" and c.get("head_sha") == sha
                   and c.get("status") == "completed" and c.get("conclusion") == "success"
                   and isinstance(c.get("app"), dict) and c["app"].get("id") == 15368 for c in checks)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def with_baseline(plan, sha, repository, token=None):
    if plan["mode"] == "full":
        return plan
    if baseline_green(repository, sha, token):
        return validate_plan({**plan, "baseline": sha})
    print("No verified successful base CI gate; running full validation.", file=sys.stderr)
    return make_plan(plan["paths"], full=True)


def check_gate(plan, fixtures, nix, *, full=False):
    validate_plan(plan)
    if fixtures != "success":
        raise ValueError(f"Fixtures and plan did not succeed: {fixtures}")
    if full and plan["mode"] != "full":
        raise ValueError("This event requires full validation")
    expected = "skipped" if plan["mode"] == "docs" else "success"
    if nix != expected:
        raise ValueError(f"{plan['mode']} plan requires Nix result {expected}, got {nix}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "gate"))
    args = parser.parse_args()
    try:
        full = requires_full(os.environ.get("GITHUB_EVENT_NAME"), os.environ.get("GITHUB_REF"),
                             os.environ.get("CI_FULL") == "true")
        if args.operation == "gate":
            plan = json.loads(os.environ.get("CI_PLAN", ""))
            check_gate(plan, os.environ.get("FIXTURES_RESULT"), os.environ.get("NIX_RESULT"), full=full)
            print(f"CI gate passed: {plan['mode']} plan")
            return
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        base = (event.get("pull_request", {}).get("base", {}).get("sha")
                if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" else event.get("before"))
        plan = make_plan(changed_paths(base, os.environ.get("GITHUB_SHA")), full=full)
        plan = with_baseline(plan, base, os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GH_TOKEN"))
        validate_plan(plan)
        encoded = json.dumps(plan, separators=(",", ":"))
        print(json.dumps(plan, indent=2))
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write(f"mode={plan['mode']}\nplan={encoded}\n")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as summary:
                summary.write(f"CI plan: **{plan['mode']}**. Schema-3 cases: {len(plan['schema3'])}; "
                              f"host cases: {len(plan['hosts'])}; work-role cases: {len(plan['legacy'])}.\n")
    except (KeyError, OSError, ValueError) as error:
        parser.exit(1, f"CI plan error: {error}\n")


if __name__ == "__main__":
    main()
