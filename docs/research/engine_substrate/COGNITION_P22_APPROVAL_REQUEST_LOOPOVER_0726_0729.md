# P22 candidate-specific simulated-adoption request: Loopover 0726–0729

**Status: awaiting exact user approval. No action has been taken.**

This request covers exactly one guarded Loopover training-simulator transition
for candidate `#10761`, followed by capture of its generation-one checkpoint
only if the native receipt verifies. It grants no validation or held-out
access, no later adoption, and no efficacy claim.

| Binding | Value |
|---|---|
| Family / domain | Loopover v2 / `p22-development` |
| Candidate / qualification | `#10761` / `#40779` |
| Expression digest | `0738c7336573a8a5ea914f9475dd0cc789007556a0c89f0527ecf740c449d80c` |
| Expression key | `compose[compose:C0':C1|C2]` |
| Effect digest | `[[3,7,8,6,1,2,0,4,5]]` |
| Parameters | `[6,4,5,0,7,8,3,1,2]` |
| Guard state | `[0,1,2,3,4,5,6,7,8]` |
| Selected qualification witnesses | `p22:loopover-v2:train:0726`, `p22:loopover-v2:train:0727` |
| Other qualifying pair | 0726/0728 (`#40780`); not part of this request |
| Transition | one Loopover permutation action on training draw 0726 |
| Validation / held-out | none |

The effect is non-identity. The candidate qualified on two independent-goal
pairs. The selected pair is bound exactly; the other qualification is not part
of this authorization. The simulator action and conditional checkpoint would
extend a lineage only and would not demonstrate improvement.

To authorize exactly this transition and its conditional generation-one
checkpoint, reply with the digest and reviewer-reported time, for example:

`approve 0738c7336573a8a5ea914f9475dd0cc789007556a0c89f0527ecf740c449d80c; review_seconds=12`

The duration will be recorded as `reviewer_self_report`; it will not be
inferred.

## Reproducible execution binding

The machine request is
[`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0726_0729.json`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0726_0729.json),
SHA-256 `0a7f3d5382eb7e351bbdca77e562b7a0c7840761a59eaefe8b26b2f27a004d07`.
It binds depth-three transfer, the 10,000 per-request and 40,000 global
training ceilings, the 30 search ticks, the four distinct training draws, the
selected qualification and the single output path
`evaluation/process_mastery/results/p22_approved_candidate_loopover_0726_0729.json`.

The compressed source artifact is
[`p22_training_panel_loopover_0726_0729_three_held.json.gz`](../../../evaluation/process_mastery/results/p22_training_panel_loopover_0726_0729_three_held.json.gz),
SHA-256 `b7360f2ca4c25af12f3cf8c2451b60ce33452dade8e27eaba52b6069b1c2b844`;
its decompressed raw SHA-256 is
`0338b3be46c8f4944c5963fe04c390764d38e5af8e4aec5bd4a74d412d820c6d`.
The guarded CLI reconstructs the candidate from these training draws and
requires this exact digest and reviewer-reported time before the one action.

## Read-only request reconstruction check

The exact four-draw request was replayed without approval flags on the same
training-only allocation. It reproduced candidate `#10761`, the expression
digest, parameters, both qualification IDs and witness pairs exactly. The
replay used 40,000 search attempts, created no approval or receipt, and had no
validation allocation. Its compressed artifact is
[`p22_candidate_approval_replay_loopover_0726_0729.json.gz`](../../../evaluation/process_mastery/results/p22_candidate_approval_replay_loopover_0726_0729.json.gz),
SHA-256 `9da556763aa04d34deac9fdb3d926a5d18cdeaf837bd89ad9a437e75462243a8`;
decompressed raw SHA-256
`bdf4dea9c0e8a7c6bbf9d77e78f5894d17ef9a33b3cca2f1b6e040a4b079cdb5`.
