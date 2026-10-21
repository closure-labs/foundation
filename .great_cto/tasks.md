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
| profile-future-readers | F1b future-format readers | Complete | CI90, full Nix build/checks, eight actual schema3 compositions, real nixGL synthetic launch, exact32legacy parity, old/new-source Finite contracts, constructor/adapter proofs and architect/QA/security review pass. Default writers stay2. Foundation jj `zlorynyq`; Finite fixtures `pqkymstk`. |
| profile-writers-migration | A2 capability editor and migration | Complete | Versioned pinned-target preview/editor APIs, explicit conversion approval, capability selection and symlink-preserving recovery implemented. CI115/full Nix checks, locked-target editing and immutable-source Finite home contracts pass; default generators remain schema2. jj `uvtpxqsw`. |
| profile-host-composition | H1 form factor and hardware aspects | Complete | Structured schema3 host and independent machine/CPU/GPU/model aspects implemented. CI124, nine pure host tests, nine actual Home Manager host cases, full Nix builds/checks and QA review pass. Native lid behavior retained. jj `ommsszxm`. |
| profile-workstation-build | This workstation build and preflight | Complete | Full schema3 workstation build passed at immutable source `7eed78af` (jj `rkxnuwlv`). Fixed icon build-file collision and local pinned-source helpers; CI131, full Nix checks, built-command/launcher/Brew checks and CLI/security review pass. Original/live configuration and generation unchanged. |
| profile-workstation-conversion | This workstation only | Complete | User approved and guarded activation succeeded on 2026-10-21. Live schema3/cache match candidate; personal modules preserved; helpers, selected Flatpaks and user services pass. Active nixGL probe confirms accelerated Intel OpenGL. Original configuration/generation retained. |
| profile-current-generation | W3 schema-3 default generator/catalog | Complete | JSON/YAML generator, host flags, default templates and shared current catalog implemented. CI141, packaged sandbox test, catalog equality, eight actual schema3 cases, nine host cases, full Nix build/checks and immutable-source consumer-template build pass. CLI/library/security/QA reviews found no blockers. Active workstation files/pin unchanged. jj `oqosqtnt`. |
| profile-update-integration | U1 Finite update hardening | Complete | Root-first guard, scoped Bash startup hook and private marker retain Just delegation and gate Foundation after successful update commands. Ten real-Just update tests pass; hermetic home check passes both 28-test runs, four maintenance tests, profile/template/seed ISO contracts and hook ShellCheck. Architecture/CLI/security/QA reviews pass. Isolated Finite jj `pmpytlzt`, workspace `/tmp/finite-profile-readers`; live files/pins unchanged. |
| profile-finite-writers | F3 negotiated first-login and seed writers | Complete | Fresh selection negotiates schemas2/3; schema3 seeds share bundled validation, target identity and structured hosts; explicit schema2 catalogs identify their format. FoundationCI141/publicAPI pass; pinned2 home contracts pass; current3 passes ten seed tests,32integration,fourmaintenance. Catalog restrictions and publication cleanup regressions pass; architecture/CLI/library/security/QA approve. Finite jj `wksovumv`, workspace `/tmp/finite-profile-readers`; pins/live files unchanged. |
| profile-personal-proposal | Personal role recommendations | Complete | User confirmed lightweight defaults and optional larger apps/launchers; Family, Media, Creative and Gaming proposed without moving apps/enabling roles. |
| profile-release-preparation | R1 Foundation0.3.0 candidate | Validation | Final release notes and matching metadata prepared in jj `ywyltuox`; immutable candidate CI/build/archive/Finite integration validation in progress. No remote release or pin adoption. |
| profile-release | Publication | Awaiting prepared ship gate | No remote release published. Candidate preparation precedes approval; this workstation's separately approved activation remains unchanged. |

Artifacts: [architecture](../docs/architecture/ARCH-profile-refactor.md),
[plan](../docs/plans/PLAN-profile-refactor.md),
[A1 contract](../docs/architecture/ARCH-profile-schema3.md),
[A1 validation](../docs/qa-reports/QA-profile-application-contract.md),
[F1b validation](../docs/qa-reports/QA-schema3-readers.md),
[A2 editor](../docs/architecture/ARCH-profile-editor.md),
[A2 validation](../docs/qa-reports/QA-profile-editor.md),
[H1 contract](../docs/architecture/ARCH-host-composition.md),
[H1 validation](../docs/qa-reports/QA-host-composition.md),
[workstation conversion](../docs/plans/PLAN-workstation-conversion.md),
[workstation build](../docs/qa-reports/QA-workstation-build.md),
[workstation activation](../docs/qa-reports/QA-workstation-activation.md),
[W3 generation](../docs/architecture/ARCH-profile-generation.md),
[W3 validation](../docs/qa-reports/QA-profile-generation.md),
[U1 update integration](../docs/qa-reports/QA-update-integration.md),
[F3 writer readiness](../docs/qa-reports/QA-finite-profile-writers.md).
