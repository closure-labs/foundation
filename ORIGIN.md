# Origin and provenance

Foundation was extracted on 2026-10-16 from Finite's `templates/home-manager/` at commit `891a6ccf66765004310c49a216efd17a9cf0fd40`.

The extraction included the template, hidden Zsh assets and dependency lock. Homebrew-provider and Dell panel-policy fixtures came from Finite's `tests/home/` and were adapted to this repository.

Foundation now owns these modules, assets, catalogs and helpers independently. It has no flake input pointing to Finite and needs no Finite checkout. The retained `finite-*` names and consumer paths preserve compatibility. Image profiles and OS provisioning remain in Finite; adopting a Foundation release there is a separate integration change.

Foundation uses the [Apache-2.0 license](LICENSE). Bundled Zsh assets retain their original [MIT license](modules/capabilities/devops/_assets/rootfs/usr/share/finite/zsh/LICENSE). See [NOTICE](NOTICE) for attribution.
