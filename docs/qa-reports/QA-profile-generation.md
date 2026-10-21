# Schema-3 default generation validation

Date: 2026-10-21. W3 follows the successful single-workstation conversion and
implements [new profile generation](../architecture/ARCH-profile-generation.md)
for Foundation broadly. No activation or live source-pin update is part of W3.

## Scope and evidence

The default generator, root/consumer-template profiles and shared current
catalog use schema 3. Professional and Personal roles can be combined with
optional capabilities and independent Intel/AMD laptop/desktop host choices.
Existing schema-2 profiles retain their reader/editor behavior. Legacy/subset
custom catalog domains explicitly request `mkHomeCatalog { schema = 2; ...; }`.

Local evidence is retained in `/tmp/foundation-profile-writer-e527ait8/`,
including the pre-change tree, CI/build logs and live-state baseline/result.
The jj implementation change is `oqosqtnt`.

## Validation results

| Check | Result |
| --- | --- |
| Focused generation suite | Ten tests pass: canonical selections, mixed classifications, structured host and Dell adapter, invalid/duplicate/injection rejection, JSON/YAML round trip, running-image checks, bundled-source boundary, shared catalog and identical template defaults |
| Pinned CI | 141 Python tests, shell/aspect fixtures, actionlint and release metadata checks pass |
| Packaged sandbox check | Real installed generator emits equivalent JSON/YAML, handles Dell presence overrides, rejects duplicates before stdout, exposes current catalog and leaves the consumer absent |
| Public catalog/constructor integration | Default API, applications and flake package catalogs are equal; current custom image mappings and explicit schema-2 custom constructor pass |
| Actual schema-3 compositions | All eight cases pass, including each Personal role, mixed Dell/work/creative, all roles/optional applications and nixGL recipe/backend assertions |
| Full host/build checks | All nine host cases, five flake checks including the default Home Manager generation build, and all-work-role evaluations on both Bluefin variants with schemas 2 and 3 pass |
| Consumer-template package | Builds from immutable jj snapshot `65a83e860257d7f0a1ea7b9c854acc4baee878b0`; emitted profile exactly matches the schema-3 default |
| Source review | CLI, library/API, security and QA reviewers found no blockers; QA independently reran all ten generation tests |
| Formatting | Changed Nix files pass Alejandra; all Nix expressions parse in CI |
| Workspace boundaries | Dependency lock, personal module defaults, live consumer digest and active generation match the baseline |

The first packaged attempt exposed Nix's default state-directory initialization
inside the sandbox. Explicit `--store dummy://` fixes it while retaining pure
evaluation. The packaged check passes without daemon access, flake evaluation,
network access or an initialized consumer. Two legacy transaction fixtures now
declare schema 2 explicitly so they remain independent of the new template
default. No validation check was disabled.

## Limits and handoff

The workstation stays at immutable source `7eed78af934634b253a84e7bbaba758234d870b2`
and generation `/nix/store/5ykg36q778pk5dm7zvbzlp3zcy7lk4bi-home-manager-generation`.
Finite's pin adoption and first-login/cloud-init default changes remain a
separate task. No new migration matrix or schema-2 writer is introduced.

Physical camera/fingerprint, suspend/dock and media/game behavior retain the
hands-on checks in the [activation report](QA-workstation-activation.md).
New declarations alone do not establish those results. The workstation's
previously verified accelerated Intel OpenGL result remains recorded there.
