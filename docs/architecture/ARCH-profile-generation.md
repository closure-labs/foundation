# New profile generation

W3 makes schema 3 the default for Foundation's new profiles, templates and
catalog. Existing profiles retain their schema. The workstation conversion is
already complete; this change leaves its live files and immutable source pin
unchanged. Finite's first-login/cloud-init writer readiness is implemented in an
[isolated follow-up](../qa-reports/QA-finite-profile-writers.md); its release pin
and the running OS have not been advanced.

## Commands

The current checkout provides the generator before a release is published:

```bash
# Mixed work/personal laptop; larger creative tools remain optional.
nix run path:.#home-profile -- --foundation bluefin-dx \
  --roles developer,creative --capabilities recording \
  --form-factor laptop --cpu intel --gpus intel-integrated --camera

# Household/media desktop, with JSON output.
nix run path:.#home-profile -- --foundation bluefin \
  --roles family,media --form-factor desktop --cpu amd \
  --gpus amd-integrated --format json

# Existing Dell adapter plus explicit device declarations.
nix run path:.#home-profile -- --foundation bluefin-dx \
  --hardware dell-xps-9350-intel --fingerprint --camera
```

Once installed from this revision, `finite-home-profile` accepts the same
arguments. It prints YAML by default; `--format json` selects JSON. Redirect
the result to a new file if desired. Both formats encode the same canonical
profile and can be supplied to `finite-home-init --profile <file>` separately.
That initialization command has its own build/activation effects.

`--foundation` is required. `--roles`, `--packages`, `--capabilities` and `--gpus`
take comma-separated identifiers. Empty selections are valid; duplicate,
unknown and trailing-empty entries fail before profile output. Omitted roles
and capabilities select shared essentials only. The account comes from the
current user; account identity and running Finite image compatibility are
validated before output.

Host options are `--system`, `--form-factor`, `--cpu`, `--gpus`, `--model`,
`--camera`/`--no-camera` and `--fingerprint`/`--no-fingerprint`. Omitted host
fields use generic, empty or false defaults. Hardware is declared explicitly;
the generator does not probe devices. The older `--hardware` adapter supplies
host defaults that explicit flags can override, subject to host/model rules.
The normalized `hardware` field remains a derived adapter for image checks.
See [host composition](ARCH-host-composition.md) for supported values and
Bluefin-owned behavior.

## Evaluation and catalog contracts

The packaged command calls the existing Python controller's `profile`
subcommand. It passes JSON files to bundled pure Nix normalization with
`nix-instantiate --store dummy:// --eval --strict --json`. It does not evaluate
a flake, fetch inputs, contact the daemon, build a home, provision Brew or touch
a consumer. Caller source/catalog overrides cannot replace the bundled rules.
JSON values cross the boundary through files and `--argstr`, without Nix code
interpolation. See the [Nix dummy-store manual](https://nix.dev/manual/nix/2.35/store/types/dummy-store.html)
for store-free evaluation.

`lib.homeCatalog`, `lib.homeCatalogForSchema 3`, the packaged
`home-profile-catalog` and `applications.profileCatalog` use one shared
projection. They expose ten roles, Professional/Personal groupings, 31
capabilities and host choices. The catalog envelope remains schema 3;
`profileSchema = 3` and `profileCapabilities.writeSchema = 3` describe profile
writing. Initialization still accepts schemas 1/2/3, normalization and editing
accept 2/3, and schema-1 initialization retains its explicit conversion to 2.

`lib.mkHomeCatalog { domainCatalog = ...; }` defaults to the current schema-3
projection for Foundation-based domains. It preserves supplied foundation/image
mappings. Domains limited to the old roles or lacking the classification
registry must request `schema = 2`; that view does not inject Personal roles.
Likewise, `lib.homeCatalogForSchema 2` remains the six-role reader view used
when editing an existing schema-2 profile.
That view now declares `profileSchema = 2`, distinguishing its supported format
from the source's preferred `writeSchema = 3`. Fresh writers must require a
matching view and helper support, rather than infer their format from the
catalog envelope version.

The empty root and consumer-template profiles share the same generic host,
empty selections and example account. Template users must supply their own
identity; the generator fills it automatically. Conversion of an existing
profile continues through the [reviewed editor flow](ARCH-profile-editor.md).

Validation: [W3 QA report](../qa-reports/QA-profile-generation.md).
