# Schema-3 application composition contract

Status: A1 executable draft, 2026-10-20. Implemented in
[`lib.profileDrafts`](../../lib/profile-drafts/default.nix), separate from the
production normalizer, constructor, catalog and writers. It does not enable
schema-3 activation or install these applications. Follow
[the staged plan](../plans/PLAN-profile-refactor.md) for rollout.

## Why a schema change helps

Classification alone needs no profile schema change: a selected work role
already implies Professional. Smaller defaults do change the meaning of an
existing selection. Schema 3 makes that boundary explicit; schema 2 keeps its
existing application declarations and providers. No roles in schema 3 means
shared essentials, rather than today's broad shared app bundle.

Keep the current fields and add optional, explicitly selected `capabilities`:

```json
{
  "schema": 3,
  "foundation": "bluefin",
  "hardware": "generic-x86_64",
  "identity": {"username": "dale", "homeDirectory": "/var/home/dale"},
  "roles": ["developer", "creative"],
  "packages": ["jj"],
  "capabilities": ["recording"]
}
```

Missing capabilities normalize to `[]`. Explicit selections must be valid and
unique; normalization preserves unknown fields and sorts known selections by
registry order. Account identity and hardware keep their current shapes. H1
owns later form-factor, CPU/GPU and model decomposition.

Derive classifications from roles, and effective capabilities from shared
defaults, declared hardware, roles and explicit capabilities. Persist neither
derived result: it would retain stale defaults when a role changes. Keep role
IDs stable and individually selectable. No category toggle, `profiles` field,
new Den class or custom entity kind is needed.

## Defaults and complete application ownership

The [data registry](../../lib/profile-drafts/contract.nix) is authoritative.
All roles receive `essentials` and `desktop-tools` once. Multiple selections
compose through a deduplicated union; there are no class-wide application sets.

| Classification | Role | Default capabilities beyond shared defaults |
| --- | --- | --- |
| Professional | Developer | devops, development |
| Professional | Sales | office, mail |
| Professional | Trainer | office, presentations, image-editing, trainer-links |
| Professional | Support | devops, support-tools |
| Professional | Executive | office, mail, executive-links |
| Professional | IT | remote-desktop |
| Personal | Family | office, mail |
| Personal | Media | playback |
| Personal | Creative | image-editing |
| Personal | Gaming | casual-games |

Capabilities also permit individual additions: a Trainer can add recording
without selecting Creative.

| Capability | Applications | Default source of selection |
| --- | --- | --- |
| essentials | Firefox, Neovim, Bitwarden desktop and CLI | Shared |
| desktop-tools | Flatseal, Extension Manager, Ignition, Warehouse, Impression, Mission Center, Gear Lever, Refine | Shared |
| office | LibreOffice | Sales, Trainer, Executive, Family |
| mail | Thunderbird | Sales, Executive, Family |
| team-chat | Element | Explicit |
| file-sync | Nextcloud client | Explicit |
| notes | Joplin | Explicit |
| playback | VLC | Media |
| image-editing | Pinta, Gradia | Trainer, Creative |
| presentations | Marp | Trainer |
| devops | Ghostty, Ansible, OpenBao, OpenTofu, Packer, DistroShelf | Developer, Support |
| development | devenv, rustup, cargo-audit, cargo-edit, cargo-watch, VSCodium | Developer |
| support-tools | Espanso, RustConn | Support |
| remote-desktop | RustDesk | IT |
| trainer-links | Existing Grist desktop entry | Trainer |
| executive-links | Existing Vates Notes desktop entry | Executive |
| chromium | Chromium | Explicit |
| camera-controls | Camera controls | Declared camera-equipped hardware, or explicit |
| web-apps | Spider web-app installer | Explicit |
| desktop-comforts | Damask, Smile | Explicit |
| pdf-tools | IceBox PDF/image conversion | Explicit |
| casual-games | GNOME Chess, GNU Chess engine | Gaming |
| painting | Krita | Explicit |
| video-editing | Kdenlive | Explicit |
| modeling | Blender | Explicit |
| recording | OBS Studio | Explicit |
| jellyfin | Jellyfin Desktop | Explicit |
| audio-player | GNOME Audio Player / Decibels | Explicit |
| steam | Steam | Explicit |
| heroic | Heroic | Explicit |
| lutris | Lutris | Explicit |

The five existing optional package IDs (`hack-font`, `herdr`, `jj`, `opencode`,
`uv`) retain their own selections and sources. Shared infrastructure retains
Foundation helpers, Brew policy, shell/editor integration, fonts/XDG, generic
Linux integration, role flags and Dell panel/IPU7/Firefox configuration.

The Dell model supplies camera controls; generic hosts can select the capability
explicitly. Pure evaluation does not probe the evaluating machine's camera.
Chromium is optional on every new profile. Schema 2 retains both applications
as before. No role infers a server, account, sync root, game download or
credential. Family does not imply a shared account or child-management policy.
The chess engine is declared explicitly; engine discovery and gameplay still
need a session test before rollout.

## Package providers and graphics

Prefer graphical Nixpkgs packages with nixGL on this non-NixOS host. Official
or verified Flathub distributions are allowed exceptions; Flathub availability
alone is insufficient. This draft uses Nix wherever an appropriate package
exists in the locked sources. All 53 Nix declarations, including
`kdePackages.kdenlive`, are checked by the
[locked provider fixture](../../tests/draft-providers.nix). Existence is not a
build, feature-parity, sandbox or physical graphics test.

Preserve current native source choices, including weekly Firefox/office clients,
unstable Herdr, and configured Firefox/Ghostty recipes. For the new format,
14 existing Flatpak apps have Nix alternatives. Missing Nix packages retain:

| Application | Flathub ID | Recorded verification |
| --- | --- | --- |
| Flatseal | `com.github.tchx84.Flatseal` | GitHub publisher tchx84 |
| Damask | `app.drey.Damask` | Website drey.app |
| IceBox | `io.github.pleromix.IceBox` | GitHub organization pleromix |
| Spider | `io.github.zaedus.spider` | GitHub organization zaedus |
| RustConn | `io.github.totoshko88.RustConn` | GitHub publisher totoshko88 |

The [verification snapshot](../../lib/profile-drafts/flathub-verification.json)
records public Flathub API endpoints and the 2026-10-20 check date. Resolution
rejects a Flatpak without a positive record. Recheck publisher status and package
availability before enabling writers; ordinary tests use the snapshot. Nixpkgs
`spider` is a different web crawler. Verification records publisher association,
not a security audit.

Use Home Manager's [nixGL integration](https://github.com/nix-community/home-manager/blob/master/modules/targets/generic-linux/nixgl.nix)
and [non-NixOS graphics guidance](https://github.com/nix-community/home-manager/blob/master/docs/manual/usage/gpu-non-nixos.md).
The intended Intel/AMD path is Mesa via [nixGL](https://github.com/nix-community/nixGL).
F1b must:

1. Pin nixGL and align its Nixpkgs input with the selected package family where
   possible. Set non-null `targets.genericLinux.nixGL.packages` and the Mesa
   default wrapper. A null package set makes wrapping a no-op.
2. Explicitly disable `targets.genericLinux.gpu.enable` for schema 3: existing
   base code sets it true, and adding nixGL alone does not override it. Preserve
   the schema-2 backend.
3. Wrap selected graphical Nix packages with `config.lib.nixGL.wrap`, retaining
   configured recipes and desktop/D-Bus/service launch paths. Keep CLI tools,
   shell sessions and Flatpaks outside wrappers. `wrappedApplicationIds` is the
   intended list, not evidence of installed wrappers.
4. Leave Vulkan and discrete-GPU offload explicit until H1 supplies tested
   choices. Do not export global graphics-library paths, install host drivers,
   or add NVIDIA work.
5. Validate Wayland/XWayland launches, browser-to-host viewers/`xdg-open`, media
   acceleration, cameras, recording and requested gaming paths in physical
   sessions. Wrapper environment inheritance can affect launched host apps;
   Steam/Wine/FHS launchers need individual checks. Retain backend rollback.

## Preview and migration

`lib.profileDrafts.normalize` validates draft JSON; `resolve` produces derived
classes, capabilities, app identities, provider-qualified declarations and the
planned graphics backend. `resolveLegacy` models schema-2 declarations.
`previewMigration { profile; roles ? null; capabilities ? []; }` compares them
without writing or activating. This is a draft API, not a production
compatibility promise.

Evaluate a preview from the repository root:

```bash
nix eval --impure --json --no-update-lock-file --expr '
  let f = builtins.getFlake ("path:" + toString ./.);
  in f.lib.profileDrafts.previewMigration {
    profile = builtins.fromJSON (builtins.readFile ./profile.json);
    roles = ["family" "media"];
    capabilities = ["file-sync"];
  }'
```

Results always set `activationAllowed = false`. Application changes are separate
from provider-qualified declaration changes, same-app provider changes and the
graphics transition. Identity, hardware, packages and unknown fields survive.
If schema 2 already contains a custom `capabilities` field, preview blocks with
the original value and no candidate; even `[]` or `null` is never repurposed.

Removing a Flatpak declaration may leave it installed under existing unmanaged
preservation; preview lists those declarations. No unmanaged uninstall, app-data
deletion or automatic transfer between Flatpak and native storage is permitted.
A2 needs app-specific transfer and desktop/MIME handling where appropriate,
particularly browsers, mail, Joplin and game clients. Review concrete provider
changes before activating migration; the user's provider preference authorizes
implementation of this design.

Restore source lock and schema-2 profile together when returning to an older
schema-2-only source. Use the prior Home Manager generation for failed
activation. Source reversion alone neither moves application data back nor
undoes external provider effects.

## Delivery boundaries

- **A1, this change:** isolated contract, resolver, migration preview, complete
  legacy declaration inventory, provider checks and focused tests/documentation.
- **F1b, next:** production dual normalization/composition and actual nixGL
  wrappers; helpers, selector read paths and Finite readers accept schema 3
  while generators still emit schema 2. Capability advertising follows actual
  support and rejects incompatible helper/source pairs.
- **A2:** negotiated schema-3 selection/writing, explicit migration and recovery.
  Only then expose Personal choices through the production catalog/selector.

Production remains six roles, profile schema 2, catalog schema 3, compatibility 1
throughout A1. The current generator enumerates catalog roles and emits schema
2; adding Personal roles there now would produce incompatible data. Additive
draft metadata needs no catalog schema 4; revisit the version only if an actual
breaking contract is necessary. Hardware schema refactoring remains separate.
