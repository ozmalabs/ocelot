# Reachability cache versus materialized profile v1.2 results

## Result

The corrected v1.2 replay passes all ten analyzer checks over 60 cases: binary/ternary trees at N=64/128, 1/4/16 reader rules, and five fresh repetitions. Cache-on has exactly N−1 misses and (N−1)(R−1) hits, matching the query work after the injective matcher omits the root self-binding. All three arms reach a zero-progress fixed point in one reader pass; source queries match independent DFS, and the materialized edge relation exactly matches the independent transitive closure. Source lock, order schedule, restricted-profile admission, and fresh-node negative control pass.

End-to-end medians include graph construction, relevant rule installation, and closure. Explicit materialization is slower than cache-on in all 12 shape/size/reader cells. At 16 reader rules it is 1.28–1.54× the cached total. The cache reduces total time versus cache-off at R=16 in every cell (ratios of cache-on/cache-off 0.65–0.91); at R=1 it can add overhead or be near parity, as no reuse is available. At N=128, cache entries retain estimated payloads of 26,348–31,324 bytes for 127 unique queried sources; the estimate excludes hash-table bucket storage and allocator slack.

## Interpretation

This comparison exercises the existing experimental cache on its intended path: repeated `ReachableFrom` Terms inside native rule execution, where one EvalCache is shared across rule firings. The earlier materialization benchmark called `PySubstrate.evaluate` directly, which constructs a fresh cache per call, so it measured the cache-off host-query path. The two results answer different questions. For rule execution, the existing same-graph memoization is the better demonstrated reuse strategy in this workload; explicit closure/materialization adds work and does not win. The cache is still opt-in/default-off and mutation invalidation coverage remains bounded by its separate tests.

Previously measured browser-profile v1.3 results offer a more task-shaped cache observation: at N=128, quiet tick time improved 12.81× for one branch and 7.46× for four branches, on synthetic DOM-shaped records. That evidence is not a live Chromium workload or natural prevalence estimate. The next broader gate is a runtime census of repeated `(start, edge_type)` keys and cache hit/miss/retained bytes across independently authored active task routes; compare cache benefit only where the real rule route actually repeats keys.

## Reproduction

The v1 raw and v1.1 artifacts preserve analyzer/fixture failures and are not admitted as results. Use the corrected [v1.2 amendment](REACHABILITY_CACHE_MATERIALIZATION_COMPARISON_V1_2_AMENDMENT_20261005.md), runner `evaluation/substrate_capability/reachability_cache_materialization_comparison_v1_2.py`, and analyzer `evaluation/substrate_capability/analyze_reachability_cache_materialization_comparison_v1_2.py`. Current [capture](../../../evaluation/reports/reachability_cache_materialization_comparison_v1_2_20261005.json) and [analysis](../../../evaluation/reports/reachability_cache_materialization_comparison_v1_2_analysis_20261005.json) pass all checks.
