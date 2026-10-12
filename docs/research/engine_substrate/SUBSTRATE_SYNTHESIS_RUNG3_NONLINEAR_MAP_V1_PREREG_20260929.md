# Integrated Rung 3 nonlinear-map synthesis v1 — preregistration

**Status:** locked protocol, before confirmatory capture. **Date:** 2026-09-29.

## Question and claim boundary

Can the shipped `domains.prog_synthesis` route, from a fresh substrate and ordinary request/example ingestion through `pump`, reach its graph-authored enumerate rung, accept a synthesized Program through the normal verification path, and correctly execute it on held-out integer-coordinate maps? This bridges the direct `SynthEnumerate` term study to the production adapter and rule route. Success is evidence for bounded task-specific program acquisition and reuse in this interface only; it is not general dimension induction, new primitive minting, or evidence about natural task prevalence.

## Registered cases

Four deterministic functions are used: linear `(r+c,c+c)`, quadratic `(r+c*c,c)`, hinge `(r+max(c-1,0),c)`, and absolute shear `(r+abs(c-2),c)`. Each has six fixed training pairs and six disjoint held-out pairs transcribed from the direct-term panel. The task names and requests are unique and do not name the target operator. Each of the four cases is run five times in a fresh `Substrate`, for 20 acquisitions total. There is no new random sampling and no replacement after outcomes are observed.

The runner calls `ensure_program_synthesis`, `ingest_spec`, and the normal `pump` loop. It does not invoke `SynthEnumerate` directly or manually choose its operator grammar. For a reported `accepted` goal, it evaluates the graph-reflected Program via `ir_subgraph` on all six holdouts with `ProgEval`. The independent scoring oracle recomputes the four registered formulas in Python. Record the selected route/rungs, enumerate outcome and operator facts, final status/gap reason, attempts, candidate program and graph representation, holdout outputs, process CPU/wall time, and peak RSS.

## Integrity gates

1. Capture source, seed, runner, analyzer, preregistration, native binary, task tables, and engine provenance match the pre-run lock; source/native state remains stable through the run.
2. Exactly 20 unique case/repetition rows are present, with five fresh substrates per case and one header/footer.
3. Every case reaches the Rung 3 marker and records a terminal status; no exception, missing goal, or nonterminal stall is counted as success.
4. Every `accepted` route has exactly one Program with one reflected IR root, and all six held-out executions match the independent oracle exactly. A non-accepted result is recorded as a failure, not omitted.
5. The linear task is a positive control; nonlinear families are reported separately. No combined percentage is presented as a general capability estimate.

## Analysis and reporting

Report per-family acceptance and exact held-out transfer, including all failed/gapped outcomes; selected operator list; median and range of candidate count, wall/CPU acquisition time, and RSS where exposed; and whether synthesis moved beyond the representation supplied by current Program IR. Compare the route path descriptively to the direct-Term result, without pooling. A passing panel demonstrates only these formulas, training/holdout tables, current source/runtime, and five repeated local processes. It does not show a residual-triggered concept/dimension mint, broad OOD generalization, noisy-data robustness, general grammar learning, or scalable cost.

## Artifacts

The runner will write a source/input lock, raw per-case capture, and independent analyzer report to versioned `evaluation/` paths. Any protocol, implementation, or analyzer defect requires an amendment and a fresh capture; preserve invalid attempts and exclude them from the confirmatory analysis.
