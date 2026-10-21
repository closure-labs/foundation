# Dell workstation build and switch readiness

Date: 2026-10-20. Code is preserved in jj change `rkxnuwlv`, immutable commit
`7eed78af934634b253a84e7bbaba758234d870b2`, after H1 change `ommsszxm`.
This report records a completed build and preflight, without a live switch.

## Build result

The full schema-3 workstation activation package built successfully:

```text
/nix/store/5ykg36q778pk5dm7zvbzlp3zcy7lk4bi-home-manager-generation
```

The candidate remains in `/tmp/foundation-host-composition-in7p4_ky/workstation/`.
`workstation-result` in that evidence directory retains the built generation as
an indirect Nix GC root. The live configuration and active generation remain
unchanged. The previous generation is still available:

```text
/nix/store/xrv2ah34mzzw0wjn62y54qgb86zd1k4w-home-manager-generation
```

The user freed space before this continuation: 32 GiB was available at its
start. The refreshed build estimate was 8.7 GiB download/23.7 GiB unpacked.
About 6.8 GiB remained after building. No generations were deleted by this work.
Builds used the existing 3 GiB memory limit, 512 MiB swap limit, CPU quota,
one build job and one core.

## Build fixes

The first full build exposed a collision between Smile and Gear Lever's installed
`share/icons/hicolor/scalable/actions/meson.build` files. Their nixGL outputs now
remove Meson build files beneath the icon directory, preserving runtime icons
and binaries. A real two-package merge check builds the wrappers, checks both
launchers and application SVGs, and rejects leftover icon build files.

The local immutable Foundation input also needed helper support. Local file Git
inputs now require matching explicit/locked revisions and a valid content hash;
metadata comes from the consumer's locked source and is verified against it.
Update/status report manual pin maintenance and skip published releases.
Advancing this workstation's Foundation source remains an explicit pin edit.

The guarded switch can include the reviewed `customize.nix` GUI bindings in the
existing file commit and rollback. Ordinary role edits/updates retain their
existing treatment of user customizations. Success/failure fixtures verify
personal metadata preservation and restoration of the original configuration.

## Verification

| Check | Result |
| --- | --- |
| Pinned CI | All 131 tests passed, plus shell/Nix fixtures, actionlint and release metadata |
| Consumer transaction tests | All 32 passed independently in security review |
| Full Nix checks | Passed current schema-3 composition/host cases, home/profile-command builds, real nixGL launch fixture and actual desktop-icon merge |
| Full workstation build | Passed against immutable source `7eed78af934634b253a84e7bbaba758234d870b2` |
| Built helper commands | `finite-app-status --json`, `finite-home-update --check`, and apply `--editor-context`/`--preview` passed against the candidate; status reports `local-git`/`manual-pin` |
| Built launchers/autostart | Element and Bitwarden execute the audited wrapped packages with their original flags/environment; five autostart declarations match the reviewed candidate |
| Built icon/model files | Both application SVGs retained, conflicting Meson file absent, nixGL wrapper markers present and Dell host declaration correct |
| Brew prerequisites | Read-only `--check-installed` passed with auto-update disabled |
| Live-state guards | Configuration digest and active generation match the original baseline; staged lock unchanged during build |
| Reviews | CLI and security approved the local-source handling and transactional customization changes |

The candidate retains the 48 current Foundation application identities and the
original personal input closures/assets recorded by [H1](QA-host-composition.md).
All source/lock/profile/customization files for the proposed switch are staged;
`workstation-reviewed-state.json` binds their digest and the existing live state.
`activate-workstation.py` prepares the switch using the immutable source's
operation lock, Brew provisioning and commit/rollback code. It has not run.

No GUI application, live activation or physical hardware test was performed.
Graphics/media, camera capture, fingerprint login, panel AC/battery behavior,
closed-lid docking and application-data checks remain post-switch acceptance.
Flatpak data is retained; provider changes do not import that data automatically.

Evidence: `/tmp/foundation-host-composition-in7p4_ky/`, including
`workstation-build-initial.log`, `workstation-build-final.log`,
`workstation-build-result.json`, `workstation-built-verification.json`, final CI
and Nix logs, and the exact original/staged configurations.
