# Foundation 0.3.1 release preparation

Status: preparation for review; no tag or release has been created. This patch
release includes the merged download recovery from
[PR 11](https://github.com/closure-labs/foundation/pull/11), the 5 GiB default
realization budget from PR 9 and the private module refactor from PR 10.
Dependency pins, profile schemas and release compatibility remain unchanged.

The [download recovery](../download-recovery.md) affects only realization.
Configuration generation, provisioning and activation are never retried.
Existing user configuration and diagnostics remain available after failure.
The controlled Nix fixture reproduced an interrupted transfer, a same-URL range
retry rejected with HTTP 416, and recovery through a fresh hash-verified request.
It does not establish guest OS acceptance.

Before tagging, require the pinned fixture/workflow suite and full Nix build and
selectable-profile evaluation on this reviewed preparation and resulting main
commit. Follow the [release checklist](../RELEASING.md): create a new annotated
`v0.3.1` tag at the reviewed green main commit, let the release workflow create
a draft, verify its source archive, checksums and notes, then review publication.
Never move a versioned tag or replace published assets.

Finite adopts the published immutable commit in a separate reviewed pin/lock
change. That new image requires fresh-install and upgrade/rollback qualification
on both active profiles, retaining Secure Boot, enforcing SELinux, both Nix
sockets and Home Manager acceptance. Publishing this source release grants no
Finite image authority and cannot repair an existing immutable candidate.

Rollback uses the prior source pin and its dependency lock through the normal
reviewed update path. No configuration deletion or shared-cache purge is needed.
