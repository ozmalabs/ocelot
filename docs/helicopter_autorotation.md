# Graph-native helicopter autorotation

## Result

Jabberwock now lands the simulated traditional helicopter after an
unannounced complete loss of engine torque. The manoeuvre is selected by the
Rust graph from opaque controls. There is no Python flight policy and no
`autorotate`, `flare`, or `lower collective` action.

The plant is a longitudinal energy-accounting research model, not a
certification simulator. It contains the causal mechanisms needed to make the
result meaningful: finite
main-rotor inertia, a freewheel clutch, upward-flow energy recovery,
collective-dependent lift and rotor drag, cyclic disc tilt, fuselage drag, and
ground contact. Once the engine fails, observed shaft energy is zero while
descent can continue adding energy to the rotor.

## What the graph learns

The graph receives ordinary pose, velocity, attitude, rotor-speed, energy, and
contact observations. It never receives an engine-failure flag or the
mechanical vectors behind its opaque action tokens.

Safe reset-bounded interventions establish local causal memories at generic
time-to-contact horizons. Each memory records the state in which an opaque
action was tried and its measured consequences for velocity, attitude rate,
rotor reserve, supplied energy, and recovered energy. At flight time an
`Argmin` Term performs local analysis-by-synthesis over those memories:

1. predict the consequence of each remembered intervention from the present
   state;
2. penalise loss of viable internal energy;
3. penalise contact-relative vertical and horizontal kinetic energy;
4. increasingly penalise attitude error as contact approaches;
5. enact the opaque token with the lowest predicted cost.

The time-to-contact contexts are not helicopter phases. They are generic
surface-approach contexts usable by legs, wheels, wings, rotors, or thrusters.
They replaced a single global action average that incorrectly mixed descent,
flare, and touchdown dynamics.

## Observed behaviour

With 45 reset-bounded interventions (15 opaque controls in each of three
contact-horizon contexts), the graph produced safe touchdowns in all 12
preregistered transfers over:

- initial altitudes of 80, 120, and 160 metres;
- initial forward speeds of 12, 15, 18, and 24 metres per second.

Touchdown vertical speeds were 0.09–0.50 m/s in magnitude, horizontal speeds
were 2.26–6.01 m/s, and rotor speed remained above the preregistered minimum.
The graph and independent world assessments agreed on every landing.

It also succeeded in a small airframe transfer probe covering a heavier
airframe, a lower-inertia rotor, and a lighter airframe: 9/9 safe touchdowns.
These are deterministic mechanism checks, not statistical performance claims.

With preflight causal calibration the graph scored 6/6. With calibration
removed it scored 4/6: the first flight failed, then online graph learning
recovered useful control consequences during later flights. Preflight memory
therefore removes cold-start failures, while the uncalibrated result shows
that the same memory can also be acquired online. No hidden scripted manoeuvre
is needed in either condition.

The successful trajectory has the recognisable energy structure of
autorotation. After torque loss it selects lower-energy control consequences,
holds rotor speed through descent, introduces aft-disc actions as the contact
horizon contracts, and increases lift-producing actions near the surface. It
then spends the retained rotor reserve to reduce touchdown velocity.

## Reproduction

```bash
python scripts/gen_helicopter_autorotation_seed.py
python scripts/jabberwock_helicopter_autorotation.py \
  --episodes 12 \
  --altitudes 80 120 160 \
  --speeds 12 18 24 15 \
  --maximum-actions 400 \
  --output results/helicopter_autorotation.json
python scripts/jabberwock_helicopter_autorotation_3d.py \
  --episodes 4 \
  --altitudes 80 120 160 100 \
  --speeds 12 18 24 15 \
  --maximum-actions 400
pytest -q \
  tests/test_helicopter_autorotation_migrated.py \
  tests/test_helicopter_autorotation_3d_migrated.py
```

The complete preregistrations are
[`protocols/helicopter_autorotation_v1.json`](../protocols/helicopter_autorotation_v1.json)
and
[`protocols/helicopter_autorotation_3d_v1.json`](../protocols/helicopter_autorotation_3d_v1.json).

## Honest limitations

- The baseline plant is two-dimensional. The extension below adds rigid-body
  yaw and lateral motion, but neither plant models blade flapping, dynamic
  inflow, retreating-blade limits, ground effect, detailed tail-rotor
  aerodynamics, or terrain.
- Reset-bounded motor babbling is a simulation-safe identification curriculum.
  Deployment would need a simulator, prior airframe experience, or tightly
  constrained real-world interventions.
- The current local memory uses three generic contact-horizon contexts.
  Growing, merging, and forgetting these local models by the substrate's
  existing order-N shape machinery is the next generalisation.
- A height–velocity envelope must be mapped before testing low/slow failures;
  physically unrecoverable states must not be scored as cognition failures.
- Success here demonstrates the causal mechanism and controller flexibility,
  not equivalence to a flight-qualified autopilot.

## Six-degree-of-freedom extension

The same `helicopter_autorotation` graph seed now runs a PyBullet rigid body
with 3-D translation, quaternion attitude, roll/pitch/yaw rates, longitudinal
and lateral cyclic, collective, pedal authority, wind-relative drag and
ground contact. The graph chooses among 81 opaque simultaneous control
combinations.

The first implementation exposed an important missing prior. One-step action
prediction controlled immediate lateral speed but could tolerate a small bank
rate whose accumulated attitude eventually caused divergence. The repair was
generic: project transverse angular rate over a longer attitude horizon,
strongly preserve roll/yaw stability, and leave pitch sufficiently permissive
for an autorotation flare. No wind or autorotation recovery rule was added.

Measured 3-D checks after that repair:

- 4/4 safe landings from 80–160 m and 12–24 m/s in still air;
- 4/4 with crosswinds from 1 m/s lateral through combined 3/−4 and −3/4 m/s
  horizontal winds;
- 2/2 after a hidden 0.25-second lateral-force and angular impulse;
- 2/2 across heavier/higher-inertia and lower-rotor-inertia airframes.

Across the crosswind matrix, touchdown longitudinal speed was 1.18–1.47 m/s,
lateral speed 0.10–0.21 m/s in magnitude, vertical speed 0.99–1.62 m/s in
magnitude, and both graph and Bullet viability assessments agreed.

The FAA's description of autorotation and height–velocity limitations is the
external operational reference:
<https://www.faa.gov/regulations_policies/handbooks_manuals/aviation/helicopter_flying_handbook>.
