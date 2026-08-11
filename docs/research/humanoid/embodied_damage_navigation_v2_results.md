# Hidden-damage navigation v2 results

The corrected preregistered primary claim **did not pass**.

The executed protocol SHA-256 was
`fe7f171a05b74a76caabb7af7a689a9760f27e3225cc8fcd7ed4c9c96d421990`.
All 54 runs completed. Every adaptive/frozen calibration trajectory matched
exactly, all adaptive damaged graphs updated after the hidden change, and no
frozen graph did. Adaptive navigation won exactly 10 of 18 pairs. The pooled
median paired advantage was `0.039420`, below the fixed `0.05` threshold.

The recalibration correction worked as designed: no adaptive run opened more
than one cycle or spent more than nine actions probing, and no frozen run
opened a cycle. Fifteen of 18 damaged adaptive runs detected enough surprise
to open a cycle. Thus v2's failure cannot be attributed to the v1 runaway
probe defect.

## Body-level outcome

| Body | Adaptive median progress | Frozen median progress | Median paired advantage | Adaptive wins |
|---|---:|---:|---:|---:|
| R2-D2 | 0.1703 | 0.1556 | -0.0554 | 2/6 |
| Husky | 0.8683 | 0.1407 | 0.3018 | 4/6 |
| Racecar | 0.6471 | 0.5725 | 0.0826 | 4/6 |

Across all bodies, adaptive median progress was `0.5390`, versus `0.3537`
frozen. Adaptive runs reached the goal in 7 of 18 cases, frozen runs in 5 of
18, and healthy randomized-dynamics references in 14 of 18. These secondary
statistics are encouraging but do not override the failed primary gate.

The remaining limitation is morphology-dependent control credit assignment.
The same scalar, action-local forward model adapts well enough for Husky,
usually helps Racecar, but cannot reliably distinguish altered actuator
authority from the coupled momentum and turning dynamics of R2-D2. A next
version should learn short action-history state and uncertainty-conditioned
model context in the graph, then be evaluated on another unseen matrix.

Machine-readable result:
`results/embodied_damage_navigation_v2.json`.
