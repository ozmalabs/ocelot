# Live self-report scale study V1: preregistration

Date: 2026-09-27

## Question

Does the substrate preserve its live self-report behavior and how does its measured rule work change as unrelated Concept memberships are added, with all seeded rules active? This is a second task topology after the live scene-description study.

## Workload and intervention

Each worker boots the full seed set, adds the requested number of synthetic `Concept` nodes (0, 1,024, or 4,096), each connected by one `has_concept` edge to a dedicated noise Microtheory, then issues the single full `converse` request `report your organisation` as Alice. The synthetic concepts have no classification edges and are unrelated to the self-report output. All rules remain active.

For each size, run two independent worker processes in each arm: ordinary untraced execution and execution with native aggregate/per-rule scale counters and runtime access tracing enabled. The fixed randomized schedule has 12 workers total. Process peak RSS, request wall time, process CPU time, graph sizes, semantic graph digest, exact reply, route, and goal lifecycle are recorded.

## Preregistered gates

1. All 12 workers use identical locked source inputs and distinct process IDs.
2. Every worker returns the same nonempty organisation-related reply, uses the `self_report` route, and resolves exactly one goal through selection, execution, and action result; the goal is closed and inactive.
3. Each audited/untraced pair has identical reply, goal record, semantic graph digest, and graph counts.
4. Noise Concept and membership counts equal the assigned size; none gains an `is_a` classification.
5. The seeded graph is constant across workers; graph node count grows exactly with the noise size.
6. Untraced workers contain no audit data; audited trace event counts reconcile with retained rows and have zero drops.
7. Native candidate and term counters reconcile with per-rule, per-clause, and term-kind totals; ambiguous/missing attribution is reported without assigning it to a unique rule.
8. Audited work and graph output repeat exactly between replicates at each size.

Any failed gate invalidates the corresponding scale claim. Timings are descriptive only: two replicates per cell are not enough to establish a complexity law. The synthetic membership axis is a controlled stressor, not a model of natural task distributions.

## Interpretation boundary

This study evaluates one live route over a second task topology and one controlled graph-size axis. It does not measure learned frame locality, treewidth, natural prevalence of the intervention, other scaling dimensions, or general capability. It is not evidence that the self-report route's semantic content is factually correct; it checks behavioral stability and lifecycle.
