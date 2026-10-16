# Security policy

Security fixes target the latest published release and `main`. Older releases
do not have a separate maintenance commitment. The initial supported release
line is `0.1.x` once published.

Report suspected vulnerabilities privately using
[GitHub's private vulnerability reporting](https://github.com/closure-labs/foundation/security/advisories/new).
Include the affected revision, host/profile details, reproduction steps, impact
and any suggested fix. Redact credentials, account data and private paths.
Avoid publishing exploit details in a public issue before maintainers have
reviewed the report.

Maintainers must enable private vulnerability reporting in the repository's
security settings. If the private reporting form is unavailable, open an issue
requesting a private contact without including vulnerability details. Response
and fix timelines depend on maintainer availability.

Foundation manages user applications and services. Review profile changes, helper
scripts and dependency updates before activation. A successful build verifies
the configuration can be built; it does not establish that activation is
appropriate for every host.
