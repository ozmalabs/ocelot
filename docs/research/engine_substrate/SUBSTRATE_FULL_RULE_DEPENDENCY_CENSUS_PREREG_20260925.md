# Full loaded rule dependency census preregistration

Date: 2026-09-25  
Status: preregistered exploratory structural census

## Question

Does the full locked seed-loaded rule store expose sparse, modular read/write dependencies, or do wildcard/resource overlap and cross-area interactions create a broad coupled system? This measures the engine's native declared access graph, not observed firing co-occurrence or semantic independence.

## Workload and extraction

- Load the same frozen 833-file / 737-indexed-ID corpus used by the seed scale and projection measurements, with the current source-locked native extension.
- Run two independent fresh full boots. Require exact equality of boot report, complete graph, grammar, rule store, access arrays, active rule order, and count across the two workers and parity against the frozen full-corpus state.
- Read `rule_access_sets()` and `export_rules()` from native state. Retain slot index, name, active flag, exact read resources, term-edge read resources, write resources, and `reads_any` / `writes_any`. Align metadata only by exact RuleIdx order.
- Build two directed active-rule dependency projections: (a) explicit resource intersections only; (b) conservative native wildcard completion, where a `writes_any` source connects to every active reader and every active `reads_any` target receives edges from every active writer. Keep self-dependencies explicit.
- Report active/inactive counts; resource key counts; wildcard populations; in/out degree distributions; weak and strong component distributions; dependency edges crossing `area` labels; and binary contiguous RuleIdx cuts at frame widths 16/32/64/128. Include five fixed-seed shuffled order baselines for each width. Count both crossing dependencies and endpoint boundary size.

## Gates and limits

Pass requires exact two-worker full-state parity, matching native access arrays, matching `export_rules` / `rule_access_sets` lengths and slot order, and source/build/corpus/runner/protocol hash stability. The native access graph is a conservative declared dependency model only to the extent `derive_access` itself is conservative; do not reinterpret it as runtime access coverage. RuleIdx blocks and shuffles are structural baselines, not learned frames or optimized separators. No partitioned execution, treewidth, cheap-cut prevalence, or task success claim is made.

The report must retain null/unknown metadata rather than silently dropping rules. If arrays differ across processes or cannot be aligned exactly, stop structural interpretation and report only the failed gate.

## Initial run note

The first two-worker capture matched full state and native access arrays, but its source-stability gate failed because `substrate/world_adapter.py` changed between the pre-run lock and post-run check. That raw run is preserved and excluded from structural claims. Six active rule names occur twice; the analyzer aligns duplicate names sequentially against native RuleIdx order and does not require globally unique names. Re-lock and rerun only after the source set is stable.
