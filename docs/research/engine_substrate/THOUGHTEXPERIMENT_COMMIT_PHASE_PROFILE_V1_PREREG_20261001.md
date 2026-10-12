# Thoughtexperiment commit phase profile v1 — preregistration

**Date:** 2026-10-01  
**Question:** Which measured portions of authorized rule-generated residual commit account for the unexpectedly high 18–60 ms medians in adoption v1.1?

## Design

Replay the same four families, two graph sizes, three seeds, and three fresh workers as generated-residual adoption v1.1. Preserve its rule-generation, snapshot, reground, gate evidence, and whole-graph oracle. Compare two isolated branches from the same rehearsed state: the legacy full-graph route and targeted native reads. Counterbalance which route executes first by family/size/seed. Immediately after the committing gate mints its audit record, append then delete a highest-ID temporary node before delta planning; where the family adds a node, both routes must allocate exactly max live ID + 1 across this trailing tombstone. Capture a paired uninstrumented commit time as the primary cost comparison, and separately instrument elapsed time for: full `commit_imagination`; `commit_gate`; information-manifold `assess`; commitment-record minting; `_judge_conclusion` checks; live `graph_to_dict`; staged `apply_experiment_graph_delta`; and `set_attr` calls. Record call counts and per-call totals as well as `imagine`, reground, and complete semantic-oracle outcomes. Unattributed commit time is reported as a remainder and is not assigned to a phase.

The profiler wraps existing Python/native methods only within each fresh worker and restores them after a trial. Require native build freshness, source and binary hashes, three unique process IDs, 72 trials, same write-family coverage, rehearsal/refusal isolation, explicit approved writeback, and full-graph oracle parity. The primary performance report uses medians per family × graph-size cell; no derived speed ratio is a pass condition.

## Limits

Instrumentation adds wrapper overhead and is intended to locate dominant phases, not provide definitive production latency. All results are one-host synthetic authored-rule measurements. It does not establish why commit cost scales on other workloads, learned-rule quality, or natural-task prevalence. Follow-up should isolate any dominant phase with an uninstrumented matched capture and vary the causal input independently.
