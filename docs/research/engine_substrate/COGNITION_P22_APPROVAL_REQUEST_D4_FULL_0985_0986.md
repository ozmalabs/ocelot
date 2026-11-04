# P22 candidate-specific simulated-adoption request: D4 full arm, 0985/0986

**Status: consumed.** The user approved the exact digest with 12
reviewer-reported seconds. Approval `#12261` and verified receipt `#12264`
produced generation-one checkpoint `p22-d4-g1-15ab127dc160`, digest
`e83c1fb3b84f589b8ca400b4b39fa03d8c04528aba262adc3b53a4c1eeca9af9`.
The raw result is `p22_approved_candidate_d4_full_0985_0986.json`, SHA-256
`2355279174397e964cfb66a960696f69e27764c2c8c7fd4911616005ddafba2c`.
This request authorizes no later action.

This packet requests exactly one D4 training-simulator transition for
candidate `#1541`, followed by a conditional generation-one
checkpoint if the native receipt verifies. It selects qualification
`#12259`, witnessed by distinct training goals 0985 and 0986.
No validation or held-out worlds are included. The candidate is rooted in the
registered D4 full-arm generation-zero checkpoint.

| Binding | Value |
|---|---|
| Parent checkpoint | Full-arm g0, `fa79f67d5ea71d15f5b70f43efd2c2047af3c84b9258b25c61a0d97d84bf8b7b` |
| Candidate / expression digest | `#1541` / `15ab127dc160101ea078c7eea5b91b5339bc4ca6a73a20048c5facb27656b651` |
| Expression key | `power2:rot90` |
| Candidate effect | `[[3,2,1,0]]` |
| Parameters | `[3, 2, 1, 0]` |
| Selected qualification | `#12259`, two native-verified trials |
| Training witnesses | `p22:d4-v2:train:0985`, `p22:d4-v2:train:0986` |
| Verified transfer child | `#4022`, effect `[[0,2,1,3]]` |

The active full-root held effects are `rot90` `[1,3,0,2]` and `flip_r`
`[2,3,0,1]`. Both the candidate effect and selected transfer-child effect are
absent from that active set. The source and exact replay with native rule-work measurement reproduce candidate
`#1541`, its two qualifications, and the selected witnesses.
Both artifacts contain zero approvals or receipts and empty validation and
held-out allocations. Source SHA-256 `8adab01214d86cbde56c2eca1d92ea0ce0b201f82373d94043d4c6c4b2e2f083`; replay
SHA-256 `b91b3dfcf59c234f0c91f8ce01c54607c972d7d13f68411f5f1df11181d72d24`.

Authorization covers only one simulator transition on training world 0985 and
the conditional g1 checkpoint. It authorizes no later-generation action,
validation or held-out access, or efficacy claim. The output path is one-shot
and currently unused.

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family d4 --training-draws 985 986 987 988 \
  --training-goal-relation distinct --validation-start 989 --validation-count 0 \
  --per-request-attempt-ceiling 5000 --global-attempt-ceiling 20000 \
  --search-ticks 60 --candidate-transfer-depth 3 --measure-native-rule-work \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_D4_FULL_0985_0986.json \
  --approve-digest 15ab127dc160101ea078c7eea5b91b5339bc4ca6a73a20048c5facb27656b651 --review-seconds REVIEWER_REPORTED_SECONDS \
  --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_d4_full_0985_0986.json
```

To authorize exactly this action, reply:

`approve 15ab127dc160101ea078c7eea5b91b5339bc4ca6a73a20048c5facb27656b651; review_seconds=<your seconds>`

Machine request: [`COGNITION_P22_APPROVAL_REQUEST_D4_FULL_0985_0986.json`](COGNITION_P22_APPROVAL_REQUEST_D4_FULL_0985_0986.json).
