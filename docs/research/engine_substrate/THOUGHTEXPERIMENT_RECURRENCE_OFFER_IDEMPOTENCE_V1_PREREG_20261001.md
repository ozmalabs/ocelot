# Thoughtexperiment recurrence offer idempotence v1 — preregistration

**Date:** 2026-10-01  
**Question:** Can an isolated thoughtexperiment branch restore an omitted idempotence guard in a distinct, production-authored minting rule, and can an independent graph oracle distinguish the faulty and repaired behavior?

## Design

Use `mrl_offer_due_once` from the production recurrence-ledger seed. In a fresh standard core substrate, construct one recurrence episode, one candidate at its minting threshold, and one supporting evidence node. Create the faulty treatment by removing only the rule's `Not Exists(candidate.has_mint_offer)` guard. Preserve the original authored rule as the candidate repair. On one fresh graph, run five bounded native closure sweeps to establish the faulty positive control. On a second isomorphic graph, keep the faulty rule in the primary, fork a deep-copy thoughtexperiment branch, replace the faulty rule in the branch with the original authored rule, and run the same sweeps. Do not adopt the branch result into the primary.

The independent task oracle counts `Observation` offers connected to the recurrence candidate. The faulty control must produce more than one offer. The repaired branch must produce exactly one offer, and a final native closure sweep must make zero progress. Compare full primary graph and rule state before and after branch rehearsal. Run three independent worker processes.

## Gates

- Three fresh worker processes complete with identical protocol and stable source/native fingerprints.
- The only injected fault is omission of the existing negative-existence guard from `mrl_offer_due_once`.
- Faulty control produces duplicate candidate-linked offers (>1).
- The branch contains the original authored guard and produces exactly one candidate-linked offer.
- Repaired branch reaches zero-progress native closure.
- Primary graph and rewrite-rule state remain identical across branch repair and rehearsal.

## Interpretation limits

This is a controlled fault-injection task in a second domain, not evidence that the live substrate autonomously found the missing guard. The repair is the known authored rule and branch creation uses the full-copy experiment backend. This does not establish cross-family outcome transfer, general candidate discovery, COW speed, or natural-task frequency. It establishes a second independently-oracled task shape for the thoughtexperiment/adoption programme.
