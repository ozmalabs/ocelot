# Live describe-scene threaded interleaving v1.1 amendment

## Reason

A one-worker pilot reached the expected Goal/event identity state, but request B raised `RuntimeError: Already mutably borrowed` and returned no reply. The original probe omitted exception stack traces and did not fingerprint the PyO3 binding source. V1.1 adds full per-thread tracebacks and locks `runners/dsl/src/py.rs` so the concurrency failure can be localized and reproduced.

## Gates

Repeat three fresh processes under the same controlled A/B barrier. Capture and analyze identity/lifecycle, reply parity, thread completion, errors, and full traceback separately. The source-current capture is valid if all workers finish/join and source fingerprints are stable, even if the semantic/concurrency gate fails. Do not convert a failure into a passing route claim.
