# Foundation

**A reproducible Linux home, configured around the way you work.**

Foundation manages your applications, shell and desktop settings with Nix Home Manager. Combine work and personal roles, add the tools you need, and keep your choices in a small configuration you own.

Built for **x86_64 Linux on Bluefin or Bluefin DX**, Foundation works as a standalone home configuration or as part of Finite. It manages your home environment; the operating system owns drivers, firmware and system services.

## What you get

- **Composable profiles.** Mix Developer, Support, Family, Creative and other roles without installing shared applications twice.
- **Your own configuration.** Keep account details and selections in `profile.json`, with personal settings in `customize.nix` and `modules/local.nix`.
- **Pinned, reviewable changes.** Build before activation, preview profile changes, and explicitly adopt reviewed `main` commits with configuration backups.

## Start here

Use a regular desktop account with Nix flakes enabled, Homebrew at `/home/linuxbrew/.linuxbrew`, and a graphical session. If you already have a Foundation configuration at `~/.config/home-manager`, open its selector:

```sh
foundation home configure
```

For a new home configuration, generate a profile, check the build, then activate it:

```sh
nix run github:closure-labs/foundation/main#home-profile -- \
  --foundation bluefin --roles family,media --format json > "$HOME/foundation-profile.json"

nix run github:closure-labs/foundation/main#home-init -- \
  --profile "$HOME/foundation-profile.json" --check

nix run github:closure-labs/foundation/main#home-init -- \
  --profile "$HOME/foundation-profile.json"
```

Choose `bluefin-dx` if that is your installed foundation. Initialization creates `~/.config/home-manager` and refuses to replace an existing configuration. The last command realizes the home, runs optional generation preparation, and activates it. On Bluefin, preparation ensures the inherited stock CLI bundle and user setup; Finite additions are declarative Nix/Flatpak packages. See [Bluefin ownership](docs/bluefin-user-environment.md).

Follow [Getting started](docs/GETTING-STARTED.md) for prerequisites, hardware choices and checkout-based setup.

## Run the Foundation command

After activation, use `foundation home <action>`. `foundation home check` builds without activating; `foundation home apply` builds and activates.

From a reviewed source checkout, the native flake app exposes the same interface:

```sh
nix run path:. -- home --help
nix run path:.#foundation -- home check
```

Use `foundation home --help` to list actions. Native apps such as `#home-update` and `#home-profile` also remain available. See [Migration](docs/MIGRATION.md#adopt-the-foundation-command-interface) when updating older command integrations.

## Make it yours

```sh
foundation home apply --roles developer,creative --capabilities recording --preview
foundation home check --roles developer,creative --capabilities recording
foundation home apply --roles developer,creative --capabilities recording
```

These commands replace the named selections; omitted selections stay unchanged. Use [Configuration](docs/CONFIGURATION.md) for personal Nix settings and [Profiles and hardware](docs/PROFILES.md) for available choices. For older configurations, start with [Migration](docs/MIGRATION.md).

## Keep it current

```sh
foundation home update --check
foundation home update
```

The first command checks for a newer eligible `main` commit. The second builds and activates that exact revision while preserving personal configuration. A new version tag is not required; the lock keeps builds reproducible until you explicitly update. See [Activation, updates and recovery](docs/ACTIVATION.md) for build limits, backups and direct Home Manager commands.

## Camera troubleshooting

If Firefox cannot find an Intel IPU7 webcam, run `foundation home camera`. Foundation can detect and repair a verified host processing-module mismatch. Follow [Camera diagnosis and repair](docs/CAMERA.md) for the next steps, including when to restart services.

## Documentation

[All guides](docs/README.md) · [Module architecture](docs/MODULES.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

Foundation began as Finite’s Home Manager template and now owns its modules and release cycle independently. Use `foundation home <action>` to manage your configuration; a Finite checkout is not required. See [Origin](ORIGIN.md) for source provenance. Licensed under [Apache-2.0](LICENSE); bundled Zsh assets retain their MIT license. See [NOTICE](NOTICE) and the [security policy](SECURITY.md).
