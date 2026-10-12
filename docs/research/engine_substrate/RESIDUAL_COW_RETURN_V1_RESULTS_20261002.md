# Residual CoW return v1 results

The paired source-locked capture has 26 rows: 13 task conditions under a native full-copy branch and a shared-graph-pages branch. All analysis gates pass. Both backends reproduce four correct `flip_comparison` proposals and held-out navigation success, with zero proposals across the nine controls. In each positive worker, the journal returns the post-induction graph delta (median 40 nodes and 2 edges); applying that delta against the captured host revision reproduces the branch facts exactly. The host rule export remains unchanged. The host graph and rules are exactly unchanged between fork and explicit residual return.

The shared-graph-pages branch's median fork time is 0.312 ms versus 0.474 ms for deep copy in this small fixture. Median induction is 6.12/6.00 ms and grounding 0.235/0.316 ms (shared pages/deep copy); median graph-delta application is 3.09/3.45 ms. These are single-host diagnostics. The observed fork difference is small and the dominant operation costs are not materially different here; this does not establish a broad CoW speedup.

## What the residual contains

The delta checkpoint is after observation/axis induction. The host receives only the later graph facts after the proposal passes held-out scoring. Branch-local rule-store changes are not merged. The delta mechanism preserves graph structure exactly for the measured cases, but this test does not show that the 40 returned nodes can independently execute the proposal: the candidate remains a separately scored rule object, and the branch's native rewrite-rule vector remains isolated. Negative and absent-target branches are discarded even when their internal grounding setup creates graph facts.

This demonstrates a usable isolation/return boundary for a narrow proposal workflow, using the existing partial-CoW backend. It does not prove full substrate CoW, broad mutation coverage, persistent agent adoption, or a general speed advantage. The next gate should test residual usability after return, branch cleanup/reclamation, and larger host graph sizes while retaining the deep-copy parity arm.

## Artifacts

- Protocol: [preregistration](RESIDUAL_COW_RETURN_V1_PREREG_20261002.md)
- Runner: [measurement script](../../../evaluation/substrate_capability/measure_residual_cow_return_v1.py)
- Analyzer: [independent gate checker](../../../evaluation/substrate_capability/analyze_residual_cow_return_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/residual_cow_return_v1_lock_20261002.json)
- Raw workers: [capture](../../../evaluation/reports/residual_cow_return_v1_20261002.json)
- Analysis: [gate results](../../../evaluation/reports/residual_cow_return_v1_analysis_20261002.json)
