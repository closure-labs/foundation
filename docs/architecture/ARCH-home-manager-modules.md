# Shared Home Manager configuration

The public Den base aspect still imports
`modules/aspects/base/home.nix`. Its private sibling modules organize shared
Home Manager settings independently of role and host selection.

| Module | Ownership |
| --- | --- |
| `home.nix` | Module assembly, external Determinate/nix-flatpak imports, account defaults, state version, system Nix ownership and ordered shell startup hook |
| `browser.nix` | Weekly Firefox package, schema-dependent nixGL wrapper and existing Dell/camera policy |
| `desktop.nix` | Generic Linux/nixGL backend, fontconfig, XDG search paths, Flatpak service policy and activation service timeout |
| `homebrew.nix` | Shared CLI provider helper, Brew policy/Brewfile and pre-write-boundary activation check |
| `shell.nix` | Shared Fzf, Git, NH and Zsh enablement |
| `legacy-applications.nix` | Explicit schema-2 Nix and Flatpak application declarations |

Schema-3 application membership remains in the pure profile resolver and
`profile-composition.nix`. The shared modules do not select Professional or
Personal roles. They do not alter the host declaration or claim ownership of
Bluefin's drivers, authentication, firmware or system power policy.

These files are private implementation modules, not new Den aspect namespaces
or independently supported entry points. Consumers continue to use
`mkHomeConfiguration` and their additive personal modules.

## Ordering and provider boundaries

The shared Brew PATH hook stays at the original base entry point. Moving it
into a private imported module changes ordering among `mkBefore` shell blocks;
keeping the hook in place preserves the existing role and consumer startup
sequence. The shell module contains the shared program enables.

The legacy Flatpak list uses `mkAfter` to retain role-before-base declaration
order. Unmanaged applications remain preserved, unused runtimes may be removed,
and automatic application updates remain disabled.

Moving package declarations can change their list position. Package membership,
multiplicity, exact ordinary output paths and priorities remain unchanged;
the actual workstation package environment is built to check collisions.
The Brew helper stays Nix-owned while its policy continues to designate
Homebrew as the shared CLI provider.

The [refactor verification](../qa-reports/QA-home-manager-modules.md) records
actual before/after Home Manager evaluations, including this workstation's
personal modules. The module split does not change schema, state version,
dependency pins, application recipes or the active workstation generation.
