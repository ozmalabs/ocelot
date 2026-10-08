# Vision multi-seed response replication v2.1 results

## Result

The source-locked phase-aware panel completed all 75 conditions across three independently initialized and adapted checkpoints. The independent analyzer passes 11/11 integrity gates: all expected trials are present; each trial names the correct seed checkpoint and passed the v1.9 restore digest check; delivered retinal bursts match active pixels; all rate-write snapshots exist and satisfy `rate=max(act-theta,0)`; update stamps match Retina step 23,010; exact cycle statistics are present; and every closure is classified within 512 passes and 1.6M progress.

Termination is seed-sensitive. Seeds 20260935 and 20260936 each have 4 fixed points and 21 exact cycles; seed 20260937 has 7 fixed points and 18 cycles. The termination class differs across seeds in 9 of 25 matched stimulus conditions; 16 conditions retain the same class across all three seeds. The blank condition is a fixed point for all seeds. Nine varying conditions are not unresolved outcomes: every trial reaches a fixed point or an exact repeated graph state.

| Seed | Adaptation progress | Adaptation closures (fixed / cycle) | Response closures (fixed / cycle) | Response passes (min / median / max) | Response progress total |
|---|---:|---:|---:|---:|---:|
| 20260935 | 429,253 | 100 / 1,900 | 4 / 21 | 4 / 194 / 410 | 5,108 |
| 20260936 | 442,062 | 88 / 1,912 | 4 / 21 | 4 / 192 / 326 | 4,968 |
| 20260937 | 438,535 | 77 / 1,923 | 7 / 18 | 4 / 192 / 256 | 4,768 |

Across all three seeds, the same adaptation schedule yields positive calibration gains and all ON/OFF channels remain active. Adaptation progress varies by about 3% from the minimum to maximum total. Response work also stays in a narrow range on this fixture, despite seed-sensitive attractor class. This is evidence for stable small-fixture work and variable dynamics, not a general complexity result.

The eight B-only rate-write sums below show an additional phase/orientation effect. Values are seeds 20260935 / 20260936 / 20260937. Zeros mean the recorded rate snapshot is silent at the contracted rate-write phase; they do not imply zero later activation.

| Orientation | Phase 0 | Phase π/2 |
|---|---:|---:|
| 0° | 0 / 0 / 0 | 0 / 0 / 0 |
| 45° | 15.271 / 16.042 / 16.789 | 12.544 / 10.974 / 13.897 |
| 90° | 0 / 0 / 0 | 0 / 0 / 0 |
| 135° | 16.340 / 15.300 / 17.705 | 8.741 / 9.380 / 9.604 |

The current evidence therefore supports this limited statement: rule closure, input delivery, and phase-specific response measurement stay within small bounded **progress counts** for this 4×4-per-sheet synthetic family, while fixed-point versus cycle outcomes depend on both stimulus and independently adapted state. The runner did not capture reliable per-condition wall-clock or peak-memory measurements, so this is not yet a commodity-CPU latency claim. It does not establish that cheap cuts hold on natural tasks, that larger frames retain bounded separators, or that rung 3/4 induction is tractable.

## Reproduction artifacts

- Protocol: [v2.1 preregistration](SUBSTRATE_VISION_MULTI_SEED_RESPONSE_REPLICATION_V2_1_PREREG_20260927.md)
- Adaptation/checkpoint protocol: [v2.0 preregistration](SUBSTRATE_VISION_MULTI_SEED_CHECKPOINT_REPLICATION_V2_0_PREREG_20260927.md)
- Runner: [response panel](../../../scripts/substrate_vision_multiseed_response_replication_v2_1.py), [checkpoint builder](../../../scripts/substrate_vision_multiseed_checkpoint_replication_v2_0.py)
- Analyzer: [v2.1 analysis script](../../../scripts/analyze_substrate_vision_multiseed_response_replication_v2_1.py)
- Raw response data: [75-condition capture](../../../evaluation/reports/vision_multiseed_response_replication_v2_1_20260927.json), [pass trace](../../../evaluation/reports/vision_multiseed_response_replication_v2_1_20260927.trace.jsonl)
- Checkpoint summary and exact graph files: [summary](../../../evaluation/reports/vision_multiseed_checkpoint_replication_v2_0_20260927.json), seed graphs under `evaluation/reports/vision_multiseed_checkpoints_v2_0/`
- Analysis and source locks: [analysis](../../../evaluation/reports/vision_multiseed_response_replication_v2_1_analysis_20260927.json), [response lock](../../../evaluation/substrate_capability/vision_multiseed_response_replication_v2_1_lock_20260927.json), [checkpoint lock](../../../evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json)
