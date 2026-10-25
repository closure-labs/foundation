# Foundation

**A reproducible Linux home, configured around the way you work.**

Foundation manages your applications, shell and desktop settings with Nix Home Manager. Combine work and personal roles, add the tools you need, and keep your choices in a small configuration you own.

Built for **x86_64 Linux on Bluefin or Bluefin DX**, Foundation works as a standalone home configuration or as part of Finite. It manages your home environment; the operating system owns drivers, firmware and system services.

## What you get

- **Composable profiles.** Mix Developer, Support, Family, Creative and other roles without installing shared applications twice.
- **Your own configuration.** Keep account details and selections in `profile.json`, with personal settings in `customize.nix` and `modules/local.nix`.
- **Pinned, reviewable changes.** Build before activation, preview profile changes, and update from published releases with configuration backups.

## Start here

Use a regular desktop account with Nix flakes enabled, Homebrew at `/home/linuxbrew/.linuxbrew`, and a graphical session. If you already have a Foundation configuration at `~/.config/home-manager`, open its selector:

```sh
finite-configure
```

For a new home configuration, generate a profile, check the build, then activate it:

```sh
nix run github:closure-labs/foundation/latest-release#home-profile -- \
  --foundation bluefin --roles family,media --format json > "$HOME/foundation-profile.json"

nix run github:closure-labs/foundation/latest-release#home-init -- \
  --profile "$HOME/foundation-profile.json" --check

nix run github:closure-labs/foundation/latest-release#home-init -- \
  --profile "$HOME/foundation-profile.json"
```

Choose `bluefin-dx` if that is your installed foundation. Initialization creates `~/.config/home-manager` and refuses to replace an existing configuration. The last command provisions shared Homebrew tools and activates the built home.

Follow [Getting started](docs/GETTING-STARTED.md) for prerequisites, hardware choices and checkout-based setup.

## Make it yours

```sh
finite-home-apply --roles developer,creative --capabilities recording --preview
finite-home-apply --roles developer,creative --capabilities recording --check
finite-home-apply --roles developer,creative --capabilities recording
```

These commands replace the named selections; omitted selections stay unchanged. Use [Configuration](docs/CONFIGURATION.md) for personal Nix settings and [Profiles and hardware](docs/PROFILES.md) for available choices. For older configurations, start with [Migration](docs/MIGRATION.md).

## Keep it current

```sh
finite-home-update --check
finite-home-update
```

The first command reports available published releases. The second builds and activates an update while preserving personal configuration. See [Activation, updates and recovery](docs/ACTIVATION.md) for build limits, backups and direct Home Manager commands.

## Documentation

[All guides](docs/README.md) · [Module architecture](docs/MODULES.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

Foundation began as Finite’s Home Manager template and now owns its modules and release cycle independently. The installed `finite-*` commands retain their names for compatibility; a Finite checkout is not required. See [Origin](ORIGIN.md) for source provenance. Licensed under [Apache-2.0](LICENSE); bundled Zsh assets retain their MIT license. See [NOTICE](NOTICE) and the [security policy](SECURITY.md).
