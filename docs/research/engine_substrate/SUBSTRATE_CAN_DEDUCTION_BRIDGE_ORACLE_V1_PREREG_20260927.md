# CAN-to-deduction bridge oracle v1 preregistration

Date: 2026-09-27  
Status: preregistered protocol; no execution result yet.  
Scope: semantic fidelity of `can_state_as_predications`, not the quality of CAN beliefs or general inference capability.

## Question

Does the live bridge produce exactly the deduction facts entailed by the settled CAN Concept states, including the null/ambivalent case, and associate them with the entity denoted by the Microtheory?

This is the answer-level follow-up to the ProblemShape solver-family transfer v1.1. That result established Goal resolution and shape transfer but explicitly did not establish bridge answer quality.

## Source-derived contract

`domains/reasoning_can_bridge.py::can_state_as_predications` reads `state` from Concepts adjacent to a target Microtheory. Its declared mapping is:

| Settled state | Expected fact |
|---|---|
| `+1` | `is_a(entity, concept_name)` |
| `-1` | `is_a(entity, not_ + concept_name)` |
| `0` | no fact |
| absent | no fact |

The entity must be the denotation of the target Microtheory. The independently computed oracle will read the fixture's frozen input state table and expected entity label, then compare the exact expected predicate set with graph records emitted by ingestion. The analyzer must not call `can_state_as_predications`, reuse its state-branch helper, or derive expected labels from its output.

The current Bigville CAN fixture has five named Concepts (`trust_mayor`, `claim_credible`, `world_safe`, `self_worth`, `debtor_trustworthy`), making the complete ternary state panel 3⁵ = 243 cases. Include absent-state cases as a separate control rather than treating missing as zero.

## Panel and controls

1. Enumerate all 243 assignments in the fixed topic order, with each state in `{-1, 0, +1}`. Build an independently recorded expected fact set using the table above.
2. For each assignment, create a unique Resident, Microtheory, and five Concepts; attach them using the ordinary graph edges and record the intended Microtheory denotation before invoking the bridge.
3. Compare the exact emitted proposition/fact set with the expected set. Check positive, negative, zero, and omitted state behavior separately, plus entity attribution.
4. Add controls for duplicate invocation (no additional semantic facts), a second unrelated Microtheory (no cross-target facts), one Concept with its `state` absent (no fact), and ambiguous name-token correspondence. For the ambiguity control, verify the correspondence Rules add no `denotes` edge; separately record the documented legacy owner-name fallback, rather than incorrectly expecting the bridge to refuse all attribution.
5. Independently inspect the resulting `SmEntity` state attributes. `ingest_predication` handles these `is_a` predications as properties, storing the complement as an attribute; it does not materialize a separate predication node or preserve `t` on this route. Count missing, extra, misattributed, and duplicate facts separately. Do not score a time-index field the current path does not store.

## Measures and gates

Primary measure: exact-set accuracy over the 243 complete state assignments. Also report per-polarity precision/recall, null-state false-positive rate, entity-attribution accuracy, duplicate-invocation delta, and all control outcomes. Preserve raw per-case expected/observed facts and stable fixture IDs.

Pass criteria: all 243 assignments match exactly; no zero or absent state emits a fact; positive and negative facts preserve polarity; no fact is attributed to another entity; duplicate calls add no semantic facts; ambiguous token matching creates no `denotes` correspondence edge. The legacy owner-name fallback is reported independently. Any failure is reported without changing the bridge during the run.

Capture wall time, CPU time, peak RSS, native audit counters, node/edge counts, and source/runtime hashes. Keep fixture-construction cost separate from per-case bridge costs. Run at least two fresh-process workers on the same source-locked snapshot and analyze raw outputs in a separate process.

## Interpretation limits

A pass validates the bridge's deterministic state-to-fact translation on this schema and target resolution path. It does not validate the CAN state against the world, establish usefulness of the facts, measure natural rung-entry frequency, or demonstrate tractability of rung 3/4 induction. The combinatorial panel is exhaustive only for the five-topic ternary fixture. It is not a representative natural-task sample.

## Next gates

If the oracle passes, freeze this bridge quality result and separately preregister a naturally selected task stream to measure how often requests enter transform, dimension inference, and minting. Selection must be independent of observed substrate success; include all failures, residuals, and solved cases, with family-specific answer oracles and complete runtime locks. If the bridge oracle fails, repair the narrow mapping defect and rerun on a new locked version before using bridge results as capability evidence.
