# P22 candidate approval request: Loopover full-arm g2

**Status:** awaiting exact user approval. No adoption has been attempted.

Candidate `#51583` has a verified expression digest of
`d260654d9a5e77ca5a42bfcfd764eaa0358ee42abb89f1bfec456050f8639dc0` and effect
`[[6, 4, 2, 0, 7, 5, 3, 1, 8]]`. It is an unapproved candidate descended from
Loopover full-arm g2 checkpoint `p22-loopover-g2-0161d4a90b5a`
(`477cfe40ae8db6158b7543f52ebf4b555a8bfb24cd524150ea0548508fe1b50b`).

The native qualification is `#54104`, kind `independent_goal_composition`,
with two verified training trials: attempts `#49127` and `#51873`, on distinct
worlds `p22:loopover-v2:train:0177` and `p22:loopover-v2:train:0228`.
The second trial produced transfer child `#53098`, which remains unapproved and
unqualified. A separate training continuation also recorded qualification
`#61610` on worlds 0177/0221. This request is bound to `#54104` because that
qualification was replayed exactly; `#61610` is recorded as corroborating
evidence but was not separately replayed. Exact replay reproduced candidate
digest, qualification, both witness attempt/task IDs and training keys. Source and replay attempt exports
are byte-identical across 60,000 IDs, SHA-256
`9f560b36723c90fdb916ada4757878499ca7948f038aa700b1bc252dab7957a7`.

The proposed action is one candidate-bound training-simulator transition and
a conditional generation-three checkpoint, using distinct training draws
0228–0231. It has no validation or held-out allocation. The request preserves
the existing per-request ceiling (2,500), global search ceiling (120,000),
search ticks (60), transfer depth (3), discovery limit (1,000), transfer
reserve (1,500), effect deduplication and all candidate qualification guards.
The run inherited two approvals and two receipts and created no new action or
receipt. This request does not reuse the earlier approvals for candidates
`#31572` or `#41661`.

Evidence:

- [Structured request](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G2_0228_0231.json)
- [Source result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g2_0228_0231_budget2500_discovery1000_transfer1500_p26.json.gz), SHA-256 `6e13ee1d7eecd20a652b9ec8d98c460dd2141accc9ad4bf9219efbadb28b4ef4`
- [Replay result](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_loopover_full_g2_0228_0231_budget2500_discovery1000_transfer1500_p26_replay.json.gz), SHA-256 `2747522df0d0cec7bf1416ea8f707146d752f5915f0e02d9b1373cae0d692cc1`
- [Source attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g2_0228_0231_budget2500_discovery1000_transfer1500.json.gz)
- [Replay attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_loopover_full_g2_0228_0231_budget2500_discovery1000_transfer1500_replay.json.gz)

To authorize exactly this candidate, reply:

`approve d260654d9a5e77ca5a42bfcfd764eaa0358ee42abb89f1bfec456050f8639dc0; review_seconds=<your seconds>`
