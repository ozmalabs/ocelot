# Multi-operator family search v1 — results

The locked study completed all 20 panels across additive conservation, product
conservation, absolute-value equality, and pairwise-minimum equality. The
independent analyzer passed source/panel binding, initial candidate fit,
selection transcript and work replay, and full rescoring of every generated
candidate on the registered 1,296-point fractional grid.

All 20 searches reached the 12-second budget, exploring a median 33,068–34,522
terms and returning partial pools with median 20–31 candidates. Exact candidates
appeared in all five absolute-value panels; native query selection resolved an
exact singleton in those five after a median five labels. No exact candidate
was generated before timeout for additive, product, or minimum equality. After
active selection, all five additive and all five minimum panels ended at false
singletons. Product ended at three false singletons and two unresolved
non-singleton sets. No panel had an empty candidate pool.

This demonstrates one positive case for synthesis and label selection in a
shared grammar, alongside a severe search-time and coverage failure. It does
not show that the wider grammar cannot express the missing targets: the search
was capped at size 7, 12 seconds, and 128 returned solutions, and this v1 does
not resynthesize after new labels. The result instead shows that this search
configuration did not find those exact candidates before its cap, and that
finite active queries over its partial pool often create unjustified
singletons. Task families, operator menu, labels, and numeric domain remain
authored and controlled.

Artifacts: [preregistration](MULTI_OPERATOR_FAMILY_SEARCH_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/multi_operator_family_search_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_multi_operator_family_search_v1.py), [source lock](../../../evaluation/substrate_capability/multi_operator_family_search_v1_lock_20261004.json), [capture](../../../evaluation/reports/multi_operator_family_search_v1_20261004.json), and [analysis](../../../evaluation/reports/multi_operator_family_search_v1_analysis_20261004.json).
