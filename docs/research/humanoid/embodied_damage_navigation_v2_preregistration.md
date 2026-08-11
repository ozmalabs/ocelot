# Hidden-damage navigation v2 preregistration

Status: frozen before execution.

V1 failed its effect-size gate and independently exposed an effect-order defect
in the intended one-cycle active-recalibration latch. V2 tests the corrected
latch on six new, unexecuted dynamics/fault/goal combinations. No learning
rate, success threshold, horizon, body, metric, or arm has been changed after
v1. The new machine-readable protocol is
`protocols/embodied_damage_navigation_v2.json`.

The experiment again contains 18 adaptive/frozen pairs plus 18 healthy
references. Calibration lasts 45 actions and navigation ends at action 240.
The primary metric includes all active-probe cost. The claim passes only if
all seven gates embedded in the protocol pass, including at least 10 adaptive
wins, pooled median paired advantage of at least `0.05`, and positive median
adaptive progress in every body.

In addition, the correction is considered mechanically realized only if no
adaptive run records more than one `opened_recalibration` event or more than
nine `change_recalibration` actions. These counts will be reported even though
they are an implementation audit rather than a post-hoc addition to the
primary claim gates.
