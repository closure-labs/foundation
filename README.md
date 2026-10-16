# Foundation

A Foundation for reproducible Linux workstations, intended to be
[Finite](ORIGIN.md)'s default Nix Home Manager flake. No psychohistory required.

Foundation is a standalone, source-controlled flake extracted from Finite. The
modules, assets, helper scripts and dependency lock live in this repository.
It does not import or require a Finite checkout. The existing `finite-*` command
names and configuration paths are retained.

This configuration targets **x86_64 Linux with Bluefin or Bluefin DX**. It expects
Homebrew at `/home/linuxbrew/.linuxbrew`, a working Nix installation with flakes,
and a graphical session for Flatpak and the role selector.

## Personal configurations

Finite provisions a small personal flake at `~/.config/home-manager` importing a
published Foundation release through `latest-release`. Foundation owns the shared modules and dependency
pins; you own `profile.json`, `customize.nix`, and `modules/local.nix`.

The constructor is also available to other consumers:

```nix
inputs.foundation.lib.mkHomeConfiguration {
  profile = builtins.fromJSON (builtins.readFile ./profile.json);
  modules = [./customize.nix ./modules/local.nix];
  extraInputs = builtins.removeAttrs inputs ["self" "foundation"];
}
```

Use schema 2 profiles with Bluefin or Bluefin DX, generic or Dell XPS 9350 Intel
hardware, and any combination of the roles and optional packages in
`lib.catalog`. Account identity must match the desktop user. Keep
`home.stateVersion` unchanged when updating.

## Updates and migration

New personal flakes track `github:closure-labs/foundation/latest-release`.
This branch advances only to published stable releases with passing CI, never
unreleased `main` commits. `flake.lock` still records the exact commit and source
hash, so switching without an update keeps the same version.

`nh home switch -u` updates the lock to the latest release and activates it.
It updates all flake inputs; use `nh home switch -U foundation` to update only
Foundation. Keep workstation-specific sources pinned in your personal modules.
These direct NH commands use NH's build and activation path; Foundation's staged
updater below additionally provisions shared Brew tools and backs up consumer files.

To opt an existing consumer into release tracking, change only its Foundation URL
in `flake.nix` to `github:closure-labs/foundation/latest-release`, then update the
Foundation input. Existing fixed-commit consumers remain supported.
Foundation commands read the selected version from `flake.lock` even when an NH
update leaves the cached `foundation.json` at an older version.

`finite-home-update --check` reports published releases. `finite-home-update`
stages a new release, builds with a 3 GiB memory limit, provisions required shared
Homebrew tools, backs up the configuration and activates the generation. Finite
also includes this step in explicit `ujust update` runs. Background checks only
notify. Root execution is rejected.

Set an explicit build budget when a larger profile needs it, for example
`FOUNDATION_BUILD_MEMORY_MAX=5G finite-home-update`. This keeps the one-job,
one-core and 512 MiB swap limits; the default remains 3 GiB.

Personal inputs and modules remain local. Release metadata and `flake.lock` pin
the exact source and dependency closure. Unsupported compatibility versions or
failed builds leave the current configuration in place. An activation failure
restores the configuration and attempts the previous generation's activation;
external Homebrew and Flatpak side effects are not transactional.

`finite-home-migrate --check` builds a migration without installing it.
`finite-home-migrate` adopts Foundation's tested dependency pins while preserving
the profile, personal modules and additional inputs. Modified upstream modules,
custom output functions, Git checkouts and symlink roots require manual migration.
Backups remain next to the configuration as `home-manager.previous.*`.

`finite-configure` selects roles and optional packages; `finite-home-apply` builds
and applies those profile changes using the same transaction. `nh home build`
and `nh home switch` remain available for direct use.

The flake and its lock determine the Home Manager package set. Activation adds
that already-built set to the user Nix profile, which exposes its commands on
`PATH`; this step does not select new package versions. Foundation uses
`nix profile add` when available, with compatibility for older Nix.

Keep private Git-backed Espanso declarations in personal modules; see
[the snapshot workflow](docs/ESPANSO.md). Foundation defaults contain no private
sources or workstation matchfiles.

## Standalone checkout

The repository root still exports `homeConfigurations` from its own profile and
personal modules. Set `profile.json` to your account, build before activation,
and use the checkout's `modules/finite-home-apply` helper to provision shared Brew
tools and activate. Standalone maintainers update their Git checkout explicitly;
release-update commands target importing personal flakes.

The Support role's Espanso backend requires administrator-managed keyboard access.
On non-NixOS hosts, run the generated `non-nixos-gpu-setup` helper after first
activation as described by Home Manager. Foundation never grants keyboard access.

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
protection setup and the release checklist. Version tags prepare a draft
GitHub release after CI passes. Weekly workflows propose reviewed Nix lock and
GitHub Actions updates.

## License

Apache License 2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). The bundled Zsh
assets retain their original MIT license. See [CHANGELOG.md](CHANGELOG.md) for
release notes and [SECURITY.md](SECURITY.md) for vulnerability reporting.
