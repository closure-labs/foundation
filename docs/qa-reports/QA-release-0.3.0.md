# Foundation 0.3.0 candidate validation

Date: 2026-10-21. Local release preparation is complete; publication awaits the
Great CTO ship gate. This report is a separate documentation change after the
frozen candidate and does not change its source or artifacts.

## Identity and artifacts

Candidate jj change: `ywyltuox`; immutable commit:
`7953c60e365d2bf1d19f87c7603c4d50faf49365`.

Source NAR: `sha256-GVRN+lNspHarVYWGf144UfOYyWa0Fyhh2J76ZDcNQMo=`.

Archive: `foundation-v0.3.0.tar.gz`, SHA-256:
`d7e28d9d5614b03888f653f9a44ff4d2cf4eddff0824178be80247a272458035`.

The [candidate manifest](../releases/0.3.0-candidate.json) records exact source
metadata, checks, outputs and recovery limits. Local logs, notes, source archive
and `SHA256SUMS` are in `/tmp/foundation-release-0.3.0-i987984u/`.

The archive uses the release workflow's `git archive | gzip -n` pipeline. Every
archived file matches the immutable source; the clean extraction's NAR hash also
matches it. Security independently reproduced the checksum and compared all 144
files. Dependency pins are unchanged by release preparation.

## Results

| Check | Result |
| --- | --- |
| Release metadata | VERSION, foundation.json, dated changelog and v0.3.0 agree; compatibility remains 1 |
| Pinned CI | 143 Python tests, shell/provider/aspect fixtures, actionlint and release metadata pass |
| Full Nix suite | Eight actual schema-3 compositions, nine host cases, all five declared flake checks/builds and four all-work-role evaluations across both Bluefin variants and schemas 2/3 pass |
| Immutable flake check | Direct candidate URI passes, including packaged generation and default Home Manager generation; no activation |
| Immutable consumer template | Builds with exact candidate revision/NAR, matching schema-3 defaults and source lock |
| Finite integration | Temporary exact-candidate override passes ten seed tests, 32 integration tests, four maintenance tests and the repeated 32-test run; committed source/pin files unchanged |
| QA/security | Both approve the frozen candidate; security separately approves artifact identity |
| Live state | Personal configuration digest, active generation and manually pinned source remain unchanged |

CI ran from an exact archive extraction with an empty Git project marker because
actionlint requires checkout metadata. Full Nix tests use normal checkout
permissions because some fixtures intentionally edit copied sources. Running
those fixture edits directly from read-only store copies fails. Generated Python
bytecode and the marker were removed before verifying the extraction's NAR;
the final flake builds also passed directly from the immutable candidate URI.
No validation check was disabled.

Immutable-source testing exposed a real template bug: copied personal files kept
read-only source modes. New copies now gain owner-write permission; existing
contents and modes are preserved. QA also caught dangling personal symlinks
being followed during template creation. Those entries are now preserved without
creating their external targets. Two regressions cover the three personal paths;
all 34 controller tests pass independently for QA and security.

## Recovery and publication boundary

The active workstation remains on source `7eed78af` and generation
`/nix/store/5ykg36q778pk5dm7zvbzlp3zcy7lk4bi-home-manager-generation`.
Its activation program remains executable. The saved pre-conversion directory
`/var/home/dale/.config/home-manager.previous.20261021T055422790592Z` still contains
the paired schema-2 profile and source lock, but historical generation
`/nix/store/xrv2ah34mzzw0wjn62y54qgb86zd1k4w-home-manager-generation` is absent.
Returning to that generation requires a rebuild, which this preparation has not
tested. This corrects the earlier evidence's assumption of its continued presence.

No candidate activation, remote push, tag or release was performed. Local checks
qualify this candidate; the eventual selected main/tag commit must pass GitHub
CI and artifact identity checks. If its SHA changes during review or merging,
regenerate its provenance, template and release assets. Never move a versioned
tag. Finite adoption revalidates the published revision separately.

Camera/fingerprint, suspend/docking, media/game behavior, graphical first-login
and OS-image rollout retain their manual boundaries. Prior physical Dell proof
qualifies the activated source, not this candidate. See the
[release review](../releases/RELEASE-0.3.0.md) for publication and adoption order.
