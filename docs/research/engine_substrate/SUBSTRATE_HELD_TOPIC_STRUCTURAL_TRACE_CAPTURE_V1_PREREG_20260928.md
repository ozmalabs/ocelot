# Held-topic structural and operation-trace capture v1 preregistration

Date: 2026-09-28  
Status: fresh instrumentation replay of the fixed seven-case held-topic suite.

## Goal and fixed workload

Extend the accepted v1.6 live held-topic suite with per-operation concrete rule-access traces, static rule access declarations, all-scope scheduler/deferred work, and typed boundary-attribute metadata. Run all seven pre-existing cases in order: three taught positive facts, one table-path positive, one honest-capability positive, one unknown-topic refusal, and one injected local-source hit. Do not select cases based on observed outcomes. Three fresh processes each boot the full runtime and replay the same teaching/query schedule.

## Measurement boundary

For each of the three teaching operations and seven conversation turns, instrumentation setup and post-call snapshot work are outside the request timer; the original operation timer includes only the teaching or conversation call. Record graph-scoped access rows, all-process-scope work rows, per-rule scale counters, static read/write/resource declarations for observed RuleUIDs, and graph-scoped/all-scope scheduler/deferred counters. Preserve host grounder call records already exposed by the fixed harness. For each declared operational task frame, record node types, attribute-key/value-kind histograms, bounded observed categorical values for designated status/kind/path fields, complete direct typed-edge cuts, and whole-graph node/edge counts. Observed values are samples, not declared domains.

## Gates

1. Three fresh worker PIDs, current base fingerprint and driver/analyzer/protocol/amendment hashes locked before and after, and embedded base worker locks stable. Record the known drift from accepted v1.6 provenance; use that report only as an outcome/structure reference.
2. Each worker replays the fixed seven prompts and three teaching inputs; independent answer, refusal, route, evidence, and release gates from v1.6 are rechecked; semantic task signatures and complete boundary structure are compared with the accepted v1.6 report, without a source-identity or causal claim.
3. Access rows conserve weighted counts and report drops; every trace RuleUID resolves to static metadata or is explicitly counted unresolved. Static-resource mismatch categories are reported without assuming unobserved accesses are absent.
4. For every measured operation, all-scope work rows reconcile exactly to all-scope scheduler/deferred counters by graph scope and metric; operation-kind markers are valid; dropped work rows are zero. Process-global totals are also compared with the sum of scopes.
5. Boundary metadata is independently reconstructed from serialized graph snapshots and the operational member IDs; full direct-cut edge lists/counts reproduce.

## Limits

This is a live capture on one authored task family with a fixed seven-case suite, not an independent prevalence sample. Task ownership is operationally declared. Runtime access tracing is partial; host-level Python execution outside exposed callbacks is not fully intercepted. Attribute values observed at a checkpoint are not complete finite domains. Passing cuts and counter reconciliation does not prove frame independence, learned cheap cuts, partitioned fixed-point correctness, or a general cost bound.
