# Attitude–trajectory generalization

The precision-driving work contained a reusable capability that was obscured
by circle-specific language: body attitude does not have to equal trajectory
direction.  A controlled drift is one instance.  A jet yawing while inertial
momentum continues forward is another.

This upgrade represents three quantities independently in the graph:

1. inertial trajectory or path tangent;
2. body attitude relative to that trajectory;
3. previewed future geometry and explicit clip commitments.

Python only transduces sensors, applies graph commands, and aggregates exact
receipts.  The graph computes targets, phase, velocity/attitude tradeoffs,
curvature-envelope braking, preview synthesis, clip selection, and actuator
commands.

## Jet pirouette

`vectoring_jet_world.py` is a planar thrust-vectoring research plant with an
unwrapped yaw state and a drag model defined for airflow from any body
direction.  This matters: the existing conventional fixed-wing plant is a
small-angle wing model and cannot honestly represent sustained backwards
airflow at 180 degrees of sideslip.

The graph commands a complete 360-degree body-yaw excursion while separately
holding an 80 m/s inertial velocity target.  Momentum covers the instant in
which axial thrust points backwards; lateral vectoring carries most of the
trajectory correction through the quarter-turn attitudes.

The reference run completed `1.0000009` turns, held the inertial velocity
heading within `0.69 degrees`, kept forward velocity above `75.49 m/s`, and
settled at `79.65 m/s`.  This demonstrates control decomposition in the
declared plant.  It is not a claim that an ordinary fixed-wing aircraft can
fly backwards or a certification of a real thrust-vectoring airframe.

## Gymkhana geometry

`gymkhana_driving_world.py` replaces a constant-radius target with a Gerono
figure eight plus a fifth-harmonic slalom.  Curvature repeatedly changes
magnitude and sign, including two tight reversals.  The same precision graph
now consumes generic path receipts:

- signed lateral path error and tangent-heading error;
- near, middle, and far body-relative preview bearings;
- current and preview curvature;
- normalized path phase, path length, and explicit clip zones.

The graph derives yaw-rate, slip, and speed targets from curvature.  It brakes
from the future curvature envelope, not after reaching a corner, and combines
steering with independently allocated wheel drive/braking.

The matched 55-second benchmark compares a local-tangent controller with the
same graph given preview and clip authority.  The preview architecture
completes the figure eight.  See
`results/attitude_trajectory_geometry_v1.json` for full traces and exact
matched deltas.

## Reproduction

```bash
python scripts/gen_attitude_trajectory_seed.py
python scripts/gen_precision_driving_seed.py
python scripts/benchmark_attitude_trajectory_geometry.py
pytest -q tests/test_attitude_trajectory_geometry_migrated.py
```
