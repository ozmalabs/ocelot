# Sorted GenInfer identity join: key semantics v1.1 results

**Result: all 12 source-stable workers pass the preregistered parity gate.**
The baseline and candidate use the same 3-D matrix solver; the candidate also
enables sorted identity joining. The six paired cases each cover training and
held-out execution, with exact status, `covered_by`, and transform-receipt
parity.

| Key case | Baseline and candidate outcome | Evidence |
|---|---|---|
| Integer IDs on source / equal-valued float IDs on target | Recognized and transformed in both phases | 1 receipt per phase in both arms |
| Float IDs on both sides | Recognized and transformed in both phases | Confirms fallback preserves solver behavior |
| Boolean IDs / equal integer IDs, predicate-disambiguated | Recognized and transformed in both phases | Confirms fallback across equality/order mismatch |
| Unique one-element list IDs | Both mint/refuse to acquire a transform | Exact refusal parity; baseline solver does not solve this fixture |
| Duplicate IDs | Both mint/refuse to acquire a transform | Exact ambiguity refusal parity |
| Disjoint source and target IDs | Both mint/refuse to acquire a transform | Exact missing-match refusal parity |

The positive float and bool/int cases prove the candidate does not lose those
baseline capabilities when it takes its exact nested fallback. The compound
case establishes parity only; it does not establish compound-key support. This
remains a semantics gate, not a performance result. NaN and rational values,
other nested values, broad key widths, and prevalence in ordinary task traffic
remain open. The optimization remains opt-in.

The v1 preregistered three-case gate also passes; v1.1 adds compound,
duplicate, and missing-key controls. See [v1.1 protocol](GENINFER_FULL_RANK_SORTED_JOIN_KEY_SEMANTICS_V1_1_PREREG_20261006.md),
[capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_key_semantics_v1_1_20261006.json),
[lock](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_key_semantics_v1_1_lock_20261006.json),
and [runner](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_key_semantics_v1_1.py).
