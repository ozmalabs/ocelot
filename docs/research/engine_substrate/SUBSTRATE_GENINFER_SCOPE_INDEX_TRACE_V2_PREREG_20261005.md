# GenInfer scope index trace v2 preregistration

Date: 2026-10-05

## Question

Can the existing exact `(node type, attribute key, value)` index eliminate GenInfer's repeated full typed-population scan while preserving scoped outputs, and what index construction work does the two-frame fixture require?

## Implementation under measurement

`load_parts_with_scope` uses `TypedGraph::nodes_where` only when the exact `(codebook_type, scope_id)` index has been declared. Otherwise it retains the full `nodes_of_type` scan and exact attribute filter. The indexed fixture declares `(ShapeSignature, scope_id)` before adding its two task codebook parts, so the graph's existing index-maintenance path must admit subsequent insertions. The capture records index declaration/backfill wall time and emits separate work events for index queries and result members.

## Protocol

Use the same production GenInfer fixture and three fresh-process replicates per condition as v1. Conditions are unscoped global, explicit shared-scope global, per-frame scope using the scan path, and per-frame scope using the declared attribute index. Run the K=2 pair. Lock runner, analyzer, protocol, source closure, seed closure, build record, and extension before capture. Preserve exact oracle results, rule attribution, source stability, and zero dropped work events.

Compare query results and candidate work between scanned and indexed per-frame scope. Report full-population nodes visited, scoped result members, selected attributes, parts parsed, search candidates, index construction time, production closure wall/CPU, and work reproducibility. Do not infer big-graph benefit from this small fixture: build/maintenance and graph snapshot clone costs require their own scale curve.

## Gates and limits

Require 12/12 captures (four arms × three fresh workers), exact outputs and valid scope membership for every arm, zero trace drops, stable sources, reproducible work counts, no typed-population enumeration in the indexed arm, exactly two indexed population lookups/members per worker, and identical parsed/candidate totals between indexed and scan-based per-frame arms. This tests index use and insert-time maintenance in an authored two-frame fixture. It does not establish automatic index admission, index behavior after type/attribute changes or graph restore, index clone cost at scale, automatic frame discovery, natural-task prevalence, or semantic safety of harness-supplied scopes.

## Reproduction

```sh
scripts/engine_build.sh --lib-only
python3 evaluation/substrate_capability/substrate_geninfer_scope_index_trace_v2.py --lock
python3 evaluation/substrate_capability/substrate_geninfer_scope_index_trace_v2.py --run
python3 evaluation/substrate_capability/analyze_geninfer_scope_index_trace_v2.py
```
