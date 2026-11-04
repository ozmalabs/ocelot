# P22 candidate-specific simulated-adoption request: D4 0635–0639

**Status: superseded by [`COGNITION_P22_APPROVAL_REQUEST_D4_0718_0721.md`](COGNITION_P22_APPROVAL_REQUEST_D4_0718_0721.md). No action has been taken under this request.**

The later candidate qualified on three independent-goal pairs rather than two.
The old machine request is marked `superseded`, so the guarded CLI will reject
it; approval of this old digest must not be used for a transition.

This request covers one guarded D4 training-simulator transition for candidate
`#26693`, followed by capture of its generation-three checkpoint only if the
native receipt verifies. It grants no validation or held-out access, no later
adoption, and no claim of efficacy. The machine request binds one of the
candidate's two independent-goal qualification records, identified as
`#66758`.

| Binding | Value |
|---|---|
| Family / domain | D4 v2 / `p22-development` |
| Candidate / qualification | `#26693` / `#66758` |
| Expression digest | `211bacf1856f917926bfff4811ff2e08d76d3f0deac3d803a898a2d5c02cc958` |
| Expression key | `compose[compose:flip_r:rot90|rot90]` |
| Effect digest | `[[1,0,3,2]]` |
| Parameters | `[1,0,3,2]` |
| Guard state | `[0,1,2,3]` |
| Training witnesses | `p22:d4-v2:train:0635`, `p22:d4-v2:train:0637` |
| Parent checkpoint | `p22-d4-g2-1e3590935d29`, generation 2 |
| Parent digest | `5799cb611c33a58de30c2590bbaa5f294794f0a9f9705707454072645bb694fc` |
| Transition | one D4 permutation action on training draw 0635 |
| Validation / held-out | none |

The measured effect is non-identity: it maps `[0,1,2,3]` to `[1,0,3,2]`.
This is a simulator lineage action only; it does not demonstrate improvement.
The source panel had five distinct goals, and all five tasks remained stuck.
The candidate has two qualification records; this request selects `#66758`
and binds exactly its two training witnesses. The other qualification is not
part of this approval binding.

To authorize exactly this one transition and its conditional generation-three
checkpoint, reply with the digest and reviewer-reported time, for example:

`approve 211bacf1856f917926bfff4811ff2e08d76d3f0deac3d803a898a2d5c02cc958; review_seconds=12`

The duration will be recorded as `reviewer_self_report`; it will not be
inferred. A response that does not name this digest and a nonnegative review
duration does not authorize action.

## Reproducible execution binding

The machine request is
[`COGNITION_P22_APPROVAL_REQUEST_D4_0635_0639.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0635_0639.json).
The guarded CLI will restore and hash-check the generation-two checkpoint,
reconstruct the candidate from the bound training draws and ceilings, verify
qualification `#66758` and both witness keys, and reserve the one-shot output
path before the action. Its exact output path is
`evaluation/process_mastery/results/p22_approved_candidate_d4_0635_0639.json`.
The source training artifact is
[`p22_training_panel_continuation_d4_0635_0639.json`](../../../evaluation/process_mastery/results/p22_training_panel_continuation_d4_0635_0639.json),
SHA-256 `da014e9efc9e9522d15920bc5bb131424963269f359accab7e663086316fa81a`.
