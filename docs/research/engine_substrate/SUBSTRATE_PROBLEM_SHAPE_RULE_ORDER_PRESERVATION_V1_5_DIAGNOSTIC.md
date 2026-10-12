# ProblemShape rule-order preservation V1.5 diagnostic

Date: 2026-09-25  
Status: stopped at the first gate; no treatment inference

V1.5 compared baseline, append, and original-slot eventization from one immutable corpus. The first triad matched observation outcomes, but its seed-load order gate failed: baseline and original-slot arms loaded `learned_lexicon` before `nd_representation`, while the appended arm loaded `nd_representation` first. The target rules shifted by five slots. The run stopped after that triad; its partial report is preserved.

## Cause: cold and warm seed-index caches change iteration order

A direct cold/warm probe used the same immutable baseline snapshot and separate fresh processes. Both loader source hashes were stable during the probe, and the seed bytes were identical. Yet:

- Cold cache: `ps_decode`…`ps_redecode` at 1826–1830; the first divergent seed-load order point was index 408, with `learned_lexicon` preceding `nd_representation`.
- Warm cache: the five rules at 1831–1835; `nd_representation` preceded `learned_lexicon`.
- Full active-rule-name and seed-load-order fingerprints differed.

The source explains the mechanism. `_topo_order` traverses the `seeds` mapping in insertion order. A cold `_build_seed_index` inserts entries in manifest-path order. The persistent cache serializes that mapping with `json.dump(..., sort_keys=True)`, and a warm `json.load` therefore reconstructs a lexically ordered mapping. Both paths are repeatable individually but produce different seed installation orders. Since rule indices follow installation order, cache state changes active-rule positions and may change runtime behavior wherever order matters.

The locked cold/warm evidence is in [`probe report`](../../../evaluation/reports/substrate_seed_index_cache_order_probe_20260925.json) and [`probe runner`](../../../scripts/substrate_seed_index_cache_order_probe.py). V1.5's failed three-arm checkpoint remains at [`partial report`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_5_partial_20260925.json).

## Follow-up

V1.6 clears and rebuilds both immutable snapshot caches before any treatment worker, verifies the cache bytes around each process, and includes `boot_all.py`, `world_adapter.py`, and `seed_loader.py` in its source lock. The first triad remains a fail-fast confirmation that baseline, append, and preserve arms see the intended seed and rule order.

This probe exposes a seed-loader cache-state reproducibility defect. It does not yet establish the downstream semantic impact on general workloads; changing the cache encoding/order contract requires a separately reviewed implementation and regression evaluation.
