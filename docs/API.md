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
| `lib.catalog` | Domain catalog |
| `lib.homeCatalog` | Current schema-3 home catalog |
| `lib.homeCatalogForSchema 3` | Schema-3 catalog (other profile schemas are rejected) |
| `lib.mkHomeCatalog { domainCatalog = …; schema = 3; }` | Project a supplied domain catalog |
| `lib.normalizeProfile profile` | Validate and canonicalize a schema-3 profile |
| `lib.resolveProfile profile` | Resolve schema-3 applications, providers and capabilities |
| `lib.hosts` | Host choices and pure normalization |
| `lib.profileCapabilities` | Supported initialization, normalization, editing and writing schemas |
| `lib.profileChanges.preview { profile = …; }` | Versioned, non-activating change preview |
| `lib.profileDrafts` | Schema-3 composition resolver; see [Migration](MIGRATION.md#integration-api) |

The catalog envelope version and profile schema are distinct. Read `profileSchema` and `profileCapabilities` when selecting a writer or editor; do not infer support from the envelope version. Only schema-3 home profiles are supported; older consumers must replace their profile before updating (see [Migration](MIGRATION.md)).

Change previews accept optional `roles`, `packages` and `capabilities` arguments. They describe changes; the controller owns approval, building and activation. The CLI's approval token binds the preview to its exact configuration and locked source.

The pure entry points under [lib/](../lib/) remain compatible façades over feature-owned implementations. Profile generation evaluates bundled normalization without evaluating the full flake or fetching Nixpkgs.

## Packaging and modules

`lib.mkApplications { pkgs = …; }` packages the Foundation helpers. `lib.mkConsumerTemplate { pkgs = …; }` creates the consumer scaffold. Both accept an optional `releaseInfo`; the argument name is retained for compatibility and does not require a published release. `lib.sourceInfo` describes the source version and provenance: `schema = 1`, `compatibility = 1`, `version`, immutable `rev`, `narHash`, and `lastModified`. Staged main adoption additionally records `upstreamCI` (workflow, run ID, attempt and URL) as additive provenance and revalidates it before activation. The version is a human milestone; the revision identifies an update. Packaging consumers must retain the exact source revision and hash, not infer identity from a version tag alone. Dirty or unpinned source metadata is not a substitute for valid consumer provenance.

Main-tracking consumer declarations use `github:closure-labs/foundation/main`; their lock node retains `original.ref = "main"` alongside immutable `locked.rev` and `locked.narHash`. Foundation owns its nested dependency graph. Do not override its Nixpkgs or Home Manager pins with consumer-level follows; unrelated personal inputs remain separately owned. See [updates](ACTIVATION.md#update-foundation) for explicit adoption and qualification.

`flakeModules.aspects` retains the exported aspect module and existing `features.*` aliases. `lib.ciPlans` exposes full and automation check selections. `lib.ciGraph` exposes the versioned dependency manifest, while `lib.discoveredFeatures` lists registered features. Registration alone does not activate them.

See [module ownership](MODULES.md) for implementation conventions and [CI](CI.md) for graph validation.
