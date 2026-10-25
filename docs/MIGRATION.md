# Migration

Use this guide to adopt Foundation in an older home configuration or convert a schema-2 profile to schema 3. Routine release updates are covered in [Activation](ACTIVATION.md#update-foundation). These are separate operations; choose the section that matches your configuration.

Before starting, back up your personal files and application data. Run commands as your desktop user. Build checks do not activate changes.

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

## Move a fixed release pin onto the release channel

To move a fixed-commit consumer onto that channel, change its Foundation URL in `flake.nix`, then update the input and apply:

```sh
cd ~/.config/home-manager
nix flake update foundation
finite-home-apply --check
finite-home-apply
```

## Integration API

`lib.profileDrafts` provides the compatibility resolver and migration previews. `lib.profileChanges.preview` accepts `migrate = true` alongside optional `roles`, `packages` and `capabilities`. Previewing does not write or activate a profile; the controller owns approval, building and activation. The catalog envelope version is separate from the profile schema.

Schema-2 homes retain their original six-role catalog and application providers until explicitly converted. Review the proposed provider changes before approving. See [Public API](API.md) for constructors and catalog interfaces.
