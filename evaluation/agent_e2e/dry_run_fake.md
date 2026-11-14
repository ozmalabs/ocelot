# Agent end-to-end evaluation

- Driver: `fake`
- Base: `a6df57f0d4b594564d993495d6d38a1b1be3170f`
- Arms: baseline, dev_memory
- Repeats per task and arm: 1
- Tasks: 7

## Per arm

| arm | runs | success | success rate | mean wall s | mean prep s | prep failures | mean tokens in | mean tokens out | mean cost USD | localization rate |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 7 | 7 | 1.0 | 0.003 | 0.0 | 0 |  |  |  | 1.0 |
| dev_memory | 7 | 7 | 1.0 | 0.038 | 70.6 | 0 |  |  |  | 1.0 |

Token and cost columns are blank where the driver reports no value. Prep (dev_memory snapshot and tag cache) runs before the driver timer; mean prep s is 0 for baseline.

## Per task (paired)

| task | baseline | dev_memory |
|---|---|---|
| architecture-entrypoint-exclusion | 1/1 | 1/1 |
| architecture-hub-order | 1/1 | 1/1 |
| dev-memory-strict-bool | 1/1 | 1/1 |
| py-cst-token-last-char | 1/1 | 1/1 |
| repo-map-baseline-budget | 1/1 | 1/1 |
| repo-map-context-truncated | 1/1 | 1/1 |
| seed-loader-engine-rules | 1/1 | 1/1 |
