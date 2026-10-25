# Profiles and hardware

Roles provide useful defaults. Capabilities add specific tools. Hardware settings describe the machine independently of either choice.

New profiles use schema 3. Every schema-3 home includes browser, credential and editor essentials plus desktop utilities. Shared applications are installed once even when several selections need them. Existing schema-2 profiles keep their original application sets until [explicitly converted](ACTIVATION.md#convert-an-existing-profile).

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

Use `finite-configure` to browse the catalog for your locked Foundation release. Contributors can inspect the complete [capability declarations](../modules/capabilities/) and [application declarations](../modules/apps/). Removing an explicit capability does not remove an application still required by a role.

## Generate a profile

```sh
finite-home-profile --foundation bluefin-dx --roles developer,creative   --packages jj --capabilities recording   --form-factor laptop --cpu intel --gpus intel-integrated --format json
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
