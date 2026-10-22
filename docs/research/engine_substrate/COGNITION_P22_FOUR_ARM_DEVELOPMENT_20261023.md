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
| D4 v2 | 3/8 | 3/8 | 3/8 | 1/8 | 5 / 1 |
| Loopover v2 | 1/8 | 1/8 | 1/8 | 0/8 | 0 / 0 |

These counts are training-panel diagnostics and must not be interpreted as
generalization or treatment effects. No arm had a candidate approval or a
world receipt. The resource comparator correctly reports mismatches across
budget requests/spend, native solver work, search attempts/work, task and
outcome counts, and serialized graph size. Consequently, neither equal
cumulative compute nor an efficiency comparison is established.

The runner exposes an additional integration failure that prevents P22.E2
freeze. In D4, the full arm completed only 2/8 curriculum tasks; one task
remained delivered to native search with a funded request and five were never
dispatched. In Loopover, the full arm completed one task and left another
delivered with a funded request; six were never dispatched. The Loopover
invention-only arm also left seven tasks with funded search requests. These
requests did not reach a recorded native terminal outcome under the bounded
development loop, so the sequential scheduler could not release the remaining
curriculum tasks. This is a structural adapter/lifecycle issue, not a negative
efficacy result. The unchanged and adaptive-only arms did terminalize all eight
tasks in each family. Search candidates remain unapproved and non-actionable.

Raw records:

- [`p22_four_arm_v2_d4.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_d4.json), SHA-256 `8ccb44e1a38f2d65239eebccfa93077555a73c4956da7299a44d84505b5b021b`.
- [`p22_four_arm_v2_loopover.json`](../../../evaluation/process_mastery/results/p22_four_arm_v2_loopover.json), SHA-256 `fc29d5f7e762f2cc6600bf7695522d82da251ebc6ae8f53e3cd5ff8fa174cb3c`.

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
