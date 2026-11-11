# Dell XPS 13 9350 GRUB console

The Dell model aspect enables GRUB's graphical terminal on EFI OSTree hosts
using bootupd's `console.cfg` override. On the tested workstation, the native
EFI console swept the cursor across the screen for 2–3 seconds before the menu
countdown started. Explicit native console output did not help; graphical
output removed the delay. This is a hardware observation, not a claim about all
Dell firmware.

## Activation and administrator access

A normal Home Manager activation with `host.model = "dell-xps-9350"` runs
`foundation-dell-grub install`. It first checks the actual Dell model, EFI and
OSTree host markers. Unsupported hosts are skipped. Evaluation, building and
Home Manager dry runs do not request sudo or change the boot partition.

Before sudo, the command explains that it will manage the console override,
font and backup in `/boot/grub2`. It invokes the fixed Nix-store installer and
Python interpreter with isolated Python imports through `/usr/bin/sudo`.
Authentication failure fails the activation step; it is not reported as success.
Home Manager activation is not transactional: earlier user configuration steps
may already have run. Re-run activation after resolving authentication errors.

After a successful privileged install, Foundation writes a root-owned, readable
receipt to `/var/lib/foundation/dell-grub/receipt.json`. It binds the installer
policy, machine identity and backing boot filesystem. An unchanged activation
checks this receipt without reading `/boot` and skips sudo. Missing or invalid
receipts, a changed installer policy or a different boot filesystem require a
new explained privileged install. The private backup remains under `/boot`.

The receipt records what Foundation applied; it does not detect administrator
edits to protected boot files after installation. Explicit verification bypasses
the receipt, inspects the console, font and backup, and refreshes the receipt
only on success:

```sh
foundation-dell-grub verify
# Or: nix run .#dell-grub -- verify
```

Verification failures invalidate the public receipt. Uninstall invalidates it
before restoring the previous configuration. The font is copied from the host's
`/usr/share/grub/unicode.pf2`; GRUB never needs the Nix store during boot.
An existing installation retains its copied font across host font updates.

The installer requires a root-owned, non-writable-by-other-users boot directory
and a bootupd-generated configuration that sources `console.cfg`. It preserves
existing console content, appends the graphical console commands, and records
the original bytes, ownership and mode in a root-owned backup directory:

- `/boot/grub2/console.cfg`: previous content followed by the managed block.
- `/boot/grub2/foundation-dell-grub/unicode.pf2`: copied GRUB font.
- `/boot/grub2/foundation-dell-grub/original.cfg` and `manifest.json`: restore state.

Individual file replacement is atomic and synced. The font and backup are
installed before the console references them. The operation is serialized
against other copies of this installer. It is not a multi-file filesystem
transaction or a lock against bootupd/administrator operations: avoid concurrent
boot maintenance. An interrupted preparation with incomplete backup state fails
closed and requires inspection. An interrupted final console replacement can
be retried or uninstalled using the recorded state.

The command does not regenerate `grub.cfg`, change EFI boot order, reinstall
GRUB, edit kernel arguments or change timeouts. No reboot occurs automatically.
The display change takes effect at the next boot.

## Flake app

The same installer is exported independently of Home Manager:

```console
nix run github:closure-labs/foundation#dell-grub -- install --dry-run
nix run github:closure-labs/foundation#dell-grub -- install
nix run github:closure-labs/foundation#dell-grub -- uninstall
```

These commands become available after this change merges. Pin a reviewed
revision when applying boot changes. In this checkout use `nix run .#dell-grub`.
The flake app uses the same hardware checks, explanation and sudo request.
It does not require selecting the Dell aspect in a personal profile.

## Disable and uninstall

First opt out in your personal module so the next activation does not reinstall:

```nix
foundation.dellGrub.enable = false;
```

Then restore the previous configuration:

```console
foundation-dell-grub uninstall
```

The command remains installed with the opt-out enabled. If removing the Dell
aspect entirely, run the uninstaller before removing the aspect. Home Manager
generation rollback and removing the aspect do not automatically revert root-owned
boot files. The uninstaller explains its sudo request and restores the original
console file (or removes it if originally absent), then removes its own state.

If the console, backup or copied font has been edited externally, installation
and removal stop without overwriting those edits. Reconcile them before retrying.
Symlink targets are rejected. An existing manual override, including the earlier
workstation test, is preserved as the original configuration; uninstalling restores
that override. The manual `finite-test-unicode.pf2` font is not owned or removed by
this installer. To return to the original firmware console, remove the manual
override before the first managed installation.

## Validation

`python3 tests/test_dell_grub.py` tests repeat installation, restore semantics,
external edits, backup/font tampering, unsafe paths, interrupted console commits,
hardware gating, dry runs and explanation-before-sudo ordering with temporary
fixtures. It never writes the workstation's `/boot`. The original graphical
configuration was verified by the workstation operator; the packaged installer
still requires host activation and reboot acceptance.
