# A1 application contract validation

Date: 2026-10-20. Scope: isolated schema-3 design API, inventory and migration
preview in jj change `tqkozxwn`, parent `tkntpuml` (`415e92d5`).
Contract: [ARCH-profile-schema3](../architecture/ARCH-profile-schema3.md).

## Implemented and checked

- Draft normalization/resolution, ten individually composable roles, 31 reusable
  capabilities and provider-qualified migration previews. Production normalizer,
  six-role catalog and schema-2 capability manifest remain unchanged.
- Existing 44 application/launcher identities are accounted for; the inventory
  fixture recursively imports actual aspect/module declarations with symbolic
  package values. It compares shared and individual-role declarations against
  the legacy contract rather than searching source text for app names.
- Chromium is optional for new profiles; camera controls follow declared Dell
  hardware or explicit selection. Larger creative tools and game launchers are
  optional. Classifications and effective capabilities are derived.
- All 53 draft Nix package declarations resolve to derivations in the actual
  locked stable/weekly/unstable/devenv inputs. Includes nested font/Kdenlive
  attributes and optional unfree launchers; this fixture only evaluates metadata.
- Five retained Flatpak app IDs have positive publisher-verification snapshots
  from the public Flathub API. A negative fixture rejects an unknown app ID.
- Migration preserves unknown fields, blocks any existing custom `capabilities`
  field, distinguishes app removals from provider changes and never permits
  activation, unmanaged uninstall, automatic data transfer or data deletion.

## Results

| Check | Result |
| --- | --- |
| Focused draft suite | 13 tests pass; independently rerun by QA and security reviewers |
| `nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh` | Pass; repository shell/Nix checks, 81 discovered Python tests, actionlint and release metadata validation |
| Locked-target validator fixtures | Legacy/bridge/candidate, standalone, unsupported/malformed capabilities and actual public normalizer pass |
| Locked draft provider fixture | All 53 declarations available; no new app builds |
| `bash tests/nix-check.sh --no-build` | Pass; flake checks and all six roles/five optional packages on both Bluefin variants with Dell hardware evaluate |
| Exact production catalog projection | Before/after JSON identical |
| Existing runtime source comparison | 47 files byte-identical: profile, flake/lock, catalogs, normalizer, capability manifest, modules, scripts and templates |
| Draft Nix formatting / dead-code check | Pinned Alejandra and deadnix pass |
| Documentation | Edited local links, code fences and trailing whitespace checked |

Read-only architect, QA and security reviews approved the draft with no blocking
findings. They explicitly exclude actual graphics compatibility and live
migration behavior from their approval.

Evidence baseline and catalog comparisons are retained at
`/tmp/foundation-application-contract-qihpbi0x/`. A1's patch is derived against
that pre-A1 working-tree snapshot, preserving prior refactor and unrelated edits.

## Limits and next stage

No new-format consumer has been written or activated. No nixGL input or wrapper
has been installed. `wrappedApplicationIds` records intended wrapping only.
Full GUI package builds, physical graphics sessions, chess-engine discovery,
Flatpak-to-Nix data transfers and activation rollback are F1b/A2 rollout checks.
Publisher verification must be refreshed before writer enablement.

The existing 32-case parity/build evidence belongs to earlier runtime-changing
stages. It is not presented as a new A1 full build: this change adds an isolated
API and tests, while all runtime composition source files are byte-identical.
No Finite files, input pins, firmware or host-owned settings changed in A1.
