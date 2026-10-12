# Generated cubic finite-grid alias control v1 — results

## Result

All three source/native-locked workers completed, and the independent analyzer passes with zero integrity or replay errors. Each worker generated the same complete 12-Term pool from 5,861 explored candidates. The pool did not contain a hypothesis that matched `x³` on the held-outs. It retained the linear Term `x`, which agrees with the target on both known rows and the only candidate `x=−1`.

Both uncached and lazy-matrix selectors queried `x=−1`, received `−1`, and terminated with the same singleton `x`. On held-outs `−9,−5,5,9`, that survivor scored 0/4 exact. The failure reproduced in all three workers. This is a false singleton caused by the finite probe grid and behavior-based pool collection, not a query-ranking divergence.

## Cost

Median pool generation was 99.20 ms. The uncached selector used 72 native evaluations in 0.401 ms; the lazy matrix used 36 in 0.349 ms. The call reduction does not mitigate the semantic adequacy failure.

## Interpretation and limits

This is a constructed counterexample showing that query entropy can select the best available probe and still certify the wrong model when the generated pool has already discarded the target as behaviorally indistinguishable on the finite probe set. Held-out validation detects the error after selection. The selector itself does not detect it; an empty-version-space contradiction control is insufficient because this label is consistent with a wrong singleton. The study establishes existence of this failure mode, not its prevalence. A production acquisition path needs residual or independent adequacy probes before converting singleton status into learned structure.

## Reproduction artifacts

- Protocol: [preregistration](SUBSTRATE_CONTRACT_QUERY_GENERATED_CUBIC_ALIAS_V1_PREREG_20261002.md)
- Runner: [source-locked runner](../../../evaluation/substrate_capability/substrate_contract_query_generated_cubic_alias_v1.py)
- Analyzer: [independent replay analyzer](../../../evaluation/substrate_capability/analyze_substrate_query_generated_cubic_alias_v1.py)
- Lock: [source/native lock](../../../evaluation/substrate_capability/substrate_contract_query_generated_cubic_alias_v1_lock_20261002.json)
- Capture: [raw worker data](../../../evaluation/reports/substrate_contract_query_generated_cubic_alias_v1_raw_20261002.json)
- Analysis: [machine-readable analysis](../../../evaluation/reports/substrate_contract_query_generated_cubic_alias_v1_analysis_20261002.json)
