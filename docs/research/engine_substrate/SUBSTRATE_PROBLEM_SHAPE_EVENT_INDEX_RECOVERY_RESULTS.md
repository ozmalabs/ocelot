# ProblemShape event/index checkpoint recovery results

**Status:** checkpoint/load plus derived-index rebuild preserves the tested event lifecycle and final application state in one N=8 workload. Cost numbers are one-run exploratory measurements; this is not a durability or crash-safety guarantee.

## Protocol

The recovery arm saved after observation 1 settled residual, when one residual-candidate event and support index count 1 existed. A fresh `WorldAdapter.load` restored graph, grammar, and rule slots. The probe verified all five ProblemShape rules and all custom event productions, removed the persisted `ProblemShapeKeyIndex` node(s), rebuilt support rows and observation links from graph-resident observations, rebuilt the host key lookup, and then processed observations 2–8.

The uninterrupted and recovery arms ran in distinct processes. Both ended at fixed point with eight recognized observations, one minted `ps_has_bound=yes` shape with mint-time support 2, codebook epoch 1, final index support 8, and no pending-decode, decoded, or residual-candidate events. Each observation retained one index link and an `about_goal` relation to its corresponding goal. Final projections keyed by goal ID matched exactly. The deliberate index rebuild changed some later observation NodeIDs; those storage IDs are excluded from application-state equivalence. The earlier node-ID-only comparison is preserved as a diagnostic and superseded by the V1.1 amendment.

Protocol: [`SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_RECOVERY_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_RECOVERY_PREREG_20260925.md), with [V1.1 readback amendment](SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_RECOVERY_V1_1_AMENDMENT_20260925.md) and [V1.2 cost amendment](SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_RECOVERY_V1_2_AMENDMENT_20260925.md). Runner: [`substrate_problem_shape_event_index_recovery.py`](../../../scripts/substrate_problem_shape_event_index_recovery.py). Raw result: [`substrate_problem_shape_event_index_recovery_20260925.json`](../../../evaluation/reports/substrate_problem_shape_event_index_recovery_20260925.json). The original node-ID comparison is retained at [`recovery_nodeid_diagnostic`](../../../evaluation/reports/substrate_problem_shape_event_index_recovery_nodeid_diagnostic_20260925.json); the V1.1 semantic run is retained at [`recovery_semantic_v1_1`](../../../evaluation/reports/substrate_problem_shape_event_index_recovery_semantic_v1_1_20260925.json).

## Recovery cost

The full-adapter checkpoint was 113,860,738 bytes. In the recovery worker, save took 9.74 s, load took 5.48 s, and rebuilding the tiny one-key index took 0.124 ms. Peak process RSS was about 3.02 GB. The file and memory costs reflect the whole default adapter graph/rule store, not a ProblemShape-only snapshot. The index itself is cheap to reconstruct; full substrate checkpoint I/O dominates by many orders of magnitude in this run.

## Claim boundary and next work

This confirms graph/grammar/rule persistence and derived-index rebuild for one checkpoint point and one fixed task. It does not exercise torn writes, crash consistency during a rule effect, file corruption, concurrent writers, schema migration, or restoration in a separately provisioned runtime. The large whole-adapter snapshot and save/load latency are a scaling concern despite successful semantic recovery. Next vary observation population and checkpoint point, measure checkpoint size/save/load/RSS, test corruption and interrupted-write behavior, and separate a minimal domain-state checkpoint from the full default graph only if that matches the actual application contract.

The initial N=8 checkpoint-cost point has now been extended with a four-size fresh-process scale sweep. Across N=2/8/16/32, checkpoint size is 113.862–113.940 MB, save time 10.13–10.43 s, load time 5.57–6.01 s, and writer/reader RSS about 2.14/1.90 GB. All eight writer/reader PIDs and every state-equivalence check pass. The full adapter graph dominates these measurements; see [`SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_CHECKPOINT_SCALE_RESULTS.md`](SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_CHECKPOINT_SCALE_RESULTS.md) and its raw record.
