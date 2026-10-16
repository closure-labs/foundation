# Changelog

User-facing changes to Finito are recorded here. Version numbers follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); during the `0.x`
series, minor releases may change configuration interfaces.

## [Unreleased]

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

[Unreleased]: https://github.com/closure-labs/foundation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/closure-labs/foundation/releases/tag/v0.1.0
