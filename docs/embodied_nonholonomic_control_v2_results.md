# Nonholonomic control v2 results

The stronger preregistered Racecar comparison **did not pass**.

The executed protocol SHA-256 was
`88fa225dd4f0fa71672fc0250b2a474c5882a42eb64d31bbc51af2b7fc924da5`.
All 54 runs completed. Enhanced and legacy arms had exact pre-change
trajectories, both adapted after damage, the enhanced graph exercised heading
escape, and the legacy graph did not.

Racecar's enhanced median normalized progress was `0.6236`, versus `0.6075`
for the matched legacy controller. It won 3 of 6 pairs and had median paired
advantage `0.0254`, below the fixed 4-of-6 and `0.05` gates.

| Body | Enhanced median progress | Legacy median progress | Median paired advantage | Enhanced wins |
|---|---:|---:|---:|---:|
| R2-D2 | 0.1742 | 0.0995 | -0.0132 | 2/6 |
| Husky | 0.9534 | 0.9218 | 0.0391 | 6/6 |
| Racecar | 0.6236 | 0.6075 | 0.0254 | 3/6 |

## Interpretation

The controller is behaviorally useful but not a reliable universal
improvement over the legacy controller. On Racecar it materially helped three
cases (`+0.1662`, `+0.0945`, and `+0.0927`) and hurt three (`-0.1724`,
`-0.0826`, and `-0.0419`). Absolute Racecar navigation on this off-axis
matrix was strong, but the matched ablation shows that much of that capability
already came from the learned distance controller.

The negative cases identify the remaining mechanism gap: heading escape is a
reactive one-action regime. It does not yet learn and validate a temporally
extended steering sequence, nor can it retain the best point on a trajectory.
A development-only backslide-hold prototype was rejected because the current
one-transition model could not reliably infer a braking action under momentum.
It is not present in version 1.5.1.

The defensible claim is therefore narrower: the new graph-native regime
removes specific wait-now/move-next local minima and substantially improves
some damaged Racecar trajectories, without a morphology name or actuator
table. Reliable Racecar superiority will require learned multi-action motor
chunks rather than another scalar heading-weight change.
