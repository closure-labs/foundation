# Releasing Foundation

`VERSION` contains the version without a `v` prefix. Git tags use `vMAJOR.MINOR.PATCH`.
The release workflow validates the tag against `VERSION`, `foundation.json`
and `CHANGELOG.md`, checks that it belongs to `main`, runs CI at that exact
commit, and prepares a draft release with a source archive and SHA-256 checksums. A maintainer reviews
and publishes the draft separately.

Foundation is intended to be Finite's default Home Manager flake, with standalone
use also supported. Publishing here and adopting the release in Finite are
separate changes.

## Bootstrap GitHub

For an initially empty remote, review the complete extraction and repository
setup, then record and push the intended initial change:

```bash
jj status
jj diff
jj describe -m "Prepare Foundation v0.2.0"
jj bookmark set main -r @
jj git push --remote origin --bookmark main
```

The installed `jj bookmark set` creates `main` if it does not exist and updates
it if it does. Confirm the selected revision before pushing; later contributions
should use pull requests. Set `main` as the default GitHub branch.

After the first successful CI run exposes its check name, configure an active
GitHub ruleset for `main`: require pull requests, require **CI gate**, block force
pushes and deletion, and leave bypasses disabled. Require a review when another
maintainer is available. If using a merge queue, keep `merge_group` CI enabled.
Use a tag ruleset matching `v*` to restrict release-tag creation to release
maintainers and prevent updates/deletions; do not grant a bypass around CI.

Enable private vulnerability reporting. Allow GitHub Actions to create pull
requests so the lock-update workflow can open its validated update branch.
Use read-only default workflow permissions; individual publishing jobs request
the permissions they need. Automated dependency pull requests still require
review and passing CI.

## Prepare a version

1. Choose the version and update `VERSION` and `foundation.json.version` together.
   Move the corresponding `Unreleased` entries into a dated
   `## [X.Y.Z] - YYYY-MM-DD` section in `CHANGELOG.md`, leaving
   an empty `Unreleased` section and updating its comparison link.
2. Review dependencies, provenance and third-party notices. Keep `flake.lock`
   committed and check the README's setup and activation instructions.
3. Run the fixture checks and full Nix validation:

   ```bash
   bash tests/check.sh
   nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
   bash tests/nix-check.sh
   ```

4. Merge the preparation change through a pull request and wait for **CI gate**
   on the resulting `main` commit. Record any manual host validation in the PR.
   A build does not activate a profile or validate physical Dell hardware.

Release `0.3.2` is published. The [0.3.3 preparation](releases/RELEASE-0.3.3.md)
records the next candidate's scope and validation. The release validator requires
`foundation.json` schema 1 and a version matching `VERSION`, in addition to the
tag/changelog checks. Confirm the changelog date if publication occurs after the
prepared date. The historical [0.3.0 release review](releases/RELEASE-0.3.0.md)
and [publication manifest](releases/0.3.0-publication.json) retain that release's
evidence.

## Tag and review the draft

Fetch the reviewed branch and inspect its commit before creating a tag:

```bash
jj git fetch --remote origin
jj log -r 'main@origin'
jj git export
release_commit=$(jj log -r 'main@origin' --no-graph -T commit_id)
git tag -a v0.3.3 "$release_commit" -m "Foundation v0.3.3"
git push origin refs/tags/v0.3.3
```

Confirm `release_commit` is the reviewed, green `main` commit. This checkout uses
colocated Git, so Git can create and push an annotated tag after export.
`jj tag set` is also available locally,
but `jj git push` pushes bookmarks; the explicit Git tag push is used here.
Do not move a released tag.

The tag push starts the release workflow. To retry, run the **Prepare release** workflow
manually with the existing tag, such as `v0.3.3`. Confirm the run checked the
expected commit, all required checks passed, release notes match the changelog,
and the source archive and checksum assets are attached. Download the assets
and verify them using `sha256sum -c` from the same directory.

Publish the reviewed draft from GitHub Releases when ready. If validation fails,
fix the preparation change and use a new version/tag when the existing tag has
already been shared. The workflow never publishes automatically.

Publication triggers **Advance latest release**. It selects the highest published
stable semantic version, checks the tag's metadata, ancestry on `main`, and a
successful **CI gate** at that exact commit, then advances `latest-release` without
force-pushing. Drafts, prereleases and unreleased `main` commits never enter this
channel. Late publication events cannot roll it back. Confirm the branch matches
the published tag before announcing the release.

For initial setup or recovery, run **Advance latest release** manually on `main`.
It rechecks published releases and CI rather than trusting an event's tag. The
script also supports `python3 scripts/release-channel.py --check` for a read-only
preview in a fetched checkout authenticated with `gh`. Never move versioned tags;
`latest-release` is the moving branch, and consumer locks preserve exact revisions.

## Adopt the release in Finite

In a separate reviewed change to Finite, pin its default Home Manager source to
the released commit, refresh the relevant lock/configuration, and verify that
the default profile builds and its initializer consumes Foundation correctly.
Check the retained `finite-*` commands and configuration paths, including any
initializer that refreshes `~/.config/home-manager`. Test activation on a
suitable host before rolling out the new default. This repository's release
does not itself update Finite or establish that integration has been switched.
