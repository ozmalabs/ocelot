# Embodied adaptation: first build scope

## Outcome

The first build is a small, falsifiable demonstration that a fresh Jabberwock
graph can discover the consequences of opaque actuators and use those learned
consequences to reduce distance to open-plane goals in three different
PyBullet bodies:

- R2D2, differential drive;
- Husky, skid steer;
- Racecar, Ackermann steering.

The claim is deliberately narrower than “general robotics”. The demonstration
does not include vision, SLAM, obstacle planning, sim-to-real transfer,
manipulation, or transfer of a learned model between bodies. It does not claim
that the substrate starts without priors: it starts with a generic experimental
and forward-model learning grammar. What starts from scratch is the graph state
that associates each opaque actuator token with that body’s observed motion.

Obstacle navigation, learning across morphology changes, and learning actuator
anatomy itself are stretch results. They are not primary success criteria.

## Architectural boundary

The agent remains graph data executed by Rust. Python is a physics peripheral.

```text
PyBullet raw state
  -> mechanical Python ingest
  -> BodyState / TransitionObservation graph facts
  -> Rust executes embodied_adaptation rules
  -> episode.selected_token matches ActionModel -> graph-authored MotorTrial
  -> mechanical Python reads MotorTrial.token and applies its vector
  -> PyBullet raw state
```

The Python world may:

- create and reset a PyBullet client;
- load a URDF and immutable hardware description;
- expose normalized actuator vectors as meaningless tokens such as
  `actuator_003`;
- report raw pose, velocity, joint, contact and goal data;
- apply the graph-selected token;
- record outputs and calculate preregistered reporting metrics.

It may not:

- choose or rank an action;
- contain a navigation policy;
- update an action model;
- calculate a reward for the agent;
- branch on graph beliefs;
- attach meanings such as `forward`, `left`, `steer`, or `throttle` to an
  actuator token;
- reuse a graph or learned `ActionModel` for another morphology.

Different joint layouts necessarily require different peripheral wiring. That
wiring is immutable anatomy, represented as data. It maps a normalized command
vector to simulator joint controls but contains no predicted effect or action
preference. Neither the adapter nor the graph rules may choose behavior by
matching the names `r2d2`, `husky`, or `racecar`.

## Graph faculty

The embodied seed should hold the generic cycle:

1. choose an untried opaque actuator while the body model is incomplete;
2. open a `MotorTrial`;
3. observe the transition;
4. update an `ActionModel` for body-frame forward, lateral and yaw displacement,
   plus collision and effort;
5. once models have evidence, predict each actuator’s next body state;
6. choose the actuator with least predicted goal error;
7. continue updating from prediction error.

The graph must supply every selected token. A Python fallback action makes the
demonstration invalid, even if it only occurs once.

Learning is online and local. The intended small-net analogue is one
low-capacity forward model per actuator, updated from the transition stream
rather than trained by gradient descent. The initial model has no body-specific
motion values.

## Bodies and observations

All bodies receive the same graph vocabulary and decision rules. The physics
adapter exposes:

- base position and quaternion;
- base linear and angular velocity;
- raw joint states;
- raw contact records;
- goal position;
- previous opaque token and its normalized vector;
- simulator step and time.

Python ingests the raw pre/post world pose. Rust-evaluated Terms in
`ea_learn_forward_model` perform the world-to-body transform and derive
forward/lateral/yaw deltas inside the graph. The graph is not told that any
actuator channel means forward or steering.

## Build slices

### Slice 1 — physics peripheral

- Direct-mode PyBullet world with deterministic stepping.
- Load all three bodies.
- Enumerate opaque actuator tokens from immutable hardware data.
- Raw observation and token application only.
- A lifecycle test must create, reset, step and close every body without
  leaking clients.

### Slice 2 — graph-native adaptation

- Seed `OpaqueActuator`, `ActionModel`, `MotorTrial`,
  `TransitionObservation`, `EmbodiedEpisode`, and `EmbodiedGoal`.
- Graph rules choose babble/model/control actions, open/close trials, and update
  the forward model.
- Candidate actions are body-independent tokens joined through graph edges.
- Every mutation is visible in the graph.

### Slice 3 — paired experiment

- Create a new physics client and new `WorldAdapter` for every morphology,
  seed and experimental arm.
- Run learning, coverage-matched no-learning, graph-native random, and
  shuffled-model arms with the same starts, goals, step budgets and simulator
  seeds.
- Use the shuffled-model arm for the stronger claim that navigation depends on
  the learned token/model association specifically.
- Write raw per-transition records before aggregating metrics.
- Refuse the claim if any non-vacuity condition fails.

### Slice 4 — stretch only

- Add obstacles and quanta navigation.
- Learn collision-conditioned effects and configuration-space clearance.
- Test retained adaptation after morphology change.
- Test whether dimensions learned on one body speed, but do not determine,
  learning on another.

No Slice 4 result may be used to rescue a failed open-plane primary result.

## Definition of done

The build is complete when:

- all three URDFs run headlessly;
- each morphology begins with a fresh graph and zero-sample action models;
- every token is sampled and every selected token has graph provenance;
- model estimates change from their initial values;
- forward prediction improves against the preregistered controls;
- graph-selected navigation improves open-plane goal progress against
  the no-learning, random and shuffled-model controls;
- failures are emitted with exact morphology, seed, goal and mode, plus token
  and epoch once action selection has begun; unavailable context is explicitly
  null and failures are never reported only as a count.

The quantitative gates and fixed protocol are in
`docs/embodied_adaptation_preregistration.md`.
