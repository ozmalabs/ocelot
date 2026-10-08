# Thoughtexperiment shape-axis full-candidate admission v1 — preregistration

**Date:** 2026-10-02  
**Question:** Does the unchanged self-correction candidate generator produce at least three distinct edits with utility differences on disjoint shape-axis train and held-out observations, when every candidate is scored independently?

## Motivation and scope

The graph-authored correction rank study enumerated six candidates but stopped rehearsal after the first successful candidate; its raw capture has held-out utility outcomes for only two of six candidates. This study fills that utility-coverage gap. It does not estimate ranker quality, cross-family transfer, natural-task prevalence, or economic advantage, and it is not the four-family confirmatory panel.

## Procedure

Use the existing sd_mint_quantum shape-axis correction setup, graph-authored composers, and unchanged _default_candidates generator. Each worker creates separate deterministic training and held-out shape episodes using disjoint observation signatures. Each candidate is scored in a fresh process-local substrate context: create the existing correction impasse, snapshot an isolated branch, apply the candidate bundle only to the branch, introduce three new observations, settle native rules, and evaluate the direct task oracle.

The independent task oracle requires every held-out observation to leave pending, exactly one induced CapabilityAxis per new signature, and a zero-work native fixed point after settling. Also record whether the candidate patch applied, branch creation time, patch time, closure work/time, and total candidate evaluation time. A failed or inert candidate is retained and scored as utility 0. The primary graph and active rule store must match their pre-rehearsal state.

Run four fresh worker processes. The candidate label/digest set must be identical between each worker's train and held-out contexts and across all workers. Train and held-out observation signatures must be disjoint. Do not stop after a successful candidate.

## Integrity gates

- Lock protocol, runner, task rules/seeds, adapter/native sources, build identity, and loaded native binary before capture.
- Require a current native engine and exact source/binary lock parity before and after all workers.
- Require four distinct worker processes, six distinct unchanged-generator candidates per worker, and all six candidate utility records in both splits.
- Require all candidate score branches to preserve primary rules, and require the direct task oracle to be recomputed from held-out branch behavior.
- Preserve raw per-candidate records, including invalid, inert, and failed candidates.

Any failed gate is reported; no candidate or worker is removed after capture.

## Interpretation

Passing establishes full candidate-level utility coverage for this authored shape-axis task and supplies a reproducible candidate bundle for a later blinded ranker panel. It does not establish a general self-improvement capability.
