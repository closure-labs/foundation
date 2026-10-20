# Proposed Personal profiles

These are recommendations for the later application-composition stage, not
newly enabled roles or installed applications. Existing schema-2 application
sets stay intact while the reader/migration bridge is developed.

Recommend four independently composable roles under **Personal**, with a small
default set and larger tools selected explicitly. The user confirmed lightweight
defaults, with larger applications and launchers optional.
The exact ownership and format are now an
[executable schema-3 draft](architecture/ARCH-profile-schema3.md); production
writers still emit schema 2.

| Role | Purpose and proposed core | Optional additions |
| --- | --- | --- |
| **Family** (`family`) | Household documents, browsing and mail: reuse shared Firefox/credential tools plus LibreOffice and Thunderbird. | Nextcloud client for an existing family server, Joplin for household notes, calendar integration once the account provider is known. |
| **Media** (`media`) | Local music/video playback: VLC, reusing the shared browser for web media. | A Jellyfin client when a server is used; GNOME Audio Player for a focused audio interface. |
| **Creative** (`creative`) | Everyday image editing and sharing: Pinta and Gradia. | Krita for painting; Kdenlive for video; Blender for 3D; OBS Studio for recording/streaming. Select the tools that match the activity rather than installing the whole suite. |
| **Gaming** (`gaming`) | A small casual game such as GNOME Chess, including a compatible engine for solo play; reuse existing user-space graphics integration. | Steam, Heroic for Epic/GOG/Amazon libraries, and Lutris for other compatibility workflows. All launchers, game libraries, and larger games remain opt-in. |

Family means general household use with individual accounts and credentials.
It does not imply a shared login, child account, parental controls, content
filtering, or kiosk mode. A child-oriented variant needs a separate request.

Firefox, credential tools, office/mail, VLC, Nextcloud, Joplin, Pinta and Gradia
are already declared in today's shared base. Their presence here describes
future ownership, not permission to remove them from existing profiles.
Professional roles may reuse the same capabilities: a Trainer can select
recording tools without selecting an entire Personal role, for example.

## Composition and delivery

- Keep reusable office, mail, file-sync, playback, image-editing, recording and
  launcher capabilities separate from role names. Include capabilities by
  explicit aspect reference and deduplicate shared selections.
- Prefer graphical Nixpkgs applications with nixGL where appropriate. Official
  or verified Flathub distributions are permitted exceptions. Keep schema-2
  providers unchanged; preview provider changes explicitly for migration to the
  new format. The draft uses Nix for proposed creative tools and launchers,
  with verified Flathub exceptions where no matching Nix package exists.
- Treat server URLs, accounts, sync folders and credentials as user configuration.
  No role starts a media/cloud server, chooses sync roots, downloads games, or
  connects accounts implicitly.
- Keep GPU drivers, power daemons and controller device permissions owned by
  Bluefin/Finite. A Gaming role does not install a second driver stack or force
  global performance settings on a laptop.
- Enable selectable roles only when they deliver meaningful behavior and the
  installed helper, selected Foundation and provisioning entry points support
  them. Keep the old application closure for schema 2, and preview changes on
  explicit migration. The Personal classification itself remains metadata until
  then.

Recommended combinations: Family + Media for a household laptop; Creative +
Media for a hobby workstation; Gaming + Media for an entertainment desktop;
Professional Developer + Personal Creative for a mixed-use machine.

## Project references

Checked 2026-10-20:

- [LibreOffice](https://www.libreoffice.org/) provides document, spreadsheet and
  presentation tools. [Nextcloud Files](https://nextcloud.com/files/) provides
  file sync/sharing with desktop clients; the household supplies its server.
- [Pinta](https://www.pinta-project.com/) covers drawing and image editing;
  [Gradia](https://apps.gnome.org/Gradia/) covers screenshot annotation.
  [Krita](https://krita.org/en/) is a specialized painting option.
- [Jellyfin clients](https://jellyfin.org/docs/general/clients/) connect to an
  existing server. [GNOME Audio Player](https://apps.gnome.org/Decibels/) is a
  focused local-audio option.
- [Steam's Flathub package](https://flathub.org/en/apps/com.valvesoftware.Steam)
  is community-maintained; [Heroic](https://heroicgameslauncher.com/) supports
  Epic, GOG and Amazon libraries; [Lutris](https://lutris.net/) covers broader
  game-library and compatibility workflows. [GNOME Chess](https://help.gnome.org/gnome-chess/index.html)
  supports local games against another person or an installed chess engine.
- Optional creative projects: [Kdenlive](https://kdenlive.org/),
  [Blender](https://www.blender.org/), [OBS Studio](https://obsproject.com/).
  The draft selects their Nixpkgs packages; the locked provider fixture checks
  availability. GUI and engine launches remain rollout checks.
