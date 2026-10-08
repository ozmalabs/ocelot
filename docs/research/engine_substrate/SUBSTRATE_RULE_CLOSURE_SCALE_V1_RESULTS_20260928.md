# Single-rule native closure scale v1 results

## Outcome

All 16 source-locked workers pass their runner gates; the independent analyzer passes 11/11 checks. The panel crosses N=10k/100k/1M/10M, two replicates, and audit off/on. Each constructs a directed ring with N attributed `WorkItem` nodes and N edges, then one rule changes each node from `pending` to `done`. Every worker reaches fixed point with exact node/edge counts, zero pending, exactly N done, and correct sampled ring links. Audit-on/off semantic projections agree within all eight paired cells.

| Nodes / edges | Audit-off median closure CPU | Audit-off median wall | Audit-off live RSS increase after closure | Process peak RSS (post-oracle high water) | Audit-on candidate tests | Attr-set attempts | Term evaluations |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10k / 10k | 6.16 ms | 6.16 ms | 9.17 MB | 40–41 MB | 20,000 | 10,000 | 80,000 |
| 100k / 100k | 59.2 ms | 59.4 ms | 62.96 MB | 89–90 MB | 200,000 | 100,000 | 800,000 |
| 1M / 1M | 805 ms | 806 ms | 381 MB | 744–745 MB | 2,000,000 | 1,000,000 | 8,000,000 |
| 10M / 10M | 8.85 s | 8.90 s | 3.29 GB | 6.125–6.126 GB | 20,000,000 | 10,000,000 | 80,000,000 |

Both audit-on replicates at every N report exactly `2N` candidate tests, `N` attr-set attempts, `8N` Term evaluations, and `2N` where evaluations, with zero unattributed candidate tests. Per-rule and per-clause candidate counts conserve exactly. The instrumented closure wall is 1.64× the plain median at 10M (larger at smaller N), so instrumented latency is excluded from the primary timing claim.

The status attribute index is part of the measured graph and is maintained during all writes. The exact terminal oracle queries both `pending` and `done`; the `done` query materializes N Python node-ID wrappers. Thus peak process RSS includes a large temporary readback allocation and is not a closure-only memory number. The post-closure current RSS increase is reported separately, before that validation query.

## Interpretation and limits

This directly measures one favorable monotone single-rule closure at 10M nodes, not only graph construction. Over this constructed ring, native candidate work and effect attempts have exact linear counts; audit-off closure CPU grows from 6.16 ms at 10k to 8.85 s at 10M. These finite points do not prove an asymptotic bound, scheduler behavior for interacting rules, or tractability for other graph topologies. They exclude boot, more than one rule, minting, inference, task-level correctness, deletes/reuse, and realistic variation in attribute/rule density.

The next engine gate should add at least one interacting rule and a non-ring topology with an independent whole-state oracle, then extend attributes and edge-degree distributions while preserving separate graph-build, index, install, closure, validation, and peak-memory measurements.

Artifacts: [preregistration](SUBSTRATE_RULE_CLOSURE_SCALE_V1_PREREG_20260928.md), [pilot amendment](SUBSTRATE_RULE_CLOSURE_SCALE_V1_PILOT_AMENDMENT_20260928.md), [runner](../../../scripts/substrate_rule_closure_scale_v1.py), [independent analyzer](../../../scripts/analyze_substrate_rule_closure_scale_v1.py), [source lock](../../../evaluation/substrate_capability/rule_closure_scale_v1_lock_20260928.json), [raw workers](../../../evaluation/reports/substrate_rule_closure_scale_v1_20260928.json), [analysis](../../../evaluation/reports/substrate_rule_closure_scale_v1_analysis_20260928.json), [excluded pilot](../../../evaluation/reports/substrate_rule_closure_scale_v1_pilot_20260928.json).
