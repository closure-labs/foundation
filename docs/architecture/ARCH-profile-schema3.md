# Schema-3 application composition contract

Status: F1b reader/composition bridge and A2 editor/conversion implemented,
2026-10-20. The public
normalizer and constructor accept explicitly supplied schema 3, backed by the
[composition resolver](../../lib/profile-drafts/default.nix) and
[application module](../../modules/aspects/profile-composition.nix). Default
generators/catalogs stay schema 2; conversion is explicitly reviewed. Follow
[the staged plan](../plans/PLAN-profile-refactor.md) for rollout.

## Why a schema change helps

Classification alone needs no profile schema change: a selected work role
already implies Professional. Smaller defaults do change the meaning of an
existing selection. Schema 3 makes that boundary explicit; schema 2 keeps its
existing application declarations and providers. No roles in schema 3 means
shared essentials, rather than today's broad shared app bundle.

Schema 3 adds explicitly selected `capabilities` and the structured
[H1 host declaration](ARCH-host-composition.md):

```json
{
  "schema": 3,
  "foundation": "bluefin",
  "host": {"formFactor": "desktop", "cpu": "amd", "gpus": ["amd-integrated"]},
  "identity": {"username": "dale", "homeDirectory": "/var/home/dale"},
  "roles": ["developer", "creative"],
  "packages": ["jj"],
  "capabilities": ["recording"]
}
```

Missing capabilities normalize to `[]`. Explicit selections must be valid and
unique; normalization preserves unknown fields and sorts known selections by
registry order. Account identity keeps its current shape. H1 normalizes host
dimensions and derives the old hardware adapter; new declarations can omit it.

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

Declaring `host.camera = true` supplies camera controls on any equipped host;
the capability can also be selected explicitly. Pure evaluation does not probe
the evaluating machine's camera.
Chromium is optional on every new profile. Schema 2 retains both applications
as before. No role infers a server, account, sync root, game download or
credential. Family does not imply a shared account or child-management policy.
The chess engine is declared explicitly; engine discovery and gameplay still
need a session test before rollout.

## Package providers and graphics

Prefer graphical Nixpkgs packages with nixGL on this non-NixOS host. Official
or verified Flathub distributions are allowed exceptions; Flathub availability
alone is insufficient. Schema 3 uses Nix wherever an appropriate package
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
The reader bridge implements the first four requirements below; physical
application/session validation remains a rollout requirement:

1. Pin nixGL and align its Nixpkgs input with the selected package family where
   possible. Set non-null `targets.genericLinux.nixGL.packages` and the Mesa
   default wrapper. A null package set makes wrapping a no-op.
2. Explicitly disable `targets.genericLinux.gpu.enable` for schema 3: existing
   base code sets it true, and adding nixGL alone does not override it. Preserve
   the schema-2 backend.
3. Wrap selected graphical Nix packages with `config.lib.nixGL.wrap`, retaining
   configured recipes and desktop/D-Bus/service launch paths. Keep CLI tools,
   shell sessions and Flatpaks outside wrappers. Actual composition is evaluated
   against `wrappedApplicationIds`; a synthetic app is built and launched through
   the pinned wrapper, with desktop, D-Bus and systemd paths checked. This does
   not establish physical rendering or every app's runtime compatibility.
4. Leave Vulkan and discrete-GPU offload explicit. H1 GPU declarations do not
   enable either. Do not export global graphics-library paths, install host drivers,
   or add NVIDIA work.
5. Validate Wayland/XWayland launches, browser-to-host viewers/`xdg-open`, media
   acceleration, cameras, recording and requested gaming paths in physical
   sessions. Wrapper environment inheritance can affect launched host apps;
   Steam/Wine/FHS launchers need individual checks. Retain backend rollback.

## Preview and migration

`lib.normalizeProfile` accepts schemas 2/3. `lib.resolveProfile` produces derived
classes, capabilities, app identities, provider-qualified declarations and the
graphics policy for schema 3. The retained `lib.profileDrafts.resolveLegacy`
models strictly schema-2 declarations.
`previewMigration { profile; roles ? null; capabilities ? []; }` compares them
under `lib.profileDrafts` without writing or activating. The controller/editor
uses the versioned `lib.profileChanges` API described in
[ARCH-profile-editor](ARCH-profile-editor.md).

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
A2 preserves original app data and documents manual export/import, account sync
and desktop/MIME checks, particularly for browsers, mail, Joplin and game clients.
Review concrete provider
changes before activating migration; the user's provider preference authorizes
implementation of this design.

Restore source lock and schema-2 profile together when returning to an older
schema-2-only source. Use the prior Home Manager generation for failed
activation. Source reversion alone neither moves application data back nor
undoes external provider effects.

## Delivery boundaries

- **A1, complete:** contract, resolver, migration preview, complete
  legacy declaration inventory, provider checks and focused tests/documentation.
- **F1b, implemented:** production dual normalization/composition and actual nixGL
  wrappers; helpers, selector read paths and Finite readers accept schema 3
  while generators still emit schema 2. Capability advertising follows actual
  support and rejects incompatible helper/source pairs.
- **A2, implemented:** negotiated schema-3 editing/writing, explicit conversion,
  exact reviewed-preview binding and symlink-preserving recovery. The schema-3
  editor exposes Personal roles; default generators remain schema 2.
- **H1, implemented:** independent host form factor, Intel/AMD CPU/GPU and model
  aspects; camera presence and laptop-only preferences. Migration planning now
  targets this workstation alone, while Foundation's refactor remains broad.

The bridge advertises initialize schemas 1/2/3 and normalize schemas 2/3 with
default write schema 2 and explicit `editSchemas = [2, 3]`. Schema 3 requires an explicit selected-source capability
descriptor; historical descriptor absence cannot imply support. Normalization
cannot change a submitted schema. Initialization preserves supplied capabilities,
custom fields and schema 3, while schema 1 retains its explicit conversion to 2.

`homeCatalogForSchema 2` equals the default six-role `homeCatalog`.
`homeCatalogForSchema 3` adds Personal roles and capabilities only for readers
requesting that format. Catalog schema remains 3 and compatibility remains 1.
`finite-configure` edits schema 3 only when the running helper and locked target
support the editor API; older targets require an input update first. Capability
checkboxes reflect explicit selections, with defaults still derived. Legacy input adoption rejects
a personal `nixGL` name collision before filtering or rebasing its pin/followers.
Host fields and model behavior follow the H1 contract linked above.
