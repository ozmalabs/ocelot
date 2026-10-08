# `NodesOfType` site-specific trace capture v2 preregistration

Date: 2026-10-03  
Status: preregistered before the source-specific replay.

## Question

Can direct evaluation of the `NodesOfType` Term be separated from typed-population helper scans in runtime access traces, while preserving task semantics and trace completeness?

## Change under measurement

The evaluator now uses event 36 (`term_nodes_of_type_query`) once per invocation, including empty populations, and event 37 (`term_nodes_of_type_candidate`) once per returned node. Existing events 34/35 remain reserved for other typed-population paths. All events retain RuleUID, type resource, candidate node where applicable, and aggregate count.

## Workload and gates

Replay the established two-prompt workload in three fresh workers using the source-built engine. Retain request traces, graph and rule exports, lifecycle/control outputs, and full worker logs. Require: (1) stable source lock and provenance; (2) exact prompt schedule and three distinct processes; (3) semantic graph parity with the accepted v1.1 digest and agreement across workers; (4) zero access/work trace drops; (5) all event-37 rows match a `term_type_read` for the same RuleUID, node, and type; (6) events 36/37 are reported separately from helper events 34/35; and (7) all existing semantic controls pass. Retain raw output on any analysis or gate failure.

## Boundary

This is a source-site instrumentation check on one authored prompt pair. It does not establish all graph dependencies, workload prevalence, frame locality, partition correctness, or instrumentation overhead. Event counts are aggregated access-trace counts, not unique query invocations unless noted.
