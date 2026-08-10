# Checkpointed damage adaptation v4 results

The preregistered primary claim **passed**.

The executed protocol SHA-256 was
`a7cc9dcbe6d8a7576547e19ea406c5fa878716482408a7416a73de94a9f68f7e`.
All 54 runs completed in 40.43 seconds. Adaptive/frozen calibration
trajectories and contextual coefficients matched exactly. Adaptive models
updated after the hidden change, frozen models did not, and every contextual
model set was non-vacuous.

Adaptive checkpointed plasticity won 12 of 18 paired comparisons. Its pooled
median advantage was `0.186992`, exceeding the fixed `0.05` gate. Median
paired advantage was positive separately in all three bodies.

| Body | Adaptive median progress | Frozen median progress | Median paired advantage | Adaptive wins |
|---|---:|---:|---:|---:|
| R2-D2 | 0.1928 | 0.1782 | 0.0734 | 3/6 |
| Husky | 0.9647 | 0.1862 | 0.5692 | 6/6 |
| Racecar | 0.0122 | 0.0009 | 0.0723 | 3/6 |

The graph opened 124 one-shot checkpoints, validated 64 changed models, and
rolled back 18 updates whose stable checkpoints had at least a five-percent
prequential error advantage. Every rollback receipt met the declared
two-observation and error-margin requirements. Recalibration remained bounded
to at most one nine-action cycle per adaptive run.

Across bodies, median normalized progress was `0.3082` adaptive versus
`0.0517` frozen. Adaptive runs reached the goal in 4 of 18 cases, frozen runs
in 1 of 18, and healthy references in 15 of 18.

## Interpretation and limit

This supports a narrow causal claim: after matched from-scratch calibration,
receipt-validated graph plasticity improves damage navigation over freezing
the same graph under this preregistered randomized matrix. The result includes
probing cost and cannot be attributed to different pre-change experience.

It does not establish robust navigation after damage. Six pairs still favored
the frozen model, Racecar's absolute median progress remained small, and the
large gap to healthy references shows substantial unrecovered capability.
Checkpointing protects against some harmful updates; it does not yet solve
long-horizon planning, observability, or complete body-model reconstruction.

Machine-readable result:
`results/embodied_damage_navigation_v4.json`.
