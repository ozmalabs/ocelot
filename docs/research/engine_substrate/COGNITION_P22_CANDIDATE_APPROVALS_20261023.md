# P22 candidate-specific approval requests (2026-10-23)

These two candidates were generated from the registered **training** worlds and each qualified after a second distinct training trial with a native-verified attempt. Their effect fingerprints were verified against family-sized probe batteries. Each fresh-process reconstruction reproduced the candidate ID, digest, expression key, effect fingerprint and parameters. Both remain `unapproved_candidate`; no approval node, action receipt, checkpoint, or held-out access has been created.

Subsequent generator auditing found that the v1 family seeds used for these cards yield only two distinct goals across 200 validation draws in each family. The cards preserve exact mechanism provenance but do not establish independent-goal generalization. The versioned v2 generators use disjoint family seed codes and a more varied goal distribution; any P22 efficacy claim must use its preregistered panel and working matched arms, not these v1 probe results.

An approval authorizes only adoption of the named expression in its stated finite domain, followed by the existing guarded simulated-world execution check. It does not authorize another candidate, physical-world action, a held-out run, or an efficacy claim.

| Family | Training world | Candidate | Proposal / qualification | Qualified trials |
|---|---|---|---|---:|
| Loopover | `p22:loopover:train:0011` (seed `32010011`) | `#751`, digest `40bdfbc6b1459d0e2d77ca7233a270a1f53c4692c06bcf3296923e3fc31090f3` | `#1111` / `#1475` | 2 |
| D4 | `p22:d4:train:0012` (seed `32020012`) | `#1082`, digest `6419f6b9869df9bfedf41ff7f7aed37008e4686b3dfd1dd7012acdf20f5eb56b` | `#1084` / `#1420` | 2 |

## Loopover candidate `#751`

- Training trials: `p22-loopover-train-11-trial1`, `p22-loopover-train-11-trial2`.
- Expression key: `compose:R0:C1`.
- Expression tree: `("guard", [0,1,2,3,4,5,6,7,8], ("subgoal", [2,0,1,3,4,5,6,7,8], ("compose","R0","C1")))`.
- Parameters: `[4,2,0,3,7,5,6,1,8]`.
- Verified effect fingerprint on the fixed training probe: `[[2,7,1,3,0,5,6,4,8]]`.
- Guard: `[0,1,2,3,4,5,6,7,8]`; domain `search`; source/model/frame epochs `0/0/0`.
- Approval kind required: `human`; candidate status: `unapproved_candidate`.

## D4 candidate `#1082`

- Training trials: `p22-d4-train-12-trial1`, `p22-d4-train-12-trial2`.
- Expression key: `compose:rot90:flip_r`.
- Expression tree: `("guard", [0,1,2,3], ("subgoal", [2,0,3,1], ("compose","rot90","flip_r")))`.
- Parameters: `[3,1,2,0]`.
- Verified effect fingerprint on the fixed training probe: `[[3,1,2,0]]`.
- Guard: `[0,1,2,3]`; domain `search`; source/model/frame epochs `0/0/0`.
- Approval kind required: `human`; candidate status: `unapproved_candidate`.

The graph instances used to inspect these candidates were ephemeral development runs. The listed IDs and bindings were reproduced in fresh runs; any later approval must still be inserted only after reconstructing the graph and rechecking that its exact candidate digest and all approval fields match this packet.
