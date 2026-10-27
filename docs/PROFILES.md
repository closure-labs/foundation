# Profiles and hardware

Roles provide useful defaults. Capabilities add specific tools. Hardware settings describe the machine independently of either choice.

New profiles use schema 3. Every schema-3 home includes browser, credential and editor essentials plus desktop utilities. Shared applications are installed once even when several selections need them. For older profiles, see [Migration](MIGRATION.md).

## Choose roles

| Category | Role ID | Adds |
| --- | --- | --- |
| Professional | `developer` | Development operations, development tools and VSCodium |
| Professional | `sales` | Office documents and mail |
| Professional | `trainer` | Office, presentations, image editing and a Grist launcher |
| Professional | `support` | Development operations, Espanso and remote-connection tools |
| Professional | `executive` | Office, mail and a Vates Notes launcher |
| Professional | `it` | RustDesk remote desktop |
| Personal | `family` | LibreOffice and Thunderbird |
| Personal | `media` | VLC playback |
| Personal | `creative` | Pinta and Gradia image editing |
| Personal | `gaming` | GNOME Chess and its engine |

Combine roles with comma-separated IDs, such as `developer,creative` or `family,media`. Roles do not connect accounts, choose sync folders, download games or configure servers. The Support role's Espanso backend needs administrator-managed keyboard access on the host.

## Add capabilities and packages

Examples of capabilities you can add without selecting another role:

| Capability | Adds |
| --- | --- |
| `file-sync`, `notes`, `team-chat` | Nextcloud client, Joplin, Element |
| `painting`, `video-editing`, `modeling` | Krita, Kdenlive, Blender |
| `recording` | OBS Studio |
| `jellyfin`, `audio-player` | Jellyfin client, GNOME Audio Player |
| `steam`, `heroic`, `lutris` | Individual game launchers |
| `chromium`, `camera-controls` | Chromium, camera controls |

Optional package IDs are `hack-font`, `herdr`, `jj`, `opencode` and `uv`.

Use the [configuration selector](CONFIGURATION.md#change-roles-and-applications) to browse the catalog for your locked Foundation release. Contributors can inspect the complete [capability declarations](../modules/capabilities/) and [application declarations](../modules/apps/). Removing an explicit capability does not remove an application still required by a role.

## Generate a profile

```sh
nix run github:closure-labs/foundation/latest-release#home-profile -- \
  --foundation bluefin-dx --roles developer,creative \
  --packages jj --capabilities recording \
  --form-factor laptop --cpu intel --gpus intel-integrated --format json
```

The generator supplies your account identity and prints JSON or YAML; it does not activate changes. `--foundation` is required. Selections must be known and unique; empty role, package and capability lists are valid. Follow [Getting started](GETTING-STARTED.md) to initialize the generated profile.

## Host settings

| Field | Values |
| --- | --- |
| `system` | `x86_64-linux` |
| `formFactor` | `generic`, `laptop`, `desktop` |
| `cpu` | `generic`, `intel`, `amd` |
| `gpus` | Any unique combination of `intel-integrated`, `intel-discrete`, `amd-integrated`, `amd-discrete` |
| `model` | `generic`, `dell-xps-9350` |
| `camera`, `fingerprint` | `true` or `false` |

Omitted host fields use generic, empty or false defaults. Laptop profiles enable an overridable battery-percentage preference. Camera-equipped profiles add camera controls; fingerprint presence is recorded without configuring authentication.

The Dell model requires a laptop, Intel CPU and Intel integrated graphics. It adds panel policy and, when a camera is declared, Dell-specific IPU7 and Firefox camera settings. The generator's `--hardware dell-xps-9350-intel` adapter supplies those host defaults; `--camera` and `--fingerprint` can declare devices explicitly.

Schema 3 uses nixGL Mesa for graphical Nix applications, with verified Flathub exceptions. Bluefin owns drivers, firmware, authentication and system power policy. GPU declarations do not enable offloading or install another driver stack. Builds do not verify physical camera, graphics or suspend behavior.

## IPU7 camera health

`foundation home camera` detects a bound Intel IPU7 controller and enumerates camera formats with the host's libcamera tools. It does not capture images. `foundation home check` includes this diagnostic before the configuration build; camera warnings do not prevent building.

A legacy `/etc/libcamera/configuration.yaml` override can select an incompatible IPA module from `/var/lib/finite/libcamera/ipa`. The sensor may appear in PipeWire while Firefox has no usable camera formats. When that exact undefined-symbol failure is detected, Foundation tests the installed host IPA module and only offers a repair if format enumeration succeeds.

```sh
foundation home camera
foundation home camera --repair
```

The `hosts/camera/ipu7` aspect performs the same guarded repair at activation time. Detection runs on the target machine, not during pure flake evaluation. It applies to actual IPU7 controllers, not every Intel CPU. Unknown failures, missing host tools and conflicting personal overrides are reported without replacing them.

The repair writes `~/.config/systemd/user/wireplumber.service.d/70-foundation-ipu7.conf`, pointing WirePlumber at the matching host IPA directory. It does not edit system files, install drivers, alter camera permissions or restart audio automatically. When it is safe to interrupt audio and calls:

```sh
systemctl --user daemon-reload
systemctl --user restart wireplumber
```

Then reload the Firefox meeting page. The check verifies format enumeration; confirm video in the application separately. To undo the workaround, remove only the generated `70-foundation-ipu7.conf`, reload systemd and restart WirePlumber. Future activation will recreate it if the verified failure remains.
