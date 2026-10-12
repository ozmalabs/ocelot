# Rooted frame-proposal panel v1.1 amendment (2026-09-28)

## Extension

Retain v1's workload, BFS roots/radii, state-graph measures, and claim limits. Add the current native `runtime_access_trace` around each prompt call, resetting the bounded trace separately before each request. Record per-event rule UID, event kind, node/resource/peer IDs, multiplicity, and dropped-event count. Project each concrete trace onto the already-generated radius-0/1/2 candidate sets and the protocol-owned reference set. Proposal construction must not inspect these trace rows or reference labels.

The primary v1 structural measurements do not change. Secondary trace measures are weighted events touching either candidate endpoint, events fully inside/outside, events with no concrete node IDs, trace coverage by event kind, and the number of rule UIDs with candidate-touching events. Require nonzero trace events, zero dropped event keys, exact weighted-count conservation, identical traced graph/task semantics to the accepted v1 baseline, and independent recomputation of all trace projections from raw trace rows plus stored candidate IDs.

## Coverage caveat

This trace is known partial: events are emitted only under an active `RuleUid`, specialized Terms and failed matcher work are not uniformly covered, and host/tool/scheduler work outside rule scopes may be absent. “Touches a candidate” does not mean the candidate contains all required dependencies; “outside” does not mean irrelevant. Preserve event kinds and no-ID counts so broad/type-query events are not misclassified as local or global.

## Provenance and exclusions

Use a new lock, runner, and analyzer; hash the accepted v1 capture as the semantic baseline. The accepted v1 report remains unchanged. If the v1.1 analyzer fails, preserve that attempt separately and amend before rerunning. This extension does not add task families or support prevalence claims.
