# Factored operator search v1 — results

The paired, source-locked study completed all 20 original panels. Each task
searched four separate size-7 grammars (`Neg/Eq/And` plus `Plus`, `Times`,
`Abs`, or `Min`) with a three-second cap, then merged canonical Terms and used
the native selector for at most six labels. The independent analyzer passed
source and paired-panel binding, initial fit checks, complete branch accounting,
query/label/survivor replay, and full candidate rescoring on the registered
1,296-point fractional grid.

The factored union contained an exact candidate in all 20 panels, and the
selector resolved all 20 to a holdout-exact singleton. This held for additive,
product, absolute-value, and minimum equality (5/5 each). The shared 13-operator
baseline on the exact same panels contained exact candidates in only the five
absolute-value cases (5/20); it reached its 12-second cap in all 20 panels.
Factored total search medians were 11.1–11.7 seconds per panel, similar to the
12.0-second shared-grammar cap, and the union-selector used median 3–4 labels
per task. Of 80 factored branches, 50 reached their three-second caps; useful
partial candidates were retained even on timed-out branches.

The result suggests that partitioning a hypothesis space by a small set of
operator additions can improve candidate coverage substantially at similar
total search cost for these tasks. It does not establish a general speedup
law: this is four hand-authored branches, four numeric targets, five panels per
target, one host, a fixed size cap, and capped partial enumeration. The
operator menu still contains the right primitive, no candidate is invented
outside it, and no post-label resynthesis or request-help action is measured.

Artifacts: [preregistration](FACTORED_OPERATOR_SEARCH_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/factored_operator_search_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_factored_operator_search_v1.py), [source lock](../../../evaluation/substrate_capability/factored_operator_search_v1_lock_20261004.json), [capture](../../../evaluation/reports/factored_operator_search_v1_20261004.json), and [analysis](../../../evaluation/reports/factored_operator_search_v1_analysis_20261004.json).
