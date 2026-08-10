# Individual-wheel and differential race control

The racing cortex now publishes independent drive and brake commands for the
front-left, front-right, rear-left, and rear-right wheels. The physical plant
applies each command against that wheel's load-sensitive friction budget and
adds the resulting left/right force difference to the body yaw moment. Brake
temperature and longitudinal tyre wear are also accumulated per wheel.

This remains graph-native. Python selects only the named experimental
condition, copies observations and commands, and reports receipts. In the
standard condition the graph emits symmetric left/right commands. In the
differential condition the same System 1 collapse composes a yaw request with
the steering, speed, stability, active-aero, gear, and Pareto strategy outputs.
Positive yaw is produced by greater right-side drive or greater left-side
braking; negative yaw mirrors the allocation. Global brake priority guarantees
that no wheel is driven and braked simultaneously.

## Matched comparison

The clean-track diagnostic isolates vehicle control:

| 120-second condition | Progress | Off-track | Fuel |
|---|---:|---:|---:|
| Standard | 2,402.93 m | 5.716 s | 0.6770 L |
| Differential | 2,405.88 m | 5.476 s | 0.6807 L |
| Differential minus standard | +2.95 m | -0.240 s | +0.0036 L |

Torque vectoring therefore bought a small line-holding improvement at a small
energy and tyre cost when the car was otherwise undisturbed.

The primary comparison used five paired 120-second runs with three seeded
traffic vehicles. Traffic makes the seeds materially different:

| Mean condition | Progress | Off-track | Fuel | Contacts |
|---|---:|---:|---:|---:|
| Standard | 2,378.62 m | 5.792 s | 0.6854 L | 2.0 |
| Differential | 2,377.95 m | 5.778 s | 0.6813 L | 2.0 |
| Differential minus standard | -0.67 m | -0.014 s | -0.0040 L | 0.0 |

That is effectively neutral: vectoring slightly reduced excursion and fuel,
but did not improve progress or contact avoidance in traffic. The result
locates the current ceiling in racecraft and in the fixed vectoring gain rather
than actuator authority. The next useful change is to make vectoring authority
itself a learned Pareto variable and learn separate wheel effectiveness from
the exact per-wheel force receipts.

## Speed Dreams boundary

Speed Dreams 2.4.2 exposes four independent brake commands but only one engine
accelerator in its robot ABI. Protocol v2 therefore applies graph-authored
per-wheel braking directly, scaled by the car's physical front/rear brake
repartition, while preserving aggregate drive. The deterministic plant is the
current full individual-wheel-drive comparison; true per-wheel drive in Speed
Dreams would require a simulator drivetrain API change rather than hiding a
policy in the bridge.

The 20-second official-simulator smoke was correspondingly worse for the
differential condition: 274.73 m versus 281.07 m and 0.168 L versus 0.140 L.
That is useful negative evidence—the brake-only approximation is not a
substitute for true torque vectoring.

## Reproduce

```bash
python scripts/benchmark_racing_control_architectures.py \
  --duration-s 120 \
  --seed-count 5 \
  --opponents 3 \
  --output results/racing_differential_control_v1.json

pytest -q tests/test_full_racing_migrated.py
```
