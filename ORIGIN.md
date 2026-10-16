# Source

Extracted on 2026-10-16 from `~/projects/finite/templates/home-manager/` at
Finite commit `891a6ccf66765004310c49a216efd17a9cf0fd40`.

The complete template, including hidden Zsh assets and `flake.lock`, was copied
to this repository's root. The Homebrew provider and Dell panel-policy fixture
tests were copied from Finite's `tests/home/` and adjusted for the new layout.

Foundation owns future changes independently. Its flake has no input referencing
Finite and no dependency on the source checkout. Runtime `finite-*` names,
profile schemas, the template compatibility marker and `home.stateVersion` are
preserved. The bundled Zsh assets retain their original license file.

This repository is intended to become Finite's default Home Manager flake.
Adoption by Finite is a separate integration step; the flake also supports
standalone checkouts.

Repository-specific changes add build checks and documentation and exclude VCS
metadata and generated results when staging a configuration for application.
