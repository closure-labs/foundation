# Camera diagnosis and repair

Use this guide when an Intel IPU7 camera is missing from Firefox, even though the system lists a built-in camera. The camera commands are available starting with Foundation **0.4.1**. For normal release updates, see [Activation](ACTIVATION.md#update-foundation); for older command names and configurations, see [Migration](MIGRATION.md).

## 1. Check the camera

```sh
foundation home camera
```

For structured output, add `--json`. From a reviewed Foundation checkout, use the native app:

```sh
nix run path:.#home-camera -- --json
```

The check detects a bound IPU7 controller and asks the host's `/usr/bin/cam` to enumerate camera formats. It does not capture images or change configuration. `foundation home check` also runs this diagnostic before building; camera warnings do not prevent the configuration build.

| Result | Next step |
| --- | --- |
| `ok` | Formats are available. Check Firefox's camera selection and site permission, then test video. |
| `not-applicable` | No bound IPU7 controller was detected. This repair does not apply; it does not prove that other cameras work. |
| `repair-available` | The known module mismatch was found and the host replacement passed validation. Continue below. |
| `configured` | The verified override already exists. Restart the service if it has not loaded the override yet. |
| `conflict` | A personal override occupies the repair path. Review it manually; Foundation leaves it unchanged. |
| `unavailable` or `unresolved` | Check the reported error, host tools, drivers and libcamera installation. Foundation has no verified automatic repair for this result. |

## 2. Apply the verified repair

```sh
foundation home camera --repair
```

The repair is limited to an IPA processing-module ABI mismatch: `/etc/libcamera/configuration.yaml` selects an old module under `/var/lib/finite/libcamera/ipa`, which fails with an undefined symbol and cannot initialize the software image processor. A camera can still be listed in that state while exposing no formats Firefox can use.

Foundation tests the matching host IPA directory first. Only if format enumeration succeeds does it write:

```text
~/.config/systemd/user/wireplumber.service.d/70-foundation-ipu7.conf
```

The drop-in sets `LIBCAMERA_IPA_MODULE_PATH` for WirePlumber alone. If `XDG_CONFIG_HOME` is set, the path is under that directory instead. System files, camera permissions and driver packages are unchanged. Conflicting files and symlinks are preserved.

The [IPU7 aspect](../modules/hosts/camera/ipu7/_feature.nix) performs the same guarded repair during Home Manager activation. Hardware detection runs on the target host at activation time; pure flake evaluation does not inspect the build machine. An Intel CPU alone does not trigger the repair.

## 3. Restart when audio can be interrupted

The repair does not restart services automatically. Once it is safe to interrupt audio and calls:

```sh
systemctl --user daemon-reload
systemctl --user restart wireplumber
```

Reload the Firefox meeting page, select **Built-in Front Camera**, and check that video appears. Bluetooth headsets may need reconnecting after the service restart. Successful format enumeration is a diagnostic result; the application test confirms usable video.

The Dell XPS 9350 profile already enables Firefox's PipeWire camera policy and filters unusable raw/IR camera nodes. Keep the [host declaration](PROFILES.md#host-settings) accurate. The IPA repair does not configure browser policies for every other IPU7 model or install missing host drivers.

## Undo the workaround

Remove only the Foundation-generated `70-foundation-ipu7.conf` above, then reload systemd and restart WirePlumber as in step 3. If you have edited that file, preserve your changes first. A later activation will recreate the workaround if the same verified failure remains.
