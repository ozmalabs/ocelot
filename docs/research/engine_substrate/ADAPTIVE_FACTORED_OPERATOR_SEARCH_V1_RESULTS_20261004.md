# Adaptive factored operator search v1 — results

The authoritative amended run completed all 20 paired panels and passed the
independent source, panel, candidate-fit, active/audit transcript, work-ledger,
decision, and fractional-holdout checks. The policy rotated four operator
branches independently of task, searched one branch at a time, incorporated
active labels into later branch synthesis, and required two matching reserve
labels before accepting a singleton. A first diagnostic capture is superseded:
it continued branch search after reaching the six-active-label cap. The
amended lock and capture enforce the registered stopping rule.

The fixed four-branch control resolves all 20 panels correctly. The adaptive
policy accepts 19 and requests help on one. Of those 19 accepted candidates,
12 are correct on the registered fractional holdout and seven are false
acceptances, despite matching both audit labels. This is a 36.8% false-accept
rate among accepted candidates. The audit examples were drawn from the
integer-valued reserve pool, while the sealed scorer includes fractional
inputs; the result shows those two checks did not protect against the observed
generalization failures.

Adaptive search reduces median branch search time relative to the fixed
11.1–11.7-second route: about 3.0 seconds for absolute/minimum and 5.6–5.8
seconds for additive/product. It uses a median of one or two branches and
three to five total labels per task. The cost reduction is not a successful
policy result because the false-accept rate is high. The evidence supports
early stopping only when the audit distribution has adequate coverage, which
this integer audit did not.

The next gate is a locked audit-distribution study: reserve task-conditioned
continuous examples, balanced between relation-valid and near-miss cases,
without using the sealed fractional score set. Compare the current integer
audit, continuous balanced audit, and help/abstention on the same panels; report
false acceptance and query/search costs. Keep the search menu closed and do
not claim generality from this numeric result.

Artifacts: [preregistration](ADAPTIVE_FACTORED_OPERATOR_SEARCH_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/adaptive_factored_operator_search_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_adaptive_factored_operator_search_v1.py), [source lock](../../../evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json), [capture](../../../evaluation/reports/adaptive_factored_operator_search_v1_20261004.json), and [analysis](../../../evaluation/reports/adaptive_factored_operator_search_v1_analysis_20261004.json).
