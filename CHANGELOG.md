# Changelog

User-facing changes to Foundation are recorded here. Version numbers follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); during the `0.x`
series, minor releases may change configuration interfaces.

## [Unreleased]

- Raise the default staged Home Manager build memory limit to 5 GiB after the full schema-3 workstation exceeded the prior 3 GiB limit. Preserve explicit budgets and existing CPU/job/core/swap limits; report killed builds with journal and budget guidance without retrying or activating a candidate.

## [0.3.0] - 2026-10-21

- Generate new schema-3 profiles in JSON or YAML with six Professional roles and four lightweight Personal roles: Family, Media, Creative and Gaming. Optional capabilities select larger applications without enabling an entire role.
- Default new templates and catalogs to schema 3. Existing schema-2 profiles retain their applications, providers and graphics backend; conversion remains explicit.
- Make newly copied personal profile and module files editable when generated from an immutable source, preserving existing personal files and permissions.
- Prefer graphical Nixpkgs applications wrapped with nixGL Mesa for schema 3, retaining verified Flathub exceptions where a matching Nix package is unavailable. Clean icon build files that otherwise collide in wrapped desktop packages.
- Compose laptop/desktop hosts independently from Intel/AMD CPU, integrated/discrete GPU and model aspects, with camera-aware controls and laptop-only preferences. Bluefin continues to own drivers, firmware, authentication and power/lid policy.
- Edit roles, packages and capabilities through the locked Foundation revision. Explicit schema-2-to-3 conversion previews application/provider changes, binds approval to the reviewed state, preserves unmanaged Flatpaks and data, and retains build-only checks, backup and activation recovery.
- Share pure Nix profile validation across composition, generation and staged writes. Reject duplicate/unknown selections, unsupported reader/writer combinations, silent format changes and conflicting legacy personal nixGL inputs; preserve symlink entries during failed operations.
- Expose format-specific catalogs, host choices and initializer/editor capabilities. Explicit schema-2 reader views identify their format independently of the source's preferred writer.
- Accept explicitly pinned local Git Foundation inputs for workstation editing, verify locked-source metadata, and report manual pin maintenance without replacing them with published releases.
- Update Den to the reviewed October revision and align gen with its tested CI pin, preserving unrelated package sources and current profile composition.
- Select Herdr from a separately locked `nixpkgs-unstable` input so terminal fixes can be updated without moving shared desktop dependencies.
- Export the managed Zsh executable to terminal multiplexers, including sessions whose account login shell is Bash.
- Keep desktop data search paths stable across user service manager reloads while retaining Flatpak exports.

## [0.2.2] - 2026-10-16

- Track published stable Foundation releases through the `latest-release` branch, keeping exact source and dependency pins in `flake.lock`.
- Advance the release branch only after publication, metadata validation and successful CI, with a manual recovery workflow.
- Support `nh home switch -u` in personal consumers and read the locked source when cached provenance is stale.
- Preserve release-channel declarations during staged updates and retain support for existing fixed-commit consumers.

## [0.2.1] - 2026-10-16

- Use `nix profile add` during Home Manager activation when supported, retaining compatibility with older Nix and legacy profiles.
- Preserve the flake-built package set and upstream activation ordering without changing dependency pins.
- Allow an explicit per-command build memory budget while retaining the 3 GiB default and job, core and swap limits.

## [0.2.0] - 2026-10-16

- Export a reusable Home Manager constructor, canonical catalog and offline consumer template.
- Keep personal profiles and modules separate from the Foundation source dependency.
- Add staged migration, bounded builds, release updates, backups and activation rollback.
- Supply profile, apply and release-notification commands from Foundation.
- Preserve workstation-specific Git snapshots in personal modules; no personal sources are defaults.

## [0.1.0] - 2026-10-16

### Added

- Home Manager flake extracted from Finite, intended as Finite's default Home
  Manager configuration while supporting standalone use, with pinned
  dependencies and source provenance in `ORIGIN.md`.
- Configurable Bluefin and Bluefin DX profiles for x86_64 Linux, six combinable
  roles, optional packages, and generic or Dell XPS 9350 Intel hardware modules.
- Desktop, Flatpak, Homebrew provider, shell and editor configuration, retaining
  the existing `finite-*` helper commands and profile schema.
- Staged Home Manager builds and a check-only apply mode before provisioning
  shared Homebrew tools and activating a generation.
- Fixture checks for Homebrew providers, Dell display policy and staged home
  application, plus Nix evaluation and activation-package build checks.
- GitHub CI with a required-check entry point, dependency update automation,
  and a validated draft release workflow with source archives and checksums.
- Apache-2.0 licensing, preserved third-party license notices, contributor and
  security guidance, and a release checklist.

### Compatibility

- Requires x86_64 Linux with Bluefin or Bluefin DX, Nix with flakes, and Homebrew
  at `/home/linuxbrew/.linuxbrew`; graphical helpers also need a desktop session.
- The example `finite` account in `profile.json` must be customized before use.
- Existing runtime names, profile schemas and `home.stateVersion` are preserved.
- Finite must adopt a reviewed release separately; this release does not change
  the consuming Finite repository.

[Unreleased]: https://github.com/closure-labs/foundation/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/closure-labs/foundation/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/closure-labs/foundation/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/closure-labs/foundation/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/closure-labs/foundation/releases/tag/v0.2.0
[0.1.0]: https://github.com/closure-labs/foundation/releases/tag/v0.1.0
