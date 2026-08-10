# HUMANOID SUCCESSIVE-LIFETIME IMPROVEMENT — preregistration

## Question

Does repeated walking make the graph-controlled humanoid behaviorally better,
or does the substrate merely accumulate motor-memory counters?

The existing result proves canonical receipt accumulation, persistence by body
shape, and safe reconsolidation. It does **not** prove an improving policy.
This experiment separates those claims.

## Frozen comparison

Run four paired lifetimes on the deterministic PyBullet humanoid:

- **accumulating** — every lifetime is a fresh Rust graph and fresh body, but
  it mechanically restores the motor library written by the preceding
  accumulating lifetime;
- **fresh control** — every lifetime is a fresh Rust graph and fresh body with
  no restored library.

Both arms use the same `humanoid_walking_v1` body, seed, calibration,
directed-walk objective, action budget, and mid-stride perturbation. The first
accumulating lifetime is necessarily cold and must match the first fresh
control. Four lifetimes distinguish cold acquisition, first transfer,
continued improvement, and saturation/forgetting without claiming that four
is a controller constant.

Only graph-minted `shape --stores_humanoid_motor_program--> program` facts
cross an accumulating lifetime boundary. Python may serialize, restore, run
the declared arms, and calculate report statistics. It may not rank programs,
map actuators, change eligibility, or choose actions.

## Primary behavioral discriminator

The deterministic paired differences are evaluated without an epsilon:

1. final accumulated lifetime directed progress must be greater than its
   matched fresh control;
2. the mean progress of accumulated lifetimes 3–4 must be greater than the
   mean of accumulated lifetimes 1–2;
3. no accumulated lifetime may fall when its matched fresh control does not;
4. final absolute lateral drift must not exceed the matched fresh control.

All four are required for **CONFIRM**. Higher memory experience, more
structural reuse, or more recalls without this behavioral result is
**DEGRADE**. Any new fall or worse final lateral drift is **FALSIFY**.

The fresh-control curve must be identical across lifetimes. If it is not, the
world is not deterministic enough for exact paired comparison and the result
must be rerun with repeated-seed statistics rather than interpreted.

## Secondary mechanistic witnesses

These diagnose, but cannot rescue, the primary result:

- held body shape recognized after lifetime 1;
- restored eligible programs completely rebound to current opaque phase
  models;
- at least one imported structure freshly reconsolidated;
- maximum canonical experience increases across accumulated lifetimes;
- direct recall, compound-action count, response cadence, support
  alternations, and aerial samples are reported per lifetime.

## Learning-curve intervention rule

Run the frozen comparison before changing policy.

- If it **CONFIRMS**, retain the mechanism and then test changed disturbance
  conditions separately.
- If it **DEGRADES** with a flat behavioral curve, identify where accumulated
  knowledge remains output-null or fails to alter analysis by synthesis.
  Make the smallest graph-native change that lets verified knowledge change
  action while preserving the fresh-receipt safety gate, then rerun the same
  frozen comparison.
- If it **FALSIFIES**, fix safety before optimizing progress.

No acceptance criterion may be weakened after seeing results. Intermediate
failed designs and their measurements remain in the results write-up.

