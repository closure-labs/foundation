# Getting started

Foundation creates a personal Home Manager flake at `~/.config/home-manager`. It installs user applications and settings without replacing the operating system.

## 1. Check your host

Use an x86_64 Linux desktop running Bluefin or Bluefin DX, with:

- Nix installed and `nix-command` and `flakes` enabled.
- Homebrew available at `/home/linuxbrew/.linuxbrew`.
- A regular desktop account and graphical session for Flatpak and the selector.

Run Foundation commands as your desktop user, not with `sudo`. If `~/.config/home-manager` already exists, use [Configuration](CONFIGURATION.md) or the [migration instructions](MIGRATION.md#adopt-foundation-in-a-legacy-configuration).

## 2. Generate a profile

For a household desktop:

```sh
nix run github:closure-labs/foundation/latest-release#home-profile -- \
  --foundation bluefin --roles family,media --form-factor desktop \
  --format json > "$HOME/foundation-profile.json"
```

For a work laptop:

```sh
nix run github:closure-labs/foundation/latest-release#home-profile -- \
  --foundation bluefin-dx --roles developer --packages jj \
  --form-factor laptop --cpu intel --gpus intel-integrated \
  --format json > "$HOME/foundation-profile.json"
```

Choose flags that match your machine; Foundation does not detect hardware. The generator fills in your current account identity. It prints a profile without initializing or activating a home. JSON and the default YAML output are both accepted by the initializer.

Review [roles, capabilities and host values](PROFILES.md) before continuing. Keep the profile file outside the configuration directory that initialization will create.

## 3. Build without activating

```sh
nix run github:closure-labs/foundation/latest-release#home-init -- \
  --profile "$HOME/foundation-profile.json" --check
```

This validates the profile and builds a staged home. It does not create the live configuration or activate it.

## 4. Initialize and activate

```sh
nix run github:closure-labs/foundation/latest-release#home-init -- \
  --profile "$HOME/foundation-profile.json"
```

Initialization creates the personal flake, provisions required shared Homebrew tools, and activates the built generation. Its `flake.lock` records the exact Foundation source and dependencies.

After activation, open a new terminal and follow [Configuration](CONFIGURATION.md) to change selections and add personal settings.

## Use a source checkout

From a Foundation checkout, replace the remote flake reference in the commands above with `path:.`, for example:

```sh
nix run path:.#home-profile -- --foundation bluefin --roles family --format json
```

To use the repository itself as your home configuration, set its `profile.json` identity to your desktop account, edit `customize.nix` or `modules/local.nix`, and run from the checkout root:

```sh
bash modules/home/commands/_assets/finite-home-apply --check
bash modules/home/commands/_assets/finite-home-apply
```

The second command activates the checkout and provisions shared Brew tools. Maintain its source and dependency pins explicitly; published-release updates target importing personal flakes. See [Configuration](CONFIGURATION.md#pin-a-source-checkout) for an immutable local input instead.
