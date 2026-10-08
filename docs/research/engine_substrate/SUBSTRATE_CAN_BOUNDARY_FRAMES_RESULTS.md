# CAN live-boundary frame scheduling pilot — 2026-09-24

## Question and protocol

Can the existing native `run_rules_scoped` path settle concepts frame by frame while retaining cross-frame semantics through live reads on one shared graph?

[`scripts/substrate_can_boundary_frames.py`](../../../scripts/substrate_can_boundary_frames.py) compares the monolithic `run_rules` path with round-robin `run_rules_scoped` calls, one Microtheory per four-concept frame. All frames share one graph and retain every original causal edge. Thus an update in a later frame is visible to subsequent scoped calls; the outer round repeats until every frame has had a quiet turn. Only the mode-specific CAN state-update rule is loaded. Hebbian minting/reweighting, explicit boundary payloads, parallel execution, and native event-driven scheduling are excluded. The harness also tests a CAN-specific Python wake queue over static causal edges. Both paths start from the same generated fields/weights and zero concept states. N=16/32, four graph families, two state modes, and three deterministic replicates produce 48 paired cases. Each call uses a 100,000 progress cap.

Both outputs are checked against a separate Python implementation of the local update equation on the full graph. The monolithic path also receives a terminal probe; the scoped path receives one probe per frame after round-robin settlement. Exact state equality is reported separately from fixed-point validity because asynchronous schedules can converge to different stable states.

## Results

All 48 monolithic and all 48 scoped executions completed within budget. Every monolithic result and every scoped result was stable under the independently evaluated full-graph update equation; all terminal probes returned zero. The two paths produced identical states in 29/48 cases. The remaining 19 cases converged to different full-graph fixed points, showing that settlement schedule changes basin selection without invalidating local stationarity.

| N | Graph family | Exact state matches | Both paths at full-graph fixed points | Median scoped rounds |
|---:|---|---:|---:|---:|
| 16 | blocks4 | 5/6 | 6/6 | 2.0 |
| 16 | path | 4/6 | 6/6 | 2.0 |
| 16 | banded-2 | 5/6 | 6/6 | 2.0 |
| 16 | complete | 3/6 | 6/6 | 3.5 |
| 32 | blocks4 | 3/6 | 6/6 | 2.0 |
| 32 | path | 5/6 | 6/6 | 3.0 |
| 32 | banded-2 | 3/6 | 6/6 | 2.5 |
| 32 | complete | 1/6 | 6/6 | 3.5 |

The historical pre-pushdown engine timings are retained in the raw baseline artifact. They exclude graph/rule setup and are sensitive to host scheduling and policy order; operation counts are the stronger comparison here.

The previous edge-dropping experiment had only 3/36 connected runs that both matched monolithic output and remained stable on the full graph. Keeping all edges and reading from shared state raises full-graph fixed-point validity to 48/48. Exact state equality is lower because grouped frame scheduling changes the update order.

Raw case records and hashes are in [`evaluation/reports/substrate_can_boundary_frames_20260924.json`](../../../evaluation/reports/substrate_can_boundary_frames_20260924.json). The artifact records the harness, seed manifest, native extension, and substrate/rewrite/term source hashes. The extension is loaded from a temporary package.

## Operation attribution

Separate audited twins were run for all three methods. Before each frame turn, the process-global scale audit was reset; the resulting candidate, where, leaf, and Term counts were stored against that frame. Audit timings were discarded. Audited progress/state matched the unaudited execution for all 48 monolithic, all 48 round-robin, and all 48 dependency-wakeup cases. The raw artifact retains per-frame counter maps.

Before matcher scope pushdown, topology-specific medians showed 5.9–13.9× candidate pairs and 5.1–11.3× Term evaluations versus monolithic execution for round-robin scoped runs. The static dependency queue still performed 5.0–12.9× candidate pairs and 4.3–10.4× Term evaluations. This was the evidence for a matcher-level restriction.

## Matcher-scope pushdown follow-up

The scoped matcher previously enumerated all bindings and filtered them afterward. I added a guarded prebinding in [`rewrite.rs::scoped_mt_seed`](../../../runners/dsl/src/rewrite.rs): for a one-edge `has_concept` rule, bind its source to the scoped Microtheory so `extend_each` enumerates only its outgoing membership edges. A structural guard checks that no other `has_concept` edge touches owned nodes and that owned members are not themselves membership sources. If this proof does not hold, the previous full-match/filter path remains in use.

The optimized extension was compared with the preserved pre-pushdown extension on the same 48 seeds and current harness. Monolithic, round-robin, and dependency-queue final states were identical between builds in 48/48 cases. All audited and unaudited outcomes match; every scoped output remains a full-graph fixed point. The overlapping-membership fallback control also passes: a foreign Microtheory binding that touches an owned Concept retains the generic behavior.

| N | Policy | Pre-pushdown candidate pairs / monolithic | Pushdown candidate pairs / monolithic | Candidate reduction, old/new | Term evaluations, old/new |
|---:|---|---:|---:|---:|---:|
| 16 | Round-robin | 7.88× | 1.97× | 4.00× | 6.38× / 1.73× |
| 16 | Dependency queue | 6.88× | 1.72× | 4.00× | 5.56× / 1.55× |
| 32 | Round-robin | 13.23× | 1.65× | 8.00× | 10.99× / 1.55× |
| 32 | Dependency queue | 12.58× | 1.57× | 8.00× | 10.30× / 1.45× |

Medians aggregate the 24 worker records per N and policy across topology/mode cells. Counts are deterministic for these fixed inputs; they are not asymptotic claims. The dependency queue results show that most of the former excess was repeated global candidate enumeration; the remaining work includes repeated frame turns and local matching. The candidate gate improved substantially without changing which fixed point each schedule selected.

The raw comparison artifacts are [`evaluation/reports/substrate_can_boundary_frames_postfilter_baseline_20260924.json`](../../../evaluation/reports/substrate_can_boundary_frames_postfilter_baseline_20260924.json), [`evaluation/reports/substrate_can_boundary_frames_20260924.json`](../../../evaluation/reports/substrate_can_boundary_frames_20260924.json), and the reproducible 48-pair analysis [`evaluation/reports/substrate_can_boundary_frames_scope_pushdown_comparison_20260924.json`](../../../evaluation/reports/substrate_can_boundary_frames_scope_pushdown_comparison_20260924.json), generated by [`scripts/analyze_substrate_can_boundary_comparison.py`](../../../scripts/analyze_substrate_can_boundary_comparison.py). Native extension SHA-256 values are `6fbf02c857b4726637121e833d91c0f81af518b8b744a711ad441a48108f63ea` (pre-pushdown) and `2c1860b10f29f8176337b64957d031ceadb7e32b101dd4518ace1b2af7261a9d` (pushdown). The sequential batch timing medians favored pushdown by 2.3–3.0× at N=16 and 4.9–6.3× at N=32, depending on policy. Because treatment ran before baseline, this is descriptive only; a counterbalanced fresh-process timing replication is required before treating it as a speed result.

## Interpretation and next gate

This demonstrates a correct opt-in frame-scoped settlement schedule on the tested CAN update family, in the limited sense that every returned state is a full-graph fixed point. It does not demonstrate exact monolithic basin selection, general rule-family correctness, a treewidth-based complexity bound, or a speed advantage. The implementation uses shared mutable state and complete per-frame rematching; it is not independent-message GALS and it does not yet use the dependency graph to wake only affected frames.

A CAN-specific static dependency-wakeup queue is compared with round-robin scoped settlement. It yields the same states in 48/48 cases and passes the full-graph fixed-point oracle in all cases. Both scoped policies match monolithic states in 29/48 cases. The queue uses static CAN causal edges; it is not a general dynamic dependency scheduler.

Next measure dynamic wakeup recall under boundary edge insertion/deletion and node/attribute changes, and add matcher candidate restrictions only for patterns with a proven scope-equivalence guard. Profile native matcher time separately from API crossings. Keep basin equality distinct from full-graph fixed-point correctness.
