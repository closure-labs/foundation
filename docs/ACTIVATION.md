# Activation, updates and recovery

Run these commands as your desktop user. Foundation's staged commands build a candidate before replacing configuration files and activating it.

## Build, then activate

After editing your personal files:

```sh
foundation home check
foundation home apply
```

The check builds without installing. Apply provisions shared Homebrew tools, backs up the configuration and activates the built generation. Preview role or capability changes with `--preview`; see [Configuration](CONFIGURATION.md).

## Update Foundation

```sh
foundation home update --check
foundation home update
```

The first command reports available published releases. The second stages, builds and activates an update while preserving personal modules and additional inputs. Consumer flakes normally track `github:closure-labs/foundation/latest-release`; `flake.lock` records the exact selected revision.

Explicit local Git pins remain manually maintained. See [pinning a checkout](CONFIGURATION.md#pin-a-source-checkout).

For older configurations and profile formats, follow [Migration](MIGRATION.md).

## Use Home Manager directly

For an existing personal flake:

```sh
cd ~/.config/home-manager
nh home build
home-manager switch --flake ~/.config/home-manager
```

These use the direct build/activation path. Foundation's staged commands additionally provision shared Brew tools and back up consumer files. Direct Home Manager activation does not provide those safeguards. Schema-2 homes on non-NixOS hosts also need the generated `non-nixos-gpu-setup` helper; schema 3 uses nixGL Mesa instead.

## Recover from a failure

- **Build failure:** the candidate is not activated. Read the error, correct the configuration or retry after a network outage, then run `--check` again.
- **Memory limit:** staged builds default to 5 GiB, one job, one core and 512 MiB swap. If your host has capacity, retry explicitly with `FOUNDATION_BUILD_MEMORY_MAX=6G foundation home check`. A killed build does not automatically increase its budget.
- **Interrupted download:** realization retries eligible transport failures up to three attempts within one 15-minute deadline. Authorization, integrity, evaluation, builder and signal failures are terminal; activation is never retried by this downloader.
- **Activation failure:** Foundation restores configuration entries and attempts to reactivate the previous generation. Inspect the error and retained `home-manager.previous.*` backups next to your configuration before another attempt.

Homebrew and Flatpak side effects are not transactional. Restoring a source lock or Home Manager generation does not restore application data; retain application-specific backups when changing providers.

## Optional stage timings

Set `FOUNDATION_TIMINGS=1` on an existing staged command to emit versioned timing
records on stderr. For example, `FOUNDATION_TIMINGS=1 foundation home check`
measures a check without activation. Instrumentation is disabled by default and
does not add a second initialization, evaluation or build invocation.

Each `FOUNDATION_TIMING ` line contains JSON with schema, kind, a fixed stage
name, UTC start time, elapsed seconds, outcome and subprocess status when known.
It excludes paths, usernames, commands, output and environment values, and grants
no publication authority. Failed and interrupted stages retain partial elapsed
time. Diagnostic write failures preserve the underlying operation's outcome.

Stages distinguish profile validation, Home Manager realization, Brew policy
evaluation, Brew bootstrap, activation and rollback activation. Initialization,
Brew provisioning and commit/activation totals contain nested stages: do not add
them together as independent cost. Realization includes Nix's internal
evaluation, fetch, build and retry waits; this first instrumentation does not
claim a separate duration for each. Flatpak work remains inside activation.
Unknown internal breakdowns must remain unknown until separately instrumented.
Resource limits, command arguments, personal configuration and activation order
are unchanged. CI consumers must bind any collected records to their native
guest/job evidence and selected Foundation release before using them in reports.
