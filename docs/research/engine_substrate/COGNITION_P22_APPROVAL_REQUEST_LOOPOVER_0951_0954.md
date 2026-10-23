# P22 candidate-specific simulated-adoption request: Loopover 0951–0954

**Status: awaiting exact user approval. No action has been taken.**

This packet requests exactly one training-simulator transition for Loopover
candidate `#6542`, followed by a conditional generation-one checkpoint if the
native receipt verifies. It selects qualification `#21560` only, witnessed by
distinct training goals 0951 and 0953. The second qualification is not part
of this request. No validation or held-out worlds are included.

| Binding | Value |
|---|---|
| Family / domain | Loopover v2 / `p22-development-loopover` |
| Parent checkpoint | Registered invention-only g0, `7308895927d5ca447ae80199e9ee369e881ed0effa223e166c65b88f51b40f2c` |
| Ephemeral candidate ID | `#6542` |
| Expression digest | `2638da0f23ae34f8bd9a2d2a763e8adeac73b07da145c93f38552c251034cc06` |
| Expression key | `compose[compose:C0:R1'|C1]` |
| Effect digest | `[[6,7,2,4,1,0,3,5,8]]` |
| Parameters | `[5,4,2,6,3,7,0,1,8]` |
| Guard state | `[0,1,2,3,4,5,6,7,8]` |
| Source/model/frame epochs | `0 / 0 / 0` |
| Selected qualification | `#21560`, two native-verified trials |
| Selected witnesses | `p22:loopover-v2:train:0951`, `p22:loopover-v2:train:0953` |

The effect differs from all active held process effects in the registered
Loopover root. Exact training-only replay reproduced the candidate, effect,
qualification and witnesses. The original and replay source panels each used
20,000 reserved attempts and added zero approvals or receipts. Their raw
SHA-256 values are `e5c83c603025f78305111f47b2831697c0738967eec31ed0542e459b539e3fe9`
and `722f78bab019eea085cf039a3a3d29e17b27d0c83946a73b52c95ceabe840784`;
deterministic gzip hashes are `1d42107cccf2ab5398f68833ae0082db3075d980737c60f93f35650827885cf3`
and `595385075af462696de556f998a0355f1647cedd8a500ebbe4e23d412ba2b963`.

The authorization covers one simulator transition on a training world and
the conditional g1 checkpoint only. It does not authorize a later-generation
action, validation or held-out access, or an efficacy claim. The output path
is one-shot and currently unused. The command reconstructs the exact bound
candidate from the registered root, checks its training qualifications and
candidate-transfer depth, consumes this digest-specific authorization, then
executes only if every check matches:

```sh
.venv/bin/python scripts/run_p22_development_probe.py \
  --family loopover --training-draws 951 952 953 954 \
  --training-goal-relation distinct --validation-start 955 \
  --validation-count 0 --per-request-attempt-ceiling 5000 \
  --global-attempt-ceiling 20000 --search-ticks 30 \
  --candidate-transfer-depth 3 \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0951_0954.json \
  --approve-digest 2638da0f23ae34f8bd9a2d2a763e8adeac73b07da145c93f38552c251034cc06 \
  --review-seconds REVIEWER_REPORTED_SECONDS --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_loopover_0951_0953.json
```

To authorize exactly this action, reply with the exact digest and your
reviewer-reported time, for example:

`approve 2638da0f23ae34f8bd9a2d2a763e8adeac73b07da145c93f38552c251034cc06; review_seconds=12`

The machine request is
[`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0951_0954.json`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0951_0954.json).
