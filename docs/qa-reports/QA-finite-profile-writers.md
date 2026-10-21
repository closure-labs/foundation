# Finite profile writer readiness

Date: 2026-10-21. F3 prepares Finite's first-login and provisioning writers for
Foundation's current schema-3 profiles. Code lives in isolated Finite jj change
`wksovumv`, workspace `/tmp/finite-profile-readers`. Foundation's additive catalog
annotation and evidence are in jj change `zyqqklzw`.

## Behavior

Fresh login selects the writer format from the bundled catalog and checks the
helper's initialization, normalization and catalog support before displaying
roles. It supports schemas 2 and 3. A capable reader whose own preferred writer
is still 2 may initialize schema 3. Existing complete consumers, partial consumers,
saved selections and provisioning seeds retain their established precedence and
failure behavior. Schema-3 fresh selections include empty explicit capabilities;
initialization supplies the account and canonical structured host.

The seed package uses the existing schema-2 writer for older bundled sources.
With a schema-3 source it uses a separate thin Python wrapper around the fixed
Foundation `lib/generate-profile.nix`, with JSON files, `--argstr` and the dummy
store. It does not evaluate a flake, invoke the current-account generator or
activate anything. The requested `--user` owns the profile identity. Personal
roles, capabilities and the W3 host flags are supported; the old writer rejects
those flags explicitly, including empty selections and negative device flags.

After shared normalization, the seed verifies foundation/hardware compatibility
and role/package/capability membership in the image catalog. Data, metadata,
profile YAML and ISO are prepared before creating output. Existing outputs and
dangling symlinks are preserved. A publication failure removes only the new
directory created by that invocation, with device/inode ownership checks; a
concurrently created output survives the failed exclusive directory creation.
Cloud-init remains disabled by default, and the ISO retains its inactivity notice.

Foundation's explicit schema-2 catalog view now declares `profileSchema = 2`.
Its globally preferred writer may be 3; consumers must distinguish that preference
from the format represented by a reader catalog. Default/current schema-3 catalog
content is unchanged.

## Evidence

Local artifacts: `/tmp/foundation-finite-writers-zryy43j5/`, including both
repository pin baselines, test/build logs, live-state check and final patches.
Current-source validation uses immutable Foundation snapshot
`63caca0f761823413a05a7c3758dabe5e71e6bee` through `--override-input` and
`--no-write-lock-file`. It is a local review snapshot, not a published release.

| Check | Result |
| --- | --- |
| Foundation pinned CI | 141 Python tests, shell/aspect fixtures, workflow lint and release metadata pass |
| Foundation public API | Real locked-target normalization and API/application/package catalog equality pass; explicit schema2 view identifies itself; custom image mappings remain |
| Finite pinned-source home contracts | Five active schema2 seed tests, real schema2 seed/ISO, template, 32 integration tests and four maintenance tests pass; current-only cases run with the current source |
| Finite current-source home contracts | Final real schema3 run passes all ten seed tests, 32 integration tests and four maintenance tests; the existing check repeats the 32-test integration suite successfully |
| First-login cases | Negotiated3 with reader preference2/3, incompatible helper rejection, view/writer mismatch and preserved saved-profile precedence, alongside existing readers/cancellation/recovery paths |
| Seed cases | Actual Foundation canonical equality, mixed roles/capabilities, Intel/AMD hosts, Dell overrides, invalid/injected data rejection, narrowed catalogs, arbitrary target identity, ISO extraction/metadata, existing/symlink output preservation, ISO failure and publication cleanup |
| Static checks | Changed Nix files pass Alejandra; first-login passes pinned ShellCheck and Bash syntax checks |
| Review | Architecture/CLI/security/library/QA reviews pass; narrowed catalog and publication-cleanup findings fixed and re-reviewed |

Review identified two concrete edge cases: custom narrowed catalogs could admit
otherwise valid selections, and failed file publication could leave a partial
directory blocking retry. The final implementation checks all selection
registries and cleans its own failed output; regressions exercise both.
First-login's dialog and helper commands are controlled fixtures. The seed path
uses the real packaged writer, shared Nix normalization and extracted ISO contents;
publication/concurrency failures use targeted injected errors. Graphical first-login
activation is not established by these checks.

## Adoption boundary

Finite's committed Foundation URL, `flake.lock` and `sources/foundation.json`
remain unchanged. Its default image therefore still uses the existing schema-2
source until a reviewed containing Foundation revision can be adopted. No
additional migration matrix or automatic conversion is introduced.

The active workstation stays on Foundation source
`7eed78af934634b253a84e7bbaba758234d870b2` and its verified generation. This work
does not rebuild an OS image, enable cloud-init, install the adapters, or alter
camera/fingerprint/power behavior. Publication and Finite pin adoption remain
separate actions.
