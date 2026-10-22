# Profile architecture and workstation review

Continuation: the user chose **classify first; split applications later**, and
reported that firmware has been updated manually. Follow the
[current architecture](architecture/ARCH-profile-refactor.md) and
[implementation plan](plans/PLAN-profile-refactor.md). They supersede this
review's original rollout order and immediate schema/application changes.
The [A1 schema-3 contract](architecture/ARCH-profile-schema3.md) supersedes the
candidate JSON and application/provider decisions below: retain the hardware
string, derive classifications, and add explicit capabilities rather than a
second persisted `profiles` selection.

Reviewed 2026-10-20. This document completes the architecture review and defines
the subsequent implementation. Proposed schemas and compositions below are not
implemented configuration. No host settings, dependency pins, activations, or
firmware were changed during the review.

## Findings and decisions

Foundation should keep standalone Home Manager, introduce composable
`professional` and `personal` selections, and separate those selections from
roles, machine form factor, CPU, GPU, and model-specific behavior. These are
profile categories, **not Den classes**: their output remains `homeManager`.
Use ordinary aspects and explicit includes first. A custom entity kind would
add a registry and policy routing without solving a current requirement.

All six existing work profiles, currently represented as roles, belong to
Professional: **Developer, Sales, Trainer, Support, Executive, and IT**. Preserve
their names, individual choices, and existing behavior under that classification.
Personal is the new peer category; do not leave the existing work profiles
unclassified or recreate them as unrelated bundles.

The requested Homebrew-before-Foundation ordering already exists. Finite's
wrapper calls Bluefin's complete update recipe before `finite-home-update`;
Homebrew is the last step in that underlying recipe. Preserve and test this
ordering rather than introduce a second update pipeline.

Firmware is managed by the host's existing fwupd/LVFS installation. The earlier
cached update list did not establish firmware currency. The user has since
reported a manual firmware update; no firmware operation is a refactor
prerequisite, and the old version observations below are historical.

### Evidence baseline

| Source | Revision or observation |
| --- | --- |
| Foundation | `30093a002b30fc86c303aeec3ef44b397d5acb8c` |
| Finite checkout | `eb4119ecf80df9f59a1bfe73f0fdfff8a9d8f413` |
| Den checkout | `27b25eeddd934dca1647025defec3275dcf9e9b9` |
| Den upstream `main` | Same revision, verified with GitHub's commits API during this review |
| Foundation's locked Den | `c7ef3f11126f24878f5c69527b4230f51c839803` (August 25) |
| Foundation's explicit gen | `0004f3c9dfd5634f47ee72575e56c54883450bcf` |
| Reviewed Den CI's gen | `6427d42770e3b1c283b8caf2929ed622e551ebb9` |

Local sources were inspected in `~/projects/nix/den`, `~/projects/finite`, and
this repository, plus the installed `/usr/share/ublue-os/just` recipes. Local
checkouts and installed image content are distinct sources; no assumption was
made that the host is running those checkouts' latest commits. Interpret
“dengen” as Den's documentation/references, including gen, as clarified by the
user; there is no separate tool to install.

## Den changes relevant to this design

Reviewed the 44 commits returned for July 20–October 20, 2026, emphasizing the
changes since Foundation's locked Den. The
[revision comparison](https://github.com/denful/den/compare/c7ef3f11126f24878f5c69527b4230f51c839803...27b25eeddd934dca1647025defec3275dcf9e9b9)
records the dependency migration boundary.

| Change | Implication for Foundation |
| --- | --- |
| [Same-user homes remain distinct across hosts, July 30](https://github.com/denful/den/commit/7f11ba1) | Standalone homes can eventually be named `user@host` without inventing a host registry. |
| [Nested definitions merge, August 11](https://github.com/denful/den/commit/e8e8de1) | Split aspect definitions across files, but test the resulting inclusion tree. |
| [Host-qualified resolution and newer gen-schema, September 15](https://github.com/denful/den/commit/6c11a13) | Update Den and its tested gen together before adopting new schema APIs. |
| [Nested inclusion/deduplication fix, September 23](https://github.com/denful/den/commit/ba9ee3a) | Shared capabilities included through two profiles should emit once. |
| [Options-first gen-schema API, October 12](https://github.com/denful/den/commit/dd59a4c) | Use current schema constructors if a custom kind becomes necessary. |
| [Naming and inclusion documentation, October 14](https://github.com/denful/den/commit/f1a3f99) | A namespace is not a bundle. Explicitly include the intended leaf aspects. |
| [Custom-kind guide, October 15](https://github.com/denful/den/commit/f9dc99a) and [resolved instances, October 15](https://github.com/denful/den/commit/6e5e413) | The supported extension exists; defer it until independent profile entities need routing or collection. |
| [Global default context clarification, October 20](https://github.com/denful/den/commit/27b25ee) | Avoid hardware policies in `den.default`; host context can also be visible in user scopes. |

Use direct nested names such as `profiles.professional`, `machines.laptop`,
`hardware.cpu.intel`, and `hardware.gpu.amd-discrete`. References in `includes`
are aspect values, not strings. Including a parent does not implicitly select
its children. `._` selects direct children only; do not use it on a namespace
containing alternatives such as laptop/desktop or professional/personal.
See the [naming and inclusion guide](https://den.denful.dev/guides/configure-aspects/#naming-and-inclusion).

The [custom entity guide](https://github.com/denful/den/blob/27b25eeddd934dca1647025defec3275dcf9e9b9/docs/src/content/docs/guides/custom-entity-kinds.mdx)
requires a kind inheriting `den.schema.conf`, a registry built with
`den.lib.schema.mkInstanceType`, and a resolving policy. None is needed just to
select application bundles. Do not create custom Nix classes named professional
or personal either: classes are module evaluation domains, not usage categories.

Den currently uses gen-schema; the full gen-based engine remains a future
design. Do not build this migration on unshipped graph/query APIs. See the
[reviewed future-design document](https://github.com/denful/den/blob/27b25eeddd934dca1647025defec3275dcf9e9b9/docs/src/content/docs/future.mdx).

## Proposed profile and aspect model

### Composition and public interfaces

The schema below is a later-stage candidate. The first implementation keeps
profile schema 2 and adds classification metadata without moving applications.

Retain `lib.mkHomeConfiguration { profile; modules; extraInputs; }` and the
existing `homeConfigurations.<username>` output for single-user consumers.
Keep `home.stateVersion` unchanged. Bluefin machines stay standalone
`den.homes`; describing their form factor does not create NixOS configurations.
Host-qualified outputs are a later fleet feature, not part of the initial
migration. The current [standalone-home guide](https://den.denful.dev/guides/standalone-home-manager/)
supports `user@host` without declaring a NixOS host if that becomes necessary.

Introduce profile schema 3, with `profiles` and a structured `host` replacing
the single `hardware` selector. Retain `foundation`, `roles`, `packages`, and
`identity` with their current meaning. Example for the verified Dell:

```json
{
  "schema": 3,
  "foundation": "bluefin-dx",
  "profiles": ["professional"],
  "host": {
    "formFactor": "laptop",
    "cpu": "intel",
    "gpus": ["intel-integrated"],
    "model": "dell-xps-9350",
    "fingerprint": true
  },
  "roles": ["developer"],
  "packages": ["jj", "uv"],
  "identity": {
    "username": "dale",
    "homeDirectory": "/var/home/dale"
  }
}
```

`profiles` accepts either or both classes; an empty list selects shared defaults
only when no work role is selected. Keep canonical order `professional`, then
`personal`. Neither category selects the other or acts as a privilege/security
boundary. Individual roles stay independently selectable **within Professional**:
professional does not silently select every work role or a Rust toolchain.
Selecting any existing work role includes the professional category during
schema 3 normalization; choosing personal plus Support therefore produces both
categories. In this example, the explicit developer role provides development
tools. Both categories share one generation rather than switching homes at runtime.

Add `classification = "professional"` to all six role catalog entries and expose
it in catalog schema 4. Group those entries under Professional in the selector,
with Personal as its peer. Do not reinterpret the existing `homeCompatible`
flag as personal/professional membership. Finite's `finite` and `finite-dev`
bootc profiles describe OS image variants and stay on the separate foundation
axis; neither becomes a professional-only or personal-only image.

`host.formFactor` is `generic`, `laptop`, or `desktop`; `cpu` is `generic`,
`intel`, or `amd`; `gpus` is a duplicate-free selection from
`intel-integrated`, `intel-discrete`, `amd-integrated`, and `amd-discrete`.
Empty GPU selection is supported. `model` is `generic` or `dell-xps-9350`;
`fingerprint` defaults to false. Generic values preserve unknown legacy hardware
without guessing. Do not reject mixed-vendor CPU/GPU combinations. The Dell
model requires laptop/Intel and its verified integrated GPU; optional additional
GPUs remain selectable. Fingerprint declaration records a capability; it does
not enroll a print or configure PAM.

Centralize normalization and validation for Nix evaluation, Python helpers,
catalog generation, and the selector. Expose the normalized result through
`lib.normalizeProfile`; reject unknown selections and duplicates, and retain
catalog ordering for roles/packages. Publish catalog schema 4 with the new
profile and hardware dimensions. Support catalog schema 3 consumers until
Finite's provisioning/selector code supports schema 4; switch the generated
default only after that consuming change ships.

### Aspect boundaries

| Aspect family | Contents and initial behavior |
| --- | --- |
| Shared base | Account, state version, generic Linux GPU integration, shell/editor/browser, credential tools, updater, and shared Brew provider contract. |
| Professional | Office/presentation tools and work communication; classify Developer, Sales, Trainer, Support, Executive, and IT here, preserving each opt-in role and its specialized tools. |
| Personal | Media, wallpaper, casual desktop conveniences, and existing personal productivity applications. New entertainment apps remain explicit selections. |
| Capabilities | Reusable leaves such as devops, office, communication, media, desktop convenience, and camera integration. Profiles explicitly include them. |
| Machine | Generic/laptop/desktop selection. Laptop owns user-level power preferences; system suspend/lid policy stays with Bluefin. |
| CPU/GPU | Independent capability metadata and proven user-space integration. Do not add system drivers or empty service wrappers just to fill the taxonomy. |
| Model | Dell panel policy, IPU7 camera filtering, and its scoped Firefox PipeWire camera policy. Runtime checks retain model/panel guards. |

For a later application-split discussion, a provisional shared base retains Neovim, Firefox,
Bitwarden desktop/CLI, Flatseal, ExtensionManager, DistroShelf, Ignition,
Warehouse, MissionCenter, and the required shell/Brew helpers. Professional adds
Marp, LibreOffice, Thunderbird, and Element. Personal adds VLC, Nextcloud,
Joplin, Damask, Gradia, Pinta, IceBox, Spider, Impression, Gear Lever, Smile,
and Refine. Chromium and camera controls become explicit optional applications;
the Dell model can include camera controls. Preserve all other current base
settings in shared base initially; split behavior only with a named acceptance
test. Keep specialized role contents and devops inclusion unchanged initially.

Composition examples (conceptual aspect references):

```nix
# Work laptop: profile choice and hardware choice are independent.
includes = [
  den.aspects.base
  den.aspects.profiles.professional
  den.aspects.roles.developer
  den.aspects.machines.laptop
  den.aspects.hardware.cpu.intel
  den.aspects.hardware.gpu.intel-integrated
  den.aspects.hardware.models.dell-xps-9350
];
```

A personal AMD desktop selects `profiles.personal`, `machines.desktop`,
`hardware.cpu.amd`, and its AMD integrated/discrete GPU leaves. An Intel work
desktop with an AMD graphics card selects the Intel CPU and AMD discrete GPU
leaves. A mixed-use laptop includes both profile leaves; shared capabilities
must deduplicate. No professional profile includes personal implicitly.

### Compatibility and migration

- Accept schema 2 indefinitely during this migration. Normalize it to an
  internal legacy bundle that reproduces all currently shipped base apps;
  do not replace that application bundle with the new professional-only defaults
  or silently remove packages.
- Classify existing work roles as professional metadata immediately in the new
  catalog, but retain the legacy application closure for schema 2. Explicit
  migration to schema 3 retains the selected roles and includes professional;
  it never expands one selected role into all six.
- Map `generic-x86_64` to generic machine/CPU/model with unknown GPUs. Map
  `dell-xps-9350-intel` to the verified Dell dimensions, leaving fingerprint
  false unless explicitly selected after detection. Keep the legacy
  `FINITE_HARDWARE` values and module paths as compatibility adapters.
- Make schema 3 adoption explicit in `finite-configure`; preview additions and
  removals before staging the changed profile. Preserve identity, local Nix
  modules, extra inputs, role/package choices, and state version.
- Keep `services.flatpak.uninstallUnmanaged = false`. Deselecting an application
  must not trigger a new unmanaged-application cleanup policy. Explain that
  previously installed Flatpaks can remain after a profile change.
- Extend catalog/CLI/UI support together, including `finite-home-profile`,
  `finite-home-apply`, Python profile validation, and Finite's initial profile
  selection. Default new installations to professional with no implicit roles;
  preserve schema 2 output until consumer support is available.
- Keep release compatibility 1 while old commands and schemas remain accepted.
  Test old updaters against the new release before publication; schema 3 writers
  must not be enabled for installations still running old profile validators.

## Verified Dell behavior and ownership

| Observation | Recommended action and owner |
| --- | --- |
| DMI: Dell Inc., XPS 13 9350; CPU: Core Ultra 5 226V; GPU PCI ID `8086:64a0`, driver `xe` | Foundation records Intel CPU/integrated GPU capabilities. Bluefin supplies the kernel, Mesa, firmware and microcode. Do not force `i915` or add speculative kernel parameters. |
| Installed image: Finite, Bluefin DX/Fedora 44, image `44.20261013` | Preserve the actual host platform. Do not equate a personal/professional selection with Bluefin versus DX. |
| `tuned` and `tuned-ppd` active; power profile is balanced; TLP and power-profiles-daemon inactive | Use the existing tuned-backed power interface. Do not install a second power daemon through Home Manager. |
| Existing Dell panel policy: 120 Hz + VRR on AC, 60 Hz on battery | Preserve the script's exact-mode validation and refusal to change external/complex layouts. Model selection alone must not assume every panel has these modes. |
| Existing IPU7 WirePlumber filtering and Dell-only Firefox policy | Keep these together as model/camera behavior; kernel/IPU7 drivers remain image-owned. |
| Goodix USB `27c6:633c`; fprintd detects it and reports an enrolled fingerprint | Fingerprint support already exists. Keep enrollment, PAM/authselect, GDM and lock-screen policy host-owned; Home Manager need not install another service. |
| No active logind drop-ins found; compiled defaults shown; no `handle-lid-switch` inhibitor in the observation | Verify actual docked behavior before changing defaults. GNOME can take over lid handling dynamically. |

The [libfprint supported-device list](https://fprint.freedesktop.org/supported-devices.html)
includes this Goodix ID, but describes development support; the installed
fprintd discovery and enrollment are the stronger evidence for this host.

For laptops, the initial target is suspend when undocked, and remain usable
closed when docked with an external display. Keep the native GNOME/logind
behavior first. An AC adapter or keyboard alone is not proof of docking.
Do not set `HandleLidSwitchExternalPower=ignore` globally: it would keep an
undocked charging laptop awake as well. If the desired AC-plus-input-only case
requires a custom rule, implement it as a separate opt-in image feature after
testing an explicit dock predicate. No polling lid daemon belongs in the initial
Home Manager migration. The [systemd logind manual](https://www.freedesktop.org/software/systemd/man/latest/logind.conf.html)
documents dock/external-power handling and desktop inhibitor precedence.

Do not add a generic Dell manufacturer aspect yet. The current panel/camera
rules are model-specific. Battery charge thresholds, BIOS power modes, GPU
driver overrides, sleep modes, and fingerprint authentication require separate
evidence and belong to the system layer when needed.

## Update sequence and firmware maintenance

### Existing sequence to retain

Finite owns `files/system/usr/share/ublue-os/just/60-custom.just`. It delegates
to `/usr/share/ublue-os/just/update.just`, then runs Foundation for an importing
consumer. The installed underlying recipe performs:

1. Check whether the automatic system updater is running.
2. Stage the OS update through rpm-ostree or bootc.
3. Update system and user Flatpaks where their remotes are present.
4. Upgrade shared Homebrew packages when the invoking user owns Brew.
5. Run `finite-home-update` in the invoking desktop user's context.

Foundation's update then locks the consumer operation, discovers a supported
published release, copies the consumer to staging, temporarily selects its
immutable Foundation revision, and resolves/verifies its dependency closure.
Channel consumers retain their `latest-release` declaration after verification;
fixed-revision consumers remain fixed to the new release. Personal input pins
are checked for drift. It builds with a default 3 GiB memory cap, 512 MiB swap,
one job/core and CPU quota, provisions missing Brew requirements, backs up the
consumer, and activates. On failure it restores consumer files and attempts the
previous activation. Brew/Flatpak side effects remain nontransactional.

Ordinary workstation updates therefore require **no Foundation source-flake
input editing**. Consumer declaration changes are already handled in staging.
Maintainer dependency updates belong to Foundation's existing
`scripts/update-locks.py` workflow, which updates the source lock and aligns the
explicit gen revision to the selected Den CI lock. Do not run that maintainer
script from `ujust update`.

The installed Bluefin recipe lacks strict shell failure handling, so its final
success status does not prove every earlier step succeeded. U1 now stages a
Finite adapter that rejects root first and delegates through Just with a scoped
Bash startup hook enabling `errexit`. It retains upstream ordering and conditional
ownership/discovery behavior, clears the hook before nested tools and verifies
a private startup marker before Foundation. Production does not parse or extract
recipe bodies. Real-Just fixtures cover actual update-command failures, skips,
nested tools, cleanup and Foundation failure. Conditional probe errors retain
upstream semantics, and the current Bash recipe must be requalified on image
changes. See the [U1 integration report](qa-reports/QA-update-integration.md).

### NH decision

Installed NH is 4.4.2 and `nh home switch --help` confirms `--no-nom`, `-u`, and
`-U`. For an explicitly requested direct update, the supported form is:

```bash
nh home switch --no-nom -U foundation "path:$HOME/.config/home-manager"
```

This is an alternative direct operation, not the staged updater's implementation.
Retain `finite-home-update` for `ujust update`: its raw `nix build` already does
not use nix-output-monitor, and replacing it with `nh home switch -u` would
bypass staging/recovery and update personal inputs too. No NH backend or new
runtime dependency is needed in the initial migration. Document `--no-nom` in
the existing direct-NH examples as an available option.

### Firmware observation and next action

Historical observation: the user subsequently updated firmware manually. Do not
use these versions as current post-update evidence or require firmware work
before implementing profile classification.

Read-only fwupd checks reported BIOS/System Firmware **1.22.0**, KIOXIA BG6
firmware **12000105**, and UEFI dbx **20260402**. `get-updates --json` returned
no devices. LVFS is enabled, but its reported metadata `Mtime` was
**2026-08-05 23:47:08 UTC**, about 75 days old, and `fwupd-refresh.timer` was
inactive with no last trigger reported. System firmware and SSD devices also
reported an AC-power requirement not satisfied at inspection time.

Do not interpret older or same-version entries under device releases as pending
upgrades. Do not infer that the BIOS is latest from this cached result. Connect
AC and use the existing Firmware application, or refresh metadata and inspect
again with `fwupdmgr refresh` followed by `fwupdmgr get-updates`. These actions
were not run during this read-only review.

[Bluefin's administration guide](https://docs.projectbluefin.io/administration/)
assigns firmware updates to the Firmware application. The
[fwupd command reference](https://fwupd.github.io/libfwupdplugin/fwupdmgr.html)
distinguishes metadata refresh, discovery, and installation. Keep installation
as an explicit maintenance action with the tool's AC/reboot requirements;
do not append an unattended firmware flash or reboot to Home Manager activation.
Finite should investigate the inactive refresh timer and existing image refresh
mechanism before adding another schedule. After normal updates, a firmware
status/reminder may report stale metadata separately from “no updates.”

## Implementation order and acceptance

| Stage | Owner and concrete change | Acceptance |
| --- | --- | --- |
| 0. Classification first | Foundation: add Professional/Personal catalog categories; classify all six work roles under Professional, preserving current apps and schemas. | See the current linked implementation plan for the authoritative task order and acceptance. |
| 1. Dependency baseline (separate change) | Foundation: update Den and its CI-tested gen together, preserving unrelated inputs where possible. | Existing schema 2 outputs evaluate; all fixtures and full CI pass; pin diff reviewed. |
| 2. Internal composition | Foundation: split reusable application/model leaves and retain legacy adapters with unchanged schema 2 behavior. | Compare package sets, Flatpak declarations, user units, Firefox policy, session variables and state version before/after. |
| 3. Profile API | Foundation: add schema 3 normalization, schema 4 catalog, selector/CLI support and explicit migration preview. | New selections evaluate; schema 2 consumers and old update commands still work; migration preserves personal files and pins. |
| 4. Consuming integration | Finite: support the new catalog/profile, then enable new defaults; verify strict upstream update delegation after Brew. | Provisioning fixtures and ordered failure-injection tests pass; no root Home Manager operation. |
| 5. Dell qualification | Foundation user-layer changes and Finite system-layer changes remain separately reviewable. | Camera/panel behavior preserved, no duplicate power daemons; physical dock, sleep and authentication checks recorded. |
| Firmware maintenance (outside refactor) | User reports manual update complete. | No firmware task blocks profile work. |

Required future automated coverage:

- Evaluate no profiles, professional, personal, and both on Bluefin and DX.
  Check that shared capabilities emit once, personal apps do not leak into
  professional-only configurations, and standalone homes require no `osConfig`.
- Evaluate generic, laptop, and desktop selections with Intel/AMD CPUs; each
  integrated/discrete GPU leaf; Intel CPU + AMD GPU; AMD CPU + Intel GPU; and
  integrated + discrete combinations. Assert desktop configurations contain no
  laptop panel/power units. No NVIDIA coverage is required in this stage.
- Reject unknown or duplicate profile/hardware selections and inconsistent Dell
  form-factor/CPU declarations. Exercise schema 2 normalization, explicit schema
  3 migration, catalog compatibility, CLI round trips, and selector cancellation.
- Assert all six existing work roles are classified under Professional; migrating
  each preserves its selection, schema 3 role-only input includes professional,
  and personal plus a work role composes both categories without selecting peers.
- Inject lock/build/Brew/activation failures and concurrent consumer edits.
  Verify unchanged personal pins/modules, backup restoration, previous-generation
  recovery, root rejection, and the existing resource budgets.
- In Finite fixtures, record the OS → Flatpak → Brew → Foundation order and each
  failure path without actually updating the OS or activating a home.

Physical acceptance is separate from Nix evaluation: qualify undocked and docked
lid behavior on AC/battery, plug/unplug transitions while closed, repeated
suspend/resume, external-display preservation, exact panel modes, camera capture,
and fingerprint login/unlock with password fallback. Do not claim these tests
passed merely because the corresponding profile evaluates.

### Validation performed for this review

`bash tests/check.sh` passed, including provider contracts, Dell panel fixtures,
23 Python consumer/update tests, and role/aspect checks. Read-only hardware,
firmware, service, inhibitor and enrollment observations were completed using
host access after sandbox bus restrictions. Public GitHub metadata confirmed
the Den revision. No full Nix build or physical sleep/docking/authentication
test was performed; this change adds documentation only.

Current priority is additive classification with application parity, followed
by independently tested dependency, compatibility, application and hardware
slices in the linked implementation plan. Firmware maintenance is already
handled. The optional AC-plus-input-only closed-lid policy remains a separate
feature requiring a concrete docking definition.
