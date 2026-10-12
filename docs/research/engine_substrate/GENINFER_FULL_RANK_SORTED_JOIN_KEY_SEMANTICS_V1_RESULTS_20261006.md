# Sorted GenInfer identity join: key semantics v1 results

**Result: the focused semantic parity gate passed (6 workers, 2026-10-06).**
The baseline and candidate used the same solver and Rust source; the candidate
also enabled the sorted identity join. Both were debug builds. Every arm's
worker reported stable source hashes. In all three controls, both training and
held-out phases returned `recognized_transformed` with one transform receipt,
and the receipt/status tuples matched exactly between arms.

| Key control | Baseline | Sorted candidate | Path exercised |
|---|---|---|---|
| Integer source IDs / equal-valued float target IDs | Pass | Pass | Sorted join; `Int`/`Float` compare and equality agree here |
| Float IDs on both sides | Pass | Pass | Exact nested fallback |
| Boolean source IDs / equal integer target IDs, unique composite keys | Pass | Pass | Exact nested fallback; `Bool`/`Int` equality crosses variants while `cmp_value` keeps their type order distinct |

The Boolean/integer case confirms why an exact fallback is needed: their key
values compare equal under `Value` equality but do not compare equal under
`cmp_value`. Float and compound identity keys are not sorted by the fast path;
they use the baseline matching loop. This preserves solver behavior while
limiting the speedup claim to keys the sorted order can safely align.

An initial exploratory run used a default-feature baseline without the matrix
solver and is discarded. The recorded v1 capture uses matched solver feature
sets. The gate does not cover NaN, rational, nested, duplicate, missing, or
large key-width cases, nor does it establish natural-task prevalence or
performance. The sorted-join feature remains opt-in pending those gates.

Evidence: [preregistered protocol](GENINFER_FULL_RANK_SORTED_JOIN_KEY_SEMANTICS_V1_PREREG_20261006.md),
[capture](../../../evaluation/reports/geninfer_full_rank_sorted_join_key_semantics_v1_20261006.json),
[lock](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_key_semantics_v1_lock_20261006.json),
and [runner](../../../evaluation/substrate_capability/geninfer_full_rank_sorted_join_key_semantics_v1.py).
