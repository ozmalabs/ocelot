# Conversation frame-scoped scale results (v1.1)

The corrected preregistered replay used the native `conversation_deliberation_phase4a` rules on 1, 2, 4, and 8 independent Deliberation tasks, with three fresh-process replicates and full-graph versus round-robin scoped closure. All 24 workers reached reported fixed points; all expected candidate decisions passed; and all 12 paired normalized projections were identical. The independent report audit also passes.

| Tasks | Full candidate pairs | Scoped candidate pairs | Full Term evaluations | Scoped Term evaluations | Full median wall | Scoped median wall | Scoped frame turns |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 39 | 109 | 323 | 784 | 0.146 ms | 0.150 ms | 2 |
| 2 | 78 | 379 | 646 | 2,782 | 0.185 ms | 0.242 ms | 4 |
| 4 | 156 | 1,402 | 1,292 | 10,420 | 0.253 ms | 0.554 ms | 8 |
| 8 | 312 | 5,380 | 2,584 | 40,264 | 0.356 ms | 1.619 ms | 16 |

This result shows exact outcome/fixpoint parity on one real runtime rule family while demonstrating that generic repeated scoped matching can cost substantially more than a single full scan on disconnected frames. At eight tasks, scoped candidate enumeration is 17.2× and Term evaluation 15.6× the full arm; median wall time is 4.5×. These are bounded observations, not asymptotic estimates. The experiment uses one generated workload, N≤8, independent/disconnected frames, and a generic scoped API; it neither tests cross-frame conversation dependencies nor proves all scoped implementations behave similarly.

The v1 coordinator incorrectly gated on equal progress counters and reported an empty `term_units_total`; its immutable raw record is retained. The v1.1 amendment changes the gate to semantic projection/fixed-point parity and uses `term_evals_total`, with the same workload and worker design. See the [protocol](SUBSTRATE_CONVERSATION_FRAME_SCOPED_SCALE_PREREG_20260925.md), [amendment](SUBSTRATE_CONVERSATION_FRAME_SCOPED_SCALE_V1_1_AMENDMENT_20260925.md), [runner](../../../scripts/substrate_conversation_frame_scoped_scale_v1_1.py), [independent analyzer](../../../scripts/analyze_substrate_conversation_frame_scoped_scale_v1_1.py), [raw report](../../../evaluation/reports/substrate_conversation_frame_scoped_scale_v1_1_20260925.json), and [lock](../../../evaluation/substrate_capability/conversation_frame_scoped_scale_v1_1_lock_20260925.json).
