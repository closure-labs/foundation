# Foundation 0.3.3 release preparation

Status: local preparation for review; no `v0.3.3` tag or publication yet.

This patch release installs the standalone Home Manager CLI alongside NH in
the shared base configuration. New Finite homes and standalone consumers can
run `home-manager switch --flake ~/.config/home-manager`. Existing consumers
receive the command after updating their Foundation pin and activating the
new generation.

Release validation now rejects missing or malformed `foundation.json`, an
unsupported metadata schema, or a version that differs from `VERSION`. This
catches errors before creating a draft instead of waiting for stable-channel
advancement to reject the published metadata.

## History review

The changelog-generator review compared Git tags `v0.3.0`, `v0.3.1` and `v0.3.2`,
current `main` at `435d8781d3708da8be9496137bdd3fbaeb111058`, and the jj working
copy/history. GitHub confirmed `v0.3.2` is the latest published stable release
and that this main commit passed all three CI checks on 2026-10-23.

- PR #15 (`59f5adff`) installs the CLI and checks installed-package membership
  across the eight actual schema-3 profile compositions.
- PR #14 (`fc39fb7c`) avoids duplicate branch/PR CI runs. Main, PR, merge-group,
  manual and exact-tag release checks remain available. This contributor-only
  change is included in the source but omitted from user-facing release notes.
- The private module split, 5 GiB realization budget and interrupted-download
  recovery already belong to the previous entries and are retained unchanged.
  The shared `v0.3.1` tag remains an unpublished preparation superseded by
  `v0.3.2`; it must not be moved or published.

The initially stale jj working copy was snapshotted as `5e48e175` before creating
this preparation on current main. Its CLI/module work was already present
upstream; no unique local edits needed carrying forward.

## Validation and compatibility

Run the pinned `tests/ci.sh`, full `tests/nix-check.sh`, exact-tag metadata
validation and source-archive checks. Local results are recorded in the
[release QA report](../qa-reports/QA-release-0.3.3.md). The CLI must appear in
both schema-2 and schema-3 package environments, and its executable must run
from the built environment without activation.

Dependency pins, third-party notices, profile schemas, release compatibility 1
and `home.stateVersion` remain unchanged. Direct Home Manager commands use
Home Manager's build/activation path; Foundation's staged commands retain
their provisioning, resource-budget, backup and rollback behavior.

## Release handoff

Follow the [release checklist](../RELEASING.md): review and merge this
preparation, require the CI gate at the resulting main commit, create a new
annotated `v0.3.3` tag, then verify the workflow-created source archive,
checksums and release notes before publishing the draft. Confirm the changelog
date if publication occurs after 2026-10-23. Never move an existing version tag.

Finite adopts the published immutable commit separately. This source
preparation does not activate a workstation or qualify a Finite OS image;
fresh-install and upgrade/rollback acceptance remain part of that adoption.
