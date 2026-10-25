# CI selection

`modules/ci/_graph.json` is a versioned projection of the feature descriptors, explicit profile selections, private asset ownership and build-check profiles. `lib.ciGraph` exports the same value. `write-ci-graph` regenerates the manifest and `docs/ARCHITECTURE.md`; `ci-graph` rejects drift. `check-flake-file` rejects drift in generated `flake.nix`.

The planner maps changed files to owners and traverses schema-specific dependencies in reverse by intersecting affected features with each case/check closure. Multiple changes are unioned. Git diff disables rename detection, retaining both old and new paths; deletions and unknown ownership conservatively require full validation. A changed manifest also forces full validation. Descriptor fingerprints make metadata or configuration-function edits invalidate the manifest; owned runtime files can still receive focused plans. The generated architecture diagram is never treated as documentation-only.

A shorter plan requires all of:

- A completed successful GitHub Actions `CI gate` on the exact base SHA.
- A supported, structurally valid graph that matches pure source regeneration.
- The identical graph at that base SHA.
- Known ownership for every runtime change.

Without that evidence the planner runs the complete suite. Documentation-only skips have the same baseline and graph requirements. Manual runs, merge groups, release calls, explicit checkout overrides and unknown events always run full validation.

Full runs execute contracts, all 21 profile cases and every flake check. The original checks are `home`, `profile-command`, `nixgl-wrapper`, `desktop-icons` and `profile-generation`; the two generated-file checks are additional requirements. Focused runs evaluate affected cases and request affected build checks plus generated-file checks. Nix derivation identities and native binary caching determine reuse. Matrix batches remain capped at two.

The always-running `CI gate` validates the exact plan again and requires successful fixtures and Nix checks. It permits a skipped Nix job only for a valid documentation plan; failures, cancellations, missing outputs, altered selections and a shortened plan on a full-validation event all fail the gate.

Run `bash tests/nix-check.sh --no-build` for evaluation-only validation, or omit `--no-build` to build. CI uses the explicit `CI_PLAN` emitted by the fixture job. See [module conventions](MODULES.md) when adding ownership or dependencies.
