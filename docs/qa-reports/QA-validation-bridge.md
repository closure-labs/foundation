# Profile validation bridge

Date: 2026-10-20. Stage N1 of the approved profile refactor.

## Implemented behavior

- `lib.normalizeProfile` validates schema-2 structure and normalizes role/package
  order using catalog order, then name. It preserves extra profile fields and
  rejects unknown selections, duplicates and malformed input.
- Direct Home Manager composition uses the same pure normalizer. Staged builds
  resolve it and `homeCatalog` from their locked Foundation input, or their own
  API for standalone configurations. Caller catalog environment variables do
  not participate. Only API absence selects the legacy Python schema-2 fallback;
  target evaluation/validation errors propagate.
- Invoking-account and running-image checks remain in Python. Memory budget
  validation still precedes evaluation; existing job/core/swap limits remain.
- Canonical selections are written before building, including update/migration
  paths. Semantically unchanged profiles retain their bytes. Changed profiles
  replace the staged directory entry atomically, preventing writes through copied
  symlinks into live data.
- Initialization explicitly converts schema 1 to 2; schema 2 is retained and
  unsupported schemas are rejected before staging. Extra identity fields survive.
  Provisioning and commit remain after successful validation/build.

## Validation

| Check | Result |
| --- | --- |
| Focused validation tests | Passed: 16 tests covering structure, order, extra fields, API fallback/failure, stale catalogs, runtime checks, initialization schemas, persistence and transactional failures. |
| Real Nix target resolution | Passed: locked legacy, bridge and additional-role candidate targets; changed-source rejection; standalone fallback and actual Foundation public export. Profiles and locks remain unchanged by validation. |
| Retained helper compatibility | Passed: six pre-bridge/bridge helper × baseline/bridge/candidate catalog combinations using the retained original helper. |
| Pinned `tests/ci.sh` | Passed: 61 discovered Python tests, workflow lint and release metadata. |
| Full `tests/nix-check.sh`, one job/core | Passed: integration fixtures, Home Manager/profile-command builds, and all-role Dell evaluation on both foundations. No activation. |
| 32-case composition and actual Finite projection | Passed: all captured fields match the D1 baseline exactly, including Foundation and actual Finite catalogs. |
| Library/controller review | Approved after fixing staged symlink write-through; both failed-build and failed-apply regressions pass. |
| QA and security review | Approved; no remaining blocking findings. |

The earlier upstream `options.json` store-context warning is still present during
evaluation. It predates N1 and does not fail the checks.

Compatibility evidence covers schema-2 validation and selected-target resolution.
The retained-helper matrix exercises its validator against each catalog, not an
end-to-end old-updater adoption or new-format migration. The candidate adds a
schema-2 role to demonstrate target-owned membership; no Personal role is enabled.
This does not establish schema-3 readiness. F1 Finite readers and A1/A2 application
and migration contracts remain separate work.

## Dependency and transaction review

No dependency was added and the lock is byte-identical to the N1 baseline.
The pure normalizer consumes an injected domain catalog; it does not import the
public API or call Python/Nix subprocesses. Both `lib/default.nix` and
`modules/finite.nix` import that leaf. Python invokes the selected API through one
Nix evaluation; the API has no callback into the controller. Review found no new
dependency cycle. Normalization handles the existing six roles and five optional
packages; repeated pure normalization during composition is bounded by these
small lists. See [dependency graph](DEP-GRAPH-validation-bridge.txt).

An independent review reproduced staged write-through on an absolute profile
symlink. Atomic replacement of the stage entry resolved it for build, initialize
and apply. Regression tests verify linked live bytes remain unchanged on failure.
Subprocesses retain argument arrays and Nix references escape interpolation;
profile contents are read as JSON from the staged source rather than interpolated
into Nix expressions.

## Evidence and rollback

Local evidence is retained in `/tmp/foundation-validation-bridge-3vpcjky8/`:
the starting tree, updated composition captures, retained-helper compatibility
harness/results, comparison summary and an N1-only rollback patch. No flake input
references that temporary directory. The baseline already contains the approved
classification and Den/gen work, along with the pre-existing Herdr/Zsh/XDG edits;
the N1 patch is measured against that tree rather than `HEAD`.

Reversing the retained patch reverts only N1 source/tests/docs, then the prior
source can be rebuilt. It does not undo a future activation. No configuration was
activated, firmware changed, or release published during N1.
