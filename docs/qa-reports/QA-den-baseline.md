# Targeted Den/gen baseline upgrade

Date: 2026-10-20. This is stage D1 of the profile refactor. It changes dependency
pins and documentation only; no application allocation, profile format, hardware
setting, or activation behavior is changed.

## Selected dependencies

| Input | Before | After |
| --- | --- | --- |
| Den | `c7ef3f11126f24878f5c69527b4230f51c839803` | `27b25eeddd934dca1647025defec3275dcf9e9b9` |
| gen | `0004f3c9dfd5634f47ee72575e56c54883450bcf` | `6427d42770e3b1c283b8caf2929ed622e551ebb9` |

The selected Den revision matched public upstream `main` at inspection. The gen
revision and its entire locked graph, including follows edges, match that Den
revision's CI lock. Updates were performed with `nix flake update den` and
`nix flake update gen`, with the explicit gen URL aligned between them. The
unrestricted maintainer update script was not used.

The lock comparison identified 25 changed/added nodes, all Den or gen libraries.
Existing nixpkgs, weekly nixpkgs, Herdr's unstable nixpkgs, Home Manager, devenv,
Determinate and nix-flatpak nodes are unchanged. Existing configuration,
controller, and test source files are also unchanged by D1.

## Validation

| Check | Result |
| --- | --- |
| Lock graph restriction | Passed: changed nodes confined to Den/gen. |
| Tested gen closure | Passed: `locked_graph` equality against selected Den CI. |
| `bash tests/check.sh` | Passed, including 23 consumer/update and 11 classification/selector tests. |
| Pinned `tests/ci.sh` | Passed: workflow lint, 45 discovered Python tests and release metadata. |
| `bash tests/nix-check.sh --no-build` | Passed flake and selectable-profile evaluation. |
| `bash tests/nix-check.sh`, one job/core | Passed full Home Manager/profile-command builds and all-role evaluation on both foundations with Dell hardware. |
| 32-case composition comparison | Passed: every captured field matches the validated pre-upgrade matrix; Foundation and actual Finite catalogs match exactly. |

The previous classification slice's validated snapshots are the comparison
baseline. Their configuration/controller/test sources match the starting D1
snapshot; only source-embedding Foundation helper paths are normalized, as in
that slice's [validation report](QA-profile-classification.md). Captured fields
include package outputs, Flatpaks, user services, environment, identity, state
version and Firefox package for both foundations/hardware IDs and all eight
role/package selections.

Local evidence is retained in `/tmp/foundation-den-refactor-fuhqifvp/`:
the starting working tree, original lock, changed-node list, updated matrix,
and final comparison summary. No flake input references that temporary path.

## Personal proposal and next stage

The user confirmed lightweight Personal defaults with optional larger apps and
launchers. [Family, Media, Creative and Gaming](../PERSONAL-PROFILES.md) are
documented proposals, not newly enabled roles. Existing schema-2 app sets remain
unchanged. The next implementation stage is N1, target-revision structural
normalization/validation, before new profile writers or app splitting.

No home was activated, no firmware operation was performed, and no release was
published.
