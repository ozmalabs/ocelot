# Shared-substrate orientation/phase response panel v1.9 preregistration

## Question
Across a small held-out grating panel, how do rate-write response, post-settle activation, exact termination class, and global/root-scoped scope effects vary on the same prepared visual state?

## Inputs
Use the v1.7 prepared graph checkpoint and v1.8-validated pass-sliced instrumentation. Keep seed, weights, Retina/SUnit IDs, parameters, and graph snapshot fixed. Run both root-scoped and global rule variants. For each scope, restore the checkpoint before every presentation. Do not adapt or learn between presentations.

## Panel
Use four orientations (0°, 45°, 90°, 135°) crossed with two phases (0, π/2), period 4, binarized using the registered complex-cell stimulus function. For every grating, run B-only (A blank), A-only (B blank), and both sheets with the same grating. Add one both-blank control. This gives 25 conditions per scope, 50 total.

## Measurements and gates
Apply the v1.9 response-phase contract: verify declared active pixels equal observed retinal bursts; capture per-unit state at the first `rate_step` update and verify the exact rate equation; trace every pass with an exact full-graph digest; report fixed point versus cycle and compute per-unit activation orbit statistics for cycles; capture progress/pass work and source-stable inputs. Use a 512-pass and 1.6M cumulative progress ceiling per condition. Persist one JSONL trace record per pass and a partial summary after each completed condition. No population or natural-task prevalence claim is permitted from this one learned graph.

## Decision use
This panel tests whether the known orientation-selective bank yields phase/orientation-dependent responses under both scope rules and whether added-sheet inputs change response/termination. It does not test learning generality, frame discovery, or scale. Any scope comparison is conditional on the same root-scoped-adapted prepared state.
