# P22 candidate-specific simulated-adoption request: D4 0962/0972

**Status: awaiting exact user approval. No action has been taken.**

This packet requests exactly one D4 training-simulator transition for
candidate `#1908`, followed by a conditional generation-one checkpoint if the
native receipt verifies. It selects qualification `#11843`, witnessed by
distinct training goals 0962 and 0972. No validation or held-out worlds are
included.

| Binding | Value |
|---|---|
| Family / domain | D4 v2 / `p22-development-d4` |
| Parent checkpoint | Registered invention-only g0, `fe39a44242987c5c97404c8b0812c3928a7324aee2911f57133417ce2650236c` |
| Ephemeral candidate ID | `#1908` |
| Expression digest | `2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46` |
| Expression key | `compose[compose:flip_r:rot90|rot90]` |
| Source effect digest | `[[1,0,3,2]]` |
| Parameters | `[1,0,3,2]` |
| Guard state | `[0,1,2,3]` |
| Source/model/frame epochs | `0 / 0 / 0` |
| Selected qualification | `#11843`, two native-verified trials |
| Selected witnesses | `p22:d4-v2:train:0962`, `p22:d4-v2:train:0972` |

The earlier 0955/0957 qualification for this expression was invalid because
its transfer child duplicated active held process `rot90`; that request is
superseded and does not authorize this action. This packet uses a new
qualification. Its 0972 transfer child has effect `[2,0,3,1]`, which differs
from both active D4 root effects. The source panel and exact replay under the
stricter source-and-child novelty rule reproduced candidate `#1908`,
qualification `#11843`, and both witness keys. Each used 10,290 attempts and
added zero approvals or receipts. No validation or held-out world was
accessed. Their raw SHA-256 values are
`3d127fabe5e87f0f35825150a747bc5f87646503094a7f1e438bc32de76ff586` and
`c1f0e884331264ae47851a9abf2a3b890533e71faa5d24c97de569f89e2fe3c3`;
deterministic gzip hashes are
`68a00650a77cadbeda5a2633d4bae6eaad2c7f021660bd83542cc92ba1fc3d89` and
`57ea54916ddf3208f26c8cbe2e4f1b18749ac06b95675cae6b7ffeca9e124368`.

The authorization covers only one simulator transition on training world
0962 and the conditional g1 checkpoint. It authorizes no later-generation
action, validation or held-out access, or efficacy claim. The output path is
one-shot and currently unused. The guarded command reconstructs the exact
candidate from the registered root and verifies the selected qualification,
transfer depth, and all candidate fields before acting:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family d4 --training-draws 962 960 963 972 \
  --training-goal-relation distinct --validation-start 973 \
  --validation-count 0 --per-request-attempt-ceiling 5000 \
  --global-attempt-ceiling 20000 --search-ticks 30 \
  --candidate-transfer-depth 3 \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_D4_0962_0972.json \
  --approve-digest 2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46 \
  --review-seconds REVIEWER_REPORTED_SECONDS --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_d4_0962_0972.json
```

To authorize exactly this action, reply with its digest and your
reviewer-reported time, for example:

`approve 2d2cb9ecda29351e1d0f513498eb6089c0f48b2dc1f8ee8650ebb2bbf39cdc46; review_seconds=12`

Machine request: [`COGNITION_P22_APPROVAL_REQUEST_D4_0962_0972.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0962_0972.json).
