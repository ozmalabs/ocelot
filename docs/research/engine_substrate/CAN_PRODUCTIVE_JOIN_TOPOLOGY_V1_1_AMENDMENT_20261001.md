# Productive CAN topology sensitivity v1.1 amendment

Date: 2026-10-01

## Reason

The initial v1 execution ran three layouts × two sizes × three populations × three replicates = **54 workers**. Its protocol and analyzer mistakenly specified 36 workers, counting only two layouts. The preserved v1 capture completed all 54 workers and passed every semantic, parity, source-stability, order, and counter gate; the two schedule-count checks failed. Treat v1 as a disclosed pilot, not a confirmatory pass.

## Amendment

No workload, arm, outcome oracle, or analysis threshold changes. Correct the preregistered matrix total from 36 to 54 workers and fresh processes. The corrected schedule remains all `cyclic`, `hub`, and `clustered` layouts; N={32,64}; Q={N,4N,floor(N(N−1)/4)}; and three replicates per cell. Freeze a refreshed source/native lock and rerun all workers under the corrected protocol and analyzer. Preserve the v1 pilot artifacts at their original paths.

## Confirmatory artifacts

The v1.1 runner, analyzer, lock, raw capture, and analysis use distinct artifact names. All other gates and claim boundaries in the [v1 preregistration](CAN_PRODUCTIVE_JOIN_TOPOLOGY_V1_PREREG_20261001.md) remain in force.
