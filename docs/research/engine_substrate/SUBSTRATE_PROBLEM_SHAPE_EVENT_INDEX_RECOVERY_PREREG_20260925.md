# ProblemShape event/index checkpoint and rebuild preregistration

**Status:** isolated recovery/equivalence probe for the all-transition event variant.

## Question

After saving an eventized ProblemShape graph with one residual mint-candidate and a support index, can a fresh `WorldAdapter.load` restore the rule/grammar state, rebuild the derived key-support index from observations, and continue to the same final state as uninterrupted closure?

## Arms and checkpoint point

Use the N=8 recurrent-residual workload. Both arms run identical boot, scaffolding, goal construction, and first-observation steps. The uninterrupted arm continues in memory. The recovery arm saves immediately after the first observation settles residual, with its residual-candidate event present and support count 1. It loads through `WorldAdapter.load`, verifies all five ProblemShape rules and event grammar productions, deletes the graph-resident `ProblemShapeKeyIndex` rows, rebuilds support rows and links from the observation records, rebuilds the host key→NodeID lookup, and continues observations 2–8. Event edges and observation nodes are retained from the checkpoint.

## Required checks

- Distinct fresh process IDs; checkpoint save/load succeeds.
- Checkpoint has one residual candidate event and correct first-observation/index support state.
- Restored rule slots and custom event productions exist.
- Rebuilt support counts equal an independent grouping of all observations by key; each observation links to exactly one index.
- Both arms end at fixed point with eight recognized observations, one minted shape (`ps_has_bound=yes`, support snapshot 2), codebook epoch 1, and no pending/decoded/residual-candidate event edges.
- Final application-visible observation states, codebook shape records, index support, codebook epoch, and event counts match between arms.

## Scope

One authored N=8 sequence, one checkpoint point, and one derived-index loss/rebuild path. This is not corruption recovery, concurrent writer safety, crash consistency under partial effects, long-term persistence, or a broad scale test. A failure is preserved as a diagnostic; no tuning during the locked comparison.
