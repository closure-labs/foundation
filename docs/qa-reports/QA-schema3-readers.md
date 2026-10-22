# F1b schema-3 readers and composition

Date: 2026-10-20. Foundation jj change `zlorynyq`, parent `tqkozxwn`
(`a0d4464b`). Finite reader fixtures are isolated in jj change `pqkymstk`, parent
`pvuoruok`, workspace `/tmp/finite-profile-readers`. No workstation activation,
profile conversion, publication or persistent input update in Finite occurred.

## Implemented behavior

- Public normalization dispatches schemas 2/3. The original strict schema-2
  implementation is extracted byte-for-byte into `normalize-profile-v2.nix`;
  legacy resolution stays bound to it, avoiding recursive dispatch.
- Actual Home Manager composition follows the schema-3 contract. Graphical Nix
  packages use the pinned nixGL Mesa wrapper; configured Firefox and patched
  Ghostty retain their recipes. Schema 3 disables the alternate generic-Linux
  GPU backend, while schema 2 retains it. No global graphics-library exports,
  implicit offload or Vulkan setting is introduced.
- Explicit capabilities work without roles: devops supplies terminal/shell
  configuration, support tools supply Espanso, and role-link capabilities supply
  desktop entries. Role flags reflect selected roles only. Optional packages are
  included once. Dell camera controls/Firefox PipeWire policy remain model-aware.
- Initialization accepts supplied schema 3 without conversion; apply/update
  preserve capabilities and custom fields. Default generators still emit schema
  2. The current selector refuses schema 3 before dialogs because its checklist
  cannot represent capabilities or Personal roles.
- The default catalog remains six roles. `homeCatalogForSchema 3` supplies ten
  roles and 31 capabilities. Reading schema 3 requires both actual-helper support
  and explicit selected-source capabilities; descriptor absence stays historical
  support. Target normalization cannot change the submitted schema.
- A legacy personal `nixGL` input name collision is rejected before filtering or
  follower rebasing, preserving its original declaration and pin. The new shared
  nixGL lock follows root Nixpkgs; all prior lock nodes/edges are unchanged.
  The locked upstream revision is `b6105297e6f0cd041670c3e8628394d4ee247ed5`.

## Validation

| Check | Result |
| --- | --- |
| Eight actual schema-3 compositions | Passed minimal, four Personal roles, capability-only, Dell mixed roles, and all roles/capabilities/packages |
| Real nixGL synthetic build/launch | Passed; desktop, D-Bus and systemd Exec paths reference the wrapped output; an argument containing spaces survives launch |
| Finite first-login fixtures | 18 passed, including supplied schema-3 saved/seeded profiles and older-helper rejection without replacement |
| Focused preservation/security fixtures | Passed initialization/apply/update preservation, schema-change rejection, legacy nixGL collision and absent-target-descriptor rejection |
| Legacy schema-2 32-case comparison | All 32 match exactly; catalogs differ only in advertised reader capabilities |
| Pinned CI | Pass; 90 Python tests, shell/Nix fixtures, actionlint and release metadata validation |
| Full `bash tests/nix-check.sh` | Passed locked-target fixtures, eight actual schema-3 cases, package availability and real home/profile-command/nixGL builds; all-role evaluations on both Bluefin variants |
| Finite pinned/new-source integration | Home contracts pass on both sources; all constructor proofs pass on the new source; actual compatibility adapter accepts schema-3 Family/Media plus notes with nixGL |

Finite home contracts passed with both its original pin and immutable Foundation
snapshot `4446c14a5a44aff9fc67771bd4de4d2a1523e5ea`, selected only through a
temporary `--override-input ... --no-write-lock-file`. Its saved lock is unchanged.
The synthetic wrapper is the flake's `checks.x86_64-linux.nixgl-wrapper`.

The schema-3 evaluator checks installed wrapped outputs against the pure plan,
rejects duplicate/raw GUI package entries, and verifies role flags, capability
services, camera/Chromium choices, Firefox recipe identity and backend settings.
The all-app case evaluates every proposed optional tool/launcher without building
or launching that full application collection.

The synthetic wrapper test uses the actual pinned Home Manager integration and
nixGL, not an identity/mock wrapper. It does not render a frame or establish GPU,
browser/media acceleration, camera, recording, chess-engine, Wine or Vulkan
compatibility on physical hardware. Those remain pre-migration rollout checks.

Read-only architect, QA and security reviews identified two negotiation/input
preservation issues during implementation; both were fixed with regression
tests. No blocking code finding remains. Reviews do not approve untested physical
graphics or app-data transfer behavior.

Evidence and pre-change source snapshot:
`/tmp/foundation-schema3-readers-dg_vjvqn/`. The next stage is A2's complete
capability editor, negotiated writer enablement and explicit migration/recovery.
