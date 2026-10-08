# Lower-than operator-shape transfer v1 — preregistration

**Status:** locked confirmatory panel. **Date:** 2026-09-29.

## Question

Does the existing graph-authored `thresholded_lower_branch` selector transfer to new scalar piecewise-scaling instances and select its registered `Times/Lt/IfThenElse` grammar without operator injection? A matched wording ablation holds training rows and constants fixed while omitting all trigger tokens. The probe measures transfer of an existing authored shape rule, not learning a new rule.

## Pilot disclosure

One exploratory worker on the threshold-4 instance selected `thresholded_lower_branch`, enumerated 50,515 candidates, and produced an accepted Program that was exact on six manually read-back holdouts. This pilot was not independently repeated or locked with the current panel and will not be pooled.

## Tasks and wording conditions

The targets are `y=4*x if x<4 else 2*x` and `y=5*x if x<6 else 3*x`. Threshold-4 training x values are `[0,2,3,4,5,7]` with disjoint holdouts `[1,6,8,10,12,15]`. Threshold-6 training values are `[0,3,5,6,8,10]` with disjoint holdouts `[1,2,4,7,9,12]`. Each value's expected output is computed independently from its fixed target function.

For each task, use the same training and constants in two semantically equivalent requests:

1. **Trigger wording:** `write a function where when value is less than threshold T, return the value times H, otherwise return value times L`.
2. **Lexical ablation:** `write a function piecewise_scale using cutoff T and output factors H for lower inputs and L for upper inputs`.

Here `(T,H,L)` is `(4,4,2)` or `(6,5,3)`. Trigger wording carries `LESS`, `THAN`, `THRESHOLD`, `WHEN`, `TIMES`, and `OTHERWISE`. The ablation has the same example evidence and quantity literals but no token from the lower-shape trigger list. No operator list is harness-injected.

Run five fresh processes for each task×wording cell, 20 workers total, with seeded counterbalanced scheduling. Each worker creates a fresh substrate, calls `ensure_program_synthesis`, `ingest_spec`, and standard `pump`, records the selected graph facts and work/cost, and checks every accepted graph-reflected Program on all six heldout inputs through `ProgEval`.

## Gates

1. Verify the explicit task/wording order, source and seed hashes, runner/analyzer hashes, native extension and engine provenance; require per-worker source/native stability.
2. Require exactly five unique workers per task×wording cell, one header/footer, Rung 3 reached in every worker, and terminal accepted/gapped outcomes.
3. Every trigger-wording worker must select `thresholded_lower_branch` with exactly `Times/Lt/IfThenElse`; the message graph must record rule selection and the same operators. No harness-injected ops are permitted. Every lexical-ablation worker must select no shape and no explicit ops.
4. Every accepted Program must have one reflected IR root and six independently checked holdout results; report every false accept.
5. Report per-cell acceptance, exact transfer, candidate work, end-to-end pump CPU/wall time, memory, and false acceptance. The selector-transfer claim requires at least 4/5 exact transfers for each trigger task, at least 4/5 cap exhaustions for each ablation task, and a ≥1.5× median candidate-work reduction from trigger wording for both tasks.

A pass supports only this existing lower-than shape across these two parameterizations and wording conditions. It does not establish robust linguistic parsing beyond the registered trigger set, novel operator-shape induction, or general synthesis capability.
