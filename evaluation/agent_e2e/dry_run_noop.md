# Agent end-to-end evaluation

- Driver: `noop`
- Base: `aef842ba6bc06acb1bab6ee74e879b9bbc81dc53`
- Arms: baseline
- Repeats per task and arm: 1
- Tasks: 7

## Per arm

| arm | runs | success | success rate | mean wall s | mean prep s | prep failures | mean tokens in | mean tokens out | mean cost USD | localization rate |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 7 | 0 | 0.0 | 0.0 | 0.0 | 0 |  |  |  | 0.0 |

Token and cost columns are blank where the driver reports no value. Prep (dev_memory snapshot and tag cache) runs before the driver timer; mean prep s is 0 for baseline.

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
