# Profile refactor architecture

Status: classification, dependency/normalization and reader-readiness slices
implemented. The [schema-3 contract](ARCH-profile-schema3.md) now has F1b dual
readers/composition and actual nixGL wrappers. A2 adds negotiated capability
editing and explicit reviewed conversion. H1 adds
[structured host composition](ARCH-host-composition.md); the workstation's
conversion has succeeded. W3 now defaults new profiles/templates and the
catalog to schema 3; see [profile generation](ARCH-profile-generation.md).
The user's
latest scope clarification keeps Foundation broad and limits migration to this
workstation; earlier multi-consumer compatibility requirements are historical.
Classification-first sequencing confirmed by the user on 2026-10-20.
This document and the
[implementation plan](../plans/PLAN-profile-refactor.md) supersede the rollout
order and immediate schema changes in the earlier
[research review](../PROFILE-ARCHITECTURE.md).

## Decision

Classify existing roles first, preserving all current application sets. Developer,
Sales, Trainer, Support, Executive, and IT belong to **Professional**. Register
**Personal** as its peer category for subsequent composition work. These are
Foundation usage categories, not new Den module classes or entity kinds.

The first release keeps profile schema 2, generated catalog schema 3, release
compatibility 1, existing role IDs/order, existing hardware IDs, and
`mkHomeConfiguration { profile; modules; extraInputs; }`. It changes catalog
metadata and selector presentation, not aspect inclusion or installed apps.

Rejected for the first release: moving apps, replacing `hardware`, upgrading
Den/gen, writing schema 3, renaming exported aspects, changing update execution,
or introducing a selectable Personal option with no application behavior.
These changes have separate compatibility or user-visible consequences.

The full migration is medium-sized; the first slice is small. Its main
correctness boundary is Foundation's catalog crossing into Finite's provisioning
and existing consumer configurations. Verification must prove that additive
metadata does not change the generated home composition.

## Additive catalog contract

- Add ordered domain entries `classifications = [{ name = "professional";
  label = "Professional"; order = 10; } { name = "personal";
  label = "Personal"; order = 20; }]`, plus `classificationsByName` and
  `classificationNames`, following the existing catalog conventions.
- Set `classification = "professional"` on each of the six existing roles.
  Preserve every other role field, including `homeCompatible`; that flag is
  unrelated to this classification.
- Export `homeCatalog.classifications.<id>` with `name`, `label`, `order`, and
  `roles`, deriving role membership from role metadata in canonical role order.
  Export `homeCatalog.roles.<id>.classification`. Personal initially has `roles=[]`.
- Preserve every existing catalog value after projecting away the new fields.
  Do not reuse `foundations.<id>.profiles`: Finite uses it for bootc image names.
- Preserve `mkHomeCatalog { domainCatalog = ...; }` for old custom catalogs.
  An absent classifications registry produces an empty registry; a role without
  classification exports `classification = null`. An explicitly supplied
  classification must reference a declared category. Never classify an unknown
  third-party role as Professional merely because it is a role.
- A catalog version bump is unnecessary for these additive, optional fields.
  Demonstrate that existing consumers tolerate them; a failing strict consumer
  test must be resolved before release rather than silently widening this scope.

Source boundaries: [domain catalog](../../lib/catalog.nix),
[home-catalog projection](../../lib/home-catalog.nix), and
[public constructor](../../lib/default.nix).

## Selector and source ownership

Expose the already generated catalog store file from `lib/applications.nix` as
`profileCatalog`. Pass its path to `finite-configure` with the packaged
`FINITE_FOUNDATION_CATALOG` environment variable in `modules/finite.nix`.

Build role rows from that catalog, ordered by `order`; show the classification
alongside each role, using the Professional label for all six current rows.
Use columns `Use`, `Classification`, `Role`, `id`, with column 4 hidden and
returned; keep role IDs as the return value. Build optional-package rows from the
same catalog while retaining their current labels, descriptions, and order.
Preserve cancellation, checked state, and the existing single
`finite-home-apply --roles ... --packages ...` call. Do not write profile state
while the user moves through the dialogs.

A missing or unreadable packaged catalog is an error before launching dialogs;
there is no second hardcoded list to drift. Unclassified custom rows use an
empty classification label. Do not expose a Personal checkbox until it selects
real behavior in a later release.

Keep `den.aspects.features.roles.<id>` and existing role file paths unchanged.
Keep the existing `FINITE_ROLE_*` variables and selected-role semantics.

## Compatibility prerequisites for later stages

These were findings at the classification baseline. N1 resolves the first four
rows for schema 2; F1a implements current-reader/projection coordination in the
isolated Finite `profile-readers` jj workspace:

| Boundary | Evidence | Required later change |
| --- | --- | --- |
| Initialization | Previously assigned `schema=2` unconditionally. | F1b accepts supplied schemas 1/2/3, converts only 1 to 2, preserves 3 and rejects unsupported formats. Default generators remain 2. |
| Build validation | Previously used the executing helper/env catalog. | N1 resolves the pure normalizer and catalog from the staged locked Foundation; fallback requires API absence. |
| Validator ownership | Validation was independently implemented in Nix and Python. | N1 shares a pure Nix normalizer between composition and staging; Python retains runtime account/image checks and a legacy-target schema-2 fallback. The schema-2 generator remains unchanged. |
| Ordering | Valid reordered selections were accepted by composition but not persisted consistently. | N1 canonicalizes by catalog order then name, persists staged selections before building, and rejects unknowns/duplicates. |
| Image initialization | Previously discarded unrecognized saved profiles before offering fresh selection. | F1a preserves saved-profile precedence, gates schemas before historical helpers, uses catalog-driven rows, and keeps schema-2 generation. F1b adds the A1-defined future format before new writers. |
| Typed projection | Previously copied role label/order/aspect only. | F1a adds typed role classification and grouped metadata with legacy null/empty defaults. |

The initial catalog change does not require changing these runtime paths.
Test Finite's existing `mkHomeCatalog` use with the added metadata without
changing its bootc mappings. Track the typed projection as a later Finite
integration task, not an artificial dependency of Foundation's catalog release.

The [N1 implementation report](../qa-reports/QA-validation-bridge.md) records
the validation bridge and its compatibility limits. Staged profile writes replace
the directory entry atomically, so copied symlinks cannot write into live data
before a build succeeds.

For the later format, keep two reader/writer transitions distinct: a bridge
release can read old and new profiles while still writing schema 2; only a
subsequent explicitly selected migration writes schema 3. A version number alone
does not establish capability. Include the executing helper, selected Foundation
revision, and Finite provisioning parser in compatibility checks. Do not bump
release compatibility casually: old updaters currently require exact equality.

F1a publishes `profileCapabilities` (descriptor schema 1) with
`initializeSchemas = [1, 2]`, `normalizeSchemas = [2]`, `writeSchema = 2` and
`catalogSchemas = [3]`. The Nix catalog and the executing Python helper read the
same manifest. The read-only `init --capabilities` query locates it relative to
the actual script, ignoring source overrides. Staging intersects this helper's
support with the locked target's descriptor; explicit malformed metadata fails.
Descriptor absence identifies a legacy target, not evidence for a future format.
First-login similarly limits helpers without the query to historical schema 1/2.
F1b extends the manifest to initialize schemas 1/2/3 and normalize schemas 2/3,
keeping write schema 2. A2 adds `editSchemas = [2, 3]` and a versioned change API.
After the successful workstation conversion, W3 changes `writeSchema` to 3 for
new Foundation profiles and templates. Initialization/normalization support is
unchanged; the earlier phase descriptions above record the bridge sequence.
Actual composition and selected-source catalog support
are implemented alongside that advertising; schema 3 requires an explicit target
descriptor and normalization cannot change the submitted version.

## Later composition boundaries

After compatibility groundwork, introduce professional/personal selections with
shared defaults and opt-in role leaves. Selecting any existing work role implies
Professional, preserving that role without selecting its siblings. Selecting
a Personal role plus a work role can compose both categories in one generation.
Schema 2 retains its complete legacy application declarations throughout the
supported migration; adopting a smaller set requires an explicit preview.

The [schema-3 contract](ARCH-profile-schema3.md) now records application ownership:
Chromium is optional and camera controls follow declared hardware or explicit
selection. F1b implements those semantics for supplied schema 3; schema 2 retains
its old base. Keep unmanaged Flatpaks preserved and explain retained installations
during an explicit migration preview.

Separate machine form factor, CPU, GPU, and model dimensions in another slice.
Preserve the current Dell panel/camera behavior and hardware adapters first.
Bluefin owns kernel drivers, firmware/microcode, PAM, fingerprint enrollment,
logind and power daemons; Home Manager owns user configuration. Intel/AMD and
mixed-vendor composition are required; NVIDIA remains deferred.

Upgrade Den with its tested gen in an isolated dependency change before adopting
new Den semantics. Classification needs no new Den API. Avoid the current
unrestricted `scripts/update-locks.py` operation for this targeted migration;
preserve unrelated pins, especially the current Herdr `nixpkgs-unstable` input.

## Maintenance and current workspace

Firmware was manually updated, as reported by the user. Earlier fwupd readings
are historical and do not describe the post-update firmware versions. Firmware
discovery/refresh is no prerequisite of this refactor, and no firmware work is
part of its implementation tasks.

Finite already orders OS → Flatpak → Brew → Foundation updates. Keep the staged
Foundation updater and its resource limits/backups/recovery. Review root-check
placement and upstream failure propagation in a separate Finite task. Prefer
an upstream-supported hook or a separately maintained, tested wrapper over
parsing and executing text from `just --show`; the latter is too brittle to
prescribe without an explicit format contract. NH's `--no-nom` remains an
optional direct-command setting; the current raw Nix build already avoids NOM.

Existing uncommitted Herdr, Zsh, desktop-search-path, and migration-test edits
are the input baseline, not refactor output. Capture/review their changes before
the first code task and use sequential ownership for overlapping files. Never
reset or overwrite them to manufacture a clean comparison.

## Acceptance and review

The first slice is ready only when metadata membership, catalog projection,
custom-domain compatibility, selector round trips/cancellation, and composition
parity pass. Parity covers roles/packages/Flatpaks/services/session variables,
identity and state version under both supported foundations and hardware IDs.
Compare application composition rather than the entire activation derivation:
the updated selector/store path legitimately changes that derivation. Foundation's
five generated command packages embed this source and can acquire new store
paths as well. Identify `finite-configure`, `finite-home-apply`,
`finite-home-update`, `finite-home-migrate`, and `finite-app-status` by package
name/version when comparing; require the same count and identities, and require
all remaining application package outputs to match exactly. Do not mask changed
providers or arbitrary paths with a global store-path replacement.

Use the [task plan](../plans/PLAN-profile-refactor.md) for ownership, validation,
and rollback. Architectural review and the concrete plan precede implementation;
release publication and actual workstation activation remain separate actions.
