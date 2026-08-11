# HumanoidBench H1 transfer test

This cross-simulator test runs the same graph-native opaque motor learner on
the official HumanoidBench `h1-walk-v0` task at repository revision
`cb1189039151c8aadaaa987b442da54383c87fab`. It loads no HumanoidBench policy,
motion data, named-joint controller, inverse kinematics, or gradient-trained
weights.

## Boundary and transfer

The thin MuJoCo boundary discovers 19 actuators and exposes 39 opaque commands:
one reset-posture tonic target and positive/negative offsets for every
actuator. It discovers the two initially load-bearing bodies from contact
forces. Python copies raw root pose, velocity, joint, and support receipts and
mechanically enacts graph-selected bundles.

HumanoidBench normally advances ten 2 ms physics frames per task action. The
boundary bypasses that fixed task step so the graph owns command duration, but
mirrors ten frames as the actuator integration prior. The graph combines that
with its gravity/morphology horizon, chooses ten frames (50 Hz), and contracts
to five frames (100 Hz) after gait prediction surprise.

The home command is the reset joint pose transformed through HumanoidBench's
actuator ranges. A normalized all-zero vector is not the reset pose and caused
the initial boundary prototype to fall in 22 decisions; that was a boundary
error and is not the reported benchmark result.

## Result: transfer fails at stable H1 control

The final paired run uses fresh graphs and deterministic H1 bodies:

| Measure | Learned graph | Tonic control |
|---|---:|---:|
| First fall decision | `65` | `64` |
| Final benchmark terminated | yes | yes |
| Nominal response horizon | `10` frames | `10` frames |
| Minimum response horizon | `5` frames | `10` frames |
| Mean realized command rate | `85.84 Hz` | `50 Hz` |
| Staged safe pair probes | `38` | `38` |
| Deployed multi-motor programs | `0` | `0` |
| Single-primitive recovery actions | `334` | `0` |
| Directed displacement | `-1.068 m` | `-1.078 m` |

The benchmark is therefore a useful falsification. Body-scaled timing,
prediction-triggered cadence contraction, opaque action discovery, staged
pair-interaction learning, and arbitrary motor-program synthesis transfer.
Stable control does not.

The graph approved all 38 reset-isolated pair probes and stored their nonlinear
interaction residuals. During the live H1 trajectory, however, its
analysis-by-synthesis search found no compatible additional primitive whose
predicted consequence strictly improved the objective. It therefore closed
263 grounded single-member programs rather than forcing concurrency. It
consequently has zero eligible multi-member motor memories and performs zero
recalls. With no safe compound population states, it also forms zero temporal
transition edges, creates zero output-null preparations, and performs zero
sequence recalls or releases. The uncertainty gate therefore has no candidate
to assess. This is the desired semantics: bundle width, repertoire reuse,
preparation, and trajectory formation are predictions, not targets.

The remaining limitation is the forward model, not the enaction boundary or a
hard-coded width. H1 falls almost immediately, before live combined-action
receipts can specialize any reusable pair. Support-conditioned local impulse
models learned from reset posture do not yet represent enough whole-body
contact dynamics to predict a stabilizing H1 program. The next rung is
graph-native multi-step counterfactual rollout and reusable higher-order
program models, learned behind the same causal safety and receipt rules.
Simply running the present controller faster does not solve that.

The recorded result remains a failure (`walking_passed: false`); no benchmark
threshold was weakened to claim success.

## Reproduce

```bash
git clone https://github.com/carlosferrazza/humanoid-bench \
  /path/on/disk/humanoid-bench
uv pip install --python /path/to/research/.venv/bin/python \
  mujoco==3.1.6 dm_control==1.0.20 imageio==2.34.2 "jax[cpu]==0.4.28"

PYTHONPATH=/path/on/disk/humanoid-bench \
  /path/to/research/.venv/bin/python \
  scripts/jabberwock_humanoid_bench_trial.py \
  --simulator-root /path/on/disk/humanoid-bench \
  --json-out results/humanoid_bench_h1_walk_v1.json
```
