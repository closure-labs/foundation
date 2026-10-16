# Contributing to Finito

Open an issue for substantial behavior or dependency changes before investing
in an implementation. Keep changes focused and describe their effect on users.
For vulnerabilities, follow [SECURITY.md](SECURITY.md).

Finito is intended to provide Finite's default Home Manager flake and also
supports standalone use. Read [README.md](README.md) for the supported host and
account setup. Preserve
profile schema compatibility, canonical role/package ordering, runtime
`finite-*` command names and `home.stateVersion` unless a change intentionally
migrates them. Keep dependency changes in `flake.lock` reviewable and preserve
third-party license notices.

Run the fixture checks using installed Bash, jq, Python 3 and Nix:

```bash
bash tests/check.sh
```

Use the pinned CI development shell to run the same repository validation as CI:

```bash
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
```

Run the full Nix checks on an x86_64 Linux host with enough memory and disk for
the desktop packages:

```bash
bash tests/nix-check.sh
```

Use `bash tests/nix-check.sh --no-build` to evaluate the same profiles without
building packages. CI and release validation always perform the full build.

These checks build configurations without activating Home Manager. Changes to
activation behavior should also be tested deliberately on a suitable host.
Record commands and results in the pull request, including any checks that
could not run. Add focused fixtures when they help prevent a behavioral
regression. Consider both standalone users and Finite's consuming setup when
changing defaults, and add user-facing changes under `Unreleased` in
[CHANGELOG.md](CHANGELOG.md).

Jujutsu and Git contributors are welcome. With `jj`, review `jj status` and
`jj diff`, describe the change with `jj describe`, then push a named bookmark
and open a pull request against `main`. CI must pass before merging; the
required check is **CI gate**. See [docs/RELEASING.md](docs/RELEASING.md) for
maintainer setup and release steps.

Contributions are provided under the repository's [Apache-2.0 license](LICENSE).
Bundled third-party material keeps its own stated license.
