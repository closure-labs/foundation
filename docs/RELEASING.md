# Releasing Foundation

Releases are reviewed separately from deployment to consuming systems. `VERSION` and `foundation.json` identify the source version; the [changelog](../CHANGELOG.md) supplies release notes.

## 1. Prepare the release

1. Update `VERSION` and `foundation.json.version` together.
2. Move the relevant `Unreleased` entries to a dated `## [X.Y.Z] - YYYY-MM-DD` changelog section. Keep an empty `Unreleased` section and update comparison links.
3. Review dependency changes, licenses and the setup instructions.
4. Run:

```sh
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
bash tests/nix-check.sh
```

Submit the preparation as a pull request. Merge through normal review and wait for **CI gate** on the resulting `main` commit. Record deliberate host validation in the PR; a successful build does not verify physical hardware or activation.

## 2. Tag the reviewed commit

From a Git checkout of the reviewed release commit, verify its identity and metadata, then create an annotated tag:

```sh
python3 scripts/release.py --check
release_version=$(cat VERSION)
git tag -a "v$release_version" -m "Foundation v$release_version"
git push origin "refs/tags/v$release_version"
```

Confirm that `HEAD` is the intended green `main` commit before running these commands. Never move a published tag.

## 3. Review and publish the draft

The tag workflow validates the version, changelog, ancestry and exact-commit CI before preparing a draft GitHub release. Review its notes, source archive and SHA-256 checksums. Download the assets and verify them with `sha256sum -c` before publishing the draft.

For a failed preparation, correct the issue through review. Retry **Prepare release** with the existing tag only when appropriate; use a new version/tag if a shared release needs correction. The workflow does not publish automatically.

## 4. Verify the release channel

Publication triggers **Advance latest release**. It selects the highest published stable version, verifies metadata and a successful exact-commit CI gate, then advances `latest-release` without force-pushing. Drafts, prereleases and unreleased `main` commits are excluded.

Confirm the channel points to the published tag. For recovery, run that workflow manually on `main`; `python3 scripts/release-channel.py --check` provides a read-only preview in a fetched checkout authenticated with `gh`.

Consumer adoption is a separate reviewed change to its immutable source pin. Validate its initializer, configuration generation and host activation before rollout.

## Repository protections

Require pull requests and **CI gate** on `main`; block force pushes and deletion. Restrict `v*` tag creation to release maintainers and prevent tag changes. Enable private vulnerability reporting and allow the dependency workflow to open review PRs. Keep default Actions permissions read-only; publishing jobs request their own permissions.
