# Graph-native full racing

This upgrade moves the embodied benchmark from a small racecar body on an open
plane to an actual race: a closed 1.053 km circuit, coupled tyre and vehicle
dynamics, wet sectors, traffic, collisions, thermal state, wear, fuel,
active aerodynamics, off-track recovery, and hidden compound damage.

The architectural boundary remains strict. `domains/full_racing_world.py`
integrates physics and returns telemetry. `scripts/jabberwock_full_racing.py`
copies that telemetry into the graph and copies the graph's simultaneous
command families back to the plant, including four drive and four brake
channels. The host does not contain a target-speed formula,
racing line, opponent policy, recovery controller, damage classifier, or
adaptation update.

## What the graph does

`racing_cognition` adds two coupled timescales:

- The hard-realtime System 1 sheet reconstructs a speed envelope from tyre
  state, surface grip, thermal retention, track-curvature envelopes, traffic,
  slip, and model surprise. In the same collapse it composes steering,
  throttle, brake, front and rear aero, and gear.
- The soft-realtime sensorimotor sheet updates steering response, grip evidence,
  and prediction surprise from exact post-action receipts. Loss of authority
  changes the next hard-realtime collapse; Python does not switch controllers.
- A slower System 2 strategy sheet maintains an explicit non-dominated set
  across pace, fuel cost, tyre cost, contact risk, and passing aggression.
  Fuel-to-finish, projected tyre reserve, tyre temperature, damage, model
  surprise, slip, race distance remaining, and passing opportunity move the
  aspiration point and objective pressure. The selected point changes System
  1's speed, tyre-utilisation, throttle, aero, and passing envelope.

Pitting is treated as a feasibility intervention, not just another weighted
preference. If learned fuel-per-metre predicts a finish shortfall, or learned
wear predicts that the tyre reserve will be crossed, System 2 commits a pit
request and System 1 respects the pit-lane speed envelope. The plant models pit
entry, a timed service, refuelling, tyres, and partial repair. Thus conserving,
attacking, and pitting are consequences of the same changing graph state rather
than host-selected modes.

Each Pareto point also carries a service threshold. A conservative point accepts
the fixed time cost of a stop at lower projected resource or repair pressure;
an attack point tolerates more degradation. Hard fuel/tyre infeasibility still
overrides that preference. Thermal pressure changes pace and tyre utilisation,
but does not itself request a stop—cold tyres need warming, not replacing.

The frontier is genuinely multi-dimensional. Besides a monotonic
conserve-to-attack family it contains a fuel-efficient/tyre-expensive point and
a tyre-efficient/fuel-expensive point. A graph `Exists` domination test removes
any candidate that is no better on any objective before aspiration collapse.

The track sensor exposes both signed point curvature and the maximum absolute
curvature in three forward arcs. Point samples alone could miss a short,
tight corner between saccades; the envelopes are the track-relative analogue
of a peripheral hazard signal. Signed near curvature still supplies the
detailed foveal steering target.

## Plant scope

The deterministic backend uses:

- a dynamic bicycle body with body-frame longitudinal/lateral velocity and yaw;
- axle cornering stiffness with load- and health-limited tyre forces;
- a combined longitudinal/lateral friction ellipse;
- longitudinal load transfer and speed-dependent drag/downforce;
- independent front/rear active-aero commands;
- wet and dry grip, off-track terrain, brake and tyre temperature, tyre wear,
  fuel use, and collision impulses;
- independently degradable steering, power, front/rear braking, aero authority,
  plus an external yaw moment.

It is intentionally more demanding and more inspectable than the earlier
PyBullet racecar demo, but it is not CFD or a suspension multibody solver.

The second backend is the official Speed Dreams 2.4.2 AppImage. A C++ robot
module is deliberately limited to ABI-checked telemetry and actuator packets;
the same `racing_cognition` graph drives the unmodified Jarama circuit and
`sc-cavallo-360`. Speed Dreams tyre temperature is converted from Kelvin at
the boundary, while its remaining tread depth—not its temperature-dependent
instantaneous grip factor—is used as the graph's wear reserve.

## Reproduce

```bash
python scripts/gen_racing_cognition_seed.py
python scripts/jabberwock_full_racing.py \
  --duration-s 120 --opponents 3 \
  --output results/full_racing_baseline_v1.json
python scripts/jabberwock_full_racing.py \
  --duration-s 120 --opponents 3 \
  --damage-onset-s 45 \
  --steering-retention 0.42 \
  --power-retention 0.68 \
  --front-brake-retention 0.45 \
  --aero-retention 0.6 \
  --yaw-bias-nm 420 \
  --output results/full_racing_damage_v1.json
pytest -q tests/test_full_racing_migrated.py

python scripts/jabberwock_full_racing.py \
  --duration-s 20 --opponents 0 \
  --speed-dreams-app-run \
    /home/matt/ozma/internal/simulators/speed-dreams-2.4.2/squashfs-root/AppRun \
  --speed-dreams-local-directory \
    /home/matt/ozma/internal/simulators/speed-dreams-2.4.2/local \
  --output results/speed_dreams_racing_smoke_v1.json
```

## Checked v1 result

Both 120-second scenarios completed two laps. Baseline progress was 2,380.8 m;
the compound-damage run reached 2,374.8 m, or 99.8% retention.
Baseline/damaged off-track time was 5.76/5.84 seconds. Median graph ticks were
about 137–150 microseconds; p99, including the slower Pareto sheet, was
approximately 0.65–0.70 milliseconds on this host after adding the eight wheel
outputs.

That progress retention is evidence of closed-loop robustness. The damaged run
stayed within the same viability envelope despite losing most steering
authority and substantial braking, power, and downforce, while the Pareto sheet
also reduced fuel consumed from 0.687 L to 0.599 L.

Racecraft is the clear v1 ceiling. Both multi-car runs reached the declared
two-contact ceiling. The next cognition increment should retain lane intent
over a horizon, model opponents as trajectories rather than a single nearest
observation, and synthesize pass/abort programs through the shared
analysis-by-synthesis machinery.

The recorded official-simulator smoke ran 20 simulated seconds and advanced
281.1 m from its starting-grid position with no contact or off-track time.
It accelerated to 20.6 m/s on the opening straight and braked for the next
corner. The dynamic strategy moved from tyre-efficient point 7 to conservative
point 1 when transient model/risk pressure peaked, then returned to point 7.
Its learned fuel rate remained live despite Speed Dreams' quantized fuel
telemetry. Median/p99 graph collapse time was 145/654 microseconds after adding
the wheel command sheet; simulator physics and UDP synchronization are outside
that measurement.

Precision-driving extensions, including graph-native controlled drifts,
donuts, body-angle regulation, and dynamic attitude/path trade-offs, are
documented in `docs/precision_driving.md`.
