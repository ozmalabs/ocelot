# Polyomino concern-key identity comparison v1 results

**Run:** 2026-09-29. **Status:** 30 paired sequence arms, 60 observations; all frozen input, key, signature, and D4-orbit gates pass.

## Outcomes

The default predicate-derived key behaved as in the prior replay: all five exact repeats and all ten distinct-shape pairs minted once, then marked the second observation `recognized_duplicate`. Under the canonical D4 structure key supplied by `name_hint`, exact repeats still deduplicated in 5/5 cases, while all ten distinct-shape pairs minted a second axis. In the frozen 15-sequence panel, the structure key therefore retains exact-repeat suppression and separates all five distinct D4 orbits; the predicate key merges them into one identity.

| Variant | Exact repeat: second call duplicate | Distinct shape: second call duplicate | Distinct shape: second call mints |
|---|---:|---:|---:|
| Predicate-derived key | 5/5 | 10/10 | 0/10 |
| Canonical D4 structure key via `name_hint` | 5/5 | 0/10 | 10/10 |

All calls in both variants used the same seven-cell signatures, base codebook, order, and native rules. The only assigned difference was the key passed into `induce_concern`. The canonicalizer is a benchmark-side Python implementation; this result does not show the engine currently derives or validates such keys. Detailed rows and paired verification are in the [capture](../../../evaluation/reports/polyomino_concern_key_identity_comparison_v1/capture.json) and [analysis](../../../evaluation/reports/polyomino_concern_key_identity_comparison_v1/analysis.json).

## Cost and limits

In this one run, the canonical D4 key calculation had a median of about 53 μs per call; the measured predicate-key proxy was about 4 μs. Median `induce_concern` wall time was about 6.16 ms for predicate and 6.32 ms for structure keys. The structure-key calculation is outside that call-time measurement and must be added for an end-to-end candidate estimate; these single-run timings are descriptive only. This shape panel is small, and no downstream use was tested. A canonical signature key also needs a defined policy for typed values, variable names, relations beyond `cell`, coordinate frame, and partial/noisy observations.

## Interpretation and next work

This controlled contrast confirms that the observed duplicate suppression is driven by the current identity key: a structure-sensitive hint separates the distinct shapes while preserving exact recurrence handling. It is a candidate measurement direction, not a recommendation to change the production key globally. Before implementation, inventory every `induce_concern` caller and define when predicate-class identity versus instance/structure identity is intended. Then extend this paired test across varied predicates, relation multiplicities, equivalent transforms, and noisy perceptual signatures; measure false split/false merge rates, key computation, downstream recognition, persistence, and compatibility with existing axes.

Artifacts: [preregistration](SUBSTRATE_POLYOMINO_CONCERN_KEY_IDENTITY_COMPARISON_V1_PREREG_20260929.md), [runner](../../../evaluation/substrate_capability/polyomino_concern_key_identity_comparison_v1.py), [analyzer](../../../evaluation/substrate_capability/analyze_polyomino_concern_key_identity_comparison_v1.py), [execution lock](../../../evaluation/substrate_capability/polyomino_concern_key_identity_comparison_v1_lock_20260929.json).
