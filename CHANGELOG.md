# Changelog

User-facing changes to Foundation are recorded here. Version numbers follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); during the `0.x`
series, minor releases may change configuration interfaces.

## [Unreleased]

- Keep policy and configuration-root contract tests enabled for focused changes to their shared implementation owners, rather than relying only on default profile evaluations.
- Align NH’s Home Manager location with the XDG config home and add optional `foundation.configRoot` for a shared explicit path. Preserve runtime CLI overrides and leave existing configuration files in place.
- Add a typed constructor package policy shared across stable, weekly and unstable Nixpkgs. Unfree packages remain allowed by default; explicit deny and allowlist modes fail clearly without dropping selected services.
- Advance stable Home Manager and Nixpkgs through their owning modules, with source declarations, lockfile and generated artifacts kept together and restored on update failure. Repair the public generic-x86_64 hardware alias.

- Deliver explicit Foundation updates from `main` without waiting for a version release or maintaining a `latest-release` branch. Consumer locks retain immutable revision and content-hash provenance; staged updates qualify the exact commit, preserve personal inputs and retain build-before-activation recovery. Version tags remain optional milestones.

- Remove legacy home-profile schema-2 readers, catalogs, composition and conversion paths. Home profiles must use schema 3; unsupported persisted profiles fail with replacement guidance before build or activation. See [Migration](docs/MIGRATION.md) before updating an older consumer.


## [0.5.1] - 2026-10-27

- Repair the exported Home Manager consumer-template builder so the initialization helper can import its observation module from the packaged source tree.
- Build the actual consumer-template export in the full hosted check set, catching packaging failures before a Foundation release is adopted by Finite. Preserve complete release provenance and the existing helper-isolation checks.

## [0.5.0] - 2026-10-27

- Preserve Bluefin's inherited stock CLI/preinstall bundles, configuration and update mechanisms through a dedicated `hosts/os/bluefin` aspect for both Bluefin profile names and supported profile schemas.
- Realize one Home Manager generation, run its optional `foundation-prepare`, commit configuration and activate once. Build-only checks skip preparation and activation; personal modules, rollback and profile formats remain preserved.
- Keep Bluefin's Fzf and Starship binaries with explicit Finite configuration. Declare bbrew, ugrep and uutils-coreutils through pinned Nixpkgs inputs; retain existing catalog providers and unmanaged Flatpaks.
- Observe supported Nix build/substitution activity and overlap, separate client/shared-daemon resources, inherited Brewfile/cache state, and actual synchronous Flatpak/service work. Keep evaluation coverage unknown, existing resource budgets and activation readiness; no performance savings are claimed.
- Retain deprecated Brew helper compatibility paths without calling their copied policy during ordinary initialization. Workstation cleanup remains a separate reviewed, manual operation.

## [0.4.1] - 2026-10-27

- Refresh locked Den, Home Manager, Determinate Nix and Nixpkgs dependencies, and update the CI Nix installer action to v3.24.0.

- Shorten CI for verified same-major GitHub Action pin updates: retain workflow lint, fixtures and Nix smoke builds while skipping the full profile matrix. Runtime dependency and workflow logic changes retain full validation.

- Restore usable Intel IPU7 camera formats when a stale host IPA processing module prevents Firefox from finding the webcam. The new hardware-detected aspect verifies the matching host module before configuring a per-user repair during activation.
- Add `foundation home camera` and the native `#home-camera` app for diagnosis and explicit repair. Build-only checks report camera health; repairs preserve personal overrides and never restart live audio automatically.
- Add a focused camera guide covering diagnosis, repair, service restart, Firefox verification and undo steps.

## [0.4.0] - 2026-10-27

- Replace installed `finite-*` home helpers with `foundation home <action>`, including build-only `foundation home check`. Run the same interface through the native default flake app or `#foundation`; individual home apps remain available.

- Make Foundation easier to configure with focused setup, profile, activation and recovery guides, a shorter README, and a single documentation index.
- Keep application and role definitions together so contributors can add features without updating separate catalogs. Existing profiles, application providers and personal configuration files remain compatible.
- Select affected CI evaluations and build checks from declared feature dependencies, with full validation when the base result or dependency graph cannot be verified. Check generated configuration and architecture files for drift.

- Add opt-in `FOUNDATION_TIMINGS=1` observations for staged profile validation, Home Manager realization, Brew policy/bootstrap, activation and rollback, including failed stages. Preserve resource budgets, command order and one initialization; internal Nix fetch/build and Flatpak durations remain unresolved.

## [0.3.3] - 2026-10-23

- Install the Home Manager CLI alongside NH in the shared base configuration so new Finite homes can run `home-manager switch`.
- Reject release preparation when `foundation.json` is missing, invalid or disagrees with `VERSION`, catching metadata errors before publication and stable-channel advancement.

## [0.3.2] - 2026-10-23

- Keep wrapper, signal and usage exits terminal even when a transient download diagnostic precedes them. Retry only Nix's ordinary failure exit 1 with verified transport diagnostics, within the existing attempt and deadline limits.
- Include the interrupted-download recovery, realization memory budget and private module refactor prepared for 0.3.1. That tagged preparation remains unpublished because release review found the wrapper-exit regression before publication.

## [0.3.1] - 2026-10-23

- Retry interrupted Home Manager realization downloads within one 15-minute deadline, with at most three attempts and two/four-second backoff. Retry HTTP 416 only after interrupted-resume evidence for the same URL. Keep authorization, integrity, evaluation and build failures terminal; preserve existing configuration and retry neither initialization nor activation.

- Organize shared Home Manager settings into private browser, desktop, Homebrew, shell and legacy application modules while retaining the base aspect, application selection, providers and ordered startup behavior.

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

[Unreleased]: https://github.com/closure-labs/foundation/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/closure-labs/foundation/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/closure-labs/foundation/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/closure-labs/foundation/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/closure-labs/foundation/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/closure-labs/foundation/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/closure-labs/foundation/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/closure-labs/foundation/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/closure-labs/foundation/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/closure-labs/foundation/releases/tag/v0.2.0
[0.1.0]: https://github.com/closure-labs/foundation/releases/tag/v0.1.0
