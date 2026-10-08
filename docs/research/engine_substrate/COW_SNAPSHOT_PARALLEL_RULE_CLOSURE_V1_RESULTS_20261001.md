# Copy-on-write snapshot parallel rule closure v1 results

## Result

All **45 fresh-process runs** across nine node-count × fanout cells completed. The analyzer passes all semantic, fixed-point, primary-isolation, later-fork, process-uniqueness, and five-repeat-per-cell gates. Each branch applies a real native `AddEdge` rewrite to closure and confirms a subsequent `run_rules(1)` makes no progress. The immutable snapshot and eager reusable base stay resident while branch work runs.

At 771 nodes, CoW serial/concurrent wall medians in microseconds were 736/923 (fanout 1), 2,856/1,082 (fanout 4), and 11,492/2,388 (fanout 16). At 10,771 nodes they were 10,818/12,668, 39,909/14,081, and 161,506/24,768. At 50,771 nodes they were 59,300/57,355, 238,048/78,594, and 975,265/143,659. Concurrent native threads therefore help at fanouts 4 and 16; at fanout 1 the setup overhead can dominate. The measured concurrency benefits apply to both CoW and eager branches, since each branch's native closure is the same workload.

The CoW versus eager concurrent medians (microseconds) were 923/1,062, 1,082/1,277, and 2,388/2,595 at 771 nodes; 12,668/13,479, 14,081/15,142, and 24,768/27,304 at 10,771; and 57,355/73,042, 78,594/95,216, and 143,659/159,429 at 50,771, for fanouts 1/4/16. CoW is modestly faster in these paired medians, but this is one synthetic host/workload, and no universal speed claim follows.

PSS shows a write-density tradeoff. Median fanout-live PSS deltas for CoW/eager were 0.88/0.24 MiB, 2.17/1.18 MiB, and 7.56/4.73 MiB at 771 nodes; 7.58/7.39, 20.32/26.08, and 71.50/100.88 MiB at 10,771; and 28.62/20.23, 74.00/62.29, and 255.50/228.32 MiB at 50,771. Thus shared pages do not guarantee lower process memory after branches perform dense derived-edge writes. Allocator retention and process-level accounting limit attribution; dropped-branch PSS is reported in the machine-readable analysis.

## Interpretation

This extends CoW evidence from branch creation and one-node writes to independent, concurrent native rule-closure consumers. It supports the value of reusable immutable state for isolation and concurrent exploration, while showing that branch workload matters: many output writes can erode or reverse memory savings. It does not test mutation of one shared live substrate, open-ended thoughtexperiment proposal utility, cancellation/reclamation bounds, or serving. The rule's `AddEdge` effect reads its output type for duplicate suppression, so the production access analysis does not certify it as `batch_safe`; the experiment deliberately measures outer branch parallelism, not within-rule Rayon batching.

Copy-on-write is a general substrate capability, not just a thoughtexperiment speed feature. Isolation, lifecycle control, and future interface compatibility are useful even when one branch workload shows no speed or memory gain. A vLLM-style shared-prefix interface is a reasonable compatibility target, but model KV blocks, request scheduling, cancellation, and reclamation are outside these measurements. The next experiment should vary branch-local write density and edge/index touch locality at fixed graph size, then separately implement a thin shared-prefix adapter only against explicit ownership and lifetime contracts.

## Reproduction

- [Preregistration and pilot deviation](COW_SNAPSHOT_PARALLEL_RULE_CLOSURE_V1_PREREG_20261001.md)
- [Python runner](../../../evaluation/substrate_capability/cow_snapshot_parallel_rule_closure_v1.py)
- [Rust probe](../../../evaluation/substrate_capability/fixtures/cow_snapshot_rule_closure/src/main.rs)
- [Raw source-captured results](../../../evaluation/reports/cow_snapshot_parallel_rule_closure_v1.json)
- [Analysis](../../../evaluation/reports/cow_snapshot_parallel_rule_closure_v1_analysis.json)
- [Analyzer](../../../scripts/analyze_cow_snapshot_parallel_rule_closure_v1.py)
