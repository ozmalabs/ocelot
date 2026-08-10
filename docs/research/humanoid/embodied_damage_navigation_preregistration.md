# Hidden-damage navigation preregistration

Status: frozen before execution of the held-out matrix.

## Question

After two fresh graph substrates receive exactly the same 45 calibration
actions and raw outcomes in a mechanically randomized body, does continued
graph plasticity improve pursuit of a newly revealed goal after an unlabelled
actuator fault, compared with freezing the same learned graph at action 45?

This is a stronger test than prediction-error recovery. The primary outcome is
closed-loop navigation after paying for every active recalibration action.

## Fixed design

The machine-readable protocol is
`protocols/embodied_damage_navigation_v1.json`. Its SHA-256 is recorded by the
runner into the result. It fixes six combinations of mass, friction, rolling
friction, motor authority, target direction, abrupt damage, and progressive
wear. Each is applied to R2-D2, Husky, and Racecar, for 18 paired comparisons.
A healthy arm under the same randomized dynamics supplies a controllability
reference but is not part of the primary adaptive-versus-frozen comparison.

All arms start with goal `(0, 0, 0)` and run graph-authored system
identification. At action 45 the environment reveals a target offset from the
body's then-current position. The damaged arms simultaneously acquire the
declared hidden fault. They run through action 240. The graph sees pose, goal,
contact, effort, opaque actuator token, and verified outcome only. It never
receives morphology semantics, randomized parameters, damage timing, affected
channel, retention, or wear.

The adaptive and frozen arms use the same seed, body, dynamics, calibration
policy, graph rules, and initial graph. The sole post-change causal difference
is whether ActionModel plasticity remains enabled. Exact pre-change
trajectories are a refusal gate.

## Outcome and refusal gates

For each run, normalized progress is:

`(distance at target reveal - final distance) / distance at target reveal`.

It includes time spent probing. The primary claim passes only if every
machine-readable gate passes:

- all 54 runs complete;
- every adaptive/frozen pre-change trajectory matches exactly;
- all adaptive damaged graphs update post-change and no frozen graph does;
- adaptive progress exceeds frozen progress in at least 10 of 18 pairs;
- pooled median paired advantage is at least 0.05; and
- median adaptive progress is positive separately for every morphology.

No failed gate may be redescribed as a pass. Per-morphology results, healthy
references, recalibration action counts, and negative cases remain in the
report.
