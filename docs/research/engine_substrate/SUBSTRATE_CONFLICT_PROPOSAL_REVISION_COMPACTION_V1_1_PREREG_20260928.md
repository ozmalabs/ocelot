# Bounded proposal revision-event retention v1.1

## Question

Does deleting the prior revision event after its three ordered closures bound event history and reduce later resolver work while preserving the v1 revision semantics?

## Protocol

Repeat the v1 explicit revision pipeline with three fresh workers and N=2/8/32/64. Before each revision after the first, remove the prior revision node (and its incident stage/event edges) from the graph, record host cleanup elapsed time and graph node/edge deltas, then apply/create the next revision event and run max/count/decision closures. Compare stage Term counts against the immutable v1 pipeline capture on the same native extension/build. Every stage captures fixed-point status and native counters. Graph snapshots must show at most one active revision node after each revision.

## Gates

All target state and top-count outputs must match the independent score oracle for initial, higher-add, tie-add, tie-remove, and score-lowering states. All stage closures reach fixed point. Exactly one revision node remains active after each completed revision. Integer native counters replicate across workers after excluding timing values. For revisions after initial, total stage Term evaluations must be lower than or equal to the matching unpruned v1 revision; the report will show both values. Cleanup timing is descriptive, and cleanup graph deltas must show one old event plus its incident edges removed.

## Limits

This measures physical event-node removal by the caller, not built-in compaction, retained external audit storage, or interrupted-pipeline recovery. The sequence and graph family are fixed and sizes stop at N=64. Host mutation and event creation remain separate from native Term counters; cleanup time and graph deltas are reported alongside them.
