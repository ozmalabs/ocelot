# Rooted-frame operation-interface crosswalk v1 preregistration

Date: 2026-09-28  
Status: offline independent reanalysis; not a new runtime capture.

## Question

How do the existing root-anchored BFS candidate sets intersect the observed per-rule dynamic footprints and static access declarations from the corrected access-scope replay on the same live task pair?

## Inputs and matching

Use accepted `rooted_frame_proposal_panel_v1_1` and `rooted_frame_access_scope_reconciliation_v1_2` raw and analysis records. Join by replicate and prompt position. Require each input analyzer to pass, each raw record's locked/post-run inputs to match, each worker's source locks to match its raw lock, and semantic graph digests to agree for every joined worker. Independently rebuild radius 0/1/2 undirected BFS node sets from the saved structural graph and require exact equality with the saved candidate IDs; recompute typed-edge boundaries from the same graph.

## Measures

For each candidate and the separate operational task-reference set, compute trace-event mass touching the set, events wholly inside/outside, concrete-edge reads/writes crossing the cut, and per-RuleUID node footprints that straddle candidate membership. For cross-scope RuleUIDs, report static finite read/write keys, wildcard flags, concrete outside attribute accesses, and their node types. Preserve unlocated/resource-only rows as unknown. Keep observed concrete interface incidences distinct from static possible dependencies and from graph-cut edge counts.

## Gates and limits

All input, join, lock, and independent BFS reconstruction gates must pass. This is an offline crosswalk on one authored two-prompt family with an existing partial trace. It does not establish trace completeness, task relevance of every access, finite domains, necessity of a cut dependency, frame discovery cost, or partitioned-execution correctness. No natural-task prevalence or learned-frame claim is permitted.
