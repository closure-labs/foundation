# Activation, updates and recovery

Run these commands as your desktop user. Foundation's staged commands build a candidate before replacing configuration files and activating it.

## Build, then activate

After editing your personal files:

```sh
finite-home-apply --check
finite-home-apply
```

The check builds without installing. Apply provisions shared Homebrew tools, backs up the configuration and activates the built generation. Preview role or capability changes with `--preview`; see [Configuration](CONFIGURATION.md).

## Update Foundation

```sh
finite-home-update --check
finite-home-update
```

The first command reports available published releases. The second stages, builds and activates an update while preserving personal modules and additional inputs. Consumer flakes normally track `github:closure-labs/foundation/latest-release`; `flake.lock` records the exact selected revision.

To move a fixed-commit consumer onto that channel, change its Foundation URL in `flake.nix`, then update the input and apply:

```sh
cd ~/.config/home-manager
nix flake update foundation
finite-home-apply --check
finite-home-apply
```

Explicit local Git pins remain manually maintained. See [pinning a checkout](CONFIGURATION.md#pin-a-source-checkout).

## Convert an existing profile

Schema-2 profiles remain supported. To review a conversion to schema 3:

```sh
finite-configure --migrate-profile
```

Or preview and build from the CLI:

```sh
finite-home-apply --migrate-profile --roles developer,creative --capabilities recording --preview
finite-home-apply --migrate-profile --roles developer,creative --capabilities recording --check
```

To activate, repeat the same selections with `--approve-preview TOKEN`, replacing `TOKEN` with `approvalToken` from a fresh preview. The token binds the exact source, configuration and selections. Request another preview if any of them change; keep saved previews outside the consumer directory.

Review provider changes before conversion. Unmanaged Flatpaks and their data remain in place; application data is not copied to native packages automatically. Verify exports, account sync and desktop defaults for affected applications before removing an old provider yourself.

## Adopt Foundation in a legacy configuration

This is separate from changing the profile schema:

```sh
finite-home-migrate --check
finite-home-migrate
```

If the helpers are not installed, run `nix run github:closure-labs/foundation/latest-release#home-migrate -- --check` first, then repeat without `--check` to migrate.

Migration adopts Foundation's dependency pins while preserving your profile, personal modules and additional inputs. Modified upstream modules, custom output functions, Git checkouts, symlink roots and conflicting personal `nixGL` inputs may require manual migration.

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
- **Memory limit:** staged builds default to 5 GiB, one job, one core and 512 MiB swap. If your host has capacity, retry explicitly with `FOUNDATION_BUILD_MEMORY_MAX=6G finite-home-apply --check`. A killed build does not automatically increase its budget.
- **Interrupted download:** realization retries eligible transport failures up to three attempts within one 15-minute deadline. Authorization, integrity, evaluation, builder and signal failures are terminal; activation is never retried by this downloader.
- **Activation failure:** Foundation restores configuration entries and attempts to reactivate the previous generation. Inspect the error and retained `home-manager.previous.*` backups next to your configuration before another attempt.

Homebrew and Flatpak side effects are not transactional. Restoring a source lock or Home Manager generation does not restore application data; retain application-specific backups when changing providers.
