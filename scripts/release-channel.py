#!/usr/bin/env python3
"""Advance latest-release to the highest published stable release with passing CI."""
import argparse
import json
import re
import subprocess

REPOSITORY = "closure-labs/foundation"
CHANNEL = "latest-release"
VERSION = re.compile(r"v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))")


def capture(command):
    return subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def api(path, data=None, paginate=False):
    command = ["gh", "api"]
    if paginate:
        command += ["--paginate", "--slurp"]
    if data is not None:
        command += ["--method", "PATCH" if path.endswith("/" + CHANNEL) else "POST", "--input", "-"]
    command.append(f"repos/{REPOSITORY}/{path}")
    result = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                            check=True, text=True, stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def latest_stable(releases):
    candidates = []
    for release in releases:
        match = VERSION.fullmatch(release.get("tag_name", ""))
        if match and release.get("published_at") and not release.get("draft") and not release.get("prerelease"):
            candidates.append((tuple(map(int, match[1].split("."))), match[0]))
    if not candidates:
        raise ValueError("No published stable Foundation release")
    return max(candidates)[1]


def require_green(checks):
    if not any(check.get("name") == "CI gate" and check.get("conclusion") == "success"
               and check.get("status") == "completed" and check.get("app", {}).get("slug") == "github-actions"
               for check in checks):
        raise ValueError("The release commit has no successful CI gate")


def advance(check=False):
    # Select the highest version, not event order or GitHub's mutable 'latest' flag.
    # This makes concurrent/late publication events and workflow retries idempotent.
    batches = api("releases?per_page=100", paginate=True)
    tag = latest_stable([release for batch in batches for release in batch])
    sha = capture(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"])
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("Invalid release commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", sha, "origin/main"], check=True)
    version = capture(["git", "show", f"{sha}:VERSION"])
    metadata = json.loads(capture(["git", "show", f"{sha}:foundation.json"]))
    if "v" + version != tag or metadata.get("version") != version or metadata.get("schema") != 1:
        raise ValueError("Published tag does not match Foundation metadata")
    batches = api(f"commits/{sha}/check-runs?per_page=100", paginate=True)
    require_green([item for batch in batches for item in batch["check_runs"]])
    refs = api(f"git/matching-refs/heads/{CHANNEL}")
    current = next((ref["object"]["sha"] for ref in refs if ref["ref"] == f"refs/heads/{CHANNEL}"), None)
    if current == sha:
        print(f"{CHANNEL} already selects {tag} ({sha})")
        return
    if current is not None:
        # Fail closed rather than roll the channel back or rewrite its history.
        subprocess.run(["git", "merge-base", "--is-ancestor", current, sha], check=True)
        previous = capture(["git", "show", f"{current}:VERSION"])
        if tuple(map(int, previous.split("."))) >= tuple(map(int, version.split("."))):
            raise ValueError("The release channel cannot move to an older or equal version")
    print(f"{'Would advance' if check else 'Advancing'} {CHANNEL} to {tag} ({sha})")
    if not check:
        if current:
            api(f"git/refs/heads/{CHANNEL}", {"sha": sha, "force": False})
        else:
            api("git/refs", {"ref": f"refs/heads/{CHANNEL}", "sha": sha})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without changing the branch")
    args = parser.parse_args()
    try:
        advance(args.check)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release channel: {error}\n")


if __name__ == "__main__":
    main()
