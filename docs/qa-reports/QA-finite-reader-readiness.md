# Finite reader readiness (F1a)

Date: 2026-10-20. Scope: current schema-1/2 readers and capability checks.
Future-format readers remain F1b, after A1 defines the format and before A2
enables new writers.

## Changes

Foundation exports `profileCapabilities` in its library and generated catalog.
The descriptor and executing Python helper share `lib/profile-capabilities.json`:
descriptor schema 1, initialize schemas 1/2, normalize schema 2, writer schema 2,
catalog schema 3. `finite-home-init --capabilities` is read-only and resolves the
manifest relative to the actual script, ignoring source/environment overrides.
Staging checks both actual-helper and selected-target profile/catalog support.
Missing target capability metadata retains the legacy schema-2 path; explicitly
malformed or unsupported advertisements fail.

Finite's first-login adapter now preserves any present saved profile ahead of a
seed, checks its schema before invoking historical helpers, and reports errors
without generating a replacement selection. Complete consumers still skip setup;
partial consumers require repair. Fresh role rows come from the image catalog,
ordered by order/name with classification labels. Seed/fresh writers remain
schema 2. A newer helper can accept that schema without changing the writer's
literal output format.

Typed Finite role metadata now retains classification and derives grouped
membership. Old domains without classification fields remain valid with
null/empty defaults. The seed generator checks explicit capabilities before
writing; legacy catalogs without the advertisement retain schema-2 generation.

## jj isolation

Foundation work remains in change `tkntpuml`. Finite edits are isolated in jj
workspace `/tmp/finite-profile-readers`, change `pvuoruok`, based on `eb4119ec`.
The original Finite working copy's unrelated CI changes were not copied or edited.
Use `jj -R /tmp/finite-profile-readers diff` to review the Finite change.

Cross-repository tests use immutable Foundation snapshot
`bf7aa297250c18c9bfbf5607f15e20fceb57d7b4` through a temporary Nix input override.
That snapshot is a local jj/Git object, not a published release. `--no-write-lock-file`
keeps the override out of the committed lock; no local input is persisted.
Both repositories' locks and the existing Foundation profile match their F1a
baselines byte for byte.

## Validation

| Check | Result |
| --- | --- |
| Foundation capability tests | Passed: 7 tests covering manifest/query consistency, no query writes, source override independence, malformed advertisements, unsupported formats and separate helper/catalog checks. |
| Foundation normalization tests | Passed: 16 tests, including staged profile symlink safety and failure preservation. |
| Pinned Foundation CI | Passed: 68 discovered Python tests, workflow lint and release metadata. |
| Actual locked-target capability fixtures | Passed: legacy/bridge/candidate normalization plus explicit malformed/unsupported target rejection without fallback. |
| Full Foundation Nix build | Passed final sequential run: Home Manager/profile-command builds and all-role Dell evaluations on Bluefin and Bluefin DX. |
| Finite login integration | Passed: 16 tests for existing/partial consumers, saved 1/2 and malformed/unsupported input, dangling saved symlinks, seed precedence/YAML, legacy/new helpers, catalog rows, cancellation and capability failures. External commands/dialogs are stubbed. |
| Finite maintenance tests | Passed: 4 tests. |
| Finite old-source home checks | Passed home contracts and typed/composition proof; final contracts include all 16 login tests and real YAML/ISO seed generation retaining schema 2. |
| Finite new-source home checks | Passed home contracts and actual typed classification/composition proof against the exact local Foundation snapshot. |
| Composition parity | Passed: all 32 cases match N1 exactly. Both Foundation/actual Finite catalogs differ only by the explicitly checked `profileCapabilities` descriptor. |
| Review | Architecture/library, QA and security review found no remaining blocking findings after the capability intersection fixes. |

The packaged initializer capability query is compared to its generated catalog
when capabilities are present. Seed contracts generate real user-data, metadata,
profile YAML and an inert NoCloud ISO, then verify schema, canonical order and
account identity. No OS image, graphical login or Home Manager activation is run.

The first concurrent new-source composition evaluation exited 137; other long
checks were interrupted. New-source home contracts and the composition proof
subsequently passed when run separately. The final legacy-source home contracts
and full Foundation Nix checks also passed sequentially; interrupted attempts
are not counted as passes.

## Boundaries and follow-up

This establishes current-reader readiness, not schema-3 support. A1 must define
the new selection/migration contract and exact app ownership; F1b must implement
and verify readers before A2 enables writers. Physical graphical login and real
activation remain integration limits. Finite's Foundation source pin is unchanged;
the new classified data becomes available there when a containing Foundation
release is intentionally selected.

Review found two concrete capability gaps during development: the helper also
needed its own catalog-schema check, and fresh-login needed full validation of
the catalog advertisement. Both were fixed and regression-tested. No new
dependency, service, package placement, hardware policy or update ordering was
introduced. The normalizer remains a pure leaf; capability data is a JSON leaf
read by Nix/Python; there is no callback from it into the controller and no new
dependency cycle.

Evidence is retained in `/tmp/foundation-finite-readers-1tqo2bjx/`, including both
starting trees, parity captures and final comparison/rollback artifacts. Reverse
only this slice's retained patches to undo F1a while keeping prior refactor and
pre-existing work. A source rollback does not undo any future activation.
