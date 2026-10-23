# P22 candidate-specific simulated-adoption request: D4 0562/0563

**Status: consumed.** The exact approval was supplied with 12 reviewer-reported
seconds. Human approval `#16727` was consumed, one identity-effect transition
was executed, and verified receipt `#16730` produced generation-two checkpoint
`p22-d4-g2-1e3590935d29`. See the result artifact below for the full record.
This request authorizes no additional action.

This request covers one guarded simulator transition for the candidate below,
then capture of its generation-two checkpoint only if the native receipt
verifies. It does not authorize any later adoption, a Loopover candidate,
preregistration, or held-out access. Candidate IDs are local to the restored
development graph; the digest and full binding are authoritative.

| Binding | Value |
|---|---|
| Family / domain | D4 v2 / `p22-development` |
| Ephemeral candidate ID | `#6731` |
| Expression digest | `1e3590935d290140171bd81f966a1dcc336e72278231d844b6411f7a2286f9b4` |
| Expression key | `inverse:p22-d4-generation-zero-identity` |
| Expression tree | `guard([0,1,2,3], inverse(generation-zero identity))` |
| Effect digest | `[[0,1,2,3]]` (identity permutation) |
| Parameters | `[0,1,2,3]` |
| Guard state | `[0,1,2,3]` |
| Source/model/frame epochs | `0 / 0 / 0` |
| Qualification | `independent_goal_composition`, two native-verified training trials |
| Training witnesses | `p22:d4-v2:train:0562`, `p22:d4-v2:train:0563` |
| Parent checkpoint | `p22-d4-g1-badd1251ee4e`, generation 1 |
| Parent digest | `f3d6c15ac7f9187cef0e4c7ca21f3615958955565101a891fbc8796c997e6ed6` |

The candidate's measured effect is the identity permutation. Its one
registered simulator transition left the D4 state unchanged. This request
therefore offers a mechanically valid lineage edge only; it cannot be
presented as a process improvement or positive efficacy result. The candidate
qualified across two distinct training goals, but it had no validation
evidence.

The parent is loaded from the exact generation-one checkpoint embedded in
[`p22_approved_candidate_d4_0406_0407.json`](../../../evaluation/process_mastery/results/p22_approved_candidate_d4_0406_0407.json).
The guarded CLI now verifies the source artifact SHA-256, checkpoint digest,
resource snapshot, and full native graph before reconstructing this
candidate. It freezes the training/search ceilings from the machine binding,
then required this exact expression digest and reviewer-reported review
seconds before reserving the one-shot output path.

The training-only source probe is
[`p22_d4_generation2_training_0562_0563.json`](../../../evaluation/process_mastery/results/p22_d4_generation2_training_0562_0563.json),
SHA-256 `f068f8ab759f78c3d38bfe994f8c0c9c65a1fadf530b09804450dbba0594a27a`.
Its two distinct training goals are `[0,1,2,3]` and `[2,3,0,1]`. The
candidate-specific qualification record names two training witnesses and
native verified effects. The source artifact contains no validation worlds.

The original exact approval instruction, now fulfilled, was:

`approve 1e3590935d290140171bd81f966a1dcc336e72278231d844b6411f7a2286f9b4; review_seconds=12`

The duration is recorded as `reviewer_self_report`; it was not inferred. The
candidate effect was identity, so this action is not evidence of improvement.

## Reproducible execution binding

The machine-readable request is
[`COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.json).
Its original `awaiting_exact_user_approval` status and bytes remain unchanged
because the CLI binds the raw document hash; consumption is recorded in the
result artifact and in this human-readable request. Its output path is
already claimed and must not be reused.
Its fixed output path is
`evaluation/process_mastery/results/p22_approved_candidate_d4_0562_0563.json`.
The consumed command was:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family d4 --training-draws 562 563 --training-goal-relation distinct \
  --validation-start 0 --validation-count 0 \
  --per-request-attempt-ceiling 10000 --global-attempt-ceiling 60000 \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_D4_0562_0563.json \
  --approve-digest 1e3590935d290140171bd81f966a1dcc336e72278231d844b6411f7a2286f9b4 \
  --review-seconds 12 --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_d4_0562_0563.json
```

This records the consumed invocation. The request-bound output already exists,
so the command cannot be replayed. It rejected any different parent artifact,
parent digest, candidate binding, training split, search ceiling, output path,
or approval digest; the output was reserved durably before proposal/action
work.
