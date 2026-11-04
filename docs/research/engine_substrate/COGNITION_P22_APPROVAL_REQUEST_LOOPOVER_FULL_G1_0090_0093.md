# P22 candidate-specific simulated-adoption request: Loopover full-arm g1 0090–0093

**Status: awaiting exact user approval.** This packet requests exactly one training-simulator transition for candidate `#51571`, followed by a conditional generation-two checkpoint if the native receipt verifies. It includes no validation or held-out worlds.

| Binding | Value |
|---|---|
| Family / domain | Loopover v2 / `p22-development-loopover` |
| Parent checkpoint | Registered full-arm g1, `p22-loopover-g1-c9f470ba1639` |
| Parent checkpoint digest | `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491` |
| Candidate | `#51571` |
| Expression digest | `9eeb0bc005bbab8a0e8a8fc28adf1cf793604e29f7ef812392acf314bade652a` |
| Expression key | `compose[compose:C0:C1|C2']` |
| Source effect | `[[6,7,5,0,1,8,3,4,2]]` |
| Parameters | `[3,4,8,6,7,2,0,1,5]` |
| Guard state | `[0,1,2,3,4,5,6,7,8]` |
| Source/model/frame epochs | `0 / 0 / 0` |
| Qualification | `#96586`, `independent_goal_composition` |
| Witness goals | `p22:loopover-v2:train:0090` and `p22:loopover-v2:train:0092` |
| Witness attempts | `#41826` and `#66931` |

The source run and exact replay agree on the candidate binding, qualification ID, kind, and both distinct-goal witness keys. Both attempt exports are byte-identical. The source result SHA-256 is `5833e255c6cc9a4b5f4cb6d3309ed2636ffe15fda5b89f901fddbef351e52a41`; replay result SHA-256 is `9c3904e47c7928219f71953b7074801d598deb2fb599f891fea21e7f775b3f76`. The shared attempt-export SHA-256 is `e9b7f86ce1b55e644dc90b32d61897ded4fb8c1d5cf2a68bcf0cf6bbf7dfb905`. Source and replay resource/native-work digest checks pass with complete native-rule identity coverage.

The source effect is absent from the 12 active processes in the registered parent. The verified transfer child `#71580` has effect `[[0,7,5,3,1,8,6,4,2]]`, also absent from those active processes. All evidence is training-only; the search tasks remained stuck, and the candidate is unapproved until this exact request is authorized.

The guarded command reconstructs the candidate from the registered parent and verifies this binding before acting. It would execute on training draw 0090 and write the one-shot output path below:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family loopover --training-draws 90 91 92 93 \
  --training-goal-relation distinct --validation-start 0 --validation-count 0 \
  --per-request-attempt-ceiling 15000 --global-attempt-ceiling 120000 \
  --search-ticks 60 --candidate-transfer-depth 3 \
  --discovery-attempt-limit-per-request 10000 --transfer-reserve-per-request 5000 \
  --effect-dedup \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0090_0093.json \
  --approve-digest 9eeb0bc005bbab8a0e8a8fc28adf1cf793604e29f7ef812392acf314bade652a \
  --review-seconds REVIEWER_REPORTED_SECONDS --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_loopover_full_g1_0090_0093.json
```

This authorization covers one transition and its conditional g2 checkpoint only. It does not authorize later actions, validation or held-out access, or an efficacy claim. To authorize exactly this action, reply with:

`approve 9eeb0bc005bbab8a0e8a8fc28adf1cf793604e29f7ef812392acf314bade652a; review_seconds=<your seconds>`

Machine packet: [`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0090_0093.json`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0090_0093.json).
