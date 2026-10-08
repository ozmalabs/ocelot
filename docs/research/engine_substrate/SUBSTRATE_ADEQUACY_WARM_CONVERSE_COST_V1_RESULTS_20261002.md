# Cold initialization and warmed code-adoption route v1 — results

Date: 2026-10-02

## Result

The source-locked panel completed 18 unique fresh workers across parity, clamp, and square; adoption and missing-evidence controls; and three repetitions per cell. All **8/8 analyzer gates pass**. Every truthful receipt was independently replayed and authenticated, every accepted call added one code-write shape, every missing-evidence call left shape inventory and epoch unchanged, and accepted native held-out predictions matched the separate oracle.

Per-cell median wall latency for the initial `converse("hello")` was 94.6–100.3 ms. The subsequent target `converse` measured 111.2–116.0 ms across all six cells. This target timing includes one ordinary user turn and its strict evidence decision; request construction is outside the timer. It is measured after one warm-up turn, but target graph snapshots still show additional per-turn graph writes, so “warmed” does not imply that every task-specific lazy action has finished.

The target call's median process CPU time was **1.65–1.70 seconds**, substantially above its 111–116 ms wall time. `process_time_ns` accumulates CPU across the process's threads; the concurrent rule-matching implementation has a Rayon worker path, but this panel did not attribute CPU to individual rules or workers. Treat this as aggregate process CPU evidence requiring a focused attribution follow-up, not as a per-core cost or proof that a fixed number of cores stayed busy.

Median target-call graph sizes also grew. For missing-evidence arms, nodes/edges grew from 1,684–1,708 / 1,423–1,447 before the turn to 1,713–1,749 / 1,489–1,553 after it. Accepted arms ended with 1,732–1,810 nodes and 1,503–1,606 edges. These include ordinary conversation state and task-path effects; full graph equality is neither expected nor a gate here. Codebook mutation was checked separately.

## Interpretation and limits

This measures a useful production-shaped live route after one controlled warm-up and separates it from the first conversation turn. The observed target wall latency is close to the earlier cold route, while aggregate CPU is much higher; this motivates rule-level work attribution before CPU tractability claims. Adoption and missing-evidence semantics transfer across three authored functions, not natural tasks. One host, one test provider, three repetitions per cell, and synthetic fixtures do not give a population cost estimate or a confidence interval. HMAC validity still does not establish truth.

The post-capture [v1.1 amendment](SUBSTRATE_ADEQUACY_WARM_CONVERSE_COST_V1_1_AMENDMENT_20261002.md) records that request/receipt construction occurred after the cold `hello` call and before the target-call timer, rather than before both timers as preregistered. Neither measured timer includes receipt construction, but protocol-order adherence is partial and should be corrected in a replication.

Next instrument native per-rule and Rayon-worker CPU/work counts for the target route; repeat under constrained thread counts and report wall, aggregate CPU, and core budget separately. Expand to additional task families and retain matched adoption/refusal arms. Keep the cold initialization gate from [v1.2](SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_2_RESULTS_20261002.md) and the exact transaction boundary from the [cross-family audit](SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V2_RESULTS_20261002.md) as separate evidence.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_WARM_CONVERSE_COST_V1_PREREG_20261002.md)
- [Protocol-order amendment](SUBSTRATE_ADEQUACY_WARM_CONVERSE_COST_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_cost_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_warm_converse_cost_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_warm_converse_cost_v1_analysis_20261002.json)
- [Fixture/oracle sources](../../../evaluation/substrate_capability/independent_codewrite_oracles.py) and [adoption path](../../../domains/code_write_growth.py)
