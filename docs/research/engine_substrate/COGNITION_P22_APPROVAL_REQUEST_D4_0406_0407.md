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
