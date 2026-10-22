# Published v0.3.0 workstation activation

Date: 2026-10-22. Status: PASS for the checks listed below.

The user authorized activation of published Foundation v0.3.0, commit
`fdeb2ab7d88cb0ff69d25ed1a02589bc28ca7006`, replacing the workstation's
manually pinned local Foundation input. The consumer now declares
`github:closure-labs/foundation/v0.3.0`; its lock retains the exact published
commit and NAR hash. Unrelated personal input graphs were verified unchanged.

The profile remained byte-for-byte unchanged: schema 3, with Developer, Sales,
Trainer, Support, Executive and IT selected. No Personal role was enabled.
Explicit capabilities, personal modules and workstation host declarations
were preserved.

The guarded build and activation succeeded with a 5 GiB memory budget. The
previous configuration and Home Manager generation were retained. A later
reboot check confirmed:

- The selected Foundation release and schema-3 profile were still active.
- The installed Firefox launcher reported version 157.0.
- Espanso and the Dell panel service were running successfully; managed
  Flatpak installation completed successfully.
- The user confirmed that both standalone Firefox password-manager extensions,
  Bitwarden and 1Password, were healthy after the reboot.

This records the observed recovery; it does not establish which change fixed
the extension startup problem. Camera, fingerprint, suspend and docking still
need their separate physical checks. This activation does not qualify an OS
image or change the broader Foundation profile contract.
