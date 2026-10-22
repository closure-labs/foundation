# Dell workstation activation

Date: 2026-10-21. The user approved the live switch after reviewing the
[completed build](QA-workstation-build.md). The guarded switch completed
successfully; this workstation now runs the verified schema-3 configuration.

| Item | Result |
| --- | --- |
| Active generation | `/nix/store/5ykg36q778pk5dm7zvbzlp3zcy7lk4bi-home-manager-generation` |
| Foundation source | Immutable local commit `7eed78af934634b253a84e7bbaba758234d870b2`, jj change `rkxnuwlv` |
| Configuration backup | `/var/home/dale/.config/home-manager.previous.20261021T055422790592Z` |
| Previous generation retained | `/nix/store/xrv2ah34mzzw0wjn62y54qgb86zd1k4w-home-manager-generation` |
| Configuration commit | Five generated files and reviewed `customize.nix` match the built candidate exactly |
| Personal modules/assets | Preserved byte-for-byte; original backup matches the reviewed live-tree digest |
| Profile/cache | Schema 3, Dell laptop/Intel integrated GPU, camera/fingerprint declarations; Finite profile cache matches |
| Installed helpers | Live status, update check, editor context and unchanged-selection preview pass |
| Update policy | Reports `local-git`/`manual-pin`; published releases are not checked or substituted |
| User services | Espanso and Dell panel policy active/running; Flatpak install oneshot completed successfully |
| Failed user units | None at post-activation inspection |
| Selected Flatpaks | All five present: Flatseal, Damask, IceBox, Spider and RustConn |
| Graphics smoke test | Probe built through the active configuration's nixGL wrapper; direct/accelerated rendering on Intel Lunar Lake `8086:64a0`, Mesa 26.1.5, OpenGL 4.6; no software renderer |

Activation checked the original live profile/tree, reviewed candidate tree and
previous generation before provisioning Brew and committing files. It used the
existing operation lock, backup, file replacement and recovery path. No fallback
activation was needed. The activation log reported two historical failed
transient scopes; the subsequent user-manager check lists zero failed units.

The OpenGL probe created a context on the current XWayland display without
launching a user application. It establishes Intel acceleration through this
wrapper, not every application's media, recording, Wine or Vulkan behavior.
Existing running applications retain their previous environment until restarted.

Camera capture, fingerprint login, panel transitions on AC/battery, suspend and
closed-lid docking remain hands-on acceptance. No biometric enrollment, system
authentication, lid policy, driver or firmware changes were made. Application
data was not copied between providers; verify data-heavy apps separately.

For a later source/profile rollback, restore the five generated files plus
`customize.nix` from the recorded configuration backup and activate the saved
previous generation. Preserve personal repository metadata and local modules.
Application-data recovery remains separate from configuration recovery.

Evidence: `/tmp/foundation-host-composition-in7p4_ky/`, including
`workstation-activation.log`, `workstation-activation-result.json`,
`workstation-live-checks.json`, `workstation-flatpak-check.json`,
`workstation-glxinfo.log` and `workstation-graphics-result.json`.
