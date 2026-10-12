# Native query-selector scaling gate v1.3 results

## Result

The fresh 40-panel, three-arm capture passes all five capture gates and the independent analyzer passes all 14 checks. The native candidate-positive arm exactly matches the paired host candidate-positive arm in query ordering and final decisions across all 40 panels. The source lock remained current, all 120 workers completed, query receipts validated, and task identity was absent from the selector inputs.

Across the 10 opposition panels, the baseline initially accepts three wrong candidates. Native and host candidate-positive querying find all three counterexamples and request help, using five labels in total; the uniform arm finds none and leaves all three false accepts. The difference from v1.2's four-label total reflects fresh panels and their candidate-positive pool sizes. Additive and product controls select correctly in all 20 panels without false help. All 10 inequality panels request help before querying. The candidate menu is supplied and the tasks are fixed numeric relations; this does not test autonomous candidate generation or establish natural-task prevalence.

## Cost

The rule is now anchored once on the episode's selected-family edge, so native `ArgminUnique` selection is evaluated once per query rather than once for every probe-row match. Across the 40 native workers, median measured query-selection closure is 20.23 ms (p90 27.61 ms), compared with 686.66 ms median in the source-locked v1.2 capture: about a 34-fold reduction. Median eligibility closure remains 75.31 ms (v1.2: 78.85 ms), so selection optimization did not materially change candidate filtering cost.

Median total worker CPU for the native arm is 375.17 ms, down from 1,046.56 ms in v1.2. The paired host candidate-positive arm is 280.69 ms, so native execution remains about 34% higher in this workload despite the selector improvement. Median peak RSS is 159,260 KiB for native and 157,052 KiB for host; this is process peak RSS and is dominated by the shared runtime, not a graph-only memory measure. Timings are one-host measurements over these authored panels and should not be generalized to larger or naturally occurring tasks.

## Interpretation and next gate

This is evidence for correct bounded native query ordering and a substantial reduction in repeated selector work. It does not establish that query utility is high outside the three observed opposition false accepts, that frame locality holds, or that the substrate can invent a missing hypothesis. The harness still constructs task-blind row priorities, reveals labels, and supplies the candidate menu.

Next, preserve this once-per-query anchor and profile eligibility construction separately. Then expand to independently authored relation families and candidate menus that can omit the target, with enough accepted errors to estimate query value and explicit abstain/refusal controls. Keep query utility, selector correctness, candidate-generation responsibility, and end-to-end cost as separate outcomes.

## Reproduction

The source-locked raw capture is [`native_candidate_adequacy_query_v1_3_20261005.json`](../../../evaluation/reports/native_candidate_adequacy_query_v1_3_20261005.json), and independent analysis is [`native_candidate_adequacy_query_v1_3_analysis_20261005.json`](../../../evaluation/reports/native_candidate_adequacy_query_v1_3_analysis_20261005.json). The protocol is [`SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_3_PREREG_20261005.md`](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_3_PREREG_20261005.md). Reproduce with:

```sh
python3 evaluation/substrate_capability/analyze_native_candidate_adequacy_query_v1_3.py
```
