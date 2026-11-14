# Agent end-to-end evaluation

- Driver: `opencode` (live backend; see docs/features/AGENT_E2E_EVAL.md)
- Backend: `opencode`, model `vllm/qwen3.8-27b (opencode config default)`
- Total reported cost: $0.0
- Base: `aef842ba6bc06acb1bab6ee74e879b9bbc81dc53`
- Arms: baseline, dev_memory
- Repeats per task and arm: 1
- Tasks: 7

## Per arm

| arm | runs | success | success rate | mean wall s | mean prep s | prep failures | driver errors | mean tokens in | mean tokens out | mean cost USD | mean tool calls | mean MCP calls | localization rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 7 | 7 | 1.0 | 40.146 | 0.0 | 0 | 0 | 27504.1 | 933.7 | 0.0 | 8.9 | 0.0 | 1.0 |
| dev_memory | 7 | 7 | 1.0 | 38.436 | 64.3 | 0 | 0 | 32400.7 | 907.0 | 0.0 | 8.9 | 0.3 | 1.0 |

Token, cost and tool columns are blank where the driver reports no value. MCP calls count calls to the Ocelot dev-memory server. Prep (dev_memory snapshot and tag cache) runs before the driver timer; mean prep s is 0 for baseline.

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
