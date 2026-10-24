# Foundation 0.3.3 candidate validation

Date: 2026-10-23. Status: local build checks passed. Final archive and
immutable-source evidence is recorded separately in the candidate manifest.

Candidate jj change: `utopuuww`, based on main
`435d8781d3708da8be9496137bdd3fbaeb111058`. This report covers local source
release preparation; the eventual merged main/tag commit still requires its
own GitHub CI gate and workflow-created asset verification.

## Results

| Check | Result |
| --- | --- |
| Release metadata | `VERSION`, `foundation.json.version`, dated changelog and `--tag v0.3.3` agree; compatibility remains 1 |
| Pinned CI | PASS: `nix develop --no-update-lock-file path:.#ci --command env PYTHONDONTWRITEBYTECODE=1 bash tests/ci.sh`; 162 Python tests, shell/provider/aspect fixtures, actionlint and release metadata |
| Metadata regressions | PASS: nine release tests; all seven new rejection cases fail against the previous validator and pass with this change |
| Full Nix suite | PASS: `bash tests/nix-check.sh`; validation/editor fixtures, eight actual schema-3 compositions, nine host cases, all five flake build checks and four all-work-role evaluations across both Bluefin variants and schemas 2/3 |
| Installed CLI | PASS: actual schema-2 and schema-3 default package environments build with CLI package membership asserted; both `bin/home-manager --version` commands return `26.05-pre` |
| Source archive and template | Exact commit, archive checksum, file-by-file comparison, immutable flake checks and generated template provenance are recorded in the final candidate manifest |
| Scope | Dependency lock, application modules, profile schemas, compatibility, state version and third-party notices unchanged from current main |

The CLI smoke check builds `home.path` for a schema-2 generic profile and the
shipped schema-3 generic profile. It checks the command in the built package
environment, without running activation. Existing schema-3 evaluation fixtures
also assert CLI membership for all eight role/capability combinations.

The existing upstream `options.json` store-context warning remains visible;
it also appears in the previous module-refactor validation. No new evaluation
or build failures were observed.

## Local evidence and handoff

Logs and the CLI result are under `/tmp/foundation-v0.3.3-{ci,nix,cli}.log`
and `/tmp/foundation-v0.3.3-cli.json`. Final source identity, archive checksum,
release notes and exact-source build evidence are recorded in
`/tmp/foundation-v0.3.3-artifacts/`, including `candidate.json`. Those artifacts
must be regenerated for the eventual merged/tagged commit.

No Home Manager activation, personal configuration update, remote push, tag or
publication is part of this preparation. The release workflow prepares a draft
after a reviewed green main commit is tagged; publication and Finite adoption
remain separate steps described in the [release review](../releases/RELEASE-0.3.3.md).
