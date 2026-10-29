# Bluefin user environment ownership

`hosts/os/bluefin` is selected by both `foundation = "bluefin"` and
`foundation = "bluefin-dx"`, for supported profiles.
`host.system` remains the architecture field. Generic `home/base` has no Brew
policy, provider preflight or shell precedence override.

The [dated ownership inventory](ownership/bluefin-2026-10-27.json) records the October 27
baseline, not an ownership policy for every Bluefin version. It records every
application descriptor and user configuration source. It joins both exact Finite
base-image digests to upstream source `339a46a`, native build 40432110222, and the
immutable common/Brew image inputs in that build's two main-image jobs. The common
image's authenticated chunk index and individual content hashes identify the
shipped files; current upstream main and installed package lists are not used as
ownership evidence. The small Brew setup layer was independently hash-verified.
The final boot/activation check against these bases remains a hosted requirement.

The subsequently verified stock CLI bundle from
[projectbluefin/common at `434daa4`](https://github.com/projectbluefin/common/blob/434daa4115864cdc5350d660da2299702887fedb/system_files/shared/usr/share/ublue-os/homebrew/cli.Brewfile)
contains all 20 copied-policy formulas, including `valkyrie00/bbrew/bbrew`,
`ugrep` and `uutils-coreutils` (file SHA256
`5302f8fdec72d2db85c32d8a721754f74b6bc1927df7928853f6d26e5d353bb0`).
This corrects the dated inventory's classification
of those three as Finite additions: the Bluefin aspect now leaves them to the
inherited bundle rather than installing duplicate Nix packages.
That CLI hash does not establish the contents of other preinstall bundles or
transitive dependencies; those are not changed or inferred here.

| Declaration | Owner and treatment |
| --- | --- |
| Inherited `cli.Brewfile` (20 formulas in the verified stock revision above) | Bluefin Brew binaries and defaults |
| Other inherited preinstall bundles | Bluefin preinstall mechanism; not duplicated or replaced by this change |
| Existing Fzf shell bindings and Starship prompt | Explicit Finite configuration, without a second binary |
| bbrew, ugrep, uutils-coreutils | Inherited Bluefin CLI bundle; no automatic duplicate Nix packages |
| Existing 60 application descriptors | Existing Nix/Flatpak provider choices retained |
| User services, desktop and hardware-specific settings | Home Manager declarations |
| Root services, mounts/sockets, SELinux and bootc plumbing | OS image |

The pinned Home Manager Fzf module always installs its package and has no
config-only option. The Bluefin aspect therefore declares only its Zsh integration
using the upstream Fzf binary. Finite's explicit devops settings stay in managed
files. Upstream shell defaults and optional bundles are otherwise preserved.
No unmanaged Flatpak removal is enabled. System Flatpaks and unrelated user apps
remain outside Foundation's ownership.

This removes only the Bluefin aspect's automatic package contribution. Other
OS aspects and explicitly selected personal Nix packages are not filtered or
removed. Existing shell integration and stock-bundle preparation remain intact;
there is no automatic Brew uninstall or user configuration migration. FINite's
Foundation pin must be advanced separately after this change is merged and
validated; changing Foundation alone does not update an existing FINite image.

The generic initializer realizes one generation, optionally executes its fixed
`foundation-prepare` entry, commits configuration, then activates once. The entry
is installed with pinned Home Manager's `home.extraBuilderCommands` interface.
Build-only checks never execute preparation or activation. Preparation waits for
Bluefin's root Brew seed, joins the inherited user `brew-preinstall.service` when
present, and ensures only the inherited CLI bundle with no-upgrade installation.
It does not toggle `ublue-bling`, replace a user config or select optional bundles.
A failed preparation leaves the configuration transaction uncommitted.

`providers/homebrew` remains a deprecated feature alias for `hosts/os/bluefin`.
The old `finite-brew-bootstrap`, migration checker and copied policy remain only
for compatibility/manual historical diagnostics. The generic initializer and
normal aspect no longer call them. Do not use their 20-entry list as a removal
list: the dated inventory found 17 overlaps for its particular stock bundles,
while the verified stock revision above contains all 20. The inventory does not authorize removal
of any installed package.

Release/pin adoption, both profiles' fresh-install and upgrade/rollback checks,
workstation activation and cleanup are subsequent gates. No performance savings,
completed pilot, stable release or paired publication follows from source tests.
