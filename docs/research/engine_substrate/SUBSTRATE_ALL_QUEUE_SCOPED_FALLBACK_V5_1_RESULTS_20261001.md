# Scoped/full snapshot drain with cross-binding edge deletion v5.1 results

Date: 2026-10-01

## Result

The corrected source-locked 27-worker factorial passes **300/300 independent checks**. It spans R={1,8,32}, M={1,4,16}, with three fresh processes per cell. Full closure and scoped-plus-fallback reach fixed point with identical canonical node and edge facts in all 27 workers. The one-shot continuation selects the same NodeID in all 27 pairs. Exact serialized graph dictionaries match in 9/27 workers; edge order remains a separate representation-level difference, consistent with slab reuse and not a canonical-fact mismatch.

For M=4 and M=16, each match's first effect deletes its successor's unique `right_i` driver edge, testing cross-binding invalidation after the rule has snapshotted its bindings. M=1 is only a single-binding deletion control: the matcher enforces distinct bindings for distinct pattern variables, so a self-loop fixture would have no matches. In all 27 workers, the expected handled and verifier outputs, five deferred-family counts, rule-effect deletion totals, fixed-point/fallback status, and queue trace reconciliation hold. Scoped-only reports the expected pending deferred effects. Inputs, native binary, and source fingerprints remain stable across all workers.

## Interpretation and limits

This is direct evidence that the tested scoped drain preserves the full-closure result when a snapshotted binding's unique match edge is removed by another binding, for this cyclic relation shape and these sizes. It strengthens the specific queue/scope correctness case. It does not establish completeness for arbitrary scopes, node deletion, changed where-term truth, natural task prevalence, or asymptotic performance. The 9/27 exact wire result must not be presented as exact serialized parity; semantic fact parity is 27/27.

The v5 predecessor is retained as a failed measurement attempt. Its M=1 self-loop produced no matches under injective variable binding, and its analyzer inherited a false selected-node-versus-serialized-tail oracle. V5.1 corrects both issues, does not overwrite v5 artifacts, and makes no claim based on v5's failed gates. See [v5 preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V5_PREREG_20261001.md), [v5.1 preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V5_1_PREREG_20261001.md), [runner](../../../scripts/substrate_all_queue_scoped_fallback_v5_1.py), [analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v5_1.py), [lock](../../../evaluation/substrate_capability/all_queue_scoped_fallback_v5_1_lock_20261001.json), [worker capture](../../../evaluation/reports/all_queue_scoped_fallback_v5_1_workers_20261001.json), and [analysis](../../../evaluation/reports/all_queue_scoped_fallback_v5_1_analysis_20261001.json).
