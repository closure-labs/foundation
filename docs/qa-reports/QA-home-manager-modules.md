# Shared Home Manager module refactor

Date: 2026-10-22. Status: PASS.

The shared base module now imports private browser, desktop, Homebrew, shell
and legacy-application modules. The public base aspect and constructor remain
unchanged. Account/state defaults and the ordering-sensitive shared shell hook
remain at the original entry point. No disk-space preflight was implemented.

## Actual configuration comparison

Captured before/after merged Home Manager projections cover:

- The Professional Dell workstation example with its camera enabled.
- The same Professional Dell declaration with its camera disabled.
- A minimal generic AMD desktop.
- A generic desktop selecting all four Personal roles.
- The schema-2 Dell recovery declaration with all six Professional roles.
- The actual workstation's current profile, personal modules and personal input
  graphs, evaluated against the candidate Foundation source.

All six preserve ordinary application output paths, multiplicities and
priorities; Firefox recipes and camera scoping; Flatpak order and policy;
services; account/state version; complete Zsh initialization; Brew activation
check/DAG ordering; desktop backend; environments; and dconf settings.

The comparison permits only documented source effects:

1. The five source-embedding Foundation commands are compared by exact
   identity/count; their individual output paths are replaced with that identity.
2. Package-list position changes are limited to the extracted Brew helper and,
   for schema 2, the legacy application block. Sorted package descriptors remain
   identical, including priorities and multiplicity.
3. Changed source references are checked against byte-identical files or the
   identical tracked parent/current asset. Only the known `home-manager-path`
   references inside generated fontconfig text are normalized. Other arbitrary
   store paths are not removed from comparisons.

The initial comparison caught shell and legacy Flatpak ordering changes. The
final implementation preserves the shell hook's original definition location
and retains role-before-base Flatpak order explicitly.

The actual candidate workstation `home.path` built successfully, checking the
merged package environment for collisions. Its structured build attributes
confirm `ignoreCollisions = false` and `checkCollisionContents = true`.
This did not activate Home Manager
or write the personal configuration. The published v0.3.0 generation remains
active with the same six Professional roles.

## Repository checks and review

The symbolic legacy inventory follows the real private module imports and is
identical to its captured baseline. Brew provider contracts pass. Read-only
architecture, QA and security reviews found no scoped blockers.

Validation passed:

- Pinned `tests/ci.sh`: all 147 tests, workflow lint and release metadata checks.
- Full `tests/nix-check.sh`: validation/editor fixtures, eight actual schema-3
  compositions, nine host compositions and all five flake build checks.
- All six Professional roles and optional packages evaluate on both Bluefin
  foundations with Dell hardware under schemas 2 and 3.

The existing `options.json` store-context warning remains visible during
evaluation; this refactor does not claim to fix it.

Temporary local comparison scripts, projections and package-build output are
under `/tmp/foundation-hm-base-refactor`; personal configuration projections are
not committed to this repository.
