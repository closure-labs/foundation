# Professional classification implementation validation

Date: 2026-10-20. Result: **passed** for the first classification slice.
No configuration was activated and no release was published.

## Change verified

Developer, Sales, Trainer, Support, Executive and IT are classified as
Professional. Personal is an ordered catalog peer with no roles or applications.
The selector uses the packaged catalog for role/package rows and shows each
role's classification, retaining the same IDs and single apply invocation.
Profiles stay at schema 2; catalog schema 3 and compatibility 1 are unchanged.

Existing Herdr, Zsh, desktop search-path and migration-test changes were copied
into the starting baseline and preserved. Dependency locks were not updated.

## Evidence

| Check | Result |
| --- | --- |
| Pre-change `bash tests/check.sh` | Passed, including 23 consumer/update tests. |
| New classification/selector tests against old code | Failed as expected: metadata absent, old hardcoded rows, and no catalog preflight. |
| Final `python3 tests/test_profile_classification.py` | 11 tests passed. |
| `bash tests/check.sh` through the pinned CI shell | Passed, including existing fixtures and new tests. |
| `nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh` | Passed: fixtures, workflow lint, 45 discovered Python tests, release metadata. |
| `bash tests/nix-check.sh --no-build` | Passed flake and selectable-profile evaluation. |
| `NIX_CONFIG` with one job/core, `bash tests/nix-check.sh` | Passed full default Home Manager and profile-command builds, plus all-role evaluation on Bluefin and DX/Dell. |
| 32-case before/after composition matrix | Exact parity after the narrowly defined helper-path normalization below. |
| Actual Finite catalog projection | Old fields unchanged; Professional/Personal metadata survives. |
| Baseline/current profile generator execution | Identical schema-2 YAML for the same unordered role/package input. |
| Starting code/lock checksums | Unrelated edits unchanged; the only new change to the existing `modules/finite.nix` edits is the catalog runtime binding. |

The matrix covers both foundations, both existing hardware IDs, and eight
selection sets: none, all roles/packages, and each individual role. Captured
fields include packages, Flatpak declarations, user services, home and systemd
environment, identity, state version, Firefox package, and the source profile.

Only five source-embedding Foundation command package paths were normalized:
`finite-configure`, `finite-home-apply`, `finite-home-update`,
`finite-home-migrate`, and `finite-app-status`. Names and multiplicity were
retained; every other application output path and captured field matched exactly.
No global store-path normalization was used.

Finite verification imported its actual
`~/projects/finite/lib/domain-catalog.nix` and passed that result through
Foundation's real `mkHomeCatalog`, using real nixpkgs lib. Removing only the new
classification fields produced the baseline catalog exactly, including the
`finite`/`finite-dev` image mappings. The committed portable fixture separately
covers those mapping and legacy-custom-catalog contracts without requiring a
Finite checkout in CI.

Selector fixtures cover checked state, canonical order, hidden IDs, custom and
unclassified rows, no Personal checkbox, cancellation at either dialog, empty
selections, one apply call, apply exit-status propagation, and missing/malformed
catalogs. No desktop session or actual Home Manager activation is used by them.

## Review and retained artifacts

Read-only library/API and CLI reviews found no blocking issues. CLI review
identified a malformed-entry layout issue; row-field type validation and
regression cases were added. Empty-selection and apply-failure tests were also
added before final CI.

The baseline, capture scripts, before/after JSON, schema-2 YAML comparison,
machine-readable summary, and refactor-only patch are retained locally at:

```text
/tmp/foundation-profile-refactor-puomwznq/
```

`classification-refactor.patch` is relative to that directory's `baseline/`
snapshot, which includes pre-existing uncommitted work. It excludes those
unrelated changes and includes this slice's fixtures/documentation. It is a
local review/rollback artifact, not a dependency or flake input.

Full Home Manager builds completed without activation. Physical desktop-dialog
interaction was covered by argument/round-trip fixtures rather than a graphical
session. Later app splitting, Den upgrades, hardware composition and Finite
update hardening remain the separate stages in the implementation plan.
