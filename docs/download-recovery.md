# Interrupted Nix downloads

Home Manager realization allows three total attempts with two- and four-second
backoff, under one 15-minute deadline including Nix's inner download retries.
Each attempt streams diagnostics. A deadline terminates the realization process
group. Configuration generation, provisioning, activation and rollback retain
their existing single invocation and transaction boundaries.

HTTP 416 is retried only when the same command previously logged an interrupted
transfer and a positive resume offset for that exact URL. A bare 416, different
URL, authorization, hash/signature, evaluation, builder or signal failure stays
terminal. Recovery never removes personal configuration or shared caches. The
only retryable process status is Nix's ordinary failure exit 1; wrapper exits
such as 137, usage failures and negative signal statuses remain terminal even
when the same log contains a transient transfer diagnostic. The
latest build memory policy and out-of-memory diagnostics remain enforced.

Run the Python regressions with:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

The controlled integration fixture requires Nix and a loopback listener. It
creates only a temporary local store, advertises byte ranges, interrupts a
2,900,000-byte response after 1,450,000 bytes, rejects the resumed request with
416 and then permits a full request:

```sh
python3 tests/nix_download_fixture.py --output /tmp/foundation-download-result.json
```

Determinate Nix 3.23.3 (Nix 2.35.3) reproduced that sequence. The first command
failed, a new command succeeded, and the recovery helper succeeded in about
2.1 seconds including backoff with the exact expected SHA256. This tests the
shared downloader; it does not simulate an entire guest installation or replace
Finite's two-profile Secure Boot fresh-install and upgrade/rollback qualification.

Finite consumes immutable published Foundation releases. Publish this change
through Foundation's existing reviewed release process, then propose the pinned
Finite dependency update separately and retain both profiles' guest evidence.
Until then, deployed images keep their existing helper. Reverting this helper
change restores single-attempt realization; existing user configuration needs
no cleanup or migration.
