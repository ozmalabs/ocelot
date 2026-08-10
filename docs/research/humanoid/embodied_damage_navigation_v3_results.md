# Contextual damage navigation v3 results

The requested body-history fix worked, but the preregistered general primary
claim still **did not pass**.

The executed protocol SHA-256 was
`504b816cc9a74fd745fb552bf967ea379d594ae516ddbd7e2354dde264cf0f02`.
All 54 runs completed in 40.59 seconds. Calibration trajectories and contextual
coefficients matched exactly between adaptive and frozen pairs. Every
adaptive damaged graph updated after the hidden change, no frozen model did,
and all nine contextual models were non-vacuous in every learned arm.

Adaptive navigation won 12 of 18 comparisons. Median paired advantage was
positive separately for R2-D2, Husky, and Racecar, passing the new
anti-masking gate. Pooled median advantage was `0.026663`, however, below the
unchanged `0.05` refusal threshold.

| Body | Adaptive median progress | Frozen median progress | Median paired advantage | Adaptive wins |
|---|---:|---:|---:|---:|
| R2-D2 | 0.2107 | 0.0765 | 0.0107 | 3/6 |
| Husky | 0.8091 | -0.0217 | 0.3466 | 6/6 |
| Racecar | 0.5414 | 0.6698 | 0.0102 | 3/6 |

R2-D2's held-out median paired advantage therefore changed from v2's
`-0.0554` to v3's `+0.0107`; its adaptive median progress also exceeded its
frozen median progress by `0.1342`. This resolves the identified systematic
negative transfer at the aggregate body level, but not every case: two R2-D2
faults still had large negative paired effects.

Across all bodies, adaptive median progress was `0.4378`, versus `0.2555`
frozen. Adaptive runs reached the goal in 6 of 18 cases, frozen runs in 5 of
18, and healthy references in 14 of 18. Adaptive graphs spent 117 of 3,510
post-change actions on bounded recalibration.

## What remains

One-transition context captures momentum well enough to remove the
morphology-wide R2-D2 deficit, but action-local online updates can still
replace a useful calibrated model after an isolated surprising receipt. A
post-result experiment that scaled fast learning by a simple error ratio made
R2-D2 worse on the now-development v3 cases, so that mechanism was rejected
and is not in the engine.

A defensible next step is not another rate adjustment. It is graph-held
candidate-model validation: learn a provisional changed-dynamics hypothesis,
compare its subsequent prediction receipts against the consolidated model,
and promote it only after repeated evidence. That would add biological
metaplasticity and protect useful priors without suppressing genuine damage
adaptation.

Machine-readable result:
`results/embodied_damage_navigation_v3.json`.
