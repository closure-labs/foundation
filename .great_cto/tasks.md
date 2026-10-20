# Profile refactor planning

Beads CLI is unavailable in this session; this file is the skill's task-tracking
fallback. Implementation uses the existing staged approach; the user explicitly
requested the first slice after the architecture and plan were presented.

| ID | Phase | Status | Result or next condition |
| --- | --- | --- | --- |
| profile-discovery | Discovery | Complete | User confirmed classify first, split apps later; firmware manually updated. |
| profile-architect | Read-only architecture review | Complete | Additive metadata first; identified later reader/validator migration prerequisites. |
| profile-plan | Implementation planning | Complete | Architect and PM reviews incorporated; baseline fixtures and documentation checks pass. |
| profile-implementation | P0–P4 sequential code work | Complete | 11 focused tests, pinned CI (45 Python tests), full Nix build, 32-case parity, actual Finite projection and profile-generator comparison passed. |
| profile-den-baseline | D1 targeted Den/gen update | Complete | Full build, pinned CI (45 tests), 32-case composition parity and exact tested gen graph passed; unrelated pins preserved. |
| profile-validation-bridge | N1 target-revision normalization | Complete | Pure normalizer, locked-target API/catalog lookup, explicit schema handling and atomic staged writes; CI61/full build, 32-case parity, retained-helper compatibility and QA/security review passed. |
| profile-finite-readers | F1a existing reader readiness | Complete | Current schema-1/2 dispatch preserves supplied data; typed classification and actual-helper/selected-source capability checks implemented. CI68, Finite16+4, full Foundation build, old/new-source Finite checks, 32-case parity and QA/security review passed. Finite edits isolated in jj change `pvuoruok`, workspace `/tmp/finite-profile-readers`. |
| profile-application-contract | A1 Personal format/application contract | Complete | Isolated schema-3 resolver/preview, full legacy app inventory and Nixpkgs/nixGL policy with verified exceptions. CI81, 13 focused tests, all 53 locked Nix providers, full no-build Nix checks, exact existing catalog/runtime-source parity and architect/QA/security review pass. jj change `tqkozxwn`. |
| profile-future-readers | F1b future-format readers | Not started | Implement the A1-defined format before A2 enables new writers; F1a does not claim schema-3 support. |
| profile-personal-proposal | Personal role recommendations | Complete | User confirmed lightweight defaults and optional larger apps/launchers; Family, Media, Creative and Gaming proposed without moving apps/enabling roles. |
| profile-release | Publication/activation | Not started | Separate release action after code review and validation; no automatic deployment. |

Artifacts: [architecture](../docs/architecture/ARCH-profile-refactor.md),
[plan](../docs/plans/PLAN-profile-refactor.md),
[A1 contract](../docs/architecture/ARCH-profile-schema3.md),
[A1 validation](../docs/qa-reports/QA-profile-application-contract.md).
