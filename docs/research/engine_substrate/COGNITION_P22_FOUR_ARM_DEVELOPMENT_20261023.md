# P22 four-arm development wiring probe

This is a development-only native wiring diagnostic, not a preregistered
comparison. Four fresh cognition-on graphs were run per family on the same
eight v2 **training** worlds (draws 0250–0257): unchanged, adaptive-only,
invention-only, and full. Every arm received the same answer-free task inputs
and held primitive schemas. Each graph used the declared shared ThinkingBudget
capacity of 64. Candidate digest attestation ran when a graph minted a
candidate; no candidate-specific approval or world action was created. No
validation or held-out world was read by this runner.

| Family | Unchanged solved | Adaptive-only solved | Invention-only solved | Full solved | Candidate proposals (invention-only / full) |
|---|---:|---:|---:|---:|---:|
| D4 v2 | 3/8 | 3/8 | 3/8 | 3/8 | 5 / 1 |
| Loopover v2 | 1/8 | 1/8 | 1/8 | 1/8 | 0 / 0 |

These counts are training-panel diagnostics and must not be interpreted as
generalization or treatment effects. No arm had a candidate approval or a
world receipt. The resource comparator correctly reports mismatches across
budget requests/spend, native solver work, search attempts/work, task and
outcome counts, and serialized graph size. Consequently, neither equal
cumulative compute nor an efficiency comparison is established.

A native settlement rule now marks funded search requests `global_attempt_ceiling`
after the aggregate native-attempt count reaches the configured limit, and the
P22 bridge records that status as a terminal `search_attempt_ceiling` outcome.
This allowed all four arms to terminalize all eight tasks in both families and
released the sequential curriculum scheduler. It repaired the stranded-request
lifecycle defect, not the attempt bound: the configured global limit is 64,
while simultaneous grammar activations yielded 68 and 66 attempts in the D4
and Loopover full arms, 108 in D4 invention-only, and 132 in Loopover
invention-only. The exact counts are in the raw records. This overshoot is a
remaining fixed-compute defect; P22.E2 cannot freeze with these settings. It is
not a negative efficacy result. Search candidates remain unapproved and
non-actionable.

Raw records:

- [`p22_four_arm_v2_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_d4.json), SHA-256 `fbe41ad128b5354b51e25e489aeb032131771b0793628042556c2224cafc631d`.
- [`p22_four_arm_v2_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_loopover.json), SHA-256 `24ab3981c21bb701b73f96571bf411d166ce923d879cbe4fde7a72eb1aae945e`.

Reproduce with:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_four_arm_development.py \
  --family d4 --training-draws 250 251 252 253 254 255 256 257 \
  --output evaluation/process_mastery/results/p22_four_arm_v2_d4.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_four_arm_development.py \
  --family loopover --training-draws 250 251 252 253 254 255 256 257 \
  --output evaluation/process_mastery/results/p22_four_arm_v2_loopover.json
```

The outputs were rerun and byte-matched. This diagnostic does not close the
four-arm learner gate, candidate authorization, matched resource accounting,
preregistration, or held-out evaluation.
