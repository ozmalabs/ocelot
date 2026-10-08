# Held-topic runtime interface trace v1.4 preregistration (2026-10-01)

## Objective

Resolve the v1.3 limitation where `NodesWhere` index-query events encoded a type symbol in a field exposed to Python as a node ID. Preserve the existing snapshot API for current clients and add a detailed snapshot that returns symbol peers as names in a distinct field. Attribute each query by rule UID, node type, attribute, and indexed-versus-fallback mode.

Record one query event per `NodesWhere` call, one candidate-scan event for each typed node visited by the fallback scan, and one result-candidate event for each returned node in either mode. These counts measure fallback nodes visited and output cardinality. They do not measure internal B-tree/index lookup instructions or latency.

## Gates

Use the same seven held-topic turns and three fresh workers with a rebuilt optimized extension and exact source lock. Require unchanged snapshot API availability, successful type-symbol resolution, zero dropped events, mapped UIDs, exact event/frame aggregate reconciliation, source stability, seven turns per worker, repeatable traces, and task-quality reporting independent of trace integrity. For each query, require both `attr:<key>` and `type:<name>` in the static read set to classify it explicitly; otherwise classify it as wildcard-covered only when `reads_any` is declared, else uncovered. Reconcile query counts, fallback scan units, and result cardinalities by type, attribute, mode, and rule where available. Retain any uncovered or unresolved query.

## Limits

Fallback scan counts are observed candidate visits. Indexed mode's B-tree internal work is not measured; result count is only the returned set size. The workload is one task route and says nothing about the distribution of index use across natural tasks. No partitioned execution claim follows from this trace.
