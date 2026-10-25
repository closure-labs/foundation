# Contributing to Foundation

Keep changes focused on reproducible Home Manager configurations for x86_64 Linux. Discuss substantial behavior or dependency changes in an issue first. Report vulnerabilities through the [security policy](SECURITY.md).

## Make the change

1. Create a Git branch or jj bookmark from `main`.
2. Read [module conventions](docs/MODULES.md) before changing features, inputs or dependencies.
3. Preserve profile compatibility, canonical selection ordering, `finite-*` commands, consumer customization files and `home.stateVersion` unless you are explicitly implementing a migration.
4. Regenerate artifacts when their sources change:

```sh
nix run path:.#write-flake
nix run path:.#write-ci-graph
```

Use the [public API reference](docs/API.md) when changing constructors or catalogs. Review input declarations and lock changes together; retain third-party notices.

## Verify the result

```sh
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
bash tests/nix-check.sh
```

For a quick fixture pass with installed Bash, jq, Python and Nix, use `bash tests/check.sh`. For evaluation without package builds, use `bash tests/nix-check.sh --no-build`. These checks do not activate a profile.

If changing activation behavior, also arrange deliberate validation on a suitable host. Add focused regression tests where they protect behavior. See [CI](docs/CI.md) for selection and caching rules.

## Open a review PR

Describe the user-visible result, commands run, results and any validation limits. Include user-facing changes under `Unreleased` in [CHANGELOG.md](CHANGELOG.md).

Keep documentation task-oriented. Update the [docs index](docs/README.md) and relevant guide; put temporary plans, benchmarks, QA results and release-preparation notes in the PR instead of committing reports. Retain reusable test tools in `tests/` or `scripts/`.

Push the branch or bookmark and open a PR against `main`. **CI gate** must pass before merging. Follow [Releasing](docs/RELEASING.md) when preparing a version.
