# Rooted frame-proposal panel v1 amendment (2026-09-28)

## Reason

The first three-worker capture passed all runner gates and preserved stable source locks, but the independent analyzer rejected its induced-width field because the runner reports `{value, order, method}` while the analyzer compared that record to a scalar. This was an analyzer schema-normalization defect; the BFS proposal, measurements, and preregistered conditions were unchanged. The initial raw capture and failed analysis are retained as attempt 1 and excluded from confirmatory results.

## Repair and rerun

The analyzer now compares the independently recomputed min-fill width to the recorded `value`, while retaining the order/method record in the raw capture. It independently recomputes all candidate membership sets, cut counts, external type counts, attribute-key summaries, label-overlap scores, and widths from the retained structural graph snapshots. The amended source lock includes this amendment and the corrected analyzer. Run three new fresh workers; attempt 1 remains diagnostic and is not pooled.

No task selection, BFS radius, edge-direction rule, primary metric, reference-label definition, timeout, or success threshold changes.
