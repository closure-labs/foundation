# User environment diagnostic boundaries

`FOUNDATION_TIMINGS=1` enables bounded, non-authoritative stage records.
Legacy schema-1 timing fields remain supported. Schema 2 adds fixed details for
Nix activities, resource scopes and the inherited Bluefin Brewfile/cache state.
No raw arguments, executable paths, package URLs or logger text enter records.
Diagnostic sink failures preserve the operation's result and exception.

The same realization command selects Nix's `internal-json` logger. Supported
`actBuild=105` and `actSubstitute=108` start/stop activities supply counts and union
intervals; overlap is reported separately, not added to parent time. Evaluation
boundaries remain unknown. Malformed, oversized and incomplete events are bounded
and retain unknown duration coverage. Existing transfer retry classification
uses decoded logger messages without adding another evaluation. Consumer rejection
of duplicate stages preserves partial evidence rather than pretending all attempts
were measured.

The client scope keeps MemoryMax=5G, MemorySwapMax=512M, CPUQuota=100%, max-jobs=1
and cores=1. Resource observations sample that identified scope and root
`nix-daemon`/`determinate-nixd` cgroups separately. Daemon observations include
other users/work, and absent cgroups remain unknown. Memory-current reports the
largest sampled current value; memory-peak is the kernel's cgroup lifetime peak.
CPU usage is the observed counter delta. These samples are neither whole-build
caps nor causal resource attribution.

Bluefin preparation distinguishes readiness/precheck, inherited stock installation
and postcheck. It records the image's Brewfile SHA256 and cache-directory presence;
it does not claim a pinned resolved bottle/dependency closure. Optional bundles
remain selected only by upstream/user policy.

The pinned Flatpak provider's actual oneshot executable is wrapped without changing
its command, Type, restart policy or synchronous activation. An opted-in activation
creates a private temporary environment marker, joins a nonce-bound small receipt,
then removes its marker/receipt. Monotonic native service timestamps supply the
service observation; the wrapped installer supplies actual Flatpak work duration.
Absent/nonmatching receipts remain unknown. Existing activation order, readiness,
customization preservation, failure propagation and rollback are retained.

Use natural both-profile qualification runs to assess these observations. The old
103/132-second activation log gaps are supporting arrival-window evidence. No
performance savings, concurrency change or closure reuse is established here.
The consumer must support schema 2 before release/pin adoption.
