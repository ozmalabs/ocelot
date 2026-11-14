# Agent end-to-end evaluation

- Driver: `noop`
- Base: `a6df57f0d4b594564d993495d6d38a1b1be3170f`
- Arms: baseline
- Repeats per task and arm: 1
- Tasks: 7

## Per arm

| arm | runs | success | success rate | mean wall s | mean tokens in | mean tokens out | mean cost USD | localization rate |
|---|---|---|---|---|---|---|---|---|
| baseline | 7 | 0 | 0.0 | 0.0 |  |  |  | 0.0 |

Token and cost columns are blank where the driver reports no value.

## Per task (paired)

| task | baseline |
|---|---|
| architecture-entrypoint-exclusion | 0/1 |
| architecture-hub-order | 0/1 |
| dev-memory-strict-bool | 0/1 |
| py-cst-token-last-char | 0/1 |
| repo-map-baseline-budget | 0/1 |
| repo-map-context-truncated | 0/1 |
| seed-loader-engine-rules | 0/1 |
