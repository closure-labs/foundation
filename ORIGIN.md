# Origin

Foundation was extracted on 2026-10-16 from the upstream `templates/home-manager/` directory at commit `891a6ccf66765004310c49a216efd17a9cf0fd40`. The [README](README.md) describes the project’s relationship to its upstream.

The extraction included the template, hidden Zsh assets and dependency lock. Homebrew-provider and Dell panel-policy fixtures came from upstream `tests/home/` and were adapted to this repository. Foundation now owns these modules, assets, catalogs and helpers independently.

Foundation uses the [Apache-2.0 license](LICENSE). Bundled Zsh assets retain their original [MIT license](modules/capabilities/devops/_assets/rootfs/usr/share/finite/zsh/LICENSE). See [NOTICE](NOTICE) for attribution.
