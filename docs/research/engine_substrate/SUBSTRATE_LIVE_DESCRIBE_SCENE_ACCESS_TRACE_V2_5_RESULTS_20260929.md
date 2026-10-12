# Live describe-scene access trace v2.5 results

**Status:** current-source paired capture and source-aware analysis on one production route.

## Gates

The six-process capture passes all eight preregistered gates: three paired replicates and distinct processes; joined threads with no errors; worker and post-run source-lock stability; task, schedule, lifecycle, and reply checks; semantic whole-graph parity between trace arms; complete nonempty per-request intervals; no trace events in untraced arms; and trace-total reconciliation. The independent analysis passes 11 checks, including current `access_trace.rs` source/hash agreement, event-kind definitions, ownership-set disjointness, repeated ownership classification, and access-count reconciliation.

## Request boundary and selected accesses

The A request has 7 lifecycle nodes and 5 rule-minted descendants (3 Goal, 1 Intent, 1 TeacherRequest); B has 6 lifecycle nodes and the same five descendant types. Descendants are classified through the source-informed `has_subgoal`, `has_intent`, and `seeks_interpretation_shadow` relation policy. A's two `SelfConcern`/`GapRecurrence` nodes remain persistent shared side effects. The shared Scene+Percept input comprises four nodes and is counted as an interface.

The stored graph projection covers the lifecycle nodes only (7 for A, 6 for B), before adding the five derived descendants. These lifecycle-only subgraphs have min-fill width upper bound 2, but their final-graph cuts have 36 and 33 incidences and 21 and 19 distinct external nodes, respectively. Because descendants were derived from operation traces after the graph projection was captured, these cut values are not measurements of the expanded request frame and must not be read as its separator size.

Across the three traced replicates, A has 1,426,593 selected access events and B has 1,399,147. Only 6,403 A events (0.45%) and 9,184 B events (0.66%) touch any explicitly classified request, other-request, shared Scene/Percept, or persistent-side-effect node. Thus 99.55% and 99.34%, respectively, touch none of those named sets. This is an “unclassified by these ownership labels” count: it does not show that the accesses are irrelevant, and the event trace is not a complete dependency log. Within-request pairwise accesses number 77 for A and 60 for B; accesses between the request frames number 0 for A and 13 for B; pairwise accesses from a request frame to other external/global nodes number 2,185 and 2,084. The visible selected-access workload is therefore dominated by nodes outside the declared request and shared-input sets.

Tracing overhead is workload-dependent in this small paired sample. Median traced versus untraced wall time is 17.64 s versus 17.33 s for A and 1.53 s versus 1.23 s for B; median thread CPU is 17.39 s versus 17.09 s for A and 0.780 s versus 0.616 s for B. Do not use traced timing as an uninstrumented cost estimate.

## Interpretation and next gate

This held-out production route does not support inferring cheap operation from a small lifecycle graph or low induced width. It reports substantial selected work against nodes outside the currently labeled request and input sets. The conclusion is limited by partial trace coverage, the lifecycle-only stored graph projection, one route and task fixture, and instrumentation overhead. This capture does not measure discovery/maintenance cost, full scheduler work, safe scoped execution, or natural-task prevalence.

The next capture should store final graph boundary projections after applying the request-descendant policy, retain separate shared input/global/persistent classes, and add operation-work counters for scheduler passes, candidate matching, and queue work across the complete request. Compare an independently supplied request partition with a blind partition and verify whole-graph parity under scoped execution plus omission and contamination controls. Run a second production task family before estimating how often these boundaries occur naturally.

## Artifacts

- Protocol: [v2.5 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_5_PREREG_20260929.md).
- Capture runner: [v2.5](../../../scripts/substrate_live_describe_scene_access_trace_v2_5.py); analyzer: [v2.5 analysis](../../../scripts/analyze_substrate_live_describe_scene_access_trace_v2_5.py).
- Lock: [source lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v2_5_lock_20260929.json); capture summary: [paired run summary](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_20260929.json); raw capture: [six workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_workers_raw_20260929.json); analysis: [ownership and access report](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_5_analysis_20260929.json).
