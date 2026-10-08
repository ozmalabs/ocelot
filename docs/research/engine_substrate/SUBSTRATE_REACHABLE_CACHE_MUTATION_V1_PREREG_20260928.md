# ReachableFrom cache mutation invalidation v1 preregistration

**Question:** Does the experimental same-graph `ReachableFrom` memo remain observationally correct after mutations through the public Python/native substrate surfaces, and does each mutation force a fresh query before the next applicable rule evaluation?

## Design

Use the authored `browser_affordance_reach` seed in a minimal `WorldAdapter`. Construct one session, four reachable elements, and four affordances, and preinstall the four expected mirror edges. Run the rules once so the cache holds one `ReachableFrom(session, contains)` result without a graph-changing effect. Confirm one entry and four result values. Reset only cumulative hit/miss statistics, retaining that live entry.

Cross ten mutation cases with cache off/on, in three fresh workers per case (30 workers total). Each worker creates independent cache-off and cache-on replicas, counterbalancing their order. Mutations use the user-facing `Substrate` wrapper where available and native `PySubstrate` methods for bulk/unchecked APIs. Cases: isolated node insertion; unchecked path insertion plus affordance edges; edge deletion; batch edge deletion; node deletion; one-node attribute write; uniform bulk attribute write; per-node bulk attribute write; node type change; and checked edge insertion after installing the required edge production. After mutation, run the rules to fixpoint and compare exact semantic graphs, cache stats, rule progress, and mirror counts. The cache-on arm must take at least one fresh miss, retain exactly one fresh result equal in cardinality to the expected reachable set, and preserve the baseline before-mutation result of four values.

Attribute and type changes do not alter `ReachableFrom`'s topology answer, but should still invalidate the graph-dependent memo under the current conservative mutation policy. Node/edge topology cases assert the expected post-mutation reachable-set cardinality. The browser seed has no deletion/retraction rule for an affordance that becomes unreachable; therefore deletion cases assess cache result freshness and cache-on/off semantic parity, not truth maintenance of pre-existing mirror edges. This limitation is reported separately.

## Gates

1. Source and native build fingerprint stable before and after every worker; native build not stale.
2. All 30 workers complete with the registered mutation case and counterbalanced cache order.
3. Every primed cache-on arm begins with exactly one entry/four result values and records no topology drift before intervention.
4. Cache-off stats remain zero; cache-on post-mutation stats have at least one miss and exactly one live result entry.
5. Cache-on/off graph, rule progress, and mirror counts match exactly for each worker.
6. The final cache result cardinality matches the case's declared reachable-node expectation; topology mutation cases also differ from four as prescribed.

No wall-time claim is made. Payload byte estimates are retained only for diagnostic context. This panel covers ordinary Python-facing graph mutations in this seed/workload, not every Rust/internal mutation route, concurrent access, or every rule family.

## Artifacts

Runner: [`scripts/substrate_reachable_cache_mutation_v1.py`](../../../scripts/substrate_reachable_cache_mutation_v1.py)  
Analyzer: [`scripts/analyze_substrate_reachable_cache_mutation_v1.py`](../../../scripts/analyze_substrate_reachable_cache_mutation_v1.py)  
Lock: `evaluation/substrate_capability/reachable_cache_mutation_v1_lock_20260928.json`  
Raw: `evaluation/reports/substrate_reachable_cache_mutation_v1_20260928.json`  
Analysis: `evaluation/reports/substrate_reachable_cache_mutation_v1_analysis_20260928.json`
