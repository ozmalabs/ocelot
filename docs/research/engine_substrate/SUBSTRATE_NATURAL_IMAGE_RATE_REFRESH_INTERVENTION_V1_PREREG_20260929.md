# Natural-image post-settlement rate refresh intervention v1 preregistration (2026-09-29)

## Question

Does the once-per-step `oo_sunit_rate` phase being earlier than final settlement explain why the production `rate` map fails to follow a spatially rotated `act` map?

## Design

- Reuse the locked BSDS300 image `101085.jpg`, its exact 180° rotation, and a blank input; three frozen checkpoints; and global/root-scoped settlement.
- Each of the 18 seed/scope/input cells starts from its exact checkpoint and runs one ordinary `WaveWorld.step(frame=...)` call. Save the default final map. In the same substrate, set only the target sheet's 16 `rate_step` values to `-1`, then invoke the existing `oo_sunit_rate` rule once using the native batch API. Save the refreshed map and graph state.
- The independent oracle checks each refreshed rate against `max(final_act-final_theta,0)`, requires all target `act` values and stamps to remain unchanged, and compares pre/post graph contents to ensure only target `rate` and `rate_step` attributes changed. Sibling state and topology must remain identical.
- Compare default and refreshed `rate` maps against the exact 180° permutation, using blank-subtracted maps. Keep seed/checkpoint as the replication unit; report the three checkpoint outcomes separately.

## Gates and limits

Require exact input delivery, checkpoint graph identity, complete worker matrix, exact intended write footprint, no unexpected edge/node changes, and zero equation residual after refresh. A refreshed map that stays zero or fails the transform criterion is a negative result. This is a diagnostic intervention after the normal tick; it does not alter or validate a new default scheduler. It tests one image, one transform, and three adapted checkpoints, not general recognition or natural-image prevalence.

