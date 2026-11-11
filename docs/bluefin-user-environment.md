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
upstream/user choice rather than installing duplicate Nix packages.
That CLI hash does not establish the contents of other preinstall bundles or
transitive dependencies; those are not changed or inferred here.

| Declaration | Owner and treatment |
| --- | --- |
| Inherited `cli.Brewfile` (20 formulas in the verified revision above) | Optional upstream bundle; Foundation neither installs nor checks it |
| Other inherited preinstall bundles | Bluefin preinstall mechanism; not duplicated or replaced by this change |
| Existing Fzf shell bindings and Starship prompt | Explicit Finite configuration, without a second binary |
| bbrew, ugrep, uutils-coreutils | Optional upstream/user choice; no automatic Nix or Brew contribution |
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
removed. Existing shell integration is retained;
there is no automatic Brew uninstall or user configuration migration. FINite's
Foundation pin must be advanced separately after this change is merged and
validated; changing Foundation alone does not update an existing FINite image.

The generic initializer realizes one generation, optionally executes its fixed
`foundation-prepare` entry, commits configuration, then activates once. The entry
is installed with pinned Home Manager's `home.extraBuilderCommands` interface.
Build-only checks never execute preparation or activation. Preparation waits for
Bluefin's root Brew seed. On images shipping `brew-preinstall`, it synchronously
starts/joins that inherited user service and requires loaded, active/exited,
successful, non-condition-skipped state. The inherited default manifest directory must be
nonempty/readable and the session must not be a GDM greeter, avoiding upstream
script exit-zero skip paths. On the exact older image layout without
that service, it only observes `brew-setup.service`: successful inactive/dead is
expected, including a condition skip for already-seeded homes. It never starts a
root service or unrelated `ublue-user-setup` hooks. Missing/broken provisioning
fails clearly; there is no fallback installer. Seed and completion waits are
bounded to 120 seconds each; a user preinstall start is bounded to 600 seconds.
A client timeout fails preparation but does not cancel an OS-owned service.

Config-only Fzf integration uses the OS `/usr/bin/fzf` when present, otherwise
the upstream Homebrew binary. Preparation checks executable availability without
installing a second package. Bluefin alone owns default manifests, trust and
package reconciliation. Foundation never runs `brew bundle`, changes tap trust,
toggles `ublue-bling`, or selects optional bundles. Explicit personal packages and
optional opt-ins remain untouched. The old `bluefin-bundle` timing receipt is no
longer emitted: no optional manifest was provisioned. Existing
readiness/install/postcheck timing names are retained for consumer compatibility,
without manufacturing a Brewfile receipt.
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

Upstream distinguishes [automatic defaults from opt-in bundles](https://github.com/projectbluefin/common/blob/main/docs/skills/brew-lifecycle/references/package-set.md).
In particular, the `cli.Brewfile` is installed by the user's `ujust bluefin-cli`
opt-in, not by Foundation. This preparation entry belongs only to
`hosts/os/bluefin` (including the bluefin-dx selection); other OS aspects and the
generic initializer receive no new provisioning policy.

### Verified image lifecycle compatibility

The exact FINite #322 base manifests are Bluefin
`sha256:afe335088014cf0c20257c64d81a474ff683c9e6796a633ea8ebadee428d26e9`
and Bluefin DX
`sha256:4b7a467b6d5f0cd65075802ad2ec9d4a4bb16fedb8d602b688f3ba64d0ab0779`.
Read-only layer inspection verified neither ships `brew-preinstall` or
`preinstall.d`; do not substitute current common source for their contents.
Both ship `brew-setup.service` SHA256
`fc4341cafce6e208888d87458539a88d21c4cf22d2adb2d0af8f032265f10307`,
a root oneshot without `RemainAfterExit`, which skips already-seeded homes.
Both ship executable `/usr/bin/fzf` SHA256
`b3fc1d67bd84b71ea81d935f0ec683c3274ff47bb6c3dadcb327bb925ba5a0da`;
the inherited Homebrew seed contains no Fzf. Their `ublue-user-setup` hooks are
unrelated theming/GPG/hardware setup and are not a Brew readiness mechanism.
The newer preinstall-capable layout remains supported through its upstream
service rather than by copying its package or trust policy into Foundation.
