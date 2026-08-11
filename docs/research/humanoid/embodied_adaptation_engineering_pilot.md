# Embodied adaptation engineering pilot

## Result

A fresh graph learned all nine opaque actuator consequences and reached the
same two-metre open-plane goal with each of three PyBullet bodies. None of the
three graph-native controls reached it.

This is an engineering pilot, not the confirmatory experiment in
`embodied_adaptation_preregistration.md`. The controller was revised while
these runs were being developed, including adding body-axis-agnostic two-step
prediction. The pilot establishes that the build is executable and
non-vacuous; it must not be presented as an untouched preregistered result.

## Fixed pilot invocation

```text
python scripts/jabberwock_embodied_adaptation.py \
  --mode all --steps 120 --babble-samples 2 \
  --seed 0 --goal 2 0 0 \
  --quiet \
  --json-out results/embodied_adaptation_engineering_pilot.json
```

Each row used a new PyBullet client, `WorldAdapter`, graph, episode and set of
zero-valued `ActionModel` nodes. There was no state transfer between a body or
arm. All arms used the same nine opaque actuator tokens and 120 action
decisions.

## Observed outcome

| Body | Arm | Initial distance (m) | Final distance (m) | Normalized progress | Graph reached |
|---|---|---:|---:|---:|---:|
| R2D2 | learned model | 2.000 | 0.271 | 0.865 | yes |
| R2D2 | round-robin, no learning | 2.000 | 2.156 | -0.078 | no |
| R2D2 | random-like, no learning | 2.000 | 2.258 | -0.129 | no |
| R2D2 | shuffled learned mapping | 2.000 | 6.149 | -2.075 | no |
| Husky | learned model | 1.972 | 0.153 | 0.923 | yes |
| Husky | round-robin, no learning | 1.972 | 5.503 | -1.790 | no |
| Husky | random-like, no learning | 1.972 | 3.121 | -0.582 | no |
| Husky | shuffled learned mapping | 1.972 | 1.656 | 0.161 | no |
| Racecar | learned model | 1.999 | 0.211 | 0.894 | yes |
| Racecar | round-robin, no learning | 1.999 | 4.278 | -1.140 | no |
| Racecar | random-like, no learning | 1.999 | 1.654 | 0.172 | no |
| Racecar | shuffled learned mapping | 1.999 | 15.959 | -6.985 | no |

All three learned rows sampled and updated 9/9 action models. Their graph
selected 18 motor-babble actions followed by 102 forward-model actions. The
round-robin and random-like controls retained zero model samples; the shuffled
arm learned 18 samples and then deliberately enacted a cyclically wrong
token/model association. All 1,440 actions matched the token on the
graph-authored `MotorTrial` and the token echoed in the simulator receipt.

The raw pre/post positions give reached-run path efficiencies of 0.702 for
R2D2, 0.194 for Husky and 0.975 for Racecar. Husky therefore reached the goal
but wandered substantially; this is useful evidence against overstating the
pilot as efficient planning.

As a diagnostic rather than a confirmatory statistic, the median pre-update
prediction error fell from the first to second sample of the same actuator by
65.5% for R2D2, 84.1% for Husky and 71.3% for Racecar. The reduction was
positive for 6/9, 8/9 and 7/9 tokens respectively.

## What this supports

The pilot supports the narrow implementation claim:

- the same graph rules can acquire distinct forward models from raw
  intervention receipts for three different mobile-body mechanics;
- every physical action is the token held by a graph-authored `MotorTrial`;
- model use, goal-distance assessment, motor babble and the three controls are
  Rust-executed graph rules;
- the learned token/effect association matters in this pilot, because its
  cyclic permutation failed despite preserving learned values and counts.

It does not establish general robotics, population-level reliability,
obstacle navigation, visual navigation, sim-to-real transfer or adaptation to
arbitrary bodies. The URDF joint wiring and common two-channel command lattice
are supplied anatomy. Only body-specific actuator consequences are learned
from scratch.

## Next evidential step

Run the frozen confirmatory matrix with its fixed graph/control seed and three
new goals. Report every failed morphology/seed/goal row, and do not tune the
goals, horizon, command lattice, weights or thresholds after looking at that
matrix. Deterministic reruns are reproducibility checks, not independent
evidence.

## Subsequent extension

The seed now also contains dual-timescale forward-model adaptation, graph-held
surprise and matched frozen-plasticity controls for hidden mechanical damage
and progressive wear. That later engineering pilot is reported separately in
`docs/embodied_damage_wear_adaptation.md`; it does not alter or upgrade the
navigation claims made here.
