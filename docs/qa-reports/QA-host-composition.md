# H1 host composition validation

Date: 2026-10-20. Foundation jj change `ommsszxm`, parent `uvtpxqsw`
(`453a8f89`). The broader Foundation refactor continues; migration validation
targets only Dale's current workstation. No live configuration files, active
generation, firmware, OS services or saved consumer pins were changed.

## Implemented behavior

- Schema-3 `host` declares platform, form factor, CPU, integrated/discrete GPUs,
  model, camera and fingerprint presence. Validation rejects unknowns, duplicate
  GPUs, invalid device types and inconsistent Dell selections.
- Den includes independent machine, CPU, GPU and model aspects. Laptop adds an
  overridable battery percentage preference; Dell retains its panel policy and
  conditional IPU7/Firefox camera configuration. Camera controls follow declared
  presence on generic hosts too.
- CPU/GPU aspects record capability selections. Existing nixGL Mesa handles
  graphical Nix packages; no new drivers, offload, Vulkan, power daemon, lid
  controller, firmware updater or authentication configuration is introduced.
- A small adapter derives the existing hardware ID; conflicting declarations
  fail. Schema-3 normalization includes the complete host; role editing preserves
  it. Conversion blocks a pre-existing schema-2 custom `host` field.

## Checks

| Check | Result |
| --- | --- |
| Pure host suite | Nine passed: declarations, adapters, validation, mixed GPUs, Dell constraints, camera presence, role-edit preservation, workstation inventory and reserved-field collision |
| Pinned CI | All 124 Python tests, shell/Nix fixtures, actionlint and release metadata passed |
| Nine actual Home Manager host cases | Passed generic; AMD/Intel laptops; Intel desktop + AMD discrete; AMD desktop + Intel discrete; AMD and Intel integrated/discrete pairs; Dell camera-disabled; actual workstation profile |
| Host effect assertions | Correct environment markers, laptop-only battery preference, model-only panel unit, conditional IPU7/Firefox policy, unchanged state version and nixGL backend; no unintended power/auth units or graphics environment overrides |
| Existing schema-3 compositions | All eight passed actual membership, wrapping, service and backend assertions |
| Full Nix checks/builds | Passed selected-source validation/editor, host cases, home/profile-command builds, previously built real nixGL synthetic check and current all-role evaluations |
| Formatter/static checks | Changed Nix files formatted; new host modules and evaluation fixture passed deadnix |
| Read-only QA review | Approved after fixing the reserved-field collision; nine host and 22 editor tests passed independently |
| Workstation staged evaluation | Dry-run evaluation passed against immutable Foundation snapshot `b5800a90494040dc1a54fe357c7b5422b2c8f794` |
| Personal input pins/assets | Devenv's 13 locked nodes and the personal unstable input unchanged; local modules/Espanso assets preserved byte-for-byte |
| Workstation merged launchers | Passed: nine custom GUI packages wrapped exactly once; Element/Bitwarden helper scripts and 1Password/Nextcloud/Firefox autostart point at the selected wrapped outputs; flags/environment preserved |
| Full workstation activation-package build | Not started: dry run requires 22.7 GiB unpacked/8.4 GiB download; only 9.6 GiB free on `/nix` |

The review found that a fully normalized old custom `host` field could otherwise
gain operational meaning during conversion. Both pure preview APIs now reject
that collision; the controller rejects it before querying the selected source
or changing the live tree. An early evaluation also caught a duplicate Nix
attribute definition in the Dell module, fixed before the passing full checks.

## Workstation candidate and limits

The checked-in candidate retains all 48 current Foundation application identities,
including the four selected optional packages, and selects only the existing
Professional roles. Provider changes remain explicit; Flatpak data is retained.
The temporary consumer wraps its custom graphical package/launcher bindings,
preserving Element's X11 argument, Bitwarden's environment, autostart choices,
CLI tools, Zsh/Deja and private Espanso configuration. Only the staged Foundation
source changes; live files and current Home Manager generation remain untouched.
The merged audit passed within the existing 3 GiB limit after removing redundant
package-set imports from the audit itself; an earlier duplicate-set audit exceeded
that limit. This audit inspects evaluated script/declaration contents and does
not establish runtime graphics or activation success.

A package build is not established by a passing evaluation. Disk capacity must
be resolved before the full workstation build. Existing generations were not
garbage-collected or deleted to make space. The candidate is not activated;
graphics/media, camera capture, docking/suspend and application-data checks
remain physical-session acceptance work.

Evidence and original source snapshot:
`/tmp/foundation-host-composition-in7p4_ky/`. The temporary consumer is
`workstation/`, the original is `workstation-original/`, and the current generation
is recorded in `previous-generation.txt`. See the
[host contract](../architecture/ARCH-host-composition.md) and
[local conversion plan](../plans/PLAN-workstation-conversion.md).
