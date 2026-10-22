# Convert Dale's workstation

Scope: only Dale's current Dell XPS 13 9350. The broader Foundation host/profile
refactor continues independently. No other consumers need a migration program,
support window or old/new helper matrix at present. This supersedes earlier
multi-consumer migration requirements in the staged refactor plan.

## Target

The [candidate profile](../../examples/workstations/dale-xps-9350.json) retains
Bluefin DX, Dale's identity, all six Professional roles and the selected
Hack font, Herdr, Jujutsu and uv packages. Its explicit capabilities preserve
the current Foundation application identities while adopting the schema-3
Nixpkgs/nixGL providers and recorded verified Flathub exceptions. It declares
the observed Intel Dell laptop, integrated graphics, camera and fingerprint
reader. Personal roles remain available for future selections.

## Implementation and validation

1. Complete [H1 host composition](../architecture/ARCH-host-composition.md).
2. Copy `~/.config/home-manager` to a private temporary stage. Retain both
   custom modules, Espanso assets/patches and all personal input pins. Change
   only the staged Foundation input to the reviewed immutable local revision.
3. Put the candidate profile in that stage. Adapt its user-owned graphical
   package bindings to `config.lib.nixGL.wrap`: Element, Bitwarden, 1Password,
   Nextcloud, Signal, Spotify, Zed, Librepods and customized Zoom. Preserve
   Element's X11 argument, Bitwarden's environment, desktop IDs and autostart
   choices. Firefox already uses the configured package. Keep shell, Deja,
   XDG paths and private Espanso inputs unchanged.
4. Evaluate the merged declarations and build the staged activation package
   with the existing memory/CPU limits. Inspect actual custom launcher and
   autostart paths as well as Foundation packages. Record the output and
   previous generation. A dry run alone is not a successful build.
5. Before the live switch, retain the exact original configuration and current
   generation. Use the existing bounded build/activation/recovery path; avoid
   adding a separate general-purpose migration controller.
6. After switching, check desktop launchers, credentials, application data,
   graphics/media, camera capture, battery/AC panel changes and suspend/docking.
   Keep fingerprint authentication and firmware maintenance with the host OS.

Application identities can stay the same while storage changes between Flatpak
and native packages. Preserve Flatpak data, use export/import or account sync
where needed, and inspect MIME/default-app choices separately. Existing
unmanaged Flatpaks can remain installed. No automatic data copying or deletion
is part of conversion.

Build failures leave the live tree untouched. An activation failure restores
the saved configuration and attempts the previous Home Manager generation;
application-data recovery remains separate. Converting the live workstation
is a distinct step from completing and testing H1 code.

## Current evidence

The candidate is staged at
`/tmp/foundation-host-composition-in7p4_ky/workstation/`, pinned to immutable local
Foundation snapshot `7eed78af934634b253a84e7bbaba758234d870b2`. Personal Devenv's
13-node input closure and the unstable input are unchanged. Local modules/assets
are byte-identical; staged graphical bindings have been adapted as above.
The full activation-package build and built-command/launcher checks passed
after the user freed disk space. The user then approved the live switch, which
completed on 2026-10-21. The original configuration and generation are retained
for recovery. The previous capacity limit and initial evaluation are recorded
in the [H1 validation report](../qa-reports/QA-host-composition.md); completed
build evidence is in the [workstation build report](../qa-reports/QA-workstation-build.md).
The merged audit also confirms nine graphical packages wrapped once and the
custom launchers/autostart using their selected wrapped outputs. Original
Element/Bitwarden arguments and environment are preserved.

This local source is manually pinned: update/status skip published releases and
explain that its Foundation input must be advanced explicitly. The proposed
switch includes the reviewed `customize.nix` changes in the existing backup and
rollback transaction, preserving personal repository metadata and local modules.
The verified candidate is now active. Post-switch checks confirm live helpers,
profile/cache consistency, healthy user services, selected Flatpaks and Intel
OpenGL acceleration through nixGL. See the
[activation report](../qa-reports/QA-workstation-activation.md) for the exact
backup and remaining hands-on camera, docking and fingerprint checks.
