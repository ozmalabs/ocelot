# Budget-cut revision recovery across process restart v1

## Result

All 106 analysis gates pass across three workers, two proposal counts (N=2 and 64), and three rule-order/guard arms. Each cell checkpoints after a `max_steps=1` closure in one process, fsyncs the checkpoint, and restores it in a fresh process. Graph and grammar serialization are exact; exported rules are semantically equal after normalizing match-clause order and recomputing the derived content hash. Checkpoint sizes and hashes match their producer manifests. Integer work and state outcomes replicate across workers; byte-for-byte checkpoint equality is not required because runtime graph IDs vary.

Reverse-order guarded runs stop after the max stage: at the cut, `resolved_revision` and `consumed_revision` remain 0 with the prior label intact. Fresh-process closure then reaches the oracle result (`p000` at N=2; `p062` at N=64), commits revision 1, and records consumption of revision 1. Normal-order guarded runs finish all five rules during the selected pass and already hold the correct revision-1 result at the cut. The reverse-order unguarded negative control commits an empty selection using stale upstream values; restart faithfully restores and preserves that wrong fixed point. Persistence restores state, but cannot repair a false commit that was allowed by the rule policy.

## Interpretation and limits

This confirms process-boundary recovery from a budget-limited closure and demonstrates why stage readiness guards matter even when all state is serializable. It does not establish crash consistency during native execution, power-loss durability, schema migration, concurrent writers, or automatic dependency enforcement by the engine. The workload is one authored score-selection family with one mutation pattern and two sizes; it does not establish general restart safety or scaling.

## Artifacts

- Preregistration: [protocol](SUBSTRATE_BUDGET_CUT_PROCESS_RESTART_V1_PREREG_20260928.md)
- Runner: [source](../../../scripts/substrate_budget_cut_process_restart_v1.py)
- Analyzer: [source](../../../scripts/analyze_substrate_budget_cut_process_restart_v1.py)
- Analysis: [gates and cell summaries](../../../evaluation/reports/budget_cut_process_restart_v1_analysis_20260928.json)
- Raw capture: [three-worker results](../../../evaluation/reports/budget_cut_process_restart_v1_20260928.json)
- Source/native lock: [locked inputs](../../../evaluation/substrate_capability/budget_cut_process_restart_v1_lock_20260928.json)
