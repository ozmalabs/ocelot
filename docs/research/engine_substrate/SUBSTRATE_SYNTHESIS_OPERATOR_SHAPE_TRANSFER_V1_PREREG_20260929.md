# Operator-shape selection transfer v1 — preregistration

**Status:** locked confirmatory panel. **Date:** 2026-09-29.

## Question and claim boundary

Does the substrate's existing graph-authored `ps_select_synthesis_operator_shape` rule select and apply its greater-than conditional grammar on a second, scalar-output task instance, and does the selection reduce search cost and improve transfer compared with a wording ablation that carries the same examples and quantities but lacks the shape trigger tokens? This tests transfer of one already-authored shape rule to fresh threshold/scaling constants and value splits. It is not evidence of general grammar induction or broad natural-language understanding.

## Pilot disclosure

Before this registration, single-worker exploratory probes used the two task formulas and descriptions below. The trigger wording selected `thresholded_greater_branch`, with operators `Times/Gt/IfThenElse`, and transferred 6/6 holdouts in each task; the neutral wording selected no shape, hit 200,000 candidates, and gapped. This registration locks a fresh five-repetition-per-cell replication. Exploratory records are not pooled with the confirmatory capture.

## Tasks and wording conditions

Both tasks are `y = 3*x if x>5 else 2*x` and `y = 4*x if x>7 else 2*x`. The six training x-values for threshold 5 are `[0,2,5,6,8,10]`, with disjoint holdouts `[1,3,4,7,9,12]`. For threshold 7, training values are `[0,3,6,7,8,11]`, with disjoint holdouts `[1,4,5,9,10,14]`. Expected outputs are computed independently from each fixed formula.

Each formula is presented in two semantically equivalent conditions, with the same training rows and the same known quantities:

1. **Trigger wording:** `write a function where when value exceeds threshold T, return the value times H, otherwise return value times L`.
2. **Lexical ablation:** `write a function scale_value using cutoff T and output factors H for upper inputs and L for lower inputs`.

Here `(T,H,L)` is `(5,3,2)` or `(7,4,2)`. The trigger condition supplies at least five registered tokens (`WHEN`, `EXCEEDS`, `THRESHOLD`, `TIMES`, `OTHERWISE`). The ablation retains the same numerical quantities and example data while omitting every token in the greater-threshold shape's trigger list. No operator list is injected into either arm.

Run five fresh processes for each of the four task×wording cells, 20 workers total, counterbalanced and seeded schedule. Every worker uses a fresh substrate, `ensure_program_synthesis`, `ingest_spec`, and ordinary `pump`; it records the selector's chosen shape/operators, enumeration work, status, Program/IR, and executes all six holdouts through graph-reflected `ProgEval`. The default candidate cap is unchanged.

## Gates

1. Lock and verify the task tables, requests, script/analyzer, relevant source and seed files, native extension, and engine provenance; verify source/native stability in every worker.
2. Require one header/footer and exactly five unique workers per task×wording cell, all reaching the enumerate rung and a terminal state.
3. Require each trigger-wording worker to select `thresholded_greater_branch` and exactly `Times/Gt/IfThenElse` without a harness-injected operator list; require each lexical-ablation worker to select no operator shape.
4. For every accepted result, require one reflected Program and six independent holdout evaluations; preserve any accepted holdout error as a false generalization.
5. Report per-cell accepted/exact-transfer rates, candidate counts, full `pump` wall/CPU time, memory, selected shape/operators, and false accepts. The measured selector-transfer claim requires exact transfer in at least 4/5 workers for each triggered task, broad-default candidate-cap exhaustion in at least 4/5 workers for each ablation task, and at least a 1.5× candidate-work reduction by trigger wording in each matched task.

A pass would show transfer of this existing selector rule across the two registered constants/splits and a controlled lexical-ablation effect. It would not establish selection for other operators, other task families, ordinary unstructured language, or general capability.
