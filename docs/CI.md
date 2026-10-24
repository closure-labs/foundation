# CI selection and derivation reuse

Every change runs shell/Nix syntax checks, provider/aspect fixtures, Python
tests, workflow lint and release metadata validation. The fixture job also
publishes a deterministic Nix test plan and its case counts in the run summary.

| Changes | Nix plan |
| --- | --- |
| README, changelog, contributor/security guidance and documentation records | Skip the Nix job |
| Existing Professional role modules | All-role schema-3 composition, applicable Dell composition, both schema-2 foundations and the workstation host |
| Devops capability or Ghostty recipe | Capability, Dell/developer and all-role compositions, both schema-2 foundations and workstation |
| Icon cleanup recipe | All-role composition, both schema-2 foundations and workstation; declared icon build check also runs |
| Dell model files | Generic and Dell/camera compositions, workstation and both schema-2 foundations |
| Shared modules, flake wiring, locks, catalogs, scripts, tests, CI or unknown files | Complete suite |

Selections are unions across changed paths. Unknown files, new roles, missing
or shallow comparison commits and empty diffs select the complete suite.
Renames count as deletion plus addition, so moving runtime code into a docs
directory cannot suppress its tests. A small edit to `flake.nix` still selects
full evaluation because it can rewire any output.

Shortened plans require a successful GitHub Actions **CI gate** on the exact
comparison base SHA. Missing, failed or unavailable baseline checks cause full
validation. CI requests only read access to contents and checks. PRs compare
the tested merge commit against the event's base; main pushes compare against
the prior commit. Merge groups, manual runs and reusable release validation
always select the complete suite. Release callers explicitly pass `full: true`;
any reusable invocation overriding `ref` also forces full validation of that
checkout, independently of the caller event's changed paths.

## Build reuse and evaluation

Every focused or full Nix job runs `nix flake check`, requesting all five
declared build checks. Nix derivation identities and the existing binary cache
determine which outputs need building. No saved Python-test result or
PR-controlled success marker substitutes for validation.

The profile matrices share their pinned Foundation input within batches of at
most two cases. Each case still evaluates its activation derivation and runs
the same membership, wrapping, service and host assertions. The four work-role
profiles use the constructor directly, with the original personal-module
imports, instead of copying and rewriting the source flake four times.

Installed helpers bundle only their runtime Python, library, template data,
lock, metadata and license files. Docs, CI files and flake comments no longer
change those runtime bundles. Full release source hashes and revision metadata
remain separate and unchanged in meaning; the published initializer and
consumer template retain exact complete-source provenance.

## Required gate

`CI gate` always runs, even after a failure or skipped dependency. It rejects
missing/malformed plans, omitted cases, failed/cancelled fixtures, unexpected
Nix skips and shortened plans on full-validation events. Only a validated docs
plan permits a skipped Nix job. The branch ruleset still requires this same
GitHub Actions check, with no bypasses.

## Local validation

```bash
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
bash tests/nix-check.sh
bash tests/nix-check.sh --no-build --batch-size 1
python3 tests/nix_schema3_validation.py --case capabilities --case all
python3 tests/nix_host_validation.py --case dell-camera-disabled --case workstation
```

`--ci` is reserved for a validated plan passed from the workflow. Direct local
runs perform full validation by default. The unit tests cover selection and
gate failures; the Nix suite also proves unchanged check derivations after
docs/flake-comment edits, runtime-source invalidation and retained full-source
provenance. These checks build and evaluate without activating a home.
