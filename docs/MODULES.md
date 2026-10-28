# Module architecture

Foundation keeps each feature's metadata, configuration and assets together. The same ordered dependencies drive Den home composition, pure catalog projections and CI selection.

| Directory | Owns |
| --- | --- |
| [flake](../modules/flake/) | Framework inputs, discovery, exports and templates |
| [home](../modules/home/) | Construction, startup, commands and activation |
| [profiles](../modules/profiles/) | Schemas, catalogs, generation and editing |
| [apps](../modules/apps/) | Individual applications, settings and recipes |
| [roles](../modules/roles/) | Professional and Personal presets |
| [capabilities](../modules/capabilities/) | Optional groups and their application dependencies |
| [hosts](../modules/hosts/) | Machine, CPU, GPU and model aspects |
| [providers](../modules/providers/) | Package sources, Homebrew, Flatpak and graphics |
| [ci](../modules/ci/) | Profile cases, build checks and dependency graph |

See the [generated diagram](ARCHITECTURE.md) for the data flow.

## Add a feature

1. Create a directory such as `modules/apps/example/`.
2. Add `_feature.nix` with its path-derived ID (`apps/example`), pure `metadata`, ordered `dependencies` and `schemaDependencies`. Keep configuration in a lazy `configuration` function. Follow an existing [application descriptor](../modules/apps/firefox/_feature.nix).
   For ordinary Nix packages without custom settings or recipes, the pure
   [`_nix-application-feature.nix`](../modules/profiles/composition/_nix-application-feature.nix)
   helper derives provider metadata and ordered package/graphics dependencies.
   Keep feature-owned special recipes explicit; Firefox and Ghostty are not
   migrated to this helper.
3. Register the descriptor from `default.nix` as a flake-parts module. Framework modules may use a separate `registration.nix`.
4. Put private Home Manager modules and functions under `_` names, and supporting files under `_assets/`. Public `.nix` files are discovered by import-tree and must be flake-parts modules.
5. Declare dependencies in the feature that selects the new feature. Discovery makes it available; profile roots determine activation. Avoid maintaining a second application or role list.
6. Regenerate and validate:

```sh
nix run path:.#write-flake
nix run path:.#write-ci-graph
nix develop --no-update-lock-file path:.#ci --command bash tests/ci.sh
bash tests/nix-check.sh
```

The pure [loader](../modules/flake/features/_loader.nix) rejects invalid IDs, missing dependencies and cycles. [Profile selection](../modules/profiles/composition/_selection.nix) provides roots for each schema. Home evaluation checks actual Den membership against that declared closure. Preserve explicit package ordering, shell initialization order and activation DAG edges when moving configuration.

## Change an input

Declare `flake-file.inputs` beside the feature or provider that owns it. Edit the declaration, run `write-flake`, then update the intended input in `flake.lock` and review both files. Do not edit generated `flake.nix` by hand.

Automatic lock pruning is disabled. The [dependency-update script](../scripts/update-locks.py) also keeps gen aligned with Den's tested revision and regenerates the flake and graph. Its workflow submits source declarations and generated artifacts together.

Consumer files remain `profile.json`, `customize.nix` and `modules/local.nix`. Keep the [public API](API.md) compatible and record user-facing changes in the [changelog](../CHANGELOG.md).
