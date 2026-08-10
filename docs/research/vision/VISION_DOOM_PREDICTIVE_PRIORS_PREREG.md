# PRE-REGISTRATION — predictive priors over the graph-native Doom map

Block **162000–162999**. Branch `gamma-substrate/doom-predictive-priors`, based on
`8807ce351b`. Written and committed before the confirmatory run. This rung composes the
161000 persistent observed map with the already-standing predictive-coding invariant:
prediction and observation are distinct graph facts; their mismatch is a residual; the
observation remains authoritative.

**CORRECTION BEFORE ANY RUN (2026-07-23):** the first committed form (`e497098fad`)
made the prior a one-cell frontier extrapolator. That is too bottom-up and is
superseded by this file. The point is the confabulation: top-down structure is present
at the same time as bottom-up evidence. A partial room is perceived as a room with an
unseen enclosing wall; a corridor with one observed wall is perceived with the
parallel wall on the unseen side. No confirmatory test or E1M1 run occurred under the
superseded mechanism.

## SEED CLAIM

```
SEED CLAIM 162000-162999: CLEAN -- no collision DETECTED.
  Scope: 860 files with seed sinks; 582 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from one generator.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots).
  A CLEAN RESULT MEANS 'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The mechanism and constructed gates are deterministic and draw no RNG. The real E1M1
demonstration replays the already-used fixed VizDoom route/seed 1234 from rung 161000;
it is a paired visualisation, not a fresh independent statistical sample. Therefore no
population inference or power claim is made and no seed in 162000–162999 is burned.

## HYPOTHESIS (two-sided)

The agent can decode partial observed free-space as a whole spatial schema and render
the schema's unobserved structure immediately, then let later observations confirm or
correct it, using the same graph-native prediction → observation → residual →
reconciliation shape as cognition.

- **P1 — distinct graph beliefs:** the observed belief remains
  `game -has_cell-> Cell{pose,value}` with unknown = absence. A separate
  `game -has_hypothesis-> SpatialHypothesis{schema,lo,hi,epoch}` projects
  `game -has_prediction-> MapPrediction{lo,hi,value,role,epoch}` over unobserved
  structure. No prediction writes `has_cell`.
  *Null:* the “prior” is a Python grid, or it pre-fills/overwrites observed belief.
- **P2 — whole-structure confabulation:** a currently observed passable
  `SpaceQuantum` is decoded by its body-relative geometry:
  - open in both dimensions → **room schema**, projecting the complete four-wall
    perimeter one cell beyond the observed free box;
  - one-body-wide in one dimension and extended in the other → **corridor schema**,
    projecting the two parallel side walls along its length, including an unseen
    opposite wall when only one side has been observed;
  - one-body-sized in both dimensions → **minimal enclosure hypothesis**, projecting
    four sides until evidence expands or breaks it.
  This deliberately predicts more than was sensed. As free-space observations expand,
  the fitted schema expands and its projected walls move outward; the old near wall
  becomes a visible correction. Transposing the evidence transposes the structure.
  *Null:* only immediate frontiers are copied, no opposite wall is present, or Python
  chooses the shape.
- **P3 — prediction error is graph data:** an `ObsCell` on the next epoch tests the
  preceding `MapPrediction`; equality mints a confirmed `PredictionOutcome`, inequality
  mints a corrected outcome / `MapResidual`. The standing 161000 observation rules
  reconcile the grounded map independently, so observation wins without deleting the
  historical prior. *Null:* a disagreement is hidden, or the renderer computes it.
- **P4 — visible live readout:** one MP4 shows Doom RGB on the left and the dynamically
  expanding map on the right. Unknown is dark; current confabulation is cyan; grounded
  observation is amber and overwrites cyan on arrival; a correction is outlined as
  surprise. Playback has a fixed FPS independent of offline compute time. Both panels
  are reads of captured RGB / graph state, not a second mechanism. *Null:* no video,
  static final map only, or the right panel is populated from an oracle buffer.

The depth and labels buffers remain scoring oracles only exactly as in rung 161000.
The predictive layer may read only graph state produced from RGB depth-from-motion +
self-motion.

## MECHANISM FIXED IN ADVANCE

1. Ingest bottom-up observations and run the existing 161000 accumulation.
2. Decode the observed free belief with the existing Rust `space_quantize` primitive.
   Its body-relative `SpaceQuantum` boxes are the partial evidence, not the prior.
3. In the same tick, seed rules classify each passable box by extents relative to
   `game.body_w`, mint an epoch-stamped `SpatialHypothesis`, and PROJECT its absent
   structure as wall-valued `MapPrediction` boxes:
   - room / minimal enclosure → four complete perimeter sides;
   - corridor → two complete parallel walls across the narrow dimension.
   Projection uses integer in-frame coordinates only. There is no lookahead to an
   oracle and no requirement that a predicted wall already have observed support.
4. On epoch `t+1`, seed rules compare incoming `ObsCell`s to predictions from epoch
   `t` and mint durable confirmation/correction outcome nodes. Corrections additionally
   mint a `MapResidual`.
5. The adapter only stamps observation epoch, invokes rules/`space_quantize`, queries
   graph nodes, and rasterises/encodes frames. It never writes `has_cell`,
   `has_prediction`, `PredictionOutcome`, or `MapResidual`.

No new Rust is predicted: `space_quantize` already extracts maximal partial-space
boxes; rule Terms can express body-relative extents, integer perimeter projection,
containment, equality, and effects. If that audit is wrong, the rung stops and a new
preregistration names the required primitive rather than moving the decision into
Python.

## EXACT GATES AND STATISTICS

Deterministic constructed gates:

1. A partial 3×3 observed free patch → a room `SpatialHypothesis` plus a complete
   predicted wall perimeter outside it; the opposite/unseen sides exist despite no
   observation there. Predicted cells do not enter observed `has_cell`.
2. A one-body-wide observed strip with only one side wall seen → a corridor hypothesis
   and TWO parallel predicted side walls, including the wholly unseen opposite side.
   Transpose the strip → transpose the predicted walls. This is the load-bearing
   anti-bottom-up gate: a one-cell frontier copy cannot pass it.
3. A matching next observation mints `result=confirmed`; a mismatching one mints
   `result=corrected` plus exactly one `MapResidual`; grounded `has_cell` equals the
   observation, never the prior.
4. Flag off is inert. Source audit proves Python does not write any belief/outcome edge
   or node type owned by the rules.
5. Renderer gate: a synthetic RGB frame + graph snapshot produces a 640×240 two-panel
   frame containing the declared prior and observation colours. If `ffmpeg` exists,
   a short MP4 is encoded and probed for two panels and the requested frame count.

Real E1M1 replay: fixed 80 frames, route and seed 1234 unchanged from rung 161000.
Report, without thresholding or rerunning:

- observed-cell and active-predicted-cell curves;
- cumulative confirmed, corrected, and total tested predictions;
- per-frame colour flips, correction fraction, and early-half vs late-half correction
  fractions (the visible learning-curve diagnostic);
- final map counts and the unchanged 161000 trajectory-consistency / seen-depth oracle
  metrics;
- MP4 path, dimensions, FPS, frame count, engine hash, and source match.

**Decision:** PASS if all five constructed gates pass, the real graph creates and tests
predictions, the observed map still satisfies trajectory consistency, and the MP4 has
the required two-panel dynamic content. The early/late correction comparison is
reported, not used to rescue or fail the mechanism: a non-declining curve means this
fixed prior did not learn enough on this route and is an honest result, not permission
to tune a rule after looking.

## PREDICTION, STATED IN ADVANCE

The constructed gates pass, especially the unseen opposite corridor wall. On E1M1,
early small free boxes produce tight enclosures whose cyan walls are frequently
overwritten amber as exploration proves floor beyond them. As observed free geometry
expands and stabilises, room/corridor hypotheses should move less and more predicted
walls should be confirmed, so the late correction fraction should be below the early
fraction. This is not guaranteed: rung 161000's noisy depth-from-motion can fragment
the passable boxes and repeatedly re-fit tight schemas. If corrections do not thin,
the result localises the residual to schema stability / seen-depth quality, not to the
graph-native loop or renderer.

## SCOPE / NOT SHOWN

- This is a room/corridor structural prior, not a full learned Doom level generator.
- Enclosure and opposite-wall completion are tested; illumination remains a named next residual
  until RGB appearance is grounded into world cells. Inventing a lighting prior without
  a graph observation that can confirm/correct it would be unfalsifiable.
- One deterministic E1M1 route demonstrates the mechanism and video; it does not
  estimate generalisation across maps or players.
- The video is real-time playback, not real-time computation. Full-resolution
  depth-from-motion remains off the compute-time real-time ceiling from rung 161000.
