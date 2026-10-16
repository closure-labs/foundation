# Finito

A Foundation for reproducible Linux workstations, intended to be
[Finite](ORIGIN.md)'s default Nix Home Manager flake. No psychohistory required.

Finito is a standalone, source-controlled flake extracted from Finite. The
modules, assets, helper scripts and dependency lock live in this repository.
It does not import or require a Finite checkout. The existing `finite-*` command
names and configuration paths are retained.

This configuration targets **x86_64 Linux with Bluefin or Bluefin DX**. It expects
Homebrew at `/home/linuxbrew/.linuxbrew`, a working Nix installation with flakes,
and a graphical session for Flatpak and the role selector.

## Configure your account

Edit [profile.json](profile.json) before building or activating. The initial
`finite` account is a placeholder; set `identity.username` and
`identity.homeDirectory` to your account's actual login name and home directory.
Keep `schema` at `2`.

| Field | Choices, in canonical order |
| --- | --- |
| `foundation` | `bluefin` or `bluefin-dx` |
| `hardware` | `generic-x86_64` or `dell-xps-9350-intel` |
| `roles` | `developer`, `sales`, `trainer`, `support`, `executive`, `it` |
| `packages` | `hack-font`, `herdr`, `jj`, `opencode`, `uv` |

Roles and optional packages may be empty or combined without duplicates. Keep
each list in the order above. Both foundations use the same Home Manager base;
this selection records the host foundation and does not change the OS image.

Add personal settings to [customize.nix](customize.nix), for example:

```nix
{pkgs, ...}: {
  home.packages = [pkgs.jq];
  services.flatpak.packages = ["org.gimp.GIMP"];
}
```

[modules/local.nix](modules/local.nix) is another imported module. Both receive
`inputs`, so custom inputs can be declared in `flake.nix` and used in either
module. Keep `home.stateVersion` at its existing value when updating dependencies.

## Build and apply

From this checkout, build without activating or changing dependency pins:

```bash
nix build --no-update-lock-file \
  ".#homeConfigurations.$(id -un).activationPackage"
```

The exported name comes from `profile.json`; it must match your account.
Building does not install the shared Homebrew tools or activate Home Manager.

For the existing `nh` and `finite-configure` commands to find this repository,
place it at `~/.config/home-manager` or link it there. If that path already
exists, move it to a backup location before creating the link. From the checkout:

```bash
mkdir -p ~/.config
ln -s "$PWD" ~/.config/home-manager
```

After reviewing your profile and customizations, provision the shared Homebrew
tools and activate the configuration:

```bash
bash modules/finite-home-apply --roles "$(jq -r '.roles | join(",")' profile.json)"
```

This builds a staged configuration using the committed lock pins, installs any
missing shared Homebrew tools, then activates the generation. Add `--check` to
build the staged profile without provisioning Homebrew or activating it.
After the first activation, `nh home build` and `nh home switch` use this flake.
`finite-configure` opens the role and optional-package selectors. Profile changes
made by the selector are written to this checkout; review them with `jj diff`.

The base includes desktop apps, user Flatpaks and Homebrew provider checks.
Activation starts user services and can install Flatpaks. The Dell hardware
module includes its display and PipeWire camera settings. The Support role's
Espanso Wayland backend needs host keyboard-device access configured by the
administrator. For Nix graphical apps on non-NixOS, the Home Manager-provided
`non-nixos-gpu-setup` helper may also need to be run as the host administrator.

Keep Finito as the owner of this checkout. Until Finite's initializer adopts this
repository, it can refresh generated modules at `~/.config/home-manager` if run
against it. The initial release prepares that adoption; it does not change the
Finite image or its initializer.

## Maintain the repository

Use `jj status`, `jj diff` and `jj describe` to review and record changes. This
repository has its own `flake.lock`; update dependencies intentionally:

```bash
nix flake update INPUT_NAME
nh home build
nh home switch
```

Review and record both the configuration and lock changes. The copied pins were
preserved during extraction. Provenance is recorded in [ORIGIN.md](ORIGIN.md).

Run the small local fixture checks with installed Bash, jq, Python 3 and Nix:

```bash
bash tests/check.sh
```

CI runs those fixtures, workflow lint, release metadata checks, and
`nix flake check`, which builds the configured Home Manager activation package.
It also evaluates all roles and optional packages with Dell hardware on both
foundations. CI never activates a configuration. Run the full checks on a host
with enough memory and disk space for the desktop package set:

```bash
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
bash tests/nix-check.sh
```

The required status is **CI gate**. See [CONTRIBUTING.md](CONTRIBUTING.md) for
contribution checks and [docs/RELEASING.md](docs/RELEASING.md) for repository
protection setup and the v0.1.0 release checklist. Version tags prepare a draft
GitHub release after CI passes. Weekly workflows propose reviewed Nix lock and
GitHub Actions updates.

## License

Apache License 2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). The bundled Zsh
assets retain their original MIT license. See [CHANGELOG.md](CHANGELOG.md) for
release notes and [SECURITY.md](SECURITY.md) for vulnerability reporting.
