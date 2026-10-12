# ProblemShape eventization on recognition-only streams at larger N

**Status:** preregistered exploratory scaling probe.

## Question

At larger observation populations, does the all-transition event/index path preserve the ordinary closure's recognition outcomes and retain its measured reduction in ProblemShape candidate work and Term evaluations? Does paired observation-path time change at N=16 and N=32?

## Locked design

Run six fresh-process baseline/candidate pairs at each of N=16 and N=32 (12 pairs, 24 unique worker processes), all on the existing `recognition` authored sequence with dynamic codebook. Balance execution order within each size (three baseline-first, three candidate-first); shuffle pair order with `random.Random(20260926)`. The ordinary path uses the locked population-scale worker; the treatment uses the all-transition event/index worker. Both workers must pass their built-in fixed-point and expected-status/mint gates, and paired final status, mint, and per-step transition vectors must match.

Each child imports its existing worker function and extends only the in-memory CLI size-choice list to permit N=16/32; no source worker is patched. Record raw worker records, PIDs, boot, RSS, observation wall/CPU, candidate-pair and Term-evaluation counters, and host index maintenance. Summarize paired ratios separately by N; do not combine sizes into a single speedup claim. Preserve failed runs and do not alter defaults.

The lock pins this preregistration, runner, baseline/candidate workers, relevant task and decomposition code, seeds, baseline population raw, native extension/build manifest, and Cargo lock. Require current engine provenance before execution.

## Interpretation and limits

This is one authored task mix and one increasing population parameter, not a natural-task distribution, an asymptotic complexity proof, or substrate-wide scaling evidence. Six pairs per size are exploratory; timing intervals will be wide. A semantic mismatch invalidates the treatment comparison at that size regardless of operation counts or timing. Persistence/rebuild, rollback, concurrency, other mixes, and allocation attribution remain untested.
