# Correction-trace declared-anchor topology comparison v1 — results

Date: 2026-10-03
Status: exploratory, source-locked result; the topology comparison was not preregistered.

## Question

Does splitting the same instruction/correction pairs into independent
`DiscourseState` graphs let the native declared-anchor matcher avoid the
fail-closed fallbacks seen when all pairs form one predecessor chain?

## Method

The source-locked runner compares three arms: monolithic closure, scoped
closure with generic same-source matching, and scoped closure with an opt-in
declared co-ownership anchor for the correction rule. It materializes the same
number of instruction/correction pairs in either one chained discourse state
or one independent state per pair. Each cell is repeated in ascending,
descending, and outside-in scope orders, with three fresh worker processes per
order. Task counts are 1, 2, 4, and 8, for 72 paired cells total. The anchor
assertion is `CommunicationInterpretation i` owned by `DiscourseEvent
current_event` through `has_interpretation`.

The runner checks source stability, state counts, exact correction statuses
and evidence paths, canonical full-graph parity among all three arms, and
separation between the fallback and declared-anchor paths. The independent
analyzer repeats those checks from the capture and source lock. This measures
authored fixture behavior and one matcher optimization; it does not establish
natural-task frequency, automatic boundary discovery, or physical isolation.

## Results

All runner and independent-analysis checks pass. All 72 cells preserve exact
semantics and canonical graph state across monolithic, fallback, and anchor
arms. In the eight-pair chained condition, the target rule took the declared
anchor path 3 times and rejected it into fail-closed fallback 53 times. In
the independent-state condition, it took the anchor path 24 times and
rejected it 32 times. Thus removing predecessor links improves anchor
eligibility, but does not make the anchor broadly applicable.

At eight independent pairs, median Candidate enumeration falls from 13,752 to
13,056 (5.1%) and Term evaluations from 135,800 to 128,476 (5.4%). Rule
enumerations are unchanged at 4,816. Median elapsed time is 24.13 ms with the
anchor and 23.64 ms with fallback, so this run shows no end-to-end speedup.
The chained eight-pair condition reduces Candidate and Term counts by only
0.5% and 0.7%; the anchored arm remains slower in median wall time. Across
both topologies the scoped arms are substantially slower than monolithic
closure at the largest task count. Timing varies considerably among sizes and
captures, so the work counters are the stronger result here.

## Interpretation and next gate

The declared-anchor guard is semantics-preserving in this panel and benefits
from graph layouts with fewer cross-frame predecessor relationships. Its
current whole-graph scoped matching still does most of the work, however, and
anchor eligibility is not equivalent to a useful total-work reduction. A
sound multi-role ownership/dependency index is still needed to prune all
applicable rules while preserving predecessor access. The next evaluation
should combine such indexing with the predecessor-dependent lifecycle panel,
charge index construction and cross-frame communication, and require exact
binding/effect parity plus explicit omitted-interface residuals. The separate
CoW residual-return work remains evidence for branch isolation/merge-back, not
for this frame-execution integration.

## Artifacts

- Runner: [thoughtexperiment_correction_trace_anchor_topology_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_correction_trace_anchor_topology_v1.py)
- Independent analyzer: [analyze_thoughtexperiment_correction_trace_anchor_topology_v1.py](../../../evaluation/substrate_capability/analyze_thoughtexperiment_correction_trace_anchor_topology_v1.py)
- Source lock: [lock](../../../evaluation/substrate_capability/thoughtexperiment_correction_trace_anchor_topology_v1_lock_20261003.json)
- Raw capture: [capture](../../../evaluation/reports/thoughtexperiment_correction_trace_anchor_topology_v1_20261003.json)
- Independent analysis: [analysis](../../../evaluation/reports/thoughtexperiment_correction_trace_anchor_topology_v1_analysis_20261003.json)
