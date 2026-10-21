# A2 capability editor and explicit conversion

Date: 2026-10-20. Foundation jj change `uvtpxqsw`, parent `zlorynyq`
(`6ed4fea4`). No workstation activation, live profile conversion, publication or
persistent Finite input update occurred. Default generators still emit schema 2.

## Implemented behavior

- Schema-2 editing retains existing roles/packages. Schema-3 editing adds
  Personal roles and explicit capabilities, using the consumer's locked source
  catalog and separately negotiated editing support.
- Conversion requires an explicit request and a reviewed preview token. The
  token binds source, lock, consumer tree, profile bytes and exact selections.
  Read-only preview stages outside the consumer and performs no build, Brew
  provisioning or activation. Check mode builds without conversion approval.
- Source and candidate resolve independently, including optional packages, so
  removals and provider changes remain visible. Unknown fields are preserved;
  a custom schema-2 `capabilities` field blocks conversion.
- Existing backup/recovery handles failed activation. File replacement now
  preserves symlink entries during commit and rollback, including external
  profile contents. Application data is retained without automatic transfer.

## Validation

| Check | Result |
| --- | --- |
| Pinned CI | Passed all 115 Python tests, shell/Nix fixtures, actionlint and release metadata checks |
| Editor suite | 22 passed: pure changes, negotiation, deterministic previews, stale state, conversion approval, build failure, real transaction recovery and symlink preservation |
| Selector suite | 15 passed: existing editing, explicit capabilities, precise preview/apply selections, conversion and cancellation at every dialog |
| Locked-target editor integration | Passed actual selected-source API/catalog negotiation, deterministic separate-invocation approval, package removal, custom-field preservation and incompatible-source rejection |
| Full `bash tests/nix-check.sh` | Passed locked validators/editor, eight actual schema-3 compositions, package availability, real nixGL synthetic launch, home/profile-command builds and all-role schema-2 evaluations on both Bluefin variants |
| Finite compatibility | Passed 18 first-login fixtures, four maintenance fixtures and 18 packaged-helper fixtures against the new immutable Foundation source; saved lock unchanged |

Read-only architecture, QA and security review found a symlink recovery defect:
the previous copy operation could flatten a restored profile link. Atomic
entry-preserving replacement fixes it, with regression tests covering restored
link identity, external bytes and the previous-generation recovery attempt.
Final QA/security reviews reported no remaining blockers.

The Finite home check used Foundation snapshot
`c47a180f8c717a0ff6895998ab8befdd289b449a` with
`--override-input foundation … --no-write-lock-file`. No Finite files changed in
A2; its existing reader work remains isolated in `/tmp/finite-profile-readers`.

The preceding [F1b report](QA-schema3-readers.md) records the 32-case exact legacy
composition comparison and original/new-source Finite constructor checks. A2
does not change application composition, providers, hardware policy or lock
pins. It does not repeat or extend physical graphics validation.

Physical graphics/media, camera, recording and application-data import remain
rollout checks before relying on a converted workstation. Synthetic launches
and mocked activation tests do not establish those behaviors. Provider review
explains retained Flatpaks, duplicate launchers and manual export/import or sync;
personal MIME overrides require separate review.

Evidence, pre-change source and retained patch:
`/tmp/foundation-profile-editor-xbme60gc/`. See the
[editor contract](../architecture/ARCH-profile-editor.md) for commands and
recovery limits. H1 host composition is the next refactor stage.
