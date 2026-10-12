# Same-addressee Goal identity replication v4.2

**Question:** do the v4.1 operation-count and caller-queue overhead measurements reproduce over fresh processes, and what resident-memory change accompanies event creation and settlement?

## Result

The locked capture ran 45 workers (five arms × three replicates × N=16/32/64); all PIDs were distinct. The runner gates and an independent reconstruction passed. At every replicate and size, explicit `for_goal` links produced the expected three transitions per Goal. The explicit owner queue matched full closure's graph digest at every event checkpoint; result notifications reached each Goal's origin; omitting wakeups left receipts stale, and a final full closure restored exact graph parity. Temporal-only and addressee-only controls failed the task oracle as intended. All scoped reports reached completion without progress-cap or deferred-effect exits.

| Goals N | Arm | Candidate pairs (median; range) | Term evaluations (median; range) | Wall time, ms (median; range) | Current RSS delta, KiB (median; range) | Peak RSS, KiB (median; range) |
|---:|---|---:|---:|---:|---:|---:|
| 16 | Explicit full | 7,544 (fixed) | 25,704 (fixed) | 2.785 (2.654–3.011) | 3,780 (fixed) | 78,252 (40,412–88,428) |
| 16 | Explicit owner queue | 9,664 (fixed) | 31,392 (fixed) | 5.890 (5.865–5.980) | 4,004 (fixed) | 66,732 (49,836–70,188) |
| 32 | Explicit full | 29,680 (fixed) | 100,816 (fixed) | 7.405 (7.282–7.611) | 6,284 (6,280–6,284) | 57,324 (56,748–69,420) |
| 32 | Explicit owner queue | 37,760 (fixed) | 121,152 (fixed) | 14.338 (14.275–14.500) | 6,468 (6,464–6,468) | 54,636 (45,420–77,484) |
| 64 | Explicit full | 117,728 (fixed) | 399,264 (fixed) | 23.023 (22.628–24.162) | 12,500 (12,500–12,504) | 82,668 (59,436–85,164) |
| 64 | Explicit owner queue | 149,248 (fixed) | 475,776 (fixed) | 39.554 (39.176–39.820) | 13,196 (13,192–13,196) | 49,712 (49,636–78,636) |

Owner-queue/full ratios are stable for operation counters: at N=16/32/64, candidate pairs are 1.281/1.272/1.268× and Term evaluations 1.221/1.202/1.192×. Wall-time ratios are 2.148/1.936/1.730× by median (individual replicate ranges 1.956–2.210, 1.905–1.960, and 1.637–1.731). The caller queue therefore preserves correctness but is slower than full closure in this workload, with a narrowing overhead ratio as N grows. The counts are exactly repeatable across the three processes; timings show modest within-size variation.

For both arms, doubling N from 16→32 and 32→64 multiplies candidate pairs and Terms by about 3.93–3.98. This reproduces v4.1's near-quadratic operation-count profile on this generated workload. It is not a complexity proof or evidence about other graph families.

Current RSS was sampled from `/proc/self/status` after imports, before event construction, and after settlement. The reported delta is the latter minus the former, not allocation-level attribution. For explicit full closure it rises from 3,780 KiB at N=16 to 12,500 KiB at N=64; for the owner queue, 4,004 to 13,196 KiB. Peak RSS varied widely between fresh processes (especially N=16), so it is descriptive only. Python/runtime floor dominates absolute memory, and these readings do not identify which graph structures or allocator arenas account for the increment.

## What this resolves and what remains open

Resolved for this fixture: multi-goal identity requires explicit event-to-goal links; native affected-owner reports are sufficient to drive the tested queue; notification omission is observably incorrect; and the v4.1 operation counts replicate. The owner queue does not yield a time win here.

Open: the identity edges are inserted by the benchmark harness, not a production event producer. This does not establish prevalence of cheap cuts, learned-frame quality, real workload scaling, treewidth bounds, commodity-scale performance, or tractability of rung 3/4 induction. RSS is not a memory attribution profile. The next useful experiment is an independently authored producer-integrated task family, with source-derived ownership edges, a global-closure control, and a real memory profiler or object-count attribution. Then measure diverse frame topology and boundary widths rather than increasing only this one workload's N.

## Reproducibility artifacts

Protocol: [v4.2 preregistration](SUBSTRATE_DISCOURSE_GOAL_IDENTITY_REPLICATED_SCALE_V4_2_PREREG_20260926.md). Runner: [script](../../../scripts/substrate_discourse_goal_identity_replicated_scale_v4_2.py). Independent analyzer: [script](../../../scripts/analyze_substrate_discourse_goal_identity_replicated_scale_v4_2.py). Locked inputs: [lock](../../../evaluation/substrate_capability/discourse_goal_identity_replicated_scale_v4_2_lock_20260926.json). Raw capture: [report](../../../evaluation/reports/substrate_discourse_goal_identity_replicated_scale_v4_2_20260926.json). Independent reconstruction: [analysis](../../../evaluation/reports/substrate_discourse_goal_identity_replicated_scale_v4_2_analysis_20260926.json).
