# Live self-report task-boundary v2 preregistration

Date: 2026-09-27 local

## Question

Do two task views produced by the current live self-report fixture have compact owned subgraphs and low complete typed-edge boundaries in the full runtime graph, and do their boundary structures reproduce across fresh processes?

## Workload and framing rule

Reuse the current-source full-seed self-report pair: `report your organisation` (the successful lifecycle route) followed by `describe who you are` (the known route-selection shortfall). After both turns, extract two explicitly protocol-defined task-owned sets from graph identity edges:

- inbound Message and its origin DiscourseEvent;
- any Goal comprehending that Message, its originated-in and transitioned-by events, subgoals, reply candidates, and matching ProductionGateReceipt;
- outbound messages that respond to that inbound Message.

This is an operational ownership definition supplied by the measurement, not a learned frame. Compute each induced subgraph, every typed edge crossing its boundary, unique external nodes and types, a deterministic min-fill upper bound on induced owned width, direct edges between the two task-owned sets, and shared external nodes. Retain only summaries and exact boundary edge lists, not the full graph dump.

Run three fresh workers under a source/native lock. The same worker also retains the per-event matcher attribution and lifecycle controls so graph projection does not replace task behavior evidence.

## Gates

1. Three distinct PIDs and stable worker start/end/post-run fingerprints.
2. The first prompt preserves its self-report Goal lifecycle; the second prompt reproduces its separately classified route shortfall; all five identity/failure controls pass.
3. Every owned ID exists in the final graph; each reported cut equals an independent recomputation from the full typed edge list; all edge endpoints and external node types resolve.
4. Per-family owned/internal/boundary counts, width upper bounds, direct cross-task edges, and shared external-node sets reproduce exactly across three workers after volatile `SystemModel.ts` and `runtime_s` fields are excluded from semantic graph comparison.
5. The carried matcher-attribution gates continue to pass at all nine producer-event intervals.

## Interpretation boundary

This tests two declared operational task views in one live self-report fixture. Small induced width is not the treewidth of matcher dependencies, does not show that inference factorizes, and does not establish cheap cuts discovered by the substrate. No size scaling or execution partition is tested. Compare the outputs descriptively with the prior held-topic, self-report, and concurrent-scene boundary panel; do not pool manually framed task families into a prevalence estimate.
