# Password-manager integration

The `home/password-managers` aspect detects a Nix 1Password GUI package in the
final Home Manager package list, including nixGL wrapping. It does not install
1Password. The CLI alone does not enable browser integration. Multiple distinct
GUI outputs require an explicit `foundation.passwordManagers.onePassword.package`.
Set `foundation.passwordManagers.enable = false` to disable this integration.

The aspect declares Firefox and Chromium native-messaging manifests with the
vendor extension allowlists. Their helper destination is versioned, so an older
Home Manager generation can retain its own helper. Browser trust verification
remains enabled; valid manifests alone do not prove a browser/app connection.

## Host setup

A Nix store executable cannot acquire setgid permissions through Home Manager.
Foundation builds the pinned Nixpkgs native security wrapper, with its exact
helper target compiled in, and emits `foundation-password-managers.json` beside
the generation's activation entry. The requirement records the selected output,
the real helper and wrapper paths, and their SHA-256 digests. The generation
retains references to their closures. No privilege bits are set in the store.

Resolve the generation link with `readlink -f` first. On Finite, inspect that
canonical immutable store JSON file with the OS-owned
`/usr/libexec/finite/password-manager-setup inspect --requirement FILE`.
After reviewing those exact artifacts, an administrator installs them using
`install` with the requirement and the literal `--approve-package`,
`--approve-helper-sha256`, and `--approve-wrapper-sha256` values printed by
inspection. The requirement is a request, not authorization. Each changed
helper/version needs another explicit privileged invocation.

Installation uses a root-owned versioned destination, group `onepassword`, and
mode `2755`, with no setuid permission or user membership in that group. It
retains Nix GC roots and the normal SELinux label. Home Manager never calls sudo,
installs a privilege policy, or refreshes a helper automatically. Other hosts
must supply equivalent administrator-owned integration.

Build-only checks do not install helpers. Preparation rejects an unmet or
inconsistent requirement before running generation preparation or activation.
Keep old helpers and their roots while any retained generation needs them.
Use the installer's status and conservative removal checks when retiring one.
Run removal while Home Manager operations are quiescent; concurrent activation
and removal are not supported.

## Adopting existing browser manifests

Back up the exact existing 1Password native-messaging files before adopting
declarative ownership. Move only the reviewed conflicting files out of the way;
do not delete browser profiles, other native hosts, extension settings or vault
data. Obsolete files for unused browsers can be retired after the active Firefox
and Chromium manifests pass a real desktop-to-extension connection check.

After installation and activation, restart the desktop app and affected browsers
when convenient. Verify connection after login, an application update and
rollback. Do not bypass browser trust checks to make the test pass.
