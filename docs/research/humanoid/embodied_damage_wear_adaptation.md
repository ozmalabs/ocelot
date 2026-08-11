# Embodied model adaptation to damage and wear

## Result

The Jabberwock can now revise graph-resident actuator forward models when the
same opaque command begins producing different physical consequences. The
simulator can impose either abrupt damage or progressive wear without exposing
the condition, onset, affected channel, retention factor, or effective command
to the agent.

In the engineering pilot, adaptive and frozen-plasticity graphs received the
same pre-onset experience, issued the same opaque action sequence, and followed
the same trajectory until the hidden mechanical change. Late prediction error
was lower with continued graph plasticity for all three bodies under both
conditions.

This is an engineering pilot, not a confirmatory result. Parameters were
selected while building and debugging the mechanism.

## Mechanism

The Python/PyBullet boundary implements only mechanics:

- abrupt damage multiplies one physical command channel by a fixed retention
  factor from a scheduled action onward;
- wear progressively reduces that channel per unit of requested use, down to a
  fixed mechanical floor;
- the requested opaque token is still echoed in the action receipt;
- observations contain raw pose, velocity, joints, contacts and effort;
- no damage label, wear estimate, effective command or fault time enters the
  graph.

The Rust-executed graph adds a dual-timescale adaptation process:

1. exact sample means establish each opaque actuator's initial forward model;
2. a recency-weighted trace follows continuing changes;
3. prediction residuals update graph-held expected error and volatility;
4. residuals above the model's own expected-error threshold produce a
   graph-held surprise event and a transient faster plasticity rate;
5. repeated surprise can open a finite active re-probing window;
6. every model change remains receipt-backed and attached to the causal
   `MotorTrial`.

This resembles, without claiming a literal neural implementation, several
well-supported properties of biological motor adaptation: cerebellar-style
sensory prediction errors, interacting fast and slow adaptation processes,
volatility-sensitive learning rates, and active information-seeking after a
model violation.

## Paired system-identification pilot

Fixed settings:

- PyBullet `DIRECT`, deterministic physics;
- 108 graph decisions;
- two initial observations for each of nine opaque actuators;
- hidden mechanical change at action 45;
- 18-transition early and late post-change metric windows;
- graph-native round-robin probing after calibration;
- a fresh simulator, graph and model table for every arm;
- seed `0`, goal `(3, 0, 0)`.

Damage sets physical channel A retention to zero. Wear reduces channel A by
`0.04` per unit of absolute requested use to a floor of `0.2`. Channel A is a
wheel group on R2D2 and Husky and drive velocity on Racecar; that anatomy is
not represented in the graph.

| Condition | Body | Adaptive early error | Adaptive late error | Recovery | Frozen late error |
|---|---|---:|---:|---:|---:|
| Damage | R2D2 | 0.0263 | 0.0120 | 54.4% | 0.0344 |
| Damage | Husky | 0.0691 | 0.0290 | 58.0% | 0.1067 |
| Damage | Racecar | 0.0587 | 0.0119 | 79.6% | 0.0881 |
| Wear | R2D2 | 0.0236 | 0.0167 | 29.2% | 0.0319 |
| Wear | Husky | 0.0309 | 0.0181 | 41.5% | 0.0809 |
| Wear | Racecar | 0.0628 | 0.0254 | 59.5% | 0.0865 |

Prediction error is the existing mixed-unit engineering diagnostic over
body-frame forward displacement, lateral displacement and yaw. It is useful
for paired model comparison but is not a physical norm.

All six adaptive arms emitted post-onset surprise events. Frozen arms emitted
none after the onset because their graph plasticity was deliberately disabled.
The frozen arm is not naïve: it shares the adaptive arm's complete history and
model state until action 45. This isolates updating after the hidden change.

Run the pilot with:

```text
PYTHONPATH="runners/dsl/python:.:scripts" \
python scripts/jabberwock_damage_wear_adaptation.py --quiet
```

The complete transition records and summaries are in
`results/embodied_damage_wear_engineering_pilot.json`.

## What is and is not established

The pilot supports a narrow claim: under matched interventions, receipt-backed
graph plasticity tracks abrupt and gradual changes in actuator consequences
better than the same frozen model.

It does not yet establish that active closed-loop navigation always benefits.
During development, finite active re-probing improved model coverage but its
exploration cost sometimes worsened short-horizon goal distance, particularly
for R2D2. Closed-loop damage recovery therefore remains exploratory and must
not be inferred from the system-identification result.

Other limitations:

- only one of two supplied hardware channels changes;
- damage is a scalar loss of effectiveness, not fracture, intermittent
  failure, backlash, sensor damage or altered joint topology;
- the graph learns one low-capacity model per opaque action rather than a
  factorized joint-level body model;
- the deterministic simulator does not establish robustness to noise;
- the surprise mechanism identifies changed consequences, not the semantic
  cause “damage” or “wear”;
- no recovery, compensation limit or safe-stop claim is made.

## Next falsifiable step

Freeze a new protocol before further runs:

- unseen onset times, affected channels and severities;
- intermittent and recovering faults;
- observation noise and load variation controls;
- a context-conditioned forward model that separates momentum from actuator
  change;
- navigation goals introduced only after matched calibration;
- explicit energetic and safety costs for active probing;
- refusal when remaining controllability is insufficient.

The key closed-loop gate should be post-change goal progress against the
identically calibrated frozen model, while reporting the exploration cost and
any morphology that fails rather than averaging it away.
