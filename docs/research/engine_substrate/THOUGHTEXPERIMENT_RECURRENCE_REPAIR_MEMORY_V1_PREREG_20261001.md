# Recurrence-ledger repair rehearsal memory v1 — preregistration

**Date:** 2026-10-01  
**Question:** What current RSS/PSS is added while an isolated thoughtexperiment branch restores the recurrence-ledger idempotence guard and runs native closure at 100k/200k graph sizes?

## Design

Use the existing controlled fault from `thoughtexperiment_recurrence_offer_idempotence_v1.py`: remove only `Not Exists(candidate.has_mint_offer)` from `mrl_offer_due_once`, retaining its authored match/effects and one candidate/evidence task graph. Add a linked unrelated noise graph of 100,000 or 200,000 nodes. Cross sizes with native eager full-copy and shared-graph-page experiment forks; run three fresh processes per cell with no warmup.

After the faulted primary is ready, sample baseline Linux `smaps_rollup`, then start a 10 ms sampler and perform the actual correction rehearsal: fork, replace the faulted branch rule with the original authored rule, run five bounded native closure sweeps, query the candidate's `has_mint_offer` count, and require a zero-progress fixed point. Sampling continues through branch deletion and garbage collection. The production task oracle is exactly one offer for this candidate; no collapse-model surrogate is used.

## Gates

- Four size/backend cells and 12 unique fresh processes complete with stable source/native provenance.
- Each corrected branch restores the original `where` clause, emits exactly one offer, and reaches zero-progress fixed point.
- The primary graph/rule revision and node/edge counts remain unchanged by branch rehearsal.
- Eager and shared-page branches produce the same task and closure outcomes at each size.
- Report baseline, sampled peak, post-drop RSS/PSS and peak deltas; retain negative deltas and outliers.

## Interpretation limits

One authored recurrence-ledger correction family and one host. PSS sampling may miss peaks shorter than 10 ms; branch closure and task fixture are synthetic. The probe does not cover concurrent branches, false candidates, natural-task graph distributions, or full serving load.
