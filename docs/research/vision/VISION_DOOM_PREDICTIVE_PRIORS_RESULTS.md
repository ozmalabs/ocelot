# RESULTS — Doom predictive priors: an assumption exists before surprise can exist

Block **162000–162999**. Branch `gamma-substrate/doom-predictive-priors`.
Preregistration: `VISION_DOOM_PREDICTIVE_PRIORS_PREREG.md`, corrected and committed
before any run after the creator rejected the first, too-bottom-up frontier design.

Engine **`64dbce1e7f47…`**, `source_match="shared"`, source fingerprint
`3a66c063…` (this rung adds no Rust; worktree and canonical Rust are identical).

## Outcome

**PASS on the mechanism and requested readout.** The agent now holds an explicit
top-down structural assumption at the same time as bottom-up map evidence:

- a partial open box confabulates a complete room perimeter;
- a one-body-wide strip with only one observed wall confabulates the parallel wall
  on the wholly unseen side;
- later observations confirm the assumption or mint a graph-resident
  `MapResidual{kind:"prediction_minus_observation"}`;
- observed `has_cell` belief remains separate and authoritative;
- an 80-frame, 640×240 MP4 shows Doom RGB on the left and the live graph map on the
  right (cyan confabulation, amber observation, white correction pulse).

Artifact:
`results/doom_predictive_priors/doom_predictive_priors.mp4`
(80 frames, 10 fps, 8.0 s, H.264, 640×240). Raw metrics:
`results/doom_predictive_priors/summary.json`.

## The load-bearing correction

The first committed preregistration proposed a one-cell frontier continuation. The
creator's correction was exact: that is not the cognitive claim. A human seeing part
of a room assumes the enclosing room; seeing one corridor wall entails an assumed
opposite wall. And without an assumption, “surprise” is merely change detection.

No confirmatory run occurred under that first design. The corrected preregistration
(`57588af925`) replaced it with simultaneous whole-structure projection:

1. bottom-up observations grow the standing 161000 `has_cell` belief;
2. existing `space_quantize` decodes maximal observed passable boxes;
3. graph rules interpret body-relative box geometry as room, corridor, or minimal
   enclosure and project the schema's absent walls immediately;
4. next observations are compared with that preserved prior, making confirmation and
   correction meaningful.

The constructed anti-bottom-up gate passes: with free cells `(1,1..4)` and only the
wall `(0,1..4)` observed, the graph predicts both that supporting wall and the entirely
unseen opposite wall `(2,1..4)`. Transposing the evidence transposes the prediction.

## E1M1 result

Fixed route/seed 1234, 80 frames, same RGB depth-from-motion and oracle discipline as
rung 161000:

| measure | result |
|---|---:|
| final observed cells | 122 (35 free, 87 wall) |
| final confabulated cells | 26 |
| final simultaneous spatial hypotheses | 29 |
| prediction/observation tests | 1,869 |
| confirmed | 1,046 |
| corrected / residual | 823 |
| overall correction fraction | 0.4403 |
| trajectory consistency | 1.0 (0 walls on walked cells) |
| seen-depth vs depth-buffer oracle | median ρ 0.3091; frac positive 0.803; n=71 |

The video begins with one observed cell surrounded by an eight-cell minimal enclosure:
the assumption is visible before there is enough evidence for a room. As the grounded
map expands, cyan walls are overwritten by amber evidence; disagreement pulses white.
By the final frame, 122 grounded cells coexist with 26 still-confabulated cells.

## The preregistered learning-curve prediction failed

The mechanism prediction was that colour-flip corrections would thin as the map
stabilised. They did not:

| half | tested | corrected | correction fraction |
|---|---:|---:|---:|
| early | 662 | 233 | **0.3520** |
| late | 1,207 | 590 | **0.4888** |

This is an honest negative, not a video failure and not permission to tune after
looking. The assumptions and residuals are real; the fitted schemas remain unstable.
Rung 161000's noisy seen-depth fragments free-space into many quanta (29 simultaneous
hypotheses at the end), so the agent repeatedly fits tight local enclosures. More map
evidence currently creates more overlapping opportunities to be wrong instead of a
single stable room model.

The next scientific residual is therefore **hypothesis persistence/competition**:
multiple local room/corridor hypotheses need to collapse into a smaller explanatory
set, using the cognition core's held-shape competition rather than adding a threshold
or suppressing residuals. The present result is the necessary substrate for that work:
there is now an explicit assumption that can win, lose, and surprise the agent.

## Architecture audit

- `seeds/doom_predictive_priors.json` contains all six decisions:
  room, minimal-enclosure, and two orientation-specific corridor projection rules;
  wall confirmation; wall-to-free correction/residual.
- `SpatialHypothesis`, `MapPrediction`, `PredictionOutcome`, and `MapResidual` are
  graph nodes. The renderer does not derive them.
- `domains/doom_prior_readout.py` only timestamps incoming observation tokens, reads
  graph state, rasterises it, and streams RGB to ffmpeg. Source gates prove it never
  writes `has_cell`, `has_prediction`, or residual nodes.
- Predictions never enter `has_cell`; unknown remains absence in grounded belief.
- Depth and labels buffers remain scoring oracles only. Prior projection reads
  `SpaceQuantum` graph state built from RGB depth-from-motion + self-motion.
- All coordinates are integer in-frame values. No continuous geometry was inserted
  into the map.
- Feature flag `predictive_map=0` is inert.

## Gates

- `tests/test_doom_predictive_priors_migrated.py`: **10 passed**, including the
  opposite-wall gate, transpose gate, confirm/correct residual gate, renderer/MP4
  gates, inert/source audits, and a real E1M1 run.
- Combined old map + new prior gates: **17 passed**.
- Standing vision oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped,
  0 failed**. The pre-existing vision path is unchanged.
- `ffprobe`: width 640, height 240, 10 fps, 80 frames, duration 8.0 s.

## What is not shown

- This does not yet collapse overlapping local hypotheses into one persistent global
  room/corridor account; the failed late-half prediction measures that gap.
- It is one E1M1 route, not cross-level generalisation.
- Illumination priors remain out of scope until appearance is grounded into map cells;
  an untestable lighting assumption would not produce a meaningful residual.
- Playback is real time; full-resolution depth-from-motion computation remains
  offline, carrying rung 161000's scale wall.
