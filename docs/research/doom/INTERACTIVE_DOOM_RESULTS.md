# Interactive autonomous Doom — implementation result

Engine **b896651472d9**, built from this worktree's Rust source. Canonical
post-merge engine **4d77633d9b3c**, `source_match="own"`.

## Architecture

The live world is a separate paced I/O process. It owns the visible VizDoom
`PLAYER` instance and advances exactly one expiring action pulse per tic. The
agent process consumes a latest-only RGB/proprioception stream and may run
slower without slowing Doom; its latest authorized action is consumed once,
otherwise the world receives zero control.

The world supplies no cognition and there is **no Doom-specific agent seed**.
It publishes:

- RGB radiance;
- legitimate body pose/resources as proprioception;
- opaque atomic controls grouped into independent actuator axes;
- concrete action consequences/resource footprints.

The agent supplies:

- asynchronous photon/retinal perception;
- native retinotopic motion/depth tasks;
- generic persistent spatial belief (`spatial_belief_core`);
- existing goals, learned `ControlResponse` navigation, curiosity, held motor
  terms, and order-N cognition;
- structural composition of compatible controls from independent axes
  (`control_bundle`);
- thermodynamic wait/refine/commit;
- epoch-bound, exactly-once `ActionIntent`s.

Depth and labels are disabled in this profile and never enter the agent graph.
The separate scored vision/map probes remain unchanged and may retain those
buffers strictly as declared oracles.

## Core correction

Native task execution now has three phases:

1. prepare immutable work and mark it running under the graph lock;
2. execute pure kernels with **no live-graph mutex**;
3. reacquire the lock only for epoch validation, deterministic result fold and
   consumer settlement.

PyO3 `run_rules`/`run_cycle` release the GIL. The visible game loop therefore
runs independently of both pure workers and graph collapse.

## Retracted live WAD smoke

The earlier action-mix result is retracted. It was produced by the deleted
hand-authored affordance scorer and enumerated composite actions, so it did not
measure Jabberwock cognitive play. The replacement below was run through the
goal/learning/control-bundle path.

Replacement headless E1M1 smoke through that path:

```
70 tics, 0 deaths
top action mix:
  noop          52
  use            2
  attack         2
  turn_right     2
  turn_left      2
  strafe_right   2
```

Attack is no longer coupled to turning or emitted continuously. This short
smoke demonstrates live execution, not competent play; simultaneous composition
is separately proven by the deterministic graph gate.

After wiring observed outcomes back into the standing `ActionStat`/resource
learning path, a 35-tic smoke also emitted
`strafe_right+attack+use` twice. That combination was assembled from three
independently selected axes; it does not exist in the world's action list.

Launch the native visible session:

```bash
PYTHONPATH=runners/dsl/python:.:scripts \
python3 scripts/jabberwock_plays_doom.py --tics 1400
```

Use `--headless` for CI/replay and `--unpaced` only for throughput probes; an
unpaced world can legitimately outrun perception and therefore receives mostly
zero-control tics.

## Gates

- Interactive Doom gates: **9 passed**.
- Navigation, commitment, action-learning and resource regressions:
  **34 passed**.
- End-to-end graph gate: an opaque control's response is learned from observed
  displacement; a graph goal selects it; the held operate term independently
  selects another axis; both become one compatible bundle.

## Honest boundary

- The native retinal flow/depth task is a bounded coarse local-shift estimator,
  not the full 158000 FOE/radial depth mechanism.
- Spatial belief is generic free/wall accumulation. Structural priors remain a
  generic faculty to extract from the earlier Doom-named research seed before
  they belong in this live agent.
- The native visible window path uses the same child process as the headless
  smoke, but this environment only exercised it headlessly; display-server
  closure remains an optional local soak gate.
- A longer visible real-WAD soak remains required; the replacement above was a
  short headless execution gate.
