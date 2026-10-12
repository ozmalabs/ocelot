# ProblemShape event/index checkpoint scale results

**Status:** all four fresh-process writer/reader pairs pass; checkpoint costs are dominated by the full default adapter graph at these sizes.

## Protocol and checks

N=2, 8, 16, and 32 recurrent observations were run to fixed point in separate writer processes. Each writer saved a `WorldAdapter` checkpoint. A distinct reader process loaded it, compared final state by goal ID, and settled the rule set again. All 8 PIDs were unique. Every size passed exact writer/reader projection equality, recognized observation status, minted shape/support, final key-index support N, empty transition-event counts, codebook epoch 1, active-rule state, exact about-goal/index links, and fixed point.

Protocol: [`SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_CHECKPOINT_SCALE_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_CHECKPOINT_SCALE_PREREG_20260925.md), amended for the timer boundary in [V1.1](SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_CHECKPOINT_SCALE_V1_1_AMENDMENT_20260925.md). Runner: [`substrate_problem_shape_event_index_checkpoint_scale.py`](../../../scripts/substrate_problem_shape_event_index_checkpoint_scale.py). Raw report: [`substrate_problem_shape_event_index_checkpoint_scale_20260925.json`](../../../evaluation/reports/substrate_problem_shape_event_index_checkpoint_scale_20260925.json). The initial four-cell raw diagnostic is preserved separately because its reader timer started after load ([timer diagnostic](../../../evaluation/reports/substrate_problem_shape_event_index_checkpoint_scale_timer_diagnostic_20260925.json)).

## Measurements

| Observations | Checkpoint bytes | Save time | Load time | Writer / reader peak RSS | Graph nodes / edges |
|---:|---:|---:|---:|---:|---:|
| 2 | 113,862,326 | 10.13 s | 5.57 s | 2.14 / 1.90 GB | 24,944 / 11,352 |
| 8 | 113,876,928 | 10.29 s | 5.92 s | 2.14 / 1.90 GB | 24,980 / 11,400 |
| 16 | 113,901,341 | 10.28 s | 5.97 s | 2.14 / 1.89 GB | 25,029 / 11,464 |
| 32 | 113,940,285 | 10.43 s | 6.01 s | 2.14 / 1.90 GB | 25,125 / 11,592 |

From N=2 to N=32, the full checkpoint grows by about 78 KB, while save time grows by 0.30 s and load time by 0.44 s in these single measurements. Peak RSS is essentially flat. The ProblemShape observations and event/index edges add a small amount next to the 24,000+ node default graph. The ~114 MB artifact and multi-second serialization cost therefore primarily measure full-adapter persistence overhead, not the ProblemShape index.

## Interpretation limits

This is a four-point scale sample over one authored workload and one native build. It does not establish a linear fit or asymptotic cost, nor does it test checkpoint compression, partial snapshots, interrupted writes, corruption, concurrent access, or schema migration. The index-specific rebuild measured separately at 0.124 ms remains negligible compared with full checkpoint save/load here. The runtime's end-to-end persistence path is the bottleneck surfaced by this probe.
