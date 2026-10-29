# System-wide IPU7 camera policy

The OS owns the kernel drivers, libcamera and its matching IPA binaries.
Foundation owns the shared WirePlumber policy for IPU7 cameras. It hides raw IPU7
capture nodes and the unusable HM1092 infrared stream from desktop applications.
It does not package or select a private IPA binary.

Profiles with `host.camera = true` enable the installer during activation. The
installer checks for a bound IPU7 controller on the target workstation. It
explains why sudo is needed before installing:

```text
/etc/wireplumber/wireplumber.conf.d/50-foundation-ipu7.conf
/etc/wireplumber/wireplumber.conf.d/50-foundation-ipu7.sha256
```

These root-owned, readable files are the policy and its ownership record. If
both match the current package, subsequent activations skip sudo. Changed
policies update only if the installed content still matches the previous owned
hash; external edits and unsafe paths are preserved. A failed install clears its
success record and restores the previous policy, or removes the new file.
Building and dry runs never request sudo or write system configuration.
Services are never restarted automatically during activation.

The same installer is available without activating Home Manager:

```sh
nix run .#ipu7-system -- install --dry-run
nix run .#ipu7-system -- install
nix run .#ipu7-system -- uninstall
```

Opt out with `foundation.ipu7.system.enable = false;` before uninstalling to
prevent the next activation from reinstalling. Removing the aspect or rolling
back a Home Manager generation does not undo root-owned system files.

## Camera check

```sh
foundation home camera
foundation home camera --json
```

The diagnostic uses the OS `/usr/bin/cam` with host-default IPA selection. It
reports format availability without capturing video or changing any files. It
has no legacy repair mode and activation does not run the old repair diagnostic.
A successful format check does not establish image quality or browser capture.

After intentionally changing the policy, restart WirePlumber when audio and
calls can be interrupted, then reload the Firefox camera page:

```sh
systemctl --user daemon-reload
systemctl --user restart wireplumber
```

The system policy applies to each user's WirePlumber process on its next start.
Firefox's PipeWire camera preference remains in the user-level Firefox module.

## One-time cleanup of the current Finite workstation

This cleanup is operator-run, not a compatibility path in Foundation. On the
reviewed workstation, `/etc/libcamera/configuration.yaml` contains only the old
private IPA selection, and the private IPA directory contains its stale shared
object. After building the new installer, archive these active paths:

```sh
sudo mkdir -p /var/lib/foundation/retired-ipu7
sudo mv -n /etc/libcamera/configuration.yaml /var/lib/foundation/retired-ipu7/configuration.yaml
sudo mv -n /var/lib/finite/libcamera/ipa /var/lib/foundation/retired-ipu7/ipa
```

Check that neither original path remains. Do not replace any existing backup.
The root archive retains rollback copies without being selected by libcamera.
Remove the old generated per-user environment override and activate the new
Foundation generation, which also removes the former Home Manager camera policy:

```sh
rm ~/.config/systemd/user/wireplumber.service.d/70-foundation-ipu7.conf
```

Then restart WirePlumber as above and run `foundation home camera`. Confirm
**Built-in Front Camera** video in Firefox. No reboot is required.
