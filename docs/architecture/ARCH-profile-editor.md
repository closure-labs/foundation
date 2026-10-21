# Profile capability editor and explicit conversion

Status: A2 implemented, 2026-10-20. This is a local code change, with no
workstation activation or profile conversion performed during implementation.
It builds on the [schema-3 contract](ARCH-profile-schema3.md) and existing
transactional updater.

## User commands

`finite-configure` edits the existing profile format. Schema 2 retains its
Professional role/package dialogs; schema 3 additionally shows Personal roles
and an **Additional capabilities** dialog. Only explicitly stored capabilities
are checked: role, hardware and shared defaults remain derived. Unchecking an
explicit selection does not remove an application still supplied by a role.

`finite-configure --migrate-profile` explicitly requests schema 2 → 3 conversion.
The selector shows the new choices, then a scrollable preview of application
declarations, provider changes and retained Flatpak/data behavior. **Build and
apply** submits the exact reviewed selections and approval token. Cancelling
any dialog leaves the configuration unchanged.

The CLI supports the same flow:

```bash
# Review the candidate without building, provisioning Brew or activating.
finite-home-apply --migrate-profile --roles developer,creative \
  --capabilities recording --preview

# Repeat the same selections with approvalToken from that result.
finite-home-apply --migrate-profile --roles developer,creative \
  --capabilities recording --approve-preview '<approvalToken>'

# Build the candidate without changing the live profile; no approval required.
finite-home-apply --migrate-profile --roles developer,creative \
  --capabilities recording --check
```

Omitting `--roles` or `--packages` preserves the existing selections. On an
existing schema-3 profile, omitted `--capabilities` preserves explicit choices;
`--capabilities ''` clears them. Capabilities on schema 2 require explicit
`--migrate-profile`, even for an empty selection. A custom schema-2 field named
`capabilities` blocks conversion rather than being overwritten. Foundation's
default generator and templates now use schema 3. Finite first-login/cloud-init
adoption is separate from this Foundation change.

`finite-home-migrate` retains its existing purpose: adopting Foundation into a
legacy standalone configuration. Profile-format conversion uses the separate
`finite-home-apply --migrate-profile` option.

## Locked-source contracts and negotiation

The additive manifest field `editSchemas = [2, 3]` describes implemented editing,
separately from initialization, normalization and default `writeSchema = 3`.
Absent editing metadata means historical schema-2 editing only. Explicit invalid
metadata fails validation. The running helper checks its own manifest, ignoring
source overrides when reporting support.

`lib.profileChanges = { schema = 1; preview = ...; }` is the selected source's
pure change API. Preview takes the original `profile` plus optional `roles`,
`packages`, `capabilities` and boolean `migrate`. It independently resolves the
original and candidate, so changing optional packages cannot conceal removals
from the source inventory. All previews set `activationAllowed = false`.
Activation is a controller action following explicit conversion approval and a
successful build, not something a Nix preview authorizes.

`finite-home-apply --editor-context` is a read-only JSON query for the selector.
It resolves normalization and the format-specific catalog from the consumer's
locked Foundation revision. It does not use a caller's packaged catalog. The
schema-3 editor requires API version 1, schema-aware catalogs and explicit target
editing support. An older source can still serve ordinary schema-2 editing;
update that Foundation input before using the new editor/conversion flow.

The existing `lib.profileDrafts.previewMigration` remains available for older
callers, now also accepting candidate-only `packages`. Its draft status does not
grant controller activation. Catalog schema 3 and release compatibility 1 remain
unchanged. The default public catalog now exposes ten roles; existing schema-2
editors request their six-role view explicitly.

## Preview binding and concurrency

CLI `--preview` returns a versioned JSON envelope with the source fingerprint,
pure preview, human-readable summary and deterministic SHA-256 `approvalToken`.
The token binds:

- Canonical consumer root and original whole-tree digest.
- Original profile bytes, including a linked profile's external contents.
- Exact lock bytes and selected source store path, revision and content hash.
- Requested selections/conversion mode, normalized candidate and full preview.

Temporary stage paths are excluded, so a separate approved invocation matches.
This token detects stale local state; it is not an authentication credential or
a substitute for the desktop user's permissions. No approval service or saved
approval file is created. If state or selections change, request a new preview.
Keep saved preview files outside the consumer tree, or retain the JSON in a
shell variable, so saving the review does not itself change the bound tree.

Read-only queries stage in `/tmp`, leave live profile/lock files untouched and
create no consumer operation lock. Apply recomputes the preview under the
existing operation lock, verifies the token before building, and checks live
state again before Brew provisioning and commit. Profile bytes are checked
separately because the general tree digest records symlink destinations.

## Recovery, providers and application data

Conversion uses the existing bounded build, Brew preflight, configuration backup,
activation and previous-generation recovery path. Build failure leaves the live
configuration unchanged. Activation failure restores committed file entries
atomically, preserving original symlinks and external profile contents, then
attempts the previous generation. Failed candidate and original backups remain
available for inspection. External Brew/Flatpak effects remain nontransactional.

Conversion changes Foundation-managed declarations. Personal modules can add or
override applications and defaults, so their effects require separate review.
Unmanaged Flatpaks are retained and app data is never deleted or automatically
copied into native application storage. Both distributions can remain visible
in the launcher; provider changes include their Flatpak ID and Nix attribute.

Before relying on a migrated data-heavy app such as Joplin or Chromium, use its
export/import or account-sync workflow, retain the original Flatpak data, and
verify the native app independently. Review personal MIME/default-app settings
that refer to Flatpak desktop IDs; the editor does not rewrite them. An old
Flatpak can still be opened explicitly with `flatpak run APP_ID`. Native package
attributes are shown in the JSON declaration diff and provider review.

Source/profile rollback and app-data rollback remain separate. Restore the saved
schema-2 profile with its previous source lock when returning to a schema-2-only
source. Physical graphics, media, camera and app-data transfer checks remain
pre-migration rollout work; a synthetic wrapper launch is not that validation.

## Sequential ownership and validation

One implementation writer owns each task in order; specialists review read-only.

| Task | Owned files | Exit condition |
| --- | --- | --- |
| Pure change contract | `lib/profile-changes.nix`, public export, manifest and retained draft adapter | Source/candidate comparisons preserve fields and correctly show package/provider removals. |
| Controller transaction | `scripts/home.py` | Negotiated editing, deterministic preview binding, no-write preview and failure recovery tests pass. |
| Selector | `modules/finite-configure` | Locked catalog, explicit capabilities, cancellation and reviewed single-apply behavior pass. |
| Integration/docs | Editor fixtures, existing test entry points, README/CHANGELOG and plan/task docs | Pinned CI, locked-target contracts, current Nix builds and Finite compatibility checks pass; no host activation. |

See [A2 validation](../qa-reports/QA-profile-editor.md) for measured results and
remaining physical-session limits.
