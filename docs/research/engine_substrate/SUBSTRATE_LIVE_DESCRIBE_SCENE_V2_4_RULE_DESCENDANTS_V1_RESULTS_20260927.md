# Live describe-scene v2.4 rule-produced descendants v1 (2026-09-27)

## Result

A derived analysis follows native `effect_node_mint` and `effect_edge_upsert` trace rows from each request's declared lifecycle and the shared Scene+Percepts input. It adds only a rule-minted node that is connected to the measured frame by a captured request-local edge-upsert path; it does not absorb Concept nodes or other pre-existing graph nodes into frame ownership.

The descendant set is identical across all three traced repeats:

| Request | Rule-produced descendants found | Types | Selected events touching lifecycle, input, or these descendants | Total selected events |
|---|---:|---|---:|---:|
| A | 7 | 3 Goal, Intent, TeacherRequest, SelfConcern, GapRecurrence | 7,775 | 1,140,892 |
| B | 5 | 3 Goal, Intent, TeacherRequest | 8,808 | 997,848 |

The result exposes rule-produced child Goals and request-associated Intent/TeacherRequest nodes that were outside the prior request-lifecycle projection. The expanded set accounts for more concrete accesses, but still touches under 0.9% of selected events. The previous projection analysis found over 99% of events touch none of its declared lifecycle/input nodes; adding these directly connected rule-minted descendants does not reverse that result.

## Interpretation and limits

This is a reproducible **lower bound** on rule-produced task descendants. It uses only native node-mint and edge-upsert events with concrete IDs. It cannot recover host-created nodes, attribute-only descendants, writes hidden inside specialized operations, dependencies without node/peer trace events, or temporal causality from the aggregated trace. It treats pre-existing Concepts and graph hubs as interfaces rather than owned descendants. Therefore the remaining events are not classified as irrelevant; they may involve omitted dependencies or broad graph scans.

The result improves dynamic ownership accounting, but does not prove a complete task frame, a small separator, causal factorization, or the benefit/safety of scoped execution. Next capture a complete mutation/dependency trace or build a validated rule-specific ownership map for the remaining dominant readers, then conduct scoped-versus-global interventions with exact task and whole-graph parity.

## Artifacts

- Analyzer: [analyze_substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1.py](../../../scripts/analyze_substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1.py)
- Analysis: [substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_20260927.json](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_20260927.json)
- Source capture: [v2.4 raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json)
- Declared-boundary analysis: [boundary-touch v1](SUBSTRATE_LIVE_DESCRIBE_SCENE_V2_4_BOUNDARY_TOUCH_V1_RESULTS_20260927.md)

## Source-level attribution of dominant rule reads

The three runtime rules named `recognise_a_thing_that_moves_itself`, `recognise_a_thing_that_stays_put`, and `recognise_a_counter` are authored in `scripts/arc_self_report.py::build_describe_faculty`; that file's SHA-256 matches the v2.4 source lock. Each rule joins `scene --has_percept--> p` with `gmt --has_concept--> con`, checks the candidate Concept's `name` and `Holds(label, p)`, then adds `p --is_a--> con`. The measured `name` reads therefore arise in a concrete candidate lookup over Microtheory membership while recognizing each percept. This is a broad relational interface whose candidate cardinality depends on the matched `has_concept` population, even when the Scene boundary has only three Percepts. The trace does not reveal how many candidates are necessary, nor does it show that a lookup index would preserve semantics.

The curiosity rule's native definition matches `mt --has_concept--> c`, checks `state` and `is_ambivalent`, then marks uncertain Concepts. This likewise traverses a Microtheory membership relation; its relevance to a task depends on which Microtheories are matched at runtime. The next controlled study should sweep distractor Concepts in the matched Microtheory while holding percept count and positive matches fixed, and measure candidate/Term work and semantic output. That would turn the current source-level diagnosis into a scaling result.

## Ownership refinement

The initial analysis counted all connected native mints as task descendants. A follow-up source-informed classification separated five task-local descendants per request from request A's two persistent shared-state writes (`SelfConcern` and `GapRecurrence`, attached to the shared Agent). See the [v1.1 amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_V2_4_RULE_DESCENDANTS_V1_1_AMENDMENT_20260927.md) and [independent v1.1 analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1_20260927.json). Interpret the original 7/5 figures as connected minted candidates, not an ownership claim.
