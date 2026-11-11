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

The first command checks the latest `main` revision; the second stages, builds and activates an eligible revision while preserving personal modules and additional inputs. The staged updater requires successful canonical CI for that exact commit. Pending or failed CI is not permission to adopt a different, older candidate. Updates are identified by commit, so two commits with the same version number can still be distinct updates. A version downgrade or non-forward history requires manual review rather than automatic adoption.

Consumer flakes normally declare `github:closure-labs/foundation/main`. Their `flake.lock` retains `original.ref = "main"` but pins the selected `locked.rev` and `locked.narHash`, together with Foundation's own dependency graph. A build or activation does not silently follow later changes to `main`. The staged updater qualifies a resolved branch revision, then updates only the staged Foundation input. If the branch moves during resolution, it rejects the mismatch rather than building an unreviewed revision. It builds only the verified immutable lock. After building, and again after generation preparation, it requalifies the same commit and CI run/attempt before activation. A rerun or changed CI proof aborts without committing the staged configuration. Once the lock is verified, a later main advance does not substitute a new candidate; the frozen candidate must still retain its original successful CI proof. It does not replace Foundation-owned dependency pins with consumer `follows` overrides.

For a manually maintained flake, the explicit Nix equivalent is:

```sh
cd ~/.config/home-manager
nix flake update foundation
foundation home check
foundation home apply
```

Review the lock diff before applying. This direct Nix command does not perform the staged updater's CI qualification, backups or personal-input preservation checks. Commit your reviewed `flake.nix` and `flake.lock` together. A version tag or exact commit remains valid for manual pinning; do not run the staged update command if you intend to keep that pin. An explicit staged update can advance supported fixed-pin consumers to the reviewed immutable main commit without changing them into branch-tracking consumers.

GitHub's `/releases/latest` URL means the latest published release, not the latest `main` commit; it is not the flake update channel. Version tags and release archives remain optional human-readable milestones. See [Nix flake references and lock files](https://nix.dev/manual/nix/2.22/command-ref/new-cli/nix3-flake) and [GitHub release links](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases).

Explicit local Git pins remain manually maintained. See [pinning a checkout](CONFIGURATION.md#pin-a-source-checkout).

For older configurations and profile formats, follow [Migration](MIGRATION.md).

## Use Home Manager directly

For an existing personal flake:

```sh
cd ~/.config/home-manager
nh home build
home-manager switch --flake ~/.config/home-manager
```

These use the direct build/activation path. Foundation's staged commands additionally provision shared Brew tools and back up consumer files. Direct Home Manager activation does not provide those safeguards. Schema-3 homes use nixGL Mesa for graphical Nix applications.

For Intel IPU7 cameras, see [Camera diagnosis and repair](CAMERA.md).

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
