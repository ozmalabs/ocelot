# Live runtime store replay v1 preregistration

## Question

Can each first-graph/cumulative-rule snapshot from live store-state capture v1.2 be restored in a fresh native substrate and replayed to a fixed point, and how closely do its per-rule work counts reproduce the corresponding live request/store counters?

## Method

For every request/store payload in v1.2, restore the captured graph with `graph_from_dict`, import the captured definitions in local-index order, and require exact graph and rule export round-trip before execution. Enable native global and per-rule counters only after restore. Run the complete imported rule store with a 100,000 progress-step cap until the first no-progress run (maximum eight calls); retain per-call progress and aggregate per-rule metric counts. Attribute replay rows by replay audit identity to local rule index. Independently derive expected per-store counts from the v1.2 request observations by mapping each parent audit ID to its source store and local rule index.

The capture stores one first-observed graph and the union of local rule slots observed during a request. It does not preserve the chronological closure-call schedule, each call's scope, or intervening host mutations. Therefore exact per-store counter parity is measured, not assumed. A mismatch is a valid result and must be explained or retained as a replay coverage gap.

## Checks

The source-matched engine and all parent/capture input hashes must match before and after replay. Every payload must pass gzip, hash, node/edge integrity, contiguous local rule-index, graph round-trip, and rule round-trip checks. The independent analyzer must reconcile the full expected/replayed metric sets, retain missing or extra metrics explicitly, and report exact parity separately for candidate tests, Term evaluations, and all per-rule metrics. It must not relabel a mismatch as success.

## Scope

This is one authored two-request route and one fixed-point replay per captured store. It measures whether the current capture is sufficient for independent replay; it is not a natural-task or scale estimate. If counts differ, the next capture must record closure-entry graph states, active rule selections/scope, and intervening mutations at sufficient resolution to replay the original schedule.
