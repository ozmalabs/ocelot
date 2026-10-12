# CAN frame factorisation pilot — 2026-09-24

## Question and protocol

Does settling the existing native CAN rules independently in each frame preserve the monolithic engine's result when the graph is decomposed by four-concept frames?

[`scripts/substrate_can_frame_factorization.py`](../../../scripts/substrate_can_frame_factorization.py) ran N=16/32, 2-state/3-state modes, three deterministic replicates, and four topology families. For each case it built (a) one monolithic native substrate and (b) one independent native substrate per frame. Each frame received only its own nodes, external fields, and intra-frame causal edges. Rule execution was sequential and used the same 100,000-progress cap. Setup is excluded from the reported engine times. Every monolithic result was checked against the direct local-update fixed-point predicate and a terminal probe; each frame also received a terminal probe.

The `blocks4` topology is the positive control: it contains complete coupling within each four-node frame and no cross-frame edges. Path, banded-2, and complete topologies are omission controls: the monolithic graph retains all couplings, while independent frame substrates omit cross-frame edges. This pilot tests separate native frame execution. It does **not** implement boundary messages, dirty-frame wakeups, dynamic migration, or parallel execution.

## Results

All 48 runs stayed within their rule budget. All 48 monolithic outcomes were fixed points under the independently coded predicate and returned zero on the terminal probe. All 192 local frame terminal probes returned zero. The disconnected positive control matched the monolithic state exactly and remained a full-graph fixed point on all 12/12 runs.

| N | Family | Directed cross-frame edges | Exact state matches | Partitioned states fixed under full graph |
|---:|---|---:|---:|---:|
| 16 | blocks4 | 0 | 6/6 | 6/6 |
| 16 | path | 6 | 2/6 | 2/6 |
| 16 | banded-2 | 18 | 1/6 | 1/6 |
| 16 | complete | 192 | 0/6 | 0/6 |
| 32 | blocks4 | 0 | 6/6 | 6/6 |
| 32 | path | 14 | 0/6 | 0/6 |
| 32 | banded-2 | 42 | 0/6 | 0/6 |
| 32 | complete | 896 | 0/6 | 0/6 |

There were only 3 exact state matches and 3 full-graph-stable partitioned outcomes among the 36 connected-topology runs. A local fixed point in every frame is therefore insufficient: the composed result can be unstable under the omitted cross-frame terms. The occasional exact matches on connected topologies do not establish safe independence; they are individual initial-condition outcomes, while the cross-frame edges remain present.

Median sequential frame-engine time was lower than monolithic time in every cell, but this is not a speedup result: frame construction and repeated seed/rule loading are excluded; cross-frame work is removed; workers are not parallel; and only N<=32 is measured. Raw paired states, times, residuals, and provenance are in [`evaluation/reports/substrate_can_frame_factorization_20260924.json`](../../../evaluation/reports/substrate_can_frame_factorization_20260924.json).

## Interpretation and next gate

This validates the positive control for disconnected components and provides a falsifying negative control for independently solving connected frames. It gives no runtime evidence for the report's hoped-for boundary-conditioned factorisation. The next engine experiment must preserve cross-frame semantics: exchange boundary state/messages, wake a frame when a relevant boundary value changes, and compare its final state and fixed-point residual with the monolithic scheduler. Test empty, single-edge, and denser cuts, including perturbations that change a boundary state. Count message/update work and include setup, boundary maintenance, and synchronization in cost. A cut that passes only because no crossing influence exists should remain labelled disconnected-component factorisation.

The harness and raw artifact hash the script, seed manifest, native extension, and source files for substrate rule execution, rewriting, and Term evaluation. The extension was loaded from an isolated temporary package.
