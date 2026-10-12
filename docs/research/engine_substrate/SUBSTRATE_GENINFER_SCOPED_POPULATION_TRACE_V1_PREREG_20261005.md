# GenInfer scoped population trace v1 preregistration

Date: 2026-10-05

## Question

When the production GenInfer rule runs with an explicit frame `scope_id`, does scope filtering reduce only parsed candidate work, or does it also avoid enumerating unrelated `ShapeSignature` population nodes?

## Protocol

Use the existing explicit-scope v1.3 source fixture and current native implementation. Capture three independent replicates for each of three K=2 conditions: `unscoped_global`, `explicit_global` (both parts carry the same scope), and `frame_scoped` (each frame has its own scope). Enable operation-work tracing only around production `run_rules()`. Preserve exact transformation oracle and output checks, task-local scope membership receipts, helper family/rule attribution, all work units, dropped-event counts, graph size, CPU/wall time, and source/build identity. Lock all source files, seeds, protocol, and analyzer before capture.

The primary trace fields are:

- kind 47: `helper_codebook_population_node`, incremented for each typed population member visited before filtering;
- kind 48: `helper_node_attribute_examined`, counted only for matching-scope members whose attributes are iterated;
- kind 49: `helper_codebook_part_parsed`, incremented for parsed codebook entries;
- kind 51: `helper_search_candidate`, incremented at instrumented search loop sites.

Compare the scope arms on exact frame outputs and report scan/parse/search work separately. Do not treat a lower scoped count as a safe frame-discovery result: scope IDs are authored by the harness and the capture contains no learned boundary.

## Gates and claim limit

Require 9/9 cases (three arms × three fresh workers), zero dropped trace events, source stability within every worker, consistent exact transformations within each frame, valid explicit scope membership, and trace counts consistent across repeats. The conclusion is limited to the tested production GenInfer rule and authored 2-D fixtures. It does not establish scope discovery, natural-task scope prevalence, complete helper cost, or end-to-end speedup.

## Reproduction

```sh
python3 evaluation/substrate_capability/substrate_geninfer_scoped_population_trace_v1.py --lock
python3 evaluation/substrate_capability/substrate_geninfer_scoped_population_trace_v1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_scoped_population_trace_v1.py
```
