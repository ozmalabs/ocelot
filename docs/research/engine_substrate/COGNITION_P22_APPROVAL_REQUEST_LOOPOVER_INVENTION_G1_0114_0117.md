# P22 candidate-specific simulated-adoption request: Loopover invention-only g1 0114–0117

**Status: awaiting exact user approval.** This packet requests exactly one training-simulator transition for candidate `#31572` and a conditional generation-two checkpoint if the native receipt verifies. It includes no validation or held-out worlds.

| Binding | Value |
|---|---|
| Family / arm | Loopover v2 / invention-only |
| Parent checkpoint | `p22-loopover-g1-2638da0f23ae` |
| Parent checkpoint digest | `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057` |
| Candidate | `#31572` |
| Expression digest | `7fb1f08e6ac6412d271feffcea1bfdec32dd3a484ecfaf42c13fa6a7a681a3ce` |
| Expression key | `compose[compose:R0:C0|R2]` |
| Source effect | `[[6,0,1,2,4,5,8,3,7]]` |
| Parameters | `[1,2,3,7,4,5,0,8,6]` |
| Guard state | `[0,1,2,3,4,5,6,7,8]` |
| Source/model/frame epochs | `0 / 0 / 0` |
| Qualification | `#76587`, `independent_goal_composition` |
| Witness goals | `p22:loopover-v2:train:0114` and `p22:loopover-v2:train:0115` |
| Witness attempts | `#21818` and `#34493` |

The source and exact replay agree on the candidate binding, qualification ID and kind, both witness goals and attempts, and all 75,000 attempt records. Their read-only attempt exports are byte-identical. Source result SHA-256: `bc68b6ba331ce4849154f934289ab7f27c7c87e774598aaa572f0ce16c298a22`; replay result SHA-256: `06b781b1349a9df53bdde85a6f17cdc7ca411804800498dddf8f365dbe5b64fa`; shared attempt-export SHA-256: `21e6dc99125665ead20ff51522995d0929093837bd540bac06d0113571fcac1f`. Source and replay resource/native-work snapshot digests validate; both have complete native-rule identity coverage and zero unresolved rules.

The source effect is non-identity and absent from the 12 active effects in the registered parent. The verified independent-goal transfer attempt derives child `#36578`, whose effect `[[6,4,2,0,7,5,3,1,8]]` is also non-identity and absent from those active effects. All evidence is training-only; the four tasks remained stuck. One approval and receipt are inherited from the parent; this candidate has not been approved and no checkpoint exists for it.

The guarded command reconstructs the candidate from the registered parent and checks the exact binding before acting. It would execute on training draw 0114 and write the one-shot output path below:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family loopover --training-draws 114 115 116 117 \
  --training-goal-relation distinct --validation-start 0 --validation-count 0 \
  --per-request-attempt-ceiling 15000 --global-attempt-ceiling 120000 \
  --search-ticks 60 --candidate-transfer-depth 3 \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_INVENTION_G1_0114_0117.json \
  --approve-digest 7fb1f08e6ac6412d271feffcea1bfdec32dd3a484ecfaf42c13fa6a7a681a3ce \
  --review-seconds REVIEWER_REPORTED_SECONDS --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_loopover_invention_g1_0114_0117.json
```

This authorization covers one transition and its conditional g2 checkpoint only. It does not authorize later actions, validation or held-out access, or an efficacy claim. To authorize exactly this action, reply with:

`approve 7fb1f08e6ac6412d271feffcea1bfdec32dd3a484ecfaf42c13fa6a7a681a3ce; review_seconds=<your seconds>`

Machine packet: [`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_INVENTION_G1_0114_0117.json`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_INVENTION_G1_0114_0117.json).
