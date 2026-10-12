# Event-reasoning Stage A envelope v1.1 amendment (2026-09-26)

This is a provenance and independent-verification rerun of the existing Stage A envelope. It preserves the v1 task generator, sizes, six replicates, arm orders, ordinary/compare-only/Stage-A conditions, budget, parity oracles, metrics, and thresholds. The original v1 lock, raw report, and analysis remain unchanged.

## Provenance amendments

- Use the shared `substrate-run-manifest-v1` record with explicit hashes for the runner, amendment and base preregistration, seed, loader, native source, engine build inputs, and independent analyzer.
- Capture parent stdout/stderr as a hashed log. Record each worker argv, relevant environment overrides, stdout hash, and stderr hash/bytes; retain parsed worker output and stderr in the raw report.
- Use a new v1.1 source lock and output paths.

This does not make the synthetic event-reasoning rule family representative of natural tasks, and it does not establish Stage A speedup. Any missing input or log hash fails the v1.1 provenance gate.
