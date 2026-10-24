# CI selection and helper-source validation

Date: 2026-10-23. Local implementation validation passed; GitHub validation of
the proposed workflow is required before merging. Base release: `v0.3.3`,
commit `0391c2e7bf7284ba0e999be73046cf03a0601918`.

## Results

- Pinned fixture/workflow suite passes, including the CI planner and gate
  regressions and the existing controller/profile/release tests.
- Full Nix validation passes all eight schema-3 cases, nine host cases, four
  work-role configurations across schemas 2/3 and both Bluefin foundations,
  locked normalization/editor contracts and all five declared build checks.
- A focused support-role plan passes end to end against the real successful
  base CI gate. Its schema-3 all-role composition, workstation host and both
  schema-2 foundations pass; all five declared build checks reuse existing
  outputs. A docs plan with the same verified baseline accepts the expected
  Nix-job skip.
- Planner tests reject missing/malformed plans, omitted cases, unexpected
  skipped/failed/cancelled jobs, absent base proof, wrong base SHA/check app,
  unknown paths and shortened plans on full-validation events. Renaming a
  runtime file into documentation retains both changed paths and runs full.
- A real docs/flake-comment/CI-only edit leaves all five check derivations
  unchanged. Editing the runtime Python changes the helper bundle. Complete
  source NAR metadata still changes with the full source, and the exported
  initializer retains that metadata independently of its filtered code bundle.
- Case inventories are checked against the planner's complete selections;
  batching tests reject duplicate/missing cases and propagate evaluation errors.

## Performance comparison

The released suite and optimized suite ran sequentially on the same workstation
with the existing Nix store/cache. Both completed successfully without activation.

| Full suite | Elapsed | Peak process memory |
| --- | --- | --- |
| Released v0.3.3 implementation | 160.15 seconds | 3,928,636 KiB |
| Optimized implementation | 96.42 seconds | 4,175,232 KiB |

This is a 40% elapsed-time reduction in one local warm-cache comparison, with
about 6% more peak process memory. It includes the new helper-source/provenance
check. GitHub runner timing, queue/setup time and cold dependency downloads are
not measured by this comparison. Batches are capped at two cases; size one
remains available for memory-constrained local evaluation.

## Scope and evidence

The required check remains **CI gate**, with its existing branch ruleset.
Missing or unavailable baseline checks cause full validation. Reusable calls
overriding the checkout revision, release tags, manual runs and merge groups
force full validation. Every focused/full Nix job requests all declared build
checks; only a validated docs plan can skip that job.

Dependency pins, profile schemas, providers, account/state defaults and source
revision/NAR semantics are unchanged. Helper bundles retain runtime libraries,
default profile/lock/personal-module data, migration manifest and license notices.
The complete consumer template still uses the full source and exact metadata.

Local logs and benchmark JSON are under `/tmp/foundation-ci-optimization/`:
`ci-final.log`, `focused.log`, `focused-plan.json`, `benchmark.json` and
`benchmark-{released,optimized}.log`. These tests evaluate/build configurations
without changing the active Home Manager generation or personal configuration.
