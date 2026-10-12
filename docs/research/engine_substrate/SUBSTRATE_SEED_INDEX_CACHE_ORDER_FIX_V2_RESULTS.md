# Seed-index cache cold/warm order repair V2 results

Date: 2026-09-25  
Status: source repair verified by a focused cold/warm runtime probe

## Finding and change

The V1.5 cold/warm probe showed that identical seed bytes loaded different seed orders because `_topo_order` traverses mapping insertion order while the persistent cache used `json.dump(..., sort_keys=True)`. That changed active native rule indices depending on whether the cache was cold or warm.

`substrate/boot_all.py` now uses seed-index cache schema v5 and writes the cache without sorting JSON object keys. This preserves the seed-index mapping order from the cold build when a warm process reconstructs it. Older v4 cache entries fail the schema check and are rebuilt.

## Verification

The focused V2 probe ran separate cold and warm boots over byte-identical files from the immutable V1.7 baseline corpus. It reports exact equality for the full seed-load order and active-rule-name order. The five target rules occupy the same indices in both boots (1827–1831), and the loader source hashes were unchanged during the probe.

A broader V3 follow-up compares hashes of the complete serialized graph, grammar, exported rule store, rule access sets, active-rule order, and seed-load order. Every cold/warm equality gate passes on the same frozen corpus: 24,784 graph nodes, 11,090 edges, 2,289 active rules, and 11 consistently failed seed records. The ProblemShape rule positions remain 1827–1831. Loader source hashes were stable during this run as well ([V3 runner](../../../scripts/substrate_seed_index_cache_state_probe_v3.py), [V3 raw report](../../../evaluation/reports/substrate_seed_index_cache_state_probe_v3_20260925.json)).

A V4 lifecycle probe on an isolated hardlink copy also passes old-schema, malformed-JSON, and invalid-payload-digest rebuilds, two simultaneous cold builders, and a final warm load. Every case reproduces the baseline graph/grammar/rule/access/order fingerprints at the same 24,784-node, 11,090-edge size ([lifecycle runner](../../../scripts/substrate_seed_index_cache_lifecycle_probe_v1.py), [lifecycle report](../../../evaluation/reports/substrate_seed_index_cache_lifecycle_probe_v1_20260925.json)). A separate source-invalidation probe appends valid JSON whitespace to one manifest: the source digest changes, the cache rebuilds, and all boot-state fingerprints stay equal ([source-invalidation runner](../../../scripts/substrate_seed_index_source_invalidation_probe_v1.py), [report](../../../evaluation/reports/substrate_seed_index_source_invalidation_v1_20260925.json)).

These probes validate cold/warm boot-state parity, selected cache recovery/concurrency cases, and source-manifest invalidation on one frozen corpus, including the serialization contract that failed in V1.5. They do not cover every seed corpus, sustained or adversarial concurrent writers, or downstream workload behavior. Order-sensitive domain regression coverage remains open.

## Artifacts

- Implementation: [`substrate/boot_all.py`](../../../substrate/boot_all.py)
- Original cold/warm failure: [`V1.5 diagnostic`](SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_5_DIAGNOSTIC.md), [`V1.5 probe report`](../../../evaluation/reports/substrate_seed_index_cache_order_probe_20260925.json)
- Follow-up probe runner: [`V2 cold/warm probe`](../../../scripts/substrate_seed_index_cache_order_probe_v2.py)
- Follow-up runtime report: [`V2 probe report`](../../../evaluation/reports/substrate_seed_index_cache_order_probe_v2_20260925.json)
- Three-arm mechanism result using explicitly normalized caches: [`V1.7 result`](SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_7_RESULTS.md)
