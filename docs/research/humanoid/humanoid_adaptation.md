# Graph-native humanoid balance adaptation

This development experiment connects Jabberwock to PyBullet's full
`mjcf/humanoid.xml` body: 21 independently actuated revolute joints spanning
the torso, legs, and arms. It does not load PyBullet's motion clips, pretrained
policies, joint names, or a humanoid gait controller.

## Boundary

The mechanical body provides a low-level tonic position servo around the
initial observed posture. It exposes 43 stable commands:

- one declared tonic-default command; and
- positive and negative position twitches for each of 21 dynamically
  discovered revolute joints.

The 42 twitch tokens carry no anatomical or directional names. Python knows
their joint wiring, advances physics, applies the declared perturbation, and
copies raw quaternion, angular velocity, height, joint, and contact receipts.
It does not select a twitch, calculate the controller's balance error, or
update an action model. The runner independently repeats the final height and
tilt calculations only as a test oracle; the graph's own assessments must
match them.

The `humanoid_adaptation` seed owns:

- systematic motor babbling across every non-tonic opaque actuator;
- receipt-backed learning of each twitch's effect on the body's vertical axis
  and angular velocity;
- a local balance prediction for every learned twitch;
- selection by a Rust-evaluated graph `Argmin`; and
- body-axis tilt, minimum height, peak tilt, and upright assessment.

The prediction horizon is not a tuned controller duration. The graph derives
the body's gravitational fall timescale as `sqrt(standing_height / gravity)`,
projects current angular velocity through that interval, adds each learned
twitch consequence, and minimizes predicted departure of the body vertical
axis.

## Paired result

`protocols/humanoid_balance_adaptation_v1.json` gives two fresh graphs and
physical bodies an identical 42-action calibration, tonic settling history,
and one-frame centre-of-mass force of `(9.0, 2.25, 0)` body weights. The
runner derives Newtons from the loaded body's mass and declared gravity rather
than embedding an asset-specific force. Their pre-perturbation and
post-perturbation trajectories are exactly identical.

The graph derives a 12-frame nominal body horizon from morphology and gravity,
then contracts balance responses to two frames (120 Hz) using the
sensor-derived confirmation horizon. Both paired arms receive that same
two-frame cadence. Over the following 360 control actions:

| Measure | Learned graph | Tonic posture control |
|---|---:|---:|
| Minimum base height | `1.205 m` | `0.060 m` |
| Peak body-axis tilt | `0.040` | `1.000` |
| Integrated tilt | `0.076` | `1.346` |
| First fall action | none | `236` |
| Final graph upright assessment | yes | no |
| Distinct recovery actuators | `35` | `1` |

The learned graph finishes at `1.205 m` base height with body-axis tilt
`0.028`. Every non-tonic actuator model contains exactly one verified
experience; no pretrained gait or body-specific action table is present.

This establishes a narrow result: local, from-scratch balance adaptation on a
high-dimensional humanoid body. It does not establish walking, contact-aware
stepping, recovery after foot slip, arbitrary impulses, hardware transfer, or
population-level robustness. The tonic servo is an innate low-level posture
reflex analogous to a joint drive; Jabberwock learns and selects the active
corrections above it.

Run:

```bash
/path/to/.venv/bin/python scripts/gen_humanoid_adaptation_seed.py
/path/to/.venv/bin/python scripts/jabberwock_humanoid_adaptation.py \
  --json-out results/humanoid_balance_adaptation_v1.json
/path/to/.venv/bin/python -m pytest \
  tests/test_humanoid_adaptation_migrated.py -q
```
