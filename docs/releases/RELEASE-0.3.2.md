# Foundation 0.3.2 release preparation

This preparation supersedes the unpublished, tagged
[0.3.1 preparation](RELEASE-0.3.1.md). Release review reproduced exit 137 being
retried after a transient transfer diagnostic. Only Nix's ordinary failure exit
1 may enter transport recovery; negative signal statuses, wrapper exits such as
137 and usage errors are terminal. The regression covers mixed diagnostics and
both negative and positive failure statuses.

The existing three-attempt limit, two/four-second backoff and one 900-second
deadline remain. Configuration generation, provisioning and activation are never
retried. Dependency pins, schemas and compatibility remain unchanged. The
realization memory budget and private module refactor from 0.3.1 are included.

Follow the [release checklist](../RELEASING.md): review and merge this preparation,
require the exact main CI gate, create a new `v0.3.2` tag and verify the
workflow-created archive, checksums and notes before publication. Keep `v0.3.1`
unpublished and preserve its tag/assets as diagnostics. Never retag it.

Finite must adopt the published immutable commit separately, with fresh-install
and upgrade/rollback qualification on both active profiles, including Secure
Boot, enforcing SELinux, both Nix sockets and Home Manager acceptance. A source
release grants no Finite image authority and cannot modify an existing image.
