# General embodied motor priors

The motor substrate now boots a small shared prior seed before the humanoid,
ground-robot, and aerial adaptation seeds. These are defeasible structural
expectations, not a supplied controller or gait:

- embodiment is a graph of connected loads, constraints, sensors, and opaque
  effectors;
- intervention receipts reveal controllability and delayed consequences;
- viability means retaining reachable recovery states, not merely surviving
  the present sample;
- momentum may be exchanged through contact, rolling, reaction mass,
  thrusters, or surrounding fluid;
- compatible actions may compose, with nonlinear interaction consequences
  credited to the exact compound program;
- useful actions persist to sensed events and become receipt-grounded temporal
  transitions;
- redundant causal roles may substitute after damage;
- repeated safe trajectories may consolidate into reusable chunks; and
- useful task work competes with free-energy, peak-power, regeneration, and
  thermal constraints.

The shared prior now sits underneath an uncertain sensorimotor state-estimation
and plasticity layer. Delayed/noisy proprioceptive, vestibular, and contact
receipts correct a predicted `EmbodiedBodyBelief`; the exact causal trial
receives eligibility-based credit; reliable controllers may consolidate and be
replayed during default-mode activity. See
[Embodied sensorimotor architecture](docs/embodied_sensorimotor_architecture.md).

Python remains a mechanical simulator boundary. It exposes raw position,
velocity, contact, torque, RPM, and elapsed-time measurements. The Rust graph
integrates actuator work, learned support loss, transport path, net energy,
peak power, cost of transport, and remaining energy/power/thermal headroom.

## Capability representation

The graph does not label an actuator as a leg, wheel, rotor, jet, or control
surface. Each opaque action model acquires an `EmbodiedEffectorCapability`
from verified receipts. Its energy-normalized translation and vertical
authority are learned separately for:

- contact-coupled and contact-free states; and
- rising, approximately level, and descending motion.

That separation is essential because the same effector can serve different
roles in different dynamics. A rotor may add launch impulse while rising,
provide cruise authority in free flight, and arrest descent before touchdown.

## North-star manoeuvre

The target demonstration is a mech approaching a canyon and learning a hybrid
sequence:

1. build horizontal momentum with contact-coupled effectors;
2. compose a launch impulse with legs and jump jets or rotors;
3. coast or boost while preserving enough energy and power headroom;
4. recruit the descending-regime model to arrest descent only as much as
   viability requires; and
5. absorb the residual impact and return to a recoverable contact state.

This must emerge as analysis by synthesis over learned compound actions and
temporal transitions. No canyon detector, jump phase machine, anatomical
label, fixed gait table, or host-side policy is admissible.

## Present evidence and remaining experiment

The shared priors currently improve the humanoid controller's directed
progress, path efficiency, compound-action use, sequence recall, and reversal
rate. Simulator-level tests verify mechanical energy sensing for articulated,
wheeled/tracked, humanoid, and rotorcraft bodies. A graph test verifies that
one opaque effector acquires distinct grounded/rising and free/descending
capabilities while the graph integrates energy and transport cost.

The repository does not yet contain a canyon-capable hybrid mech body. The
next falsifying experiment is therefore a body with both contact limbs and
independently opaque impulse/continuous-thrust effectors, a finite energy
store, a power ceiling, and landing damage. Passing requires cold-start
discovery, a successful crossing, lower energy use with experience, retained
landing viability, and adaptation after one propulsion effector is degraded.
