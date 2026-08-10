# Graph-native fixed-wing and jet control

The fixed-wing experiment extends the shared `embodied_motor_program` rather
than adding a Python autopilot. The Rust graph now learns forward, lateral,
vertical, roll, pitch, yaw and normal-load consequences. Its local models are
conditioned on signed body-relative airflow, squared flow magnitude and the
observed power state, which lets the same mechanism represent aerodynamic
authority and delayed engine spool.

The plant exposes seven independent groups and three opaque commands per
group. It contains lift, induced drag, departure beyond a critical incidence,
surface force/moment coupling, engine spool, asymmetric thrust, wind and
hidden authority loss. The graph never receives aileron, elevator, rudder,
throttle, stall or failed-component labels.

Analysis by synthesis adds compatible groups only while predicted consequence
error falls. A successful program can then become a graph-held System-1
default for a bounded number of releases. Periodic reconstruction and
surprise-triggered recalibration remain System-2 work. Existing users of the
shared seed retain zero default reuse unless they explicitly opt in.

## Structural body knowledge

The controller does not learn an airframe's breaking point by approaching it.
Before action, the adapter copies trusted design and inspection facts into the
graph: component allowables, the fraction of each load carried by a component,
specification confidence, and fatigue rate. In a deployed body these facts
would come from its bill of materials, CAD/finite-element load cases, material
allowables, maintenance history, and inspection. They are priors in the same
sense that an animal inherits tissue limits and then updates its estimate after
injury.

`embodied_structural_limits` derives the weakest participating component for
each physical load channel. It reduces the rated limit by current capacity,
confidence, and a graph-held safety factor. The motor-program graph then
combines the current measured whole-body load once with certified incremental
loads from each simultaneous effector. An inadmissible primitive is excluded
before calibration, so exploration cannot deliberately use destructive probes.
The same check applies to composed programs and to learned System-1 defaults.

The graph deliberately keeps two boundaries. Crossing the conservative safe
envelope interrupts release and admits a zero-increment unloading action, but
does not claim the body is destroyed. Exceeding the rated limit, or exhausting
cumulative fatigue capacity, records structural failure. Every receipt updates
per-channel utilization for normal load, peak force, impulse, impact energy,
and thermal load. This distinction avoids both unsafe optimism and the equally
dangerous assumption that touching a safety margin makes recovery impossible.

This is an architectural body-schema demonstration, not a certified airframe
model. Real deployment still requires appropriate load channels (including
joint torques, bending/torsion, pressure and temperature where applicable),
validated material data, uncertainty bounds, inspection updates, and
independent hardware interlocks. The important capability here is that those
facts participate directly in graph-native action selection rather than living
in a Python controller or being discovered by failure.

The preregistered damage run removes one opaque group. The graph consumes the
changed receipt at its exact monotonic boundary, performs one recalibration
pass, excludes the failed group, and constructs a replacement from surviving
effectors. The accompanying transfer changes mass, geometry, inertia, thrust,
engine spool and wind.

The controller has two distinct latency claims. A previously measured direct
Rust aerial reflex takes 155.6 microseconds median. A fresh arbitrary-width
program can take much longer because it yields between composition steps.
The experiment reports both reuse/synthesis request latency; it does not call
the latter a 1 kHz path.

## Hidden-goal mission

A separate mission test places an unreported target behind terrain-dependent
line of sight. Reset-bounded interventions teach the graph the consequences of
four opaque mission effectors. During flight it selects the action whose
learned consequence advances search. When a nonzero local signal is observed,
a hard-real-time graph rule binds the current location as the goal and selects
the learned payload-emission effector. The world confirms one flare at the
target; the runner never reads the hidden target location.

This mission layer is deliberately slower than stabilization. It demonstrates
the allocentric search/goal/action boundary, not integrated camera perception
or a certified terrain-following autopilot.

## Reproduce

```bash
python scripts/gen_embodied_motor_program_seed.py
python scripts/gen_embodied_structural_limits_seed.py
python scripts/gen_hidden_goal_aerial_mission_seed.py
python scripts/jabberwock_fixed_wing_jet.py \
  --output results/fixed_wing_jet_control_v1.json
python scripts/jabberwock_hidden_goal_aerial_mission.py \
  --output results/hidden_goal_aerial_mission_v1.json
pytest -q tests/test_fixed_wing_jet_control_migrated.py
```
