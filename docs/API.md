# Public API

Import Foundation from a pinned flake input. The [consumer template](../templates/default/flake.nix) is the complete starting point.

## Construct a home

```nix
inputs.foundation.lib.mkHomeConfiguration {
  profile = builtins.fromJSON (builtins.readFile ./profile.json);
  modules = [ ./customize.nix ./modules/local.nix ];
  extraInputs = builtins.removeAttrs inputs [ "self" "foundation" ];
}
```

`modules` defaults to `[]` and `extraInputs` to `{}`. The constructor normalizes the profile and returns a Home Manager configuration. It does not activate it. The supported system is `x86_64-linux`.

## Catalogs and profiles

| Entry point | Purpose |
| --- | --- |
| `lib.catalog` | Compatibility domain catalog |
| `lib.homeCatalog` | Current schema-3 home catalog |
| `lib.homeCatalogForSchema 2` or `3` | Catalog for the requested profile format |
| `lib.mkHomeCatalog { domainCatalog = …; schema = 3; }` | Project a supplied domain catalog |
| `lib.normalizeProfile profile` | Validate and canonicalize a schema-2 or schema-3 profile |
| `lib.resolveProfile profile` | Resolve schema-3 applications, providers and capabilities |
| `lib.hosts` | Host choices and pure normalization |
| `lib.profileCapabilities` | Supported initialization, normalization, editing and writing schemas |
| `lib.profileChanges.preview { profile = …; }` | Versioned, non-activating change preview |
| `lib.profileDrafts` | Compatibility resolver and migration-preview interface |

The catalog envelope version and profile schema are distinct. Read `profileSchema` and `profileCapabilities` when selecting a writer or editor; do not infer support from the envelope version. Existing schema-2 consumers keep their six-role catalog. New profiles default to schema 3.

Change previews accept optional `roles`, `packages`, `capabilities` and `migrate` arguments. They describe changes; the controller owns approval, building and activation. The CLI's approval token binds the preview to its exact configuration and locked source.

The pure entry points under [lib/](../lib/) remain compatible façades over feature-owned implementations. Profile generation evaluates bundled normalization without evaluating the full flake or fetching Nixpkgs.

## Packaging and modules

`lib.mkApplications { pkgs = …; }` packages the Foundation helpers. `lib.mkConsumerTemplate { pkgs = …; }` creates the consumer scaffold. Both accept an optional `releaseInfo`; `lib.sourceInfo` describes the source version and provenance.

`flakeModules.aspects` retains the exported aspect module and existing `features.*` aliases. `lib.ciGraph` exposes the versioned dependency manifest, while `lib.discoveredFeatures` lists registered features. Registration alone does not activate them.

See [module ownership](MODULES.md) for implementation conventions and [CI](CI.md) for graph validation.
