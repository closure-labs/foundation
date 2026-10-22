# Home Manager build memory budget

Date: 2026-10-22. Status: PASS; unreleased repository fix.

## Observed failure and correction

The full schema-3 Dell workstation build was killed with Python subprocess
return code `-9` while using the default `MemoryMax=3G`. The user journal
reported `oom-kill`. Repeating the build with
`FOUNDATION_BUILD_MEMORY_MAX=5G` succeeded, and the user confirmed healthy
Bitwarden and 1Password Firefox extensions after activation and a full reboot.

The shared staged builder now defaults to 5 GiB. Explicit positive M/G budgets
remain supported, including smaller limits. One job, one core, 100% CPU quota
and 512 MiB swap limits are unchanged. This budget is a cap, not a guarantee
that every custom configuration can build within it.

Only a direct SIGKILL from the build subprocess receives the new diagnostic.
It identifies the actual budget and recommends journal inspection before a
manual budget adjustment. It does not infer that every SIGKILL is an OOM event,
retry automatically, provision packages or activate the failed candidate.
Validation failures and ordinary subprocess failures retain their behavior.

## Verification

- The three new regression cases failed against the previous implementation.
- All 38 controller tests pass, including explicit G/M overrides, unchanged
  resource limits, exception chaining, single-attempt behavior, ordinary exit
  codes/signals and an update failure that preserves the live configuration
  without provisioning or committing.
- Pinned `tests/ci.sh` passes all 147 tests, shell/Nix checks, workflow lint and
  release metadata validation.
- The `home-init` package builds; its bundled helper contains the 5 GiB default
  and its `--capabilities` command still advertises schema-3 writing.
- Read-only CLI, QA and security reviews found no blockers.

The fix does not change dependency pins, schemas, profile membership or the
running workstation. The live consumer continues to use published v0.3.0;
shipping this fix requires a subsequent reviewed release.
