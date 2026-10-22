# Finite update integration

Date: 2026-10-21. U1 completes the update-order follow-up from the
[profile plan](../plans/PLAN-profile-refactor.md). Implementation is isolated in
Finite jj change `pmpytlzt`, workspace `/tmp/finite-profile-readers`. Foundation
records the contract and evidence in jj change `rrpmlwkw`.

## Result

Finite's owned `60-custom.just` rejects root before any upstream work. It invokes
the installed Bluefin updater through real Just with a fixed Bash startup hook.
The hook enables `errexit`, writes a private marker and removes its environment
variables before nested tools run. Successful upstream completion plus the
marker allows Foundation's existing staged updater to run for importing
consumers. Failed actual update commands stop later stages; Foundation errors
remain nonzero. The temporary directory is removed on success and failure.

This uses Bash's documented [noninteractive startup file](https://www.gnu.org/software/bash/manual/html_node/Bash-Startup-Files.html)
mechanism. Production does not parse/extract recipe bodies or maintain a copied
updater implementation. The hook adds neither `nounset` nor `pipefail` upstream;
the owned wrapper keeps its strict options. This preserves discovery pipelines
and avoids changing error handling inside nested Brew/Bash tools.

The order remains OS → system/user Flatpaks → owned Brew → Foundation.
The current installed recipe chooses rpm-ostree for layering or sudo/bootc
otherwise. No source-flake maintainer update or NH backend is inserted.
Foundation already uses plain Nix builds with its existing resource limits,
staging, backups and recovery; direct NH commands may use `--no-nom` separately.

## Validation

Local evidence: `/tmp/foundation-update-guard-mfudqnao/` retains the original
wrapper/docs, installed upstream recipe, test/build logs and final patch.

| Check | Result |
| --- | --- |
| Real-Just integration | Ten update tests plus 18 existing reader/shim tests pass locally |
| Failure injection | Both OS paths; system Flatpak, user Flatpak, Brew and Foundation failures stop subsequent stages and retain diagnostics |
| Skips and guards | Intentional absent-remotes/Brew skips reach Foundation; busy updater, root, missing hook and missing startup marker stop it; legacy consumers keep the migration message |
| Shell scope | Nested Bash sees neither hook variable nor injected errexit/nounset/pipefail; upstream conditional-pipeline semantics are preserved |
| Temporary state | Success and failure remove private marker state |
| Static checks | Changed Nix file passes Alejandra; finalizer and sourced hook pass pinned ShellCheck and Bash syntax checks |
| Hermetic home contracts | Pass: real profile/template generation, schema-2 YAML/seed ISO, both 28-test runs, four maintenance tests and startup-hook ShellCheck |
| Review | Architecture, CLI/shell, security and QA reviews found no blockers; QA independently reran all ten update tests and verified the installed fixture |
| Live state | No OS updates, package upgrades, Foundation activation or live pin edits were invoked |

The real-Just fixture is byte-identical to the installed
`/usr/share/ublue-os/just/update.just`, captured on 2026-10-21, SHA-256
`f9f3a9844e1a9c4e934f3bbb529a9857550ffc768de5ac2853a6226aabddaa8c`.
Only interpreter/policy/Brew paths and external update commands are substituted
in test copies. The root test substitutes EUID in the owned test copy; production
has no root-check bypass. The image finalizer requires the startup hook to exist.

The first hermetic attempts identified test-environment assumptions about Just's
runtime directory and `/usr/bin/env`; fixtures now use private runtime state and
store interpreter paths. No check was removed.

## Limits and next step

Bash exempts conditional probes from `errexit`. An upstream discovery error can
therefore still look like an intentional skip. The startup marker proves the
hook ran, not that arbitrary future recipe implementations preserve strictness.
The qualified baseline is this installed single-Bash-script updater with bare
update commands; refresh its fixture and requalify when the image updater changes.

The active Dell remains on Foundation source `7eed78af934634b253a84e7bbaba758234d870b2`
and its previously verified generation. This change is ready for later Finite
image adoption; it is not installed on the running OS. Finite schema-3 first-login
and cloud-init writer adoption remains a separate slice.
