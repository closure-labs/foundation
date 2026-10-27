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


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = "modules/ci/_graph.json"
CASE_PROFILES = json.loads((ROOT / "modules/ci/profiles/_cases.json").read_text())
SCHEMA3, HOSTS, LEGACY = (list(CASE_PROFILES[group]) for group in ("schema3", "hosts", "legacy"))
FULL_CHECKS = json.loads((ROOT / GRAPH_PATH).read_text())["plans"]["full"]["checks"]


def closure(graph, schema, roots):
    if type(schema) is not int or schema != 3:
        raise ValueError("Unsupported home profile schema; expected schema 3")
    visited = set()
    def visit(name, trail):
        if name in trail:
            raise ValueError("Dependency cycle")
        if name not in graph["features"]:
            raise ValueError("Missing dependency")
        if name in visited:
            return
        feature = graph["features"][name]
        for dependency in feature["dependencies"] + feature["schemaDependencies"].get(str(schema), []):
            visit(dependency, trail | {name})
        visited.add(name)
    for name in roots:
        visit(name, set())
    return visited


def load_graph(path=None, validate_sources=False):
    graph = json.loads((Path(path) if path else ROOT / GRAPH_PATH).read_text())
    if type(graph.get("schema")) is not int or graph["schema"] != 1:
        raise ValueError("Unsupported dependency graph")
    if graph["fullChecks"] != FULL_CHECKS or set(graph["checks"]) != set(FULL_CHECKS):
        raise ValueError("Unsupported check set")
    if (graph["plans"]["full"]["checks"] != FULL_CHECKS
            or not graph["plans"]["automation"]["checks"]
            or any(name not in FULL_CHECKS for name in graph["plans"]["automation"]["checks"])):
        raise ValueError("Invalid flake CI plan targets")
    owners = set()
    for name, feature in graph["features"].items():
        directory = "modules/" + name + "/"
        if feature["directory"] != directory or not feature["files"]:
            raise ValueError("Invalid feature ownership")
        for file in feature["files"]:
            if not file.startswith(directory) or ".." in PurePosixPath(file).parts or file in owners:
                raise ValueError("Ambiguous feature ownership")
            owners.add(file)
    closure(graph, 3, graph["features"])
    for group, profiles in CASE_PROFILES.items():
        if set(graph["cases"][group]) != set(profiles):
            raise ValueError("Stale profile cases")
        for case in graph["cases"][group].values():
            closure(graph, case["schema"], case["roots"])
    for check in graph["checks"].values():
        closure(graph, check["schema"], check["roots"])
    if validate_sources:
        generated = subprocess.check_output(
            ["nix-instantiate", "--store", "dummy://", "--eval", "--strict", "--json", str(ROOT / "modules/ci/_graph.nix")],
            text=True, stderr=subprocess.PIPE)
        if graph != json.loads(generated):
            raise ValueError("Stale dependency graph")
    return graph


def graph_digest(graph):
    import hashlib
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def documentation(path):
    if path == "docs/ARCHITECTURE.md":
        return False
    return (path in {"README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md"}
            or (path.startswith("docs/") and path.endswith((".md", ".txt", ".json")))
            or (path.startswith(".great_cto/") and path.endswith(".md")))


# Preserve every byte except a pinned action SHA and its same-major version label.
ACTION_PIN = re.compile(
    r"(?P<prefix>[ \t]*(?:- )?uses: )(?P<action>[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)"
    r"@(?P<sha>[a-f0-9]{40})(?P<gap>[ \t]+)# v(?P<version>[0-9]+(?:\.[0-9]+){0,2})(?P<end>[ \t]*)"
)


def action_pin_update(before, after):
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    if len(old) != len(new) or old == new:
        return False
    for left, right in zip(old, new):
        if left == right:
            continue
        a, b = ACTION_PIN.fullmatch(left.rstrip("\n")), ACTION_PIN.fullmatch(right.rstrip("\n"))
        if not a or not b:
            return False
        if any(a[k] != b[k] for k in ("prefix", "action", "gap", "end")):
            return False
        av, bv = tuple(map(int, a['version'].split('.'))), tuple(map(int, b['version'].split('.')))
        if av[0] != bv[0] or bv < av or a['sha'] == b['sha']:
            return False
        if left.endswith("\n") != right.endswith("\n"):
            return False
    return True


def action_pins_only(paths, base, cwd=None):
    cwd = cwd or ROOT
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True, stderr=subprocess.PIPE).strip()
        actual = changed_paths(base, head, cwd=cwd)
        if actual is None or sorted(set(actual)) != paths:
            return False
        found = False
        for path in paths:
            if documentation(path):
                continue
            if not re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml", path):
                return False
            # Require regular files on both sides; additions/deletions/renames fail closed.
            contents, modes = [], []
            for rev in (base, head):
                mode = subprocess.check_output(["git", "ls-tree", rev, "--", path], cwd=cwd, text=True, stderr=subprocess.PIPE)
                if not mode.startswith("100644 blob ") and not mode.startswith("100755 blob "):
                    return False
                modes.append(mode.split()[0])
                contents.append(subprocess.check_output(["git", "show", f"{rev}:{path}"], cwd=cwd, text=True, stderr=subprocess.PIPE))
            if modes[0] != modes[1] or not action_pin_update(*contents):
                return False
            found = True
        return found
    except (OSError, UnicodeError, subprocess.SubprocessError):
        return False


def make_plan(paths, full=False, baseline=None, graph=None):
    if paths is not None:
        if (not isinstance(paths, list) or any(not isinstance(p, str) or not p
                or PurePosixPath(p).is_absolute() or ".." in PurePosixPath(p).parts for p in paths)):
            raise ValueError("Invalid changed paths")
        paths = sorted(set(paths))
    plan = {"schema": 2, "mode": "full", "paths": paths, "schema3": list(SCHEMA3),
            "hosts": list(HOSTS), "legacy": list(LEGACY), "contracts": True,
            "checks": list(FULL_CHECKS), "baseline": None, "graph": None}
    if full or not paths or not isinstance(baseline, str) or not re.fullmatch(r"[a-f0-9]{40}", baseline):
        return plan
    try:
        graph = graph if graph is not None else load_graph()
        owners = {file: name for name, feature in graph["features"].items() for file in feature["files"]}
        if action_pins_only(paths, baseline):
            plan.update(mode="automation", contracts=False, baseline=baseline,
                        graph=graph_digest(graph), checks=list(graph["plans"]["automation"]["checks"]),
                        schema3=[], hosts=[], legacy=[])
            return plan
        affected = set()
        for path in paths:
            if path in owners:
                affected.add(owners[path])
            elif not documentation(path):
                return plan
        selections = {group: [name for name, case in graph["cases"][group].items()
                       if affected & closure(graph, case["schema"], case["roots"])]
                      for group in ("schema3", "hosts", "legacy")}
        checks = [name for name in FULL_CHECKS if affected & closure(
            graph, graph["checks"][name]["schema"], graph["checks"][name]["roots"])]
        if affected:
            checks += [name for name in ("check-flake-file", "ci-graph") if name not in checks]
        plan.update(mode="focused" if affected else "docs", contracts=False, baseline=baseline,
                    graph=graph_digest(graph), checks=checks, **selections)
        return plan
    except (OSError, ValueError, KeyError, TypeError):
        return plan


def validate_plan(plan):
    if (not isinstance(plan, dict) or type(plan.get("schema")) is not int or plan.get("schema") != 2
            or type(plan.get("contracts")) is not bool or not isinstance(plan.get("mode"), str)
            or plan.get("mode") not in {"docs", "automation", "focused", "full"}):
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
    if not plan.get("paths") or not baseline_green(repository, sha, token):
        return make_plan(plan.get("paths"), full=True)
    try:
        graph = load_graph(validate_sources=True)
        base_graph = json.loads(subprocess.check_output(
            ["git", "show", f"{sha}:{GRAPH_PATH}"], cwd=ROOT, text=True, stderr=subprocess.PIPE))
        if base_graph != graph:
            raise ValueError("Dependency graph changed since base")
        return validate_plan(make_plan(plan["paths"], baseline=sha, graph=graph))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print("No unchanged validated graph; running full validation.", file=sys.stderr)
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
        if not full:
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
