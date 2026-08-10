# Contextual damage navigation v3 preregistration

Status: frozen before execution.

## Change made before the retest

The v2 postmortem identified a representational problem rather than a
morphology label to special-case: an action-local mean cannot separate an
actuator's contribution from momentum carried into the action.

V3 gives every graph-resident ActionModel three learned persistence
coefficients. The prior receipt-backed forward, lateral, and turning
transition is rotated into the new body frame and held on the episode node.
Each action prediction is its learned intercept plus its learned coefficient
times that one-transition context. Both quantities update through graph terms.
The host supplies no velocity estimate, action semantics, morphology feature,
damage feature, or learning calculation.

The frozen arm learns exactly the same contextual model during calibration
and continues updating its transient history state after action 45, but its
ActionModel intercepts and coefficients cannot change. This isolates
post-change model plasticity rather than depriving the control of observations.

## Development evidence

The implementation and its `0.5` normalized context-learning rate were frozen
after replaying the already published v2 cases. On that development matrix it
produced 13/18 adaptive wins and pooled median paired advantage `0.07746`.
R2-D2 changed from v2's held-out median advantage `-0.05540` to development
advantage `+0.08381`. These are engineering observations, not new evidence.

## Held-out design and gates

The machine-readable protocol
`protocols/embodied_damage_navigation_v3.json` fixes six new combinations of
goal, mass, friction, rolling friction, motor authority, abrupt loss, and wear
across R2-D2, Husky, and Racecar. None was executed before protocol freeze.
As before, 18 adaptive/frozen pairs receive exactly 45 matched calibration
actions and then 195 goal-directed actions, with all probe cost included.
Eighteen healthy arms establish controllability.

The previous gates remain. V3 adds two refusal gates:

- at least one contextual coefficient must become nonzero in every learned
  adaptive and frozen model set; and
- median paired advantage must be positive separately for every morphology.

Consequently, a strong Husky result cannot conceal another R2-D2 failure.
