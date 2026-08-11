# The jabberwock's generalisation — controls as a CONCEPT, goals as standing-error

Creator's steer (2026-06-26) after the Tetris stress test failed: "it should understand controls as a CONCEPT
and be able to generalise. it already has translation that includes rotation, this just needs to be wired in.
goals are all general. aiming isnt the end state. it should also be able to play adventure games." Tetris is ONE
case of many — generalise, don't patch.

The Tetris finding (3 mismatches): (1) the controllable locus is EPHEMERAL — the piece re-segments as a new
region every spawn AND rotation (7 region-ids in 120 frames), so the per-locus control model never accumulates;
(2) ROTATE is not a displacement — the stack treats a control as a basis-displacement; (3) the goal is LINES
CLEARED — a configuration/value objective, not a colour contacted / place reached, so aim_goal finds nothing.

The jabberwock's generalisation (reusing held faculties; the steps 1-5 stack is just the `change_location` leaf):

## 1. Control as a concept — effect-KIND, not displacement
A control is "a thing that, when pressed, produces an effect that is one of my OperationPrimitives"
(enact.json: change_location / transform_attribute / exchange / put / combine / select / signal / ...). New rule
`control_effect`: observe the bound locus pre/post-press and FIT the held transforms to the point-set change:
- centroid moves, shape preserved → `change_location` parametrised by today's (dr,dc,dz);
- centroid fixed, post-set maps onto pre-set under the held `Rotate` (angle via `AngleBetween`) →
  `transform_attribute(rotate, θ)`;
- active/highlighted token changes → `select`; world-state flips → `signal`.
Writes a `produces_effect` edge; `select_operator` (held) binds each control's Act to its revealed primitive.
`affordance_basis` is no longer the trunk — it is the `change_location` LEAF. Wired (taxonomy, select_operator,
Rotate, AngleBetween, shape_sense already exist) + one fit rule.

## 2. Locus identity by AGENCY, not region-id (dissolves mismatch 1)
Re-key the controllable locus off `avatar_agency` (controls → produces_delta → MotorEffect): the locus IS the
region whose change correlates with my presses, persisted as a node in the binding tree, NEVER a segmentation
id. On rotate, the post-region is the SAME binding because it is the `transform_attribute` image of the prior
locus under the just-learned `Rotate`; on respawn, re-bind by agency-correlation. Ephemerality was an artefact
of identifying by pixels instead of by agency + transform-continuity.

## 3. Goal as a standing-error on the value_signal — aim is one case
The general goal is autonomy's setpoint: a desired world-state and a STANDING ERROR vs the current value_signal,
action chosen to descend it. `aim_goal` (locus → location) is the special case where the measured quantity is
distance-to-target and the setpoint is zero; `pick_control_for_goal`'s `Argmax Dot(delta, goal-self)` is the
linear collapse of the general rule when the only effect-kind is `change_location`. General rule:
`Argmax ΔValue(predicted_state_after_control)` — apply each control's learned OperationPrimitive (translate,
rotate, ...) to the locus/world in a SCRATCH ROLLOUT (the held postulate/deduce arena), predict the resulting
value_signal, pick the control that most reduces standing-error. Tetris value proxy = filled-row-ness / holes,
so rotate-then-translate placements get scored by line-completion; lines-cleared falls out as "monotonic value
increase," no contact-colour needed.

## 4. Adventure games for free
Controls fit to `select / put / combine / signal`; the goal is a desired CONFIGURATION (door-open, item-held);
the error is the mismatch between the world-state descriptor and that target; the same rollout-and-descend rule
plans the verb sequence. No new machinery — other OperationPrimitive leaves + a configuration setpoint.

## Wired vs new + bench-provable order
- WIRED: OperationPrimitive + select_operator, Rotate/AngleBetween, avatar_agency, binding tree, value_signal +
  autonomy setpoint, postulate/deduce rollout.
- NEW RULES: `control_effect` (fit+classify → produces_effect), locus-identity-by-agency, generalised-goal
  (setpoint error), generalised `pick_control` (Argmax predicted-ΔValue).
- ONE POSSIBLE AUTHORED PRIMITIVE: `fit_transform(points_before, points_after) → {kind, param, residual}`
  choosing among {translation, rotation}; may assemble from centroid-diff + AngleBetween; only if the residual
  fit is unexpressible does the jabberwock AUTHOR it (HumanImpasse → self-extension, no donkey).
- BUILD ORDER: (1) `control_effect` classifies Tetris LEFT/RIGHT as change_location and ROTATE as
  transform_attribute(rotate) from observation, donkey=0; (2) the locus stays ONE binding across the 7
  respawns/rotations (vs 7 ids today); (3) regression — the generalised goal reproduces snake foraging as the
  distance-setpoint special case (zero behaviour change), then drives Tetris by value-setpoint; (4) `pick_control`
  rollout places pieces to clear >=1 line; (5) a tiny adventure room solved by the same rules with no new code.
