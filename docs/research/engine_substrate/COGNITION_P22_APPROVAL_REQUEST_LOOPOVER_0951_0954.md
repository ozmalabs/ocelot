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
Loopover root. The source panel and exact replay were both rerun with the
stricter transfer-child novelty guard. They reproduced the candidate, both
qualifications and their witnesses; each used 20,000 reserved attempts and
added zero approvals or receipts. Their raw SHA-256 values are
`d4494ea8fd590af5f33baf736940843209c155a65b1b12d53e5a18653f2146bc` and
`cdc4421f8425369e12df717b7cb495c6033f40ba1480729497f7b2a476ea7238`;
deterministic gzip hashes are `0efa12606c579971601b505c3e82823caff62bf59a634e3d2d23031db2146384`
and `cde29f3416c936bf42b7b5d651f7b8f8d8ba7d82cf4970cf7c3bc8fd17578c17`.

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
