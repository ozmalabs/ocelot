# Live frame rule-scope capture v1.2 results

A fresh current-source native build passed the engine provenance check. The
source-locked capture then ran three fresh workers over the two registered live
requests. All runner gates passed: source-lock stability, task/lifecycle and
controls, stable post-request rule exports, identical final semantic graph
digests, and complete resolution of 2,394/2,394 runtime RuleUID observations
to same-request native rule definitions. Independent raw analysis confirms the
same graph and access/work traces across workers and all six request records.

The final graph has 25,065 nodes and 11,543 edges. The protocol-declared cuts
replicate across workers: turn 0 owns 8 nodes, with 16 internal edges, 38
crossing incidences, 20 distinct external nodes, and induced min-fill upper
bound 2; turn 1 owns 3 nodes, with 2 internal edges, 20 crossing incidences,
16 distinct external nodes, and upper bound 1. The cuts are tiny relative to
the full graph, but their boundaries exceed their owned-node counts. These
bounds describe each induced node subgraph only; they do not bound a rule
factor/dependency graph. Of 401 runtime rule definitions, 93 contain a
whole-population term and 124 contain local-adjacency terms. Across requests,
1,688,754 weighted access events were observed. This combination does not
support a claim of complete frame factorization: the active rules include
population-wide reads and no complete task-variable/domain or operation
dependency model is available.

The result is a fresh, reproducible baseline for the current worktree, replacing
stale-source live captures for this prompt pair. It is not a learned separator
result, a representative natural-task sample, or a partitioned-execution speed
claim. Frame discovery and maintenance cost, runtime access-to-frame coverage,
coupled cross-frame mutation controls, and independently authored task families
remain necessary before asserting cheap-cut prevalence or an inference bound.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_LIVE_FRAME_RULE_SCOPE_CAPTURE_V1_2_PREREG_20261004.md)
- [Current-source capture runner](../../../scripts/substrate_live_frame_rule_scope_capture_v1_2.py)
- [Independent rule-scope analyzer](../../../scripts/analyze_live_frame_rule_scope_capture_v1_2.py)
- [Structural reanalysis](../../../scripts/analyze_live_frame_rule_scope_structural_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/live_frame_rule_scope_capture_v1_2_lock_20261004.json)
- [Capture summary](../../../evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_20261004.json)
- [Raw worker archive](../../../evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz)
- [Independent rule-scope analysis](../../../evaluation/reports/live_frame_rule_scope_capture_v1_2_analysis_20261004.json)
- [Independent structural analysis](../../../evaluation/reports/live_frame_rule_scope_structural_v1_2_analysis_20261004.json)

Reproduce from the repository root with python3 scripts/substrate_live_frame_rule_scope_capture_v1_2.py, then run both analysis scripts.
