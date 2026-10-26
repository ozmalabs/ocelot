# P22 Loopover full-arm generation-one continuation approval request

Status: **awaiting exact user approval**. This packet requests exactly one
training-simulator transition for candidate `#44071` on the registered full-arm
g1 lineage, followed by a conditional generation-two checkpoint if its native
receipt verifies. It uses no validation or held-out world.

## Candidate and replay evidence

Candidate `#44071` has expression digest
`20e47b09a3ffcac98a672c43a43cb94c6bccc4a5ae958428d54ff9845ab28b5e`, expression key `compose[compose:C1:R0|C0']`,
parameters `[1,4,6,0,7,5,3,2,8]`, and effect `[[3,0,7,6,1,5,2,4,8]]`.
The complete native expression tree is bound by its digest and will be
reconstructed and checked by the guarded runner. It qualified as `#59086` under
`independent_goal_composition` on the distinct training worlds `p22:loopover-v2:train:0126` and
`p22:loopover-v2:train:0128`, with witness attempts `#43754` and `#50753`.
The source and exact replay agree on the candidate digest, parameters,
qualification ID and kind, witness attempts, and training-world keys. Their
read-only attempt exports are byte-identical (57,500 unique IDs; 57,461
residual and 39 verified) with SHA-256
`3909dd2341bcbd16dd7e2361964f4a6d5e6263b62233712f05caf450344bae8f`.

The qualification transfer on draw 0128 produced child `#51580`, digest
`50b021ab7c8ebc706d9238bdee527c67ed0ae19a77bba2dc0a6115fe97d1a818`, parameters `[0,1,6,2,3,4,5,7,8]`, and effect
`[[0,1,3,4,5,6,2,7,8]]`. A direct comparison against the 12 active
process effects in the bound g1 parent found both source and child effects
absent. Both are non-identity. Source and replay resource and native-work
snapshot checks pass; native-rule identity coverage is complete with zero
unresolved rules. Neither run added an approval, receipt or checkpoint, and
both have empty validation and held-out allocations.

The source result SHA-256 is
`500787ceac7f618e2a99dcb0bd814a6f649418d18dd5f61bc5e6d36fff21eca0`; the exact
replay result SHA-256 is
`33fc4106307607f533376b98ffa42cd4fdff7b13cdcdf167bb507a6fefee6673`. The
source resource snapshot digest is
`bad1db222202cf3bde4e71095b506b5725865905fe91db10052a715657c5d4eb`, and its
native-work digest is
`95985d3a446e5e883ea9f9b1a6186a35b45d4d14827ef7696cd07d8f09d32849`.
The source records 127 native rule steps, 1,570.792 seconds wall time,
3,957,927,936-byte peak RSS (PID `343274`), and 292,794 cumulative declared
primitive work, below the current 600,000 development ceiling. The replay has
127 native steps, 1,565.798 seconds wall time, 3,958,132,736-byte peak RSS, and
the same cumulative primitive work. These are development measurements, not
frozen P22 per-field ceilings or efficacy results.

## Requested transition

If approved, the guarded runner will reconstruct and verify this exact candidate
from the registered parent, record the reviewer-reported review time, perform
one simulated transition on `p22:loopover-v2:train:0126`, verify its receipt,
and conditionally capture child checkpoint `p22-loopover-g2-20e47b09a3ff`.
The parent is `p22-loopover-g1-c9f470ba1639`, digest
`0b3c72435539f7785833f1ca1474b105ef9d4d358620b92f1950820e718ec491`. The
one-shot output path is currently unused. This authorization would not permit
any later action, validation or held-out access, or an efficacy claim.

To authorize exactly this action, reply with:

`approve 20e47b09a3ffcac98a672c43a43cb94c6bccc4a5ae958428d54ff9845ab28b5e; review_seconds=<your seconds>`

Machine binding: [`COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0126_0128.json`](COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_FULL_G1_0126_0128.json).
