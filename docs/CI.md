# Continuous integration

CI validates configurations without activating a home. The always-running **CI gate** is the required merge check.

## Run checks locally

```sh
# Fixtures, workflow lint and release metadata
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh

# Full profile matrix and build checks
bash tests/nix-check.sh
```

Use `bash tests/nix-check.sh --no-build` for evaluation only. Matrix batches are capped at two profiles; add `--batch-size 1` to evaluate one at a time.

Full runs cover contracts, all 21 profile cases and seven build checks: `home`, `profile-command`, `nixgl-wrapper`, `desktop-icons`, `profile-generation`, `check-flake-file` and `ci-graph`.

## How affected checks are selected

The [generated manifest](../modules/ci/_graph.json) records feature ownership, private assets, schema-specific dependency edges, profile roots and build-check roots. `lib.ciGraph` exports the same value. The planner combines changed-file owners with dependency closures to select affected cases and checks.

A shorter plan requires:

- A successful GitHub Actions `CI gate` on the exact base commit.
- A supported graph that matches pure source regeneration.
- The same graph at the base commit.
- Known ownership for every runtime change.

Without that evidence, CI runs full validation. Rename detection is disabled so both old and new paths are considered. Missing files, unknown ownership, changed graphs and descriptor fingerprints force the conservative path. Documentation skips require the same proof; the generated architecture diagram is never documentation-only.

Manual runs, merge groups, release calls and explicit checkout overrides always validate fully. Focused runs request affected build checks plus generated-file checks. Nix's derivation cache determines what actually rebuilds.

## Keep generated files current

```sh
nix run path:.#write-flake
nix run path:.#write-ci-graph
```

The second command writes the manifest and [diagram](ARCHITECTURE.md). Drift fails CI. The gate recomputes the plan and rejects missing results, changed selections, failures, cancellations or an unexpected skipped Nix job.

See [module conventions](MODULES.md) before changing dependency declarations. Record validation results in the pull request rather than adding temporary reports to the documentation tree.
