# Thoughtexperiment coverage-class receipt v1 results

## Result

Five fresh workers replay the five upstream panels that returned one
coverage-qualified finite behavior class. A later term-diversity audit found
that each panel's four member IDs encode the same canonical Term JSON. Each
worker creates a candidate
graph, forks a `shared_graph_pages` snapshot, journals a receipt and an edge
for every returned member, then applies the derived-only residual at the
primary's captured revision. The independent analyzer recomputes the complete
primary-before to branch-after graph diff from captured graph states. It
passes all five cases: 20 membership edges are transported exactly, the
primary graph is unchanged before return, the adopted primary matches the
branch graph canonically, rule state is identical, and reapplying the receipt
at the stale revision is rejected without further mutation.

Median times for this small fixture are 33.5 microseconds to fork,
35.5 microseconds to add the receipt and member links, 135.8 microseconds to
extract the diff, and 226.2 microseconds to apply it. These values describe
five tiny graphs on one host and are not a scale or throughput estimate.

## Interpretation and limits

This closes a graph-transport mechanism gate for duplicate candidate entries:
the selected IDs can be isolated, stored in a graph receipt, and returned to
the primary with revision checking. It does not demonstrate transport of a
diverse equivalence class. Selection, labels, and finite-holdout safety are
inherited from the upstream authored numeric study. No new dimension or
candidate is induced, no active rule is changed, no receipt survives a
process restart, and no persistent adoption or natural-task transfer is
measured. See the [deduplication audit](TERM_DEDUPLICATION_CLASS_RETURN_V1_RESULTS_20261004.md).

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_COVERAGE_CLASS_RECEIPT_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_coverage_class_receipt_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_coverage_class_receipt_v1_lock_20261004.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_coverage_class_receipt_v1.py)
- [Analysis](../../../evaluation/reports/thoughtexperiment_coverage_class_receipt_v1_analysis_20261004.json)
- [Upstream policy results](COVERAGE_AWARE_CLASS_RETURN_V1_RESULTS_20261004.md)
