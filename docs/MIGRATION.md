# Migration

Use this guide to adopt Foundation in an older home configuration or replace an unsupported home profile. Routine release updates are covered in [Activation](ACTIVATION.md#update-foundation). These are separate operations; choose the section that matches your configuration.

Before starting, back up your personal files and application data. Run commands as your desktop user. Build checks do not activate changes.

## Replace an unsupported profile

Foundation accepts only schema-3 home profiles. Older profiles are rejected before building or activating; they are not silently reinterpreted. The former `--migrate-profile` conversion option is no longer available.

Before updating an older consumer, back up `profile.json`, personal modules and application data. Generate a fresh schema-3 profile with `foundation home profile`, then deliberately reselect roles, packages, capabilities and host settings. Preserve custom fields only after reviewing their meaning in the new format. Do not merely change the schema number: application providers and defaults differ.

Review the resulting configuration with `foundation home check` before applying it. Existing unmanaged Flatpaks and their data are retained; application data is not copied to native packages automatically. Verify exports, account sync and desktop defaults before removing an old provider yourself.

## Adopt Foundation in a legacy configuration

This is separate from changing the profile schema:

```sh
foundation home migrate --check
foundation home migrate
```

If the helpers are not installed, run `nix run github:closure-labs/foundation/latest-release#home-migrate -- --check` first, then repeat without `--check` to migrate.

Migration adopts Foundation's dependency pins while preserving your profile, personal modules and additional inputs. Modified upstream modules, custom output functions, Git checkouts, symlink roots and conflicting personal `nixGL` inputs may require manual migration.

## Move a fixed release pin onto the release channel

To move a fixed-commit consumer onto that channel, change its Foundation URL in `flake.nix`, then update the input and apply:

```sh
cd ~/.config/home-manager
nix flake update foundation
foundation home check
foundation home apply
```

## Integration API

`lib.profileDrafts` resolves schema-3 selections. `lib.profileChanges.preview` accepts optional `roles`, `packages` and `capabilities` for a schema-3 source. Previewing does not write or activate a profile; the controller owns approval, building and activation. The catalog envelope version is separate from the profile schema. See [Public API](API.md).

## Adopt the Foundation command interface

The installed `finite-*` helpers are replaced by `foundation home <action>`. Update shell aliases, scripts and external launchers before removing the old generation. For example, `finite-home-update` becomes `foundation home update`, `finite-home-apply --check` becomes `foundation home check`, and `finite-configure` becomes `foundation home configure`.

Before the new command is installed, run a reviewed Foundation checkout directly: `nix run path:.#foundation -- home check`. Activate that source through your normal pinned-input update process. Existing environment variables and consumer metadata retain their compatibility names.
