# Foundation 0.3.0 release review

Status: [v0.3.0 is published](https://github.com/closure-labs/foundation/releases/tag/v0.3.0),
2026-10-21 in America/Chicago (2026-10-22 UTC). PR #8 merged at
`fdeb2ab7d88cb0ff69d25ed1a02589bc28ca7006`; main CI, release validation and the
stable-channel workflows passed. The annotated tag and `latest-release` select
that commit. The [publication manifest](0.3.0-publication.json) records final
source identity and verified artifacts separately from the local candidate.

Local preparation results are recorded in the
[candidate validation report](../qa-reports/QA-release-0.3.0.md) and
[manifest](0.3.0-candidate.json), in a separate documentation change after the
frozen candidate. The published archive was independently reproduced from the
final tagged commit; its checksum and release notes match. The final immutable
consumer template and Finite home contracts also passed before publication.

## Shipped behavior

New profiles/templates use schema 3, with six Professional and four Personal
roles, optional capabilities, independent host declarations and graphical
Nixpkgs/nixGL composition. The selector supports locked-source editing and
explicit conversion previews. Existing schema-2 profiles remain readable and
retain their composition. Local immutable Git consumers remain manually pinned.
See the [changelog](../../CHANGELOG.md), [generation guide](../architecture/ARCH-profile-generation.md),
[editor contract](../architecture/ARCH-profile-editor.md) and
[host contract](../architecture/ARCH-host-composition.md).

The default format/catalog changes fit the repository's documented `0.x` minor
version policy. Release compatibility stays 1; `home.stateVersion` is unchanged.
The original local candidate kept its dependency lock unchanged during
preparation. Integration with current `main` retains that branch's subsequent
dependency and workflow updates; the integrated source requires fresh validation.

Finite's guarded `ujust update` integration and negotiated first-login/seed
writers are prepared in a separate workspace. They are not installed by this
Foundation archive. Finite's committed source pin remains at 0.2.2 until a
reviewed adoption change; its code changes are described in
[U1](../qa-reports/QA-update-integration.md) and
[F3](../qa-reports/QA-finite-profile-writers.md).

## Candidate validation

The immutable candidate must pass:

- `VERSION`, `foundation.json.version`, tag and dated changelog agreement.
- Pinned CI, full Nix checks/builds and the selectable profile evaluations.
- Immutable consumer-template generation and packaged schema-3 generation.
- Finite's current-source home contracts through a temporary input override,
  including seed ISO contents, target identity and failure cleanup.
- Source archive/checksum verification using the same archive format as the
  release workflow, with version and default profile/catalog checks on extraction.
- Read-only QA/security release review and unchanged live configuration checks.

Candidate results and artifacts are recorded in the task tracker and local
release manifest. Local validation does not substitute for the required GitHub
CI gate at the eventual reviewed main/tag commit.

## Publication and adoption order

1. Review the candidate, release notes and validation evidence.
2. Approve shipping, then merge the preparation through a pull request and wait
   for CI at the selected immutable commit. This repository currently has no
   enforced main protection; the release operator must check the CI gate before
   merging and tagging.
3. Tag that reviewed commit as `v0.3.0`. The release workflow checks ancestry,
   runs validation and prepares a draft with source/checksum assets.
4. Review the workflow-created assets, then publish the approved draft. The
   release-channel workflow verifies the release/CI and advances `latest-release`.
5. Prepare Finite's separate published-commit pin/lock/provenance adoption and
   validate its home contracts before OS-image rollout.

No versioned tag should be moved. Existing fixed and manually pinned consumers
keep their exact source until explicitly updated. If a consumer update fails,
the staged updater's backup and previous-generation recovery remain available;
restore source lock and profile together when returning to a schema-2-only source.
Previously installed Brew/Flatpak side effects remain outside that transaction.

## Manual validation boundary

The Dell workstation's prior activation and accelerated Intel OpenGL probe
qualified source `7eed78af`, not this release candidate. This preparation does
not activate the candidate. Camera/fingerprint, suspend/docking and media/game
behavior remain the documented hands-on checks. A Foundation source release
does not establish graphical first-login activation or qualify a new OS image.

Post-publication update, 2026-10-22: the user authorized activation of the final
published release on this workstation and confirmed both Firefox password-manager
extensions healthy after a full reboot. The [activation report](../qa-reports/QA-workstation-release-0.3.0.md)
records the preserved schema-3 Professional profile, Firefox version and service
checks separately from candidate preparation and remaining physical hardware tests.
