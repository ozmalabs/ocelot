# Graph-native precision driving

The racing cortex can now use independent wheel drive and braking for
deliberate body-attitude control. Four graph-authored manoeuvres are included:

- left and right controlled drifts around a 34 m reference circle;
- left and right donuts around an 8.5 m reference circle.

Python declares the course, transduces exact plant receipts, and reports
metrics. The graph owns launch, attitude acquisition, hold, exit, target slip,
target yaw rate, target speed, steering, and all eight wheel commands.

## Attitude is a trade-off, not a fault

There is no stability/fault switch. Body slip, yaw-rate error, radial path
error, speed, actuator energy, tyre temperature, and tyre wear remain ordinary
costs and affordances.

During the hold phase, radial error raises a continuous path-pressure value.
That pressure moves the controller along the attitude/path trade-off surface:
near the reference circle it spends authority on the requested body angle; as
radial error grows it spends more on path recovery. The selected pressure is
published as `path_tradeoff_weight` in every trace.

The plant now exposes exact near/middle/far course geometry as body-frame
bearing and heading receipts. It does not turn those receipts into commands.
The graph composes those preview horizons with current attitude and stores
clipping zones as `PrecisionClipZone` nodes. It selects the nearest zone ahead,
ramps a distance-dependent commitment, and synthesizes its steering, torque
vectoring, and individual-wheel braking contribution into the same action
sheet. Setting `preview_authority` to zero provides the matched radial-only
control condition without changing the plant.

The manoeuvre graph also learns yaw and slip response from exact action
receipts. Learning is gated to meaningful-speed manoeuvre phases so low-speed
angle wrapping cannot contaminate the learned response.

## Physical model

The ordinary race-car plant remains unchanged by default. Precision driving
selects an explicit stunt-car body plan:

- rear-biased high-output drive;
- stronger independent brakes;
- lower rear tyre grip than front tyre grip;
- smooth brush-tyre lateral saturation;
- reciprocal combined-slip coupling through the friction envelope;
- 500 Hz physics and 100 Hz graph control.

These parameters create a controllable breakaway region. Earlier hard
friction-circle saturation produced an attached/spun discontinuity that could
not support meaningful angle regulation.

## Measured result

The deterministic 35 s protocol runs all four manoeuvres:

| Manoeuvre | Complete | Hold | Mean angle error | Within ±5° | Mean radial error | Within 2 m | Clip hit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Drift left | yes | 5.00 s | 2.05° | 100% | 0.55 m | 93.4% | 73.6% |
| Drift right | yes | 5.00 s | 2.05° | 100% | 0.55 m | 93.4% | 73.6% |
| Donut left | yes | 6.77 s | 0.86° | 100% | 1.82 m | 48.2% | 36.1% |
| Donut right | yes | 6.77 s | 0.86° | 100% | 1.82 m | 48.2% | 36.1% |

Compared with the identical radial-only graph condition:

- drift radial error falls from 6.80 m to 0.55 m, a 92% reduction;
- drift time inside the strict 2 m band rises from 9.6% to 93.4%;
- donut radial error falls from 2.59 m to 1.82 m;
- preview improves drift angle error from 2.77° to 2.05° while preserving
  100% of donut samples inside the ±5° attitude band.

Left/right metric differences are below `2e-12`. Graph tick p99 is below
0.41 ms across both architectures in the recorded run.

The next path ceiling is generalization beyond circular skid-pad geometry:
multi-apex, changing-curvature trajectories and obstacle-defined clipping
zones should use the same graph preview and commitment machinery without new
control functions.

## Reproduce

```bash
python scripts/gen_precision_driving_seed.py
python scripts/benchmark_precision_driving.py \
  --output results/precision_driving_v1.json
pytest -q tests/test_precision_driving_migrated.py
```

The machine-readable experiment definition is
`protocols/precision_driving_v1.json`; compact receipts are in
`results/precision_driving_v1.json`.
