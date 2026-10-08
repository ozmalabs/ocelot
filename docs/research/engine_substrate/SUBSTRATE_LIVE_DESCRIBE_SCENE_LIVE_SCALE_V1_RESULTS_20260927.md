# Live describe-scene membership scaling v1

Date: 2026-09-27

## Question and design

This sweep measures how full-request native work changes as the live full-seed route receives additional Concept vocabulary that cannot match the scene labels. The same three-Percept Scene, prompt, speaker, and loaded/authored rule set are used in all cells. Noise Concepts are placed in one dedicated Microtheory with unique `tractability_noise_concept_NNNN` names and `kind=noise`; no rule is disabled. Sizes are 0, 1,024, and 4,096 added Concepts, with two fresh-process audited/uninstrumented pairs per size.

The audit and native access trace wrap the complete `converse` request. Trace records are aggregated by rule UID, operation kind, and resource; counts are conserved, while node-level trace rows are not retained. Request wall/CPU, peak RSS, full graph size, and exact reply/Goal/graph parity are captured separately.

## Gates and behavior

All 13 independent gates pass across 12 source-locked workers: two pairs in each cell, stable source fingerprints, unique PIDs, exact audited/uninstrumented parity, expected reply, resolved Goal lifecycle, three scene Percepts, zero noise classification, counter conservation, zero dropped trace events, repeatable work profiles, and repeatable graph structure within cells. All rules remain active.

The base graph before adding noise is constant at 10,793 Concepts and 6,320 `has_concept` memberships. Graph size increases by exactly one node and one membership edge per noise Concept. Scene classifications remain at three and the exact public reply stays `I see the grey thing stays, the yellow counter, and the blue thing moves.` in every worker. The graph-visible outbound Message mismatch remains in all cells.

## Measured work and resources

| Added noise Concepts | Total memberships | Candidate tests | Term evaluations | Selected access events | Uninstrumented wall median | Audited wall median | Uninstrumented peak RSS median |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 6,320 | 678,432 | 3,676,862 | 1,140,892 | 10.469 s | 10.917 s | 1.923 GiB |
| 1,024 | 7,344 | 781,856 | 4,212,414 | 1,263,772 | 10.861 s | 11.263 s | 1.924 GiB |
| 4,096 | 10,416 | 1,092,128 | 5,819,070 | 1,632,412 | 10.690 s | 11.388 s | 1.928 GiB |

Each tested added membership contributes exactly **101 candidate tests**, **523 Term evaluations**, and **120 selected access events**. Across these points the aggregate profiles are affine in the added membership count. Global candidate and Term totals reconcile exactly with per-rule and explicit unattributed counts at every size.

Native per-rule attribution localizes the entire observed increase to four rules:

| Rule | Candidate tests per added Concept | Term evaluations per added Concept |
|---|---:|---:|
| `recognise_a_counter` | 28 | 112 |
| `recognise_a_thing_that_moves_itself` | 28 | 112 |
| `recognise_a_thing_that_stays_put` | 28 | 112 |
| `curiosity_targets_ambivalent_nodes` | 17 | 187 |

Other rules in the measured profile show no work-count change across these cells. The recognition and curiosity rules therefore scan more broadly than the new noise Microtheory’s semantics would require, while task output remains unchanged. This is evidence of broad candidate domains in the current active rule set, not evidence of learned-frame locality.

The uninstrumented wall medians vary only about 0.4 seconds across the three cells and are not monotone; two samples per arm/cell are too few to resolve a timing slope against boot/faculty and runtime noise. Peak RSS rises about 5.4 MiB uninstrumented from 0 to 4,096 Concepts, while audited peak RSS rises about 8.4 MiB. Treat both as small-fixture high-water observations, not asymptotic memory costs.

## Interpretation and limits

This is source-grounded linear measured work for one live full-rule route and one controlled `has_concept` membership axis. It shows how the full active rule population behaves on a 10k-node-class graph, not how natural tasks are distributed. Added nodes are synthetic; the test holds Percept count, prompt, and all other inputs constant. It does not measure scene-count scaling, learned separators, general task transfer, or the prevalence of irrelevant vocabulary on natural workloads. Selected access events, candidate tests, Term invocations, latency, and RSS are distinct measures.

Next vary a second independent axis (Scene/Percept count) with an output contract that tolerates repeated or distractor inputs, then run the same scale protocol on a separately authored task topology. Keep the graph-visible reply projection as a separate correctness gate.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_LIVE_SCALE_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_live_describe_scene_live_scale_v1.py)
- [Initial locked analyzer](../../../scripts/analyze_substrate_live_describe_scene_live_scale_v1.py)
- [Corrected independent analyzer](../../../scripts/analyze_substrate_live_describe_scene_live_scale_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/live_describe_scene_live_scale_v1_lock_20260927.json)
- [Analysis](../../../evaluation/reports/live_describe_scene_live_scale_v1_1_analysis_20260927.json)
- [Raw workers](../../../evaluation/reports/live_describe_scene_live_scale_v1_workers_raw_20260927.json)

## Analysis correction note

The initially locked analyzer v1 had a candidate-conservation expression bug: it compared the global candidate total directly to the per-clause attributed subtotal, despite the separately reported unattributed count. The raw values satisfy the intended identities (`global = attributed + unattributed`; `attributed = per-rule = per-clause`). The independent v1.1 analyzer corrects that equation and passes all 13 gates on the locked raw workers. This was an analysis-code correction; the captured runtime source and worker outputs remain source-stable.
