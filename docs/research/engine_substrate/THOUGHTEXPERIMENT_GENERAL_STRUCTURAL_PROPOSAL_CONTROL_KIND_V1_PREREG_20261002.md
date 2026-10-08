# General-rule structural proposal transfer to control-kind v1 — preregistration

**Question:** Can the substrate's graph-term structural editor select a target rule and edit operator for a non-action classifier, then produce a useful held-out repair without receiving the host candidate list?

## Scope and responsibility boundary

This is a bounded proposal-generation handoff. The task adapter supplies a faulted source rule and a symptom cue naming the affected classifier/comparison. The new `compose_general_structural_variant` path exposes non-frozen rules as `RuleSummary` candidates, then uses the existing graph Term Argmax to select a rule and an applicable `EditOp`. The existing mechanical applier materializes the selected JSON variant in Python. The scorer and expected labels remain outside proposal generation. This does not test open-ended diagnosis, rule invention, or adoption.

## Cases and controls

Use the control-kind fixture `classify_kind_family`, faulted by the existing comparison-flip mutator. Four fresh workers each receive the same fixed training/held-out split from the source fixture. Prompted residual predicates are `classify`, `kind`, `family`, `flip`, and `comparison`; the unprompted control has an empty residual list. Both order-stage contexts are outcome-blind. The host `_default_candidates` list is captured only as a reference set. Held-out scoring occurs only after all four order records are written.

## Gates

- Lock runner, analyzer, composer sources, fixture, adapter, preregistration, existing fixture protocol/results, build inputs, and loaded native binary before order capture.
- In all workers, the prompted graph path must select `classify_kind_family`, build `flip_comparison`, preserve the target rule during composition, and produce a semantic candidate digest present in the host reference list.
- The unprompted graph path must abstain without a candidate.
- A separate scorer applies the proposal in an isolated branch and scores both held-out classifier examples. Receipts and primary-state preservation must pass.
- The source rule must pass both held-outs and the fault must fail at least one; host candidate outcomes must contain both success and failure.
- Report graph decision, host applicability extraction, host materialization, branch, task scoring, and receipt-verification costs separately where exposed. Do not claim a speed advantage from this small fixture.

Any failed gate is retained as a negative/diagnostic capture. Four workers are repetitions on one authored classifier and two held-out names, not independent task families. Passing supports only cued target/operator choice for this classifier. General proposal generation and self-improvement remain open.
