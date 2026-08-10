# EFFECTOR AUTHORITY IS A WEIGHTED COLLAPSE — results, gate 1

Measured 2026-08-07 against `EFFECTOR_AUTHORITY_COLLAPSE_PREREG.md`, whose gates
were registered before any of this existed.

Artifacts: `scripts/jabberwock_humanoid_desk_authority.py`,
`scripts/gen_effector_authority_axis_seed.py` →
`seeds/effector_authority_axis.json` v1.0.0, `results/desk_authority_gate.json`.

## The physical rig

Standing MJCF humanoid (base z=1.205, both feet loaded 216 N / 184 N), torso yaw
commanded to 0.70 rad — inside the `abdomen_z` limit of ±0.785, so "the turn
completed" is a measurable outcome and not a saturation artefact. A static box at
(0.30, −0.28, 1.20) sits in the right arm's sweep. Deterministic: seeds 0/1/2
return identical numbers, so n=1 per condition and there is no variance to
report.

| arm authority | peak | arm deflection | base z | upright | turn |
|---|---|---|---|---|---|
| hold (120 N)  | 2245.8 N | 0.000 | **0.12** | **no** | completes |
| yield (2 N)   | 1394.3 N | 0.726 | 1.205 | yes | completes |
| no desk, hold | 0 | 0.000 | 1.205 | yes | completes |
| no desk, yield | 0 | **0.922** | 1.205 | yes | completes |

Holding the arm at setpoint through the obstruction **throws the body to the
floor**. The user's predicted failure mode — "smash the hand into the desk and
have some sort of other failure" — turns out to be a fall.

THE NO-DESK CONTROL EARNS ITS PLACE: a released arm deflects 0.922 rad with no
desk at all. That is gravity, not yielding. Arm deflection therefore proves
nothing on its own, and any gate built on it would have been measuring the wrong
thing. The discriminators are `upright` and peak load.

## Gate 1 (Desk) — PASSES

Identical rules, identical candidates, identical physics. Only the goal's
declared demand differs.

```
goal=turn          demand(turn=700, reach=0)   priority_axis=0  adopted=yield_arm
    hold_arm   (0,    0, -2246,  120)   dominated=1     <- eliminated
    yield_arm  (0,    0, -1394, 1205)   dominated=0

goal=reach_through demand(turn=0, reach=700)   priority_axis=1  adopted=hold_arm
    hold_arm   (0,    0, -2246,  120)   dominated=0
    yield_arm  (0, -508, -1394, 1205)   dominated=0
```

axes = (turn shortfall, reach shortfall, −peak load, retained base height),
all signed so higher is better.

The turn case is decided more strongly than the gate asked for. With no reach
demanded, `hold_arm` is not merely deprioritised — it is **dominated**, strictly
worse on damage and posture and tied elsewhere, so goal-blind relational
dominance eliminates it before the priority axis is consulted. When reach IS
demanded the two become genuinely incomparable, both survive, and the one
declared priority axis chooses.

Gate 1's three clauses: the turn completes (yaw 0.70 in both arms), the hand
yields (0.726 rad), and no rule drives the hand to setpoint against the
obstruction — the adopted regime surrenders the arm's authority rather than
re-targeting it.

## Gate 3 (not zero) — PASSES, and this is the substance

During the turn the hand is not ignored. Both candidates tie on the turn axis
(holding the arm did NOT prevent the turn — yaw reached 0.70 either way), so the
turn axis alone cannot discriminate. What eliminates `hold_arm` is damage and
posture. **The hand is released because damage weighed, not because the goal
stopped caring where the hand was.** A binary instrumentality design fails here
by construction, which is what the gate was written to catch.

## Gate 4 (no scalar) — HOLDS BY CONSTRUCTION

Nowhere in `seeds/effector_authority_axis.json` are two axes combined into one
number. Dominance compares axis-by-axis (`ParetoDominates`, existing and
unmodified); selection reads a single declared axis off each survivor, after the
F-16's `_priority_value_from_axes`: "a single declared axis's own reading, never
a weighted sum, never folded into dominance."

A consequence worth recording: because nothing is ever summed, the axes never
need a common scale, so the integer shortfall form works where the F-16 needed a
ratio. Refusing to scalarise bought the integer frame for free.

## No contact reflex

Nothing in the seed reads whether a collision occurred. The axes are shortfalls
against declared demand — quantities that are just as meaningful with no obstacle
in the world, which the desk merely makes large. The prereg calls a contact
reflex, a fall handler, or a smash mode appearing in the implementation a design
failure rather than a feature; none appears.

## THE ERROR THIS GATE CAUGHT IN ITS OWN FIRST RUN

The first formulation scored the reach axis as "how well the arm held its
position" unconditionally. Under that formulation **both goals adopted
`hold_arm`** — the option that throws the body to the floor — because holding the
arm scored a perfect 0 on an objective nobody had demanded, and that perfect
score is what saved it from dominance.

That is the same error the F-16 seed records at v2.1.0, reproduced here within an
hour of quoting it: scoring a STATE as though it were an OBJECTIVE. The
correction is the F-16's own sentence — "a tracking error out of band is not an
unachievable objective; a demand past the loop's own declared authority is" —
so a shortfall now presupposes a demand, and the demand comes from the goal.

The distinction that makes this legal: DEMAND IS NOT PRIORITY. Only priority must
be kept out of dominance. Dominance stays blind to which axis will be READ; it
cannot be blind to what was ASKED, because an unasked objective is not an
objective at all.

## Enabling fix: the declared authority was dark

An achievability axis needs an authority to measure against, and every clamp was
unwritten in a live graph: `maximum_joint_force`, `joint_twitch_radians`,
`specified_maximum_position_change_per_action` (7,196 rule reads / 0 writes).

Located the loss point: `PyBulletHumanoidWorld.actuator_options()` computed
`twitch = (joint_ordinal, magnitude)` and published only `twitch[0]`, discarding
the magnitude at the boundary. Now published on each of the 43
`EmbodiedOpaqueActuatorAffordance` nodes with `*_measured = 0` provenance, after
the F-16 pattern, so a declared bound is never confusable with an observed one:
42 twitch options at 1000 declared units, the 1 tonic option at 0 (a tonic hold
commands no displacement), all 43 at 50 declared force units.

## HONEST SCOPE — what this does NOT show

* **The decision layer only.** Candidates are MEASURED post-hoc and published to
  the frontier; nothing predicts them. Prereg route (b) — the forward model
  projecting a crossing BEFORE contact — is untested here and has still never
  fired live.
* **The loop is open at the emit end.** The adopted regime's
  `arm_authority_units` is read back but not yet applied to a live body by the
  agent; the two physical trials were driven by a hand-written controller, not by
  the agent's own motor programs.
* **n=1, deterministic.** No variance, no seeds, one desk placement, one turn
  amplitude. Nothing here establishes robustness to any of those.
* **Gates 2 (wall), 3a, 3b, 3c (fall), 3d, 5, 6 are NOT addressed.**
* Uniform denominator: `declared_joint_force_units` is one config constant across
  all 43 actuators, so the axis can distinguish demand but never differential
  authority between joints — thinner than the F-16, where each loop declares its
  own clamp.
