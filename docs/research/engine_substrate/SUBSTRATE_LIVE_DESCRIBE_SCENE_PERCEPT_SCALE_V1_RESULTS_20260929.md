# Live describe-scene Percept-count scaling v1 results

**Status:** all 16 source-locked worker records are complete. The corrected independent analysis passes all 13 gates. The capture runner's final process-count check and the originally locked analyzer each had a disclosed defect; see the analysis amendment.

## Result

The 3/6/12/24 Percept factorial passes the task oracles in all audited and uninstrumented workers. Every request Scene view contains the assigned number of Percepts, each is classified exactly once to its expected class, no wrong classification is present, and the fixed 4,096 noise Concepts receive no classification. Each request resolves its one Goal, and every public reply includes the three semantic propositions. Exact reply text also stays at the three-fact baseline when repeated Percepts are added. Audited/control pairs match on Goal state, reply, graph counts and semantic graph digest; replicated graphs and discrete work profiles match exactly within each size. Counter accounting, access traces and work traces reconcile with zero drops; all 16 workers have distinct PIDs and matching source hashes.

## Measured scaling

| Request-view Percepts | Candidate tests | Term evaluations | Selected access events | Scheduler/deferred counter units | Untraced wall median | Untraced CPU median | Peak RSS median |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 1,563,164 | 7,711,634 | 2,102,412 | 231,164 | 16.80 s | 16.64 s | 1,939.1 MiB |
| 6 | 2,909,504 | 13,101,796 | 3,449,397 | 231,164 | 16.69 s | 16.53 s | 1,939.1 MiB |
| 12 | 5,602,184 | 23,882,120 | 6,143,367 | 231,164 | 17.56 s | 17.47 s | 1,939.0 MiB |
| 24 | 10,987,544 | 45,442,768 | 11,531,307 | 231,164 | 19.29 s | 19.08 s | 1,939.1 MiB |

Candidate tests, Term evaluations and selected accesses are affine over these four tested sizes. Every additional Percept adds exactly 448,780 candidate tests, 1,796,720⅔ Term evaluations, and 448,995 selected-access events. The three target-recognition rules (`recognise_a_counter`, `recognise_a_thing_that_moves_itself`, `recognise_a_thing_that_stays_put`) account for 9,411,066 of the 9,424,380 added candidate tests from 3 to 24 Percepts. Their aggregate work follows the number of Percepts even though the same 4,096 noise Concepts remain semantically irrelevant.

The operation-work trace stays constant at 21 operations and 231,164 summed heterogeneous counter units across all sizes: 37 scheduler passes, 54,392 selected-rule slots, 87,771 dirty-vector slots, 87,771 external-poll slots, and 1,172 fixed-point-probe slots. These counters describe scheduler/deferred call sites, not matcher work. The separate candidate and Term counters show substantial growth that the scheduler counter total does not represent. Do not interpret the unchanged scheduler counters as constant total engine work.

Graph size rises from 29,297 nodes/15,794 edges to 29,360/15,962. Peak RSS remains near 1.94 GiB, dominated by the full seed graph and process high-water mark. Untraced medians rise about 2.50 s across the 8× input-size interval; two replicates per cell do not resolve this wall-time trend precisely against route and scheduler noise. The output profile remains a graph-visible mismatch: outbound-message alignment is false in all sizes, even though the public reply and per-Percept classification oracle pass.

## Interpretation and limits

This measures one authored full-seed route with a balanced multiset of three known semantic classes and a fixed 4,096-Concept distractor population. It shows near-linear measured matching work in Percept count under this fixture, with most added work in three recognition rules. It does not establish asymptotic complexity, natural task prevalence, learned cheap-cut locality, factorized inference, scoped-execution safety, or novel concept learning. Latency/RSS remain descriptive at two replicates; they do not prove commodity-scale performance. Exact public reply text is not sufficient for full route correctness while outbound graph-message alignment fails.

Next vary both axes factorially: Percept count 3/6/12/24 crossed with noise Concepts 0/1,024/4,096, then fit interaction terms on exact candidate/Term counts and report timing separately. Follow with an independently authored production family and a source-complete operation boundary. A scoped/full intervention still requires exact graph parity and omission/contamination controls.

## Artifacts

- Protocol: [v1 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_SCALE_V1_PREREG_20260929.md); [analysis amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_SCALE_V1_ANALYSIS_AMENDMENT_20260929.md).
- Runner: [source-locked v1](../../../scripts/substrate_live_describe_scene_percept_scale_v1.py); corrected independent analyzer: [analysis v1](../../../scripts/analyze_substrate_live_describe_scene_percept_scale_v1.py); exact locked analyzer bytes: [archived source](../../../scripts/analyze_substrate_live_describe_scene_percept_scale_v1_locked_source.py).
- Lock: [source lock](../../../evaluation/substrate_capability/live_describe_scene_percept_scale_v1_lock_20260929.json); capture summary: [driver report](../../../evaluation/reports/live_describe_scene_percept_scale_v1_20260929.json); raw workers: [16-process capture](../../../evaluation/reports/live_describe_scene_percept_scale_v1_workers_raw_20260929.json); analysis: [corrected independent report](../../../evaluation/reports/live_describe_scene_percept_scale_v1_analysis_20260929.json).
