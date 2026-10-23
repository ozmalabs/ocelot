# P22 candidate-specific simulated-adoption request: D4 0406/0407

**Status: awaiting exact user approval; no approval or action has been created.**

This request covers one guarded simulator transition for the candidate below,
then capture of its generation-1 checkpoint only if the native receipt
verifies. It does not authorize a later-generation adoption, a Loopover
candidate, validation or held-out access, or an efficacy claim. Candidate IDs
are local to the fresh development graph; the digest and complete binding are
authoritative.

| Binding | Value |
|---|---|
| Family / domain | D4 v2 / `p22-development` |
| Ephemeral candidate ID | `#1089` |
| Expression digest | `badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255` |
| Expression key | `inverse[inverse:rot90]` |
| Expression tree | `guard([0,1,2,3], subgoal(null, inverse(null)))` |
| Effect digest | `[[2,0,3,1]]` |
| Parameters | `[1,3,0,2]` |
| Guard state | `[0,1,2,3]` |
| Source/model/frame epochs | `0 / 0 / 0` |
| Qualification | `independent_goal_composition`, two native-verified training trials |
| Training witnesses | `p22:d4-v2:train:0406`, `p22:d4-v2:train:0407` |

The registered D4 simulator binding is one transition from initial state
`[0,1,2,3]`, with predicted/expected observed state `[2,0,3,1]`. The native
guard must match exactly. The action is derived from the candidate's stored
parameters after a fresh training-only reconstruction checks the complete
tree/digest, effect, guard, epochs and both qualification witnesses. A
mismatch aborts before approval creation.

The source probe has no validation worlds, approvals or receipts. Its raw
SHA-256 is
`b1fc33b6b5a8d8044085662718ed3621b5c28e167ff661ec4742ed122797bad3` at
[`p22_approval_cost_instrument_probe_d4_406_407.json`](../../../evaluation/process_mastery/results/p22_approval_cost_instrument_probe_d4_406_407.json).

To authorize the one transition and conditional generation-1 checkpoint,
reply with an explicit approval naming this digest and your reviewer-reported
time in seconds, for example: `approve badd1251…d255; review_seconds=12`.
That duration will be recorded with source `reviewer_self_report`; it will not
be inferred from elapsed time or message length. A plain approval without the
duration does not authorize action because the preregistered resource field
would remain incomplete.

## Reproducible execution binding

The machine-readable candidate binding is [`COGNITION_P22_APPROVAL_REQUEST_D4_0406_0407.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0406_0407.json), SHA-256 `176035d013ba82192655b5461bfa45e7cbba2b5ed34a11eeb973940db5f8bc93`. It contains the exact candidate binding and registered training draws, but no reviewer duration. After explicit approval of the digest above and a reviewer-reported duration, execute only this training-only guarded transition with:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python scripts/run_p22_development_probe.py \
  --family d4 --training-draws 406 407 --training-goal-relation distinct \
  --validation-start 0 --validation-count 0 --measure-native-rule-work \
  --approved-candidate-binding docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_D4_0406_0407.json \
  --approve-digest badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255 \
  --review-seconds REVIEWER_REPORTED_SECONDS --execute-approved-adoption \
  --output evaluation/process_mastery/results/p22_approved_candidate_d4_0406_0407.json
```

Replace `REVIEWER_REPORTED_SECONDS` only with the duration explicitly supplied by the reviewer. The command rejects missing authorization fields, a mismatched digest, non-training-only settings, or an output path other than the one bound into the request. The CLI durably reserves that path before running any proposal or action work; success replaces the marker with the result, while an interrupted attempt leaves the marker and cannot be retried. Its CLI guard tests pass. This command is prepared for a future authorized action; it has not been run and creates no approval, receipt, or checkpoint by itself.
