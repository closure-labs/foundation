# Host composition

H1 separates the machine from Professional/Personal application choices.
Schema-3 profiles declare a `host`; the same roles and capabilities can be used
on a laptop, desktop or workstation with independently selected Intel/AMD parts.

The user clarified the scope on 2026-10-20: Foundation remains a broader refactor;
only conversion is limited to the current Dell workstation. Existing schema-2
code is retained where useful, with no additional cross-version migration
framework or downstream compatibility matrix required for this stage.

## Profile declaration

```json
{
  "schema": 3,
  "foundation": "bluefin-dx",
  "host": {
    "system": "x86_64-linux",
    "formFactor": "desktop",
    "cpu": "intel",
    "gpus": ["intel-integrated", "amd-discrete"],
    "model": "generic",
    "camera": true,
    "fingerprint": false
  },
  "roles": ["developer", "creative"],
  "capabilities": [],
  "packages": ["jj"],
  "identity": {"username": "dale", "homeDirectory": "/var/home/dale"}
}
```

| Dimension | Values | Behavior |
| --- | --- | --- |
| `system` | `x86_64-linux` | Selects the package platform; other architectures are outside H1. |
| `formFactor` | `generic`, `laptop`, `desktop` | Selects the machine aspect. Laptop adds an overridable GNOME battery percentage preference. |
| `cpu` | `generic`, `intel`, `amd` | Selects a CPU aspect and records its vendor. |
| `gpus` | Any duplicate-free subset of `intel-integrated`, `intel-discrete`, `amd-integrated`, `amd-discrete` | Includes each selected GPU aspect, independent of CPU vendor. Empty selection is valid. |
| `model` | `generic`, `dell-xps-9350` | Dell includes its existing panel policy and, when a camera is declared, its IPU7 filtering and Firefox camera policy. |
| `camera` | Boolean, default false | Adds camera controls on any equipped host; Dell-specific camera configuration also requires the Dell model. |
| `fingerprint` | Boolean, default false | Records presence; does not enroll fingers or configure authentication. |

Omitted fields use generic/empty/false defaults. Unknown fields, unknown values,
invalid types and duplicate GPUs fail validation. GPU order is canonical.
The Dell model requires laptop, Intel CPU and Intel integrated graphics;
additional discrete GPUs are allowed. A model declaration does not imply
fingerprint enrollment or working drivers.

`lib.hosts` exports the choices and pure normalizer. The schema-3 catalog exposes
the choices as `hosts`. Normalized schema-3 profiles always contain the complete
host object. The role/capability editor preserves it; hardware selection is
currently made in profile JSON rather than an additional graphical dialog.

## Aspect ownership

Den includes `features.machines.<formFactor>`, `features.hardware.cpu.<cpu>`,
each `features.hardware.gpu.<gpu>`, and `features.hardware.models.<model>`.
The aggregate host module writes `~/.config/finite/host.json` and host session
metadata; the CPU/GPU leaves add the selected markers. A desktop never includes
the laptop battery preference or Dell panel unit.

CPU/GPU aspects currently declare capabilities, without speculative vendor
tuning. All supported schema-3 graphical Nix packages use the existing nixGL
Mesa integration. GPU selection does not enable offloading, Vulkan, global
library paths, driver overrides or kernel parameters.

Bluefin owns the kernel, Mesa, firmware/microcode, PAM/fprintd, power daemons and
lid handling. There is no manufacturer-wide Dell aspect: the current user-space
rules are specific to this model. Firmware has already been updated manually.

The laptop preference uses GNOME's
[battery percentage setting](https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/blob/master/schemas/org.gnome.desktop.interface.gschema.xml.in).
Suspend and docking continue to follow the installed desktop/logind behavior;
[logind documents](https://www.freedesktop.org/software/systemd/man/latest/logind.conf.html)
the external-display/dock handling and inhibitor precedence. An AC supply and
keyboard alone are not treated as proof of docking. A custom closed-lid rule
needs a concrete predicate and physical testing before implementation.

## Small hardware adapter and local conversion

The old `hardware` field is derived: Dell model maps to
`dell-xps-9350-intel`; other hosts map to `generic-x86_64`. New declarations may
omit it. Supplying a contradictory value fails. This keeps current image checks
and session consumers working without a second hardware selection axis.

An absent host maps from those two current hardware IDs. The Dell adapter
declares its camera, leaving fingerprint false until explicitly selected.
This is the sole host-shape adapter. A custom schema-2 field named `host` blocks
conversion, preserving its data rather than silently giving it a new meaning.

The [workstation candidate](../../examples/workstations/dale-xps-9350.json)
records the observed Dell laptop, Intel integrated graphics, camera and
fingerprint reader. It keeps all six existing Professional roles and explicitly
retains applications that are no longer shared defaults. Its normalized copy
was [activated on this workstation](../qa-reports/QA-workstation-activation.md)
after the full build and user approval. See the
[single-workstation conversion plan](../plans/PLAN-workstation-conversion.md).

## Acceptance

Pure tests cover shape validation, canonical GPUs, conflicting adapters,
camera presence, unchanged host data during role edits, reserved-field
collisions and the workstation's application identities. Sequential Home
Manager evaluations cover generic, Intel/AMD laptops and desktops, mixed
vendor GPUs, integrated/discrete combinations, Dell camera-disabled and the
workstation candidate. They inspect the selected aspect effects and graphics
backend, rather than only testing a list of aspect names.

Physical suspend, closed-lid docking, GPU/media acceleration, camera capture and
fingerprint login remain session checks. Evaluations cannot establish them.
