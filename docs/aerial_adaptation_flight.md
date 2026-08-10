# Graph-native aerial adaptation

Jabberwock now flies an official Crazyflie 2.x model in
[`gym-pybullet-drones`](https://github.com/learnsyslab/gym-pybullet-drones).
The external simulator is pinned at commit
`e712698a05a80728b06572819dcf044596707754`.

## Boundary

The simulator provides six-degree-of-freedom rigid-body dynamics and the
vehicle's low-level stabilized velocity controller. That is the aerial
equivalent of the low-level wheel velocity and steering controllers used by
the existing ground-body simulator.

The adapter exposes seven stable opaque tokens. Only the adapter knows how
those tokens connect to the low-level controller. The fresh graph must infer
their spatial consequences from raw pre/post pose receipts.

For asymmetric propeller experiments, the body exposes two additional opaque
yaw-rate actuators. Their meaning is not labelled in the graph: it learns
their linear and angular consequences through the same motor-babbling process.

The `aerial_adaptation` seed owns:

- systematic motor babbling over the opaque alphabet;
- learned three-dimensional displacement and resulting-velocity models for
  every token;
- learned angular-velocity-change models and angular stability control when
  the body has yaw authority;
- model-based selection by predicted spatial residual;
- prediction-error baselines and surprise-triggered fast plasticity;
- takeoff and peak-altitude assessment;
- goal-region assessment; and
- selection of the empirically quietest action once inside the goal region.

Python creates the world, mirrors raw measurements, enacts the graph-authored
token, and records the graph's verdict. It does not calculate a reward or
select an action.

## Demonstration

The default fresh run starts at `(0, 0, 0.25)` and targets
`(0.75, 0.75, 1.0)`. With two samples of each of seven opaque commands:

- calibration used 14 graph-authored interventions;
- the graph classified takeoff from its own altitude history;
- final position was `(0.640, 0.718, 0.911)`;
- final three-dimensional goal distance was `0.145 m`;
- the graph judged the goal reached; and
- it selected the learned quiet action and stayed in the goal region for the
  final 51 actions.

Three additional targets in the other horizontal quadrants were reached with
final distances of `0.142 m`, `0.134 m`, and `0.108 m`.

## Hidden damage in flight

`AerialMechanicalCondition` applies rotor-speed loss after the official
velocity controller has calculated motor RPM. The damaged RPM reaches the
rigid-body simulation, while the observation returned to Jabberwock contains
no condition name, onset, retention value, or damage flag. The only evidence
available to the graph is that an opaque action stops producing its predicted
motion.

The development protocol
`protocols/aerial_damage_in_flight_v1.json` compares two initially identical
graphs. Both receive two healthy samples of every opaque actuator. Immediately
after that calibration completes, motor 1 retains 92% of requested RPM:

- the adaptive and frozen pre-damage action and position traces are identical;
- both vehicles remain airborne and have zero contact actions;
- the adaptive graph detects 22 command-model surprise events and updates its
  velocity/consequence models;
- the adaptive vehicle finishes within the graph's goal radius at `0.191 m`;
- the frozen-model control finishes at `0.539 m`; and
- adaptation reduces final distance by `0.348 m`.

This is a deterministic development demonstration for one rotor, damage level,
goal, and simulator seed—not yet a preregistered claim across the full damage
envelope. The frozen condition isolates online graph plasticity: simulator,
initial graph, motor babble, goal, seed, and hidden physical failure are held
constant.

## Broken propeller

The broken-propeller condition does not directly attenuate commanded motor
RPM. Instead, the simulator applies independent thrust and reaction-torque
effectiveness to each propeller inside its force model. This represents
averaged partial-blade damage; it is not a blade-resolved CFD or vibration
model.

In `protocols/aerial_broken_prop_v1.json`, the vehicle flies normally until
action 40. Propeller 1 then retains 87% of nominal thrust effectiveness and 74%
of nominal reaction torque. The condition is not named or measured in graph
state. Jabberwock must infer the changed body from pose, linear velocity, and
angular velocity prediction errors:

- adaptive and frozen traces are identical through the first 40 actions;
- the adaptive graph records 17 surprise events and revises its learned
  linear/angular action consequences;
- both vehicles remain airborne with no contact actions;
- adaptive mean angular speed is `0.484 rad/s`, versus `0.657 rad/s` with
  frozen models;
- the adaptive vehicle finishes inside the goal radius at `0.189 m`;
- the frozen vehicle finishes at `1.026 m`; and
- online adaptation reduces final goal distance by `0.837 m`.

The yaw actuators are part of the body plan rather than a propeller-specific
recovery rule. They are opaque, are babbled before the break, and are selected
by the same graph-native residual minimisation used for every other actuator.
As with the motor-loss run, this is a deterministic development demonstration,
not yet a population-level claim across break locations and severities.

## Complete propeller loss through the stabilized interface

`protocols/aerial_complete_prop_failure_v1.json` sets both thrust and reaction
torque effectiveness of propeller 1 to zero at action 70. Immediately before
failure the vehicle is in established flight at `(0.731, 0.520, 0.887)`.

The stabilized velocity interface cannot recover:

- the adaptive graph detects six post-failure surprise events;
- angular speed nevertheless exceeds `37 rad/s`;
- adaptive and frozen vehicles both first contact the ground at action 72,
  `0.75 s` after the failure begins; and
- neither reaches the goal.

This is not a detection failure. Four oracle replay controls bypass graph
choice and force hover, climb, positive yaw, or negative yaw from the first
failed action. Every available response still contacts the ground after
`0.75 s`. The forced climb control requests the simulator maximum of
`21,666 RPM` from every motor, but one request now produces no force.

The boundary in this arm is control authority. The stock four-rotor velocity
PID saturates without reallocating thrust around the missing propeller, and
the opaque stabilized interface can request translation or yaw but cannot
directly command the three surviving motors into a spinning three-rotor
equilibrium. Faster surprise detection alone cannot solve that interface.

## Direct three-rotor recovery

`protocols/aerial_three_rotor_direct_recovery_v1.json` gives the graph explicit
raw-RPM authority while keeping it disabled during ordinary stabilized flight.
The pre-failure action alphabet, selected actions, and trajectory therefore
match the failed stabilized run. The new authority is not a Python fallback:

- the graph detects emergency angular motion and infers the failed motor from
  the measured rotational signature;
- simulator body mass, arm length, thrust coefficient, RPM limit, and gravity
  are mirrored as graph-held body properties;
- a seeded Rust-evaluated rule reconstructs attitude from the measured
  quaternion, forms a reduced-attitude target, relaxes yaw, allocates force
  around the missing motor, and authors four continuous RPM values; and
- Python only transfers sensor values and enacts those graph-authored RPMs.

Ordinary velocity control remains at the simulator's inherited 60 Hz cadence.
Once complete loss begins, the adapter switches the raw-motor and graph loop to
the simulator's 240 Hz physics cadence. The graph waits for two samples so the
initial transient cannot identify the wrong rotor, giving a measured detection
latency of `8.33 ms`.

For complete loss of propeller 1 at action 70:

- the pre-failure vehicle is at `(0.731, 0.520, 0.887)`, exactly matching the
  stabilized failure protocol;
- the graph identifies motor 1 and emits 3,600 consecutive direct commands;
- it remains airborne for the full 15-second observation with no contact;
- minimum altitude is `0.887 m` and maximum altitude is `1.376 m`; and
- final error from the position latched at detection is `0.0017 m`.

Angular speed peaks at `87.5 rad/s`. This is expected degraded-mode behavior:
with one rotor absent, yaw is deliberately uncontrolled and the body settles
into a fast-spinning equilibrium while preserving thrust direction and
position. The demonstration currently implements allocation for diagnosed
motor 1; it is not yet evidence for arbitrary motor locations or unmodelled
airframe damage.

### Controller response floor

The 240 Hz figure is a simulator limit, not Jabberwock's compute limit. A
10,000-cycle warm benchmark on an AMD Ryzen 5 9600X measured:

| Path | Median | p99 | Median throughput |
|---|---:|---:|---:|
| active Rust graph control cycle | `155.6 µs` | `192.7 µs` | `6.43 kHz` |
| sensor attributes through Python/Rust to four RPM values | `167.3 µs` | `211.9 µs` | `5.98 kHz` |
| above plus one PyBullet physics step | about `196.7 µs` | — | about `5.08 kHz` |

Thus the current sensor-to-command computation floor is about `0.17 ms`.
The observed `8.33 ms` response is evidence acquisition at 240 Hz, not
controller execution. At a real 1 kHz sensor cadence, the same two-sample
detector would respond in roughly `2.17 ms`, assuming comparable host and
transport latency. Reproduce the controller-only measurements with
`scripts/benchmark_aerial_direct_controller.py`.

Run:

```bash
uv pip install --python /path/to/.venv/bin/python -r requirements-drone.txt
/path/to/.venv/bin/python scripts/gen_aerial_adaptation_seed.py
/path/to/.venv/bin/python scripts/jabberwock_aerial_adaptation.py \
  --json-out results/aerial_adaptation_flight_v1.json
/path/to/.venv/bin/python scripts/jabberwock_aerial_damage_trial.py \
  --json-out results/aerial_damage_in_flight_v1.json
/path/to/.venv/bin/python scripts/jabberwock_aerial_damage_trial.py \
  --protocol protocols/aerial_broken_prop_v1.json \
  --json-out results/aerial_broken_prop_v1.json
/path/to/.venv/bin/python scripts/jabberwock_aerial_damage_trial.py \
  --protocol protocols/aerial_complete_prop_failure_v1.json \
  --json-out results/aerial_complete_prop_failure_v1.json
/path/to/.venv/bin/python scripts/jabberwock_aerial_direct_recovery.py \
  --json-out results/aerial_three_rotor_direct_recovery_v1.json
```
