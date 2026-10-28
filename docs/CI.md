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

## Automation dependency updates

Same-major GitHub Action pin updates use an `automation` plan when the exact base has a successful CI gate and the generated dependency graph is unchanged and valid. The planner compares the complete Git diff: only existing workflow `uses:` lines may change, preserving the action identity and changing only a full commit SHA and its version comment. Documentation may accompany those changes.

[Flake-owned plan declarations](../modules/ci/_plans.nix), exported as `lib.ciPlans`, name the selected checks. The generated manifest carries the same declarations, and the graph check verifies those names against the actual flake check outputs.

Automation plans run workflow lint, all fixtures and Python tests, plus the `profile-generation`, `check-flake-file` and `ci-graph` build checks. They skip the profile matrix and full home build. This exercises Nix setup and packaged helpers while retaining the strict required gate. Major action updates, workflow logic/permissions/runner changes, added or deleted workflows, mixed runtime changes and unavailable diff evidence use full validation.

A dependency label alone never selects this shortcut. In particular, `flake.lock` changes can update Den, Home Manager and shared package sources, affecting every profile; those still run full validation. Manual, release and merge-group runs remain full even for action-pin-only changes.

## Dependency-update ownership

Renovate is the intended owner of GitHub Actions pin updates. The repository
[`renovate.json`](../renovate.json) limits it to the `github-actions` manager,
retains digest pins, groups weekly updates on Monday morning UTC and disables
automerge. Nix updates remain in the existing reviewed lock/stable-pair workflows:
those regenerate source-owned artifacts and preserve Den's tested gen revision.
Renovate must not independently rewrite generated `flake.nix` or compete for
`flake.lock` ownership.

### Complete the Renovate handoff

The configuration alone does not prove that a Renovate app or runner can access
this repository. Before removing `.github/dependabot.yml`, a maintainer must:

1. Confirm an authorized Renovate installation/runner covers
   `closure-labs/foundation`; granting app access is a separate owner decision.
2. Verify a successful Renovate run reads this configuration and discovers the
   GitHub Actions dependencies, with a reviewed update PR or runner/dashboard
   evidence when no update is needed.
3. Remove Dependabot's Actions configuration in a focused follow-up PR, then
   verify that only Renovate proposes subsequent Actions updates.

Dependabot remains temporarily configured solely to avoid leaving updates
unowned during this handoff. This is not permanent dual ownership. Do not
remove the fallback based only on the presence of `renovate.json` or on a
repository label. No app access, repository rulesets or organization settings
are changed by this configuration.

## Keep generated files current

```sh
nix run path:.#write-flake
nix run path:.#write-ci-graph
```

The second command writes the manifest and [diagram](ARCHITECTURE.md). Drift fails CI. The gate recomputes the plan and rejects missing results, changed selections, failures, cancellations or an unexpected skipped Nix job.

See [module conventions](MODULES.md) before changing dependency declarations. Record validation results in the pull request rather than adding temporary reports to the documentation tree.
