# Live describe-scene Percept × distractor factorial v1.1 results

## Scope

This source-locked, full-seed benchmark crosses 3, 6, 12, and 24 request-view Percepts with 0, 1,024, and 4,096 synthetic distractor Concepts. Every cell has two fresh-process replicates, each paired across untraced and audited arms (48 workers total). The request, three known Percept classes, expected semantic propositions, and active seeds are fixed. Noise Concepts belong to a separate Microtheory and receive no class edges. Noise and scene construction happen outside the timed request.

The factorial asks how this authored `describe_scene` route responds to changes in task-visible Percepts and unrelated global Concept memberships. It does not evaluate a learned frame partition, a general workload distribution, novelty acquisition, or asymptotic complexity.

## Gate outcomes

All 13 corrected analysis checks pass. The 48 workers have unique PIDs, the complete paired design is present, and locked fingerprints match at worker start/end and after the run. All workers pass class assignment, semantic reply coverage, route, and resolved-Goal lifecycle oracles. Noise remains unclassified. Audited and untraced members of every pair have exact reply, Goal, graph digest/count, and classification parity. Candidate, Term, per-rule, per-clause, selected-access, and operation-work counters reconcile; no rows are dropped, and control instrumentation streams are empty. Audited work profiles and semantic graphs repeat across both replicates in every cell.

The constant base graph has 10,796 Concepts and 6,323 `has_concept` memberships in every worker. Request Percepts use `has_percept`, so they do not alter that base membership count. The first offline analyzer incorrectly subtracted Percept count from the membership count; the initial output and exact locked analyzer source are preserved, and an analysis amendment documents the corrected invariant. The corrected report records the captured and corrected analyzer hashes.

## Results

Counts below are from one repeated audited work profile per cell. Wall time is the median of two untraced processes and is descriptive only. Operation-work units are scheduler/deferred counters and do not measure matching or Term evaluation.

| Request Percepts | Noise Concepts | Candidate tests | Term evaluations | Selected access events | Scheduler/deferred units | Untraced wall median (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0 | 965,172 | 4,832,386 | 1,426,632 | 231,164 | 10.65 |
| 3 | 1,024 | 1,114,676 | 5,552,258 | 1,595,592 | 231,164 | 10.79 |
| 3 | 4,096 | 1,563,188 | 7,711,874 | 2,102,472 | 231,164 | 16.60 |
| 6 | 0 | 1,783,128 | 8,109,012 | 2,245,233 | 231,164 | 13.55 |
| 6 | 1,024 | 2,064,728 | 9,357,268 | 2,546,289 | 231,164 | 11.05 |
| 6 | 4,096 | 2,909,528 | 13,102,036 | 3,449,457 | 231,164 | 11.57 |
| 12 | 0 | 3,419,040 | 14,662,264 | 3,882,435 | 231,164 | 10.94 |
| 12 | 1,024 | 3,964,832 | 16,967,288 | 4,447,683 | 231,164 | 14.37 |
| 12 | 4,096 | 5,602,208 | 23,882,360 | 6,143,427 | 231,164 | 13.80 |
| 24 | 0 | 6,690,864 | 27,768,768 | 7,156,839 | 231,164 | 11.52 |
| 24 | 1,024 | 7,765,040 | 32,187,328 | 8,250,471 | 231,164 | 11.69 |
| 24 | 4,096 | 10,987,568 | 45,443,008 | 11,531,367 | 231,164 | 15.90 |

Peak RSS medians are 1.89 GiB in every untraced cell at the available precision. The finite least-squares model was `y = β₀ + βP(P−3) + βD D + βPD(P−3)D`, where `D` is the number of added noise Concepts. It has rank four and near-zero residuals over the tested grid:

| Metric | β₀ | βP per additional Percept | βD per noise Concept | βPD interaction |
|---|---:|---:|---:|---:|
| Candidate tests | 965,172 | 272,652 | 146 | 43 |
| Term evaluations | 4,832,386 | 1,092,208.667 | 703 | 172 |
| Selected access events | 1,426,632 | 272,867 | 165 | 43 |

Thus the tested route is sensitive to global distractor population, and the incremental Percept work rises with distractor count. For example, each additional 1,024 noise Concepts corresponds to 149,504 candidate tests at three Percepts, plus 43×1,024 additional candidate tests for each Percept above three. This is a finite fixture-specific interaction, not evidence of an asymptotic order. Scheduler/deferred work stays at 21 operations and 231,164 heterogeneous units across all cells, so it does not account for the observed matcher, Term, or access growth. Untraced wall medians range 10.65–16.60 s and do not follow a clean monotonic pattern with either factor; two replicates per cell are insufficient for a latency claim. Public semantic oracles pass, but outbound graph-message alignment remains false.

## Censored first capture

The initial v1 48-worker capture is retained but excluded from factor interpretation because its source gate detected edits to `domains/discourse_state.py`, `domains/conceptualizer.py`, and `seeds/communication_intent_arbitration.json` during execution. Its rows pass semantic and attribution checks, but audited/control parity, repeated profiles, and base-population checks fail in parts of the mixed-source run. See the [v1.1 capture amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_NOISE_FACTORIAL_V1_1_AMENDMENT_20260929.md), [censored raw report](../../../evaluation/reports/live_describe_scene_percept_noise_factorial_v1_workers_raw_20260929.json), and [censored analysis](../../../evaluation/reports/live_describe_scene_percept_noise_factorial_v1_analysis_20260929.json).

## Limits and next gate

This is one route and one synthetic distractor family on one build/machine. It provides measured candidate, Term, and access work for this route, not a proof that frame-local execution is polynomial or that real tasks have this hierarchy. The flat scheduler counters cannot stand in for complete route cost. Timing is noisy and small-n. The next gate should use an independently authored task family with the same factorial, capture exact scoped/full semantic parity plus omission and contamination controls, and add a counter family for any matcher/adapter costs not represented by these metrics. Then measure a task-family transfer without changing the held structure.

An independent visual task family already provides complementary structural scaling evidence. A source-locked 144-cell two-sheet `st_settle` panel reaches 8,192 SUnits, uses an independent equation oracle, and tests global versus root-scoped aggregation under equal and contrasting sibling states. At 8,192 units, total Term evaluations are 268,961,824 global versus 134,760,480 scoped, with counter-off closure medians 6.297 s versus 2.786 s; exact checks confirm global cross-sheet coupling and scoped independence. This supports a second workload-family result, but its factors and operation differ from this Percept × unrelated-Concept grid, so it is not a matched replication or natural locality estimate. See [vision v2.4 results](SUBSTRATE_VISION_TWO_SHEET_CURRENT_SOURCE_SCALE_V2_4_RESULTS_20260927.md) and [independent analysis](../../../evaluation/reports/vision_two_sheet_current_source_scale_v2_4_analysis_20260927.json).

## Reproduction and artifacts

- Original factorial specification: [v1 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_NOISE_FACTORIAL_V1_PREREG_20260929.md).
- Source-drift repeat procedure: [v1.1 capture amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_NOISE_FACTORIAL_V1_1_AMENDMENT_20260929.md).
- Offline invariant correction: [analysis amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_NOISE_FACTORIAL_V1_1_ANALYSIS_AMENDMENT_20260929.md).
- Runner: [v1.1 capture script](../../../scripts/substrate_live_describe_scene_percept_noise_factorial_v1_1.py).
- Corrected analyzer: [v1.1 analysis script](../../../scripts/analyze_substrate_live_describe_scene_percept_noise_factorial_v1_1.py); [exact captured analyzer source](../../../scripts/analyze_substrate_live_describe_scene_percept_noise_factorial_v1_1_locked_source.py).
- Lock: [v1.1 input lock](../../../evaluation/substrate_capability/live_describe_scene_percept_noise_factorial_v1_1_lock_20260929.json).
- Driver: [48-worker driver report](../../../evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_20260929.json); [raw workers](../../../evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_workers_raw_20260929.json); [corrected analysis](../../../evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_analysis_20260929.json); [preserved initial analysis](../../../evaluation/reports/live_describe_scene_percept_noise_factorial_v1_1_analysis_initial_invariant_bug_20260929.json).
- Censored v1 analysis source and output are preserved separately under their original v1 names.

Reproduce in a fresh tree with `PYTHONPATH=runners/dsl/python:. OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_live_describe_scene_percept_noise_factorial_v1_1.py --lock`, then invoke the same script without `--lock`. Analyze with `PYTHONPATH=runners/dsl/python:. python3 scripts/analyze_substrate_live_describe_scene_percept_noise_factorial_v1_1.py`. The recorded v1.1 raw digest is `5a56e1e3e504ce2ae6ba544a40f042d2614bb199f4fa48953d1b274432a7454e`; the analysis was corrected offline from the exact captured analyzer after detecting the stated invariant error.
