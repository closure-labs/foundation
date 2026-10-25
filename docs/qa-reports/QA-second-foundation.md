# Second Foundation verification

Baseline: merged PR #17, `a8ec1f405f5894367b036fe863c935c43001ab70`. Its exact commit has a successful GitHub Actions CI gate. Verification date: 2026-10-25.

## Structure

The generated tree has 140 feature descriptors: 60 applications, 10 roles and 31 capabilities, with home, profile, host, provider and framework features. [Module conventions](../MODULES.md) describe ownership; [the generated diagram](../ARCHITECTURE.md) and `modules/ci/_graph.json` come from the same source as Den composition. Catalogs retain pure evaluation and the existing `lib` façades.

## Verification

- All 177 Python tests pass; existing shell/Nix parsing fixtures, workflow lint and release metadata validation pass.
- All 21 matrix cases pass with actual Den membership checked against declared dependencies.
- All seven build checks pass: the original five plus generated-flake and graph/diagram checks.
- Intentional generated-flake drift fails its build check.
- Pure catalog and composition-contract JSON match the baseline exactly.
- Before/after comparisons cover all 21 cases. Application package store paths, package order, multiplicity and priorities match exactly. The five Foundation helper package paths change because their bundled source moves; the configuration comparator permits only these package-identity differences.
- Shell initialization, Flatpak ordering, schema defaults, activation DAGs, service definitions and file settings match after normalizing generated store hashes and relocated source references. No application/provider differences were accepted.
- Discovery tests prove that private files are excluded, unselected descriptors stay lazy, new features appear without central lists, and invalid IDs/missing edges/cycles fail. Graph tests cover transitive/shared features, schema variants, assets, changed-file unions, rename/delete paths, stale/unsupported manifests, missing base proof and strict gate results.
- Every pre-existing locked revision and the consumer defaults are unchanged. No live profile was activated; tests use temporary fixtures. Finite's pin, tags, releases and merge state were not changed.

Run the comparison again with an immutable baseline checkout:

```sh
python3 scripts/compare-configurations.py --baseline /path/to/pr17 --output /tmp/parity.json
nix develop path:.#ci --command bash tests/ci.sh
bash tests/nix-check.sh
```

## Evaluation benchmarks

Single local samples measured with `/usr/bin/time -v`, `bash tests/nix-check.sh --no-build`, and warmed shared caches. Peak RSS is the maximum reported for the runner and its children, not aggregate concurrent memory. The initial colder baseline was 1:59.92; the warmed baseline below is the more useful comparison. These are measurements, not statistically established performance changes.

| Evaluation | Elapsed | Peak RSS | Cases |
| --- | --- | --- | --- |
| PR #17 full | 1:35.90 | 4.78 GiB | 21 |
| Second Foundation full | 1:47.15 | 4.84 GiB | 21 |
| PR #17 focused | 0:49.42 | 4.31 GiB | 6 |
| Second Foundation focused | 1:03.96 | 4.7 GiB | 8 |

The refactor adds module/graph evaluation overhead. Its focused Ghostty workload also evaluates two additional schema-3 work-role cases that the old path mapping omitted, so the focused timings are not equal workloads. The old focused runner evaluates all five checks; the new runner requests profile-generation and the two generated-file checks for this change.

Focused measurements directly exercise a controlled unchanged-graph/green-base plan. The rollout PR itself cannot use that plan: PR #17 has no generated graph, so it receives full validation. [Raw summary](second-foundation-evidence.json) records the measurements and parity result.
