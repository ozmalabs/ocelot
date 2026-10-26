# P22 Loopover full-arm generation-one continuation approval request

Status: **awaiting exact user approval**. This packet requests exactly one training-simulator transition for candidate `#41661` on the registered full-arm g1 lineage, followed by a conditional generation-two checkpoint if its native receipt verifies. It uses no validation or held-out world.

## Candidate and replay evidence

Candidate `#41661` has expression digest `0161d4a90b5a2c8f07dbf673ce09ef7c4dbf0bafaf4047af36891a2eabee92f9`, expression key `compose:C0:R0'`, parameters `[3, 0, 1, 6, 4, 5, 2, 7, 8]`, and effect `[[1, 2, 6, 0, 4, 5, 3, 7, 8]]`. It qualified as `#50336` under `independent_goal_composition` on distinct training worlds `p22:loopover-v2:train:0174` and `p22:loopover-v2:train:0177`, with witness attempts `#41601` and `#47877`. Source and exact replay agree on candidate digest, parameters, qualification, witness attempts and training-world keys. Their read-only attempt exports are byte-identical (48,750 unique IDs: 48,709 residual and 41 verified), SHA-256 `d92c50c0d4b70256a82b00055fea863948f34f718c059d5fb0eee86636eaca71`.

The candidate effect is non-identity and absent from all 12 active process effects in the bound g1 parent. Source resource snapshot `1fd99993760a1a6b8d82ac82ad57b6dafa827a25f5a9ca1b6b398112be42a040` and native-work snapshot `7a153632cf733794e4c5befb3d29c30d6b6c125dd6cc15fa7f1b7882a7342531` validate; native-rule identity coverage is complete with zero unresolved rules. The source records 124 native rule steps, 1,314.329 seconds wall time, 3,959,246,848-byte peak RSS (PID `2286726`), and 233,212 cumulative declared primitive work, below the 600,000 development ceiling. The replay source result SHA-256 is `035ce23d6bfc727d4826204b532d0dcadf75ca2edd5c01406a388be430a130a5`; its attempt export has the same digest as the source. These are development measurements, not frozen P22 ceilings or efficacy results.

Source result SHA-256: `940b012c2feeaf9ffeb88bb252a6d5122d0730b89ecb8bd1a5ef94610977998d`. Replay result SHA-256: `035ce23d6bfc727d4826204b532d0dcadf75ca2edd5c01406a388be430a130a5`.

## Requested transition

If approved, the guarded runner will reconstruct and verify this exact candidate from the registered parent, record reviewer-reported review time, perform one simulated transition on `p22:loopover-v2:train:0174`, verify its receipt, and conditionally capture child checkpoint `p22-loopover-g2-0161d4a90b5a`. The parent is `p22-loopover-g1-c9f470ba1639`, digest `0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`. This authorization covers only this one action; no later action, validation, held-out access, or efficacy claim is permitted by it.

To authorize exactly this action, reply with:

`approve 0161d4a90b5a2c8f07dbf673ce09ef7c4dbf0bafaf4047af36891a2eabee92f9; review_seconds=<your seconds>`

Machine binding: [`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0174_0177.json`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0174_0177.json).
