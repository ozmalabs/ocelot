# P22 v2 candidate-specific simulated-adoption requests

These candidates were produced and qualified only from v2 training worlds.
The exact digests below come from [`COGNITION_P22_V2_DEVELOPMENT_PROBES_20261023.md`](COGNITION_P22_V2_DEVELOPMENT_PROBES_20261023.md) and its raw records. Neither candidate has an approval, action receipt, or checkpoint. The validation outcomes shown are already-consumed development diagnostics and are not evidence of independent-goal improvement.

An approval request is limited to reconstructing the named candidate, checking its complete native binding, and running the existing guarded simulated-world adoption check within the stated finite family domain. It does not authorize other candidates, physical actions, any held-out allocation, or an efficacy claim. If reconstruction changes any digest, parameter, guard, or epoch, the approval does not apply.

| Family | Candidate | Expression digest | Expression key | Parameters | Qualified training trials | Prior dev validation |
|---|---:|---|---|---|---|---:|
| D4 v2 | `#752` | `8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788` | `compose:flip_r:rot90` | `[0, 2, 1, 3]` | `p22:d4-v2:train:0001`, `p22:d4-v2:train:0007` | 16/200 |
| Loopover v2 | `#2945` | `4df6b75c23c6dec5e67c45d09e3e2d31ad416fd9202c6b44fd9c0783dfff5711` | `compose[compose:R2':C1|C2]` | `[0, 4, 5, 3, 7, 8, 2, 6, 1]` | `p22:loopover-v2:train:0001`, `p22:loopover-v2:train:0003` | 0/200 |

The two training worlds per family had the same generated goal, although they had distinct world IDs and training trials. This supports candidate qualification, not an independent-goal lineage. Before any approval is consumed, the candidate must be reconstructed in a fresh graph and its exact expression digest, operator parameters, guard, source/model/frame epochs, effect probes, and two qualification witnesses must be checked against the authoritative graph. No development validation draw may be reused for later preregistered evaluation.

A later selected-pair mechanism probe is recorded in
[`COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md`](COGNITION_P22_CROSS_GOAL_COMPOSITION_20261023.md).
The D4 `#752` expression digest above is unchanged and received an additional
distinct-goal training qualification witness in that ephemeral graph. The
Loopover source candidate from that probe has digest
`f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d`, which is
different from the Loopover candidate listed in this request; it is not covered
by this table. This evidence does not approve either expression, change the
scope of this request, or authorize an action or checkpoint.

## Updated candidate-specific requests after distinct-goal qualification

The selected-pair composition probes produced a later exact candidate in
each family. These are the candidates relevant to a cross-goal simulated
adoption check; the earlier same-target Loopover row above is retained as
history and must not be treated as the current Loopover binding.

| Family | Candidate | Expression digest | Parameters | Distinct training goals | Qualification witnesses | Validation diagnostic |
|---|---:|---|---|---|---|---:|
| D4 v2 | `#752` | `8a737c4d9d27d7e97233ddbc57921fb661e088a65fecce23eea884b7a8753788` | `[0, 2, 1, 3]` | draws `0200 → 0202` | source attempt `#751`, second-goal attempt `#3194` | 3/8 |
| Loopover v2 | `#5761` | `f8277f0f8d7df4de63aed09cfc4f265ed2f6d9293034ae73ec18fdb9babfe75d` | `[0, 3, 2, 5, 1, 7, 6, 4, 8]` | draws `0015 → 0026` | source attempt `#1483`, second-goal attempt `#5770` | 0/8 |

These digests and parameters match the raw cross-goal artifacts. Node IDs are
local to their ephemeral graphs. Before any approval is consumed, each
candidate must be reconstructed and its complete tree, effect digest, guard,
epochs, training split, qualification witnesses and simulator action binding
must match. The scope requested is exactly one guarded attempt per candidate
in its registered finite simulator. A mismatch aborts before approval
creation. No other candidate, held-out draw, physical action, or lineage
generation is included; generation 2+ requires separate candidate-specific
authorization. The source candidates remain unapproved in the raw records.

Fresh training-only graph reconstructions verify the complete current
bindings without replaying validation:

- D4, draws `0200/0202`, raw SHA-256
  `9e903ccadb7127aeeba55a7e2be85bc1713f278047a00214f50086cf497b5668`.
- Loopover, draws `0015/0026`, raw SHA-256
  `b79b41a785784c2abbe04761be49c881f09f0967742ce6cb496a4d84ee312834`.

Both artifacts retain the expression tree, effect digest, guard, epochs,
parameters and native qualification witnesses. They contain no validation
worlds, approvals or receipts. The Loopover digest above is the corrected raw
value; any candidate-specific approval must match it exactly.

**Digest transcription correction:** The D4 digest in the first version of
this request was transcribed incorrectly. The value above now matches the
authoritative raw candidate record and the later composition probe. No
approval was consumed against the incorrect transcription; any future
approval must bind the corrected digest and full candidate bindings.

## Approved simulated-adoption record (2026-10-23)

The user approved the exact two candidate bindings above for one guarded
attempt apiece in their registered finite simulators. Fresh graphs were
rebuilt from training draws only. Each graph checked the full candidate
binding, the two named distinct-goal training witnesses, and the current
digest before creating one human-kind candidate-specific approval. Each
approval was consumed by the native adoption gate, followed by exactly one
guarded transition in the finite permutation simulator. Both native execution
receipts verified.

- D4 `#752`: one verified transition on `p22:d4-v2:train:0200`, producing
  `[0,2,1,3]`; approval `#7141` was consumed and receipt `#7143` verified; raw result is
  [`p22_simulated_adoption_d4_200_202.json`](../../../evaluation/process_mastery/results/p22_simulated_adoption_d4_200_202.json).
- Loopover `#5761`: one verified transition on `p22:loopover-v2:train:0015`,
  producing `[0,4,2,1,7,3,6,5,8]`; approval `#10771` was consumed and receipt
  `#10773` verified; raw result is
  [`p22_simulated_adoption_loopover_015_026.json`](../../../evaluation/process_mastery/results/p22_simulated_adoption_loopover_015_026.json).

Each raw result records one approval, one world receipt, and one simulator
transition. No validation or held-out world was used, and neither run makes an
efficacy claim or authorizes a later lineage generation. New candidates and
generation 2+ adoptions still require their own exact authorization.
