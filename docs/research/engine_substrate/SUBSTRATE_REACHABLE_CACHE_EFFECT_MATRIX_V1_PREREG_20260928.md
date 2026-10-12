# ReachableFrom internal rule-effect matrix v1 protocol

**Question:** Does the post-fix immediate invalidation preserve rule semantics when an earlier rule changes graph state through each common effect family and a later same-pass rule consumes `ReachableFrom`?

This is a targeted post-fix regression panel, following the known in-pass falsifier. Cross eight effect classes with cache off/on in five fresh workers per class (40 workers total), counterbalancing cache order: `AddEdge`, `DelEdge`, `AddNode`, `AddNodeIfAbsent`, `DelNode`, `SetAttr`, `SetAttrIfDifferent`, and `ReplaceValue`. Each graph begins with a reachable subject and an idempotent priming rule. An intermediate rule performs one listed effect. A later rule queries reachability (and, for attribute cases, the updated attribute) and derives a detection edge. Delete/replace cases expect the subject to be absent from the new closure and use a negated membership condition. Both modes must reach the declared fixed-point graph with identical progress counts; the cache-on arm must record a post-mutation miss.

Retain per-rule read/write sets, exact graphs, progress steps, reachability counters, source/native fingerprints, and a run manifest. This tests effect dispatch through the rule engine in a minimal monotone/stratified probe; it makes no timing, natural frequency, or universal Term-dependency claim. `SetRuleClause`, rule patches, deferred I/O/identity/net-collapse effects, arbitrary dynamic Terms, and concurrent behavior remain outside this matrix.

Runner: [`scripts/substrate_reachable_cache_effect_matrix_v1.py`](../../../scripts/substrate_reachable_cache_effect_matrix_v1.py)  
Analyzer: [`scripts/analyze_substrate_reachable_cache_effect_matrix_v1.py`](../../../scripts/analyze_substrate_reachable_cache_effect_matrix_v1.py)  
Lock: `evaluation/substrate_capability/reachable_cache_effect_matrix_v1_lock_20260928.json`  
Raw: `evaluation/reports/substrate_reachable_cache_effect_matrix_v1_20260928.json`  
Analysis: `evaluation/reports/substrate_reachable_cache_effect_matrix_v1_analysis_20260928.json`
