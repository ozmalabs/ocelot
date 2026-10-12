# Native string-composition execution audit v1 preregistration

Date: 2026-10-03

## Question

Can the current native ProgEval path execute direct DSL terms for the six newly benchmarked string compositions exactly, independently of the P4 candidate-generation route?

## Procedure

Use the frozen 18-task fresh string-composition fixture. Construct an evaluator-only ProgSeq AST for each task from the registered family and parameter, using only existing `CaseFold`, `StrCount`, `Split`, `Reverse`, `Replace`, `Fold`/`StringConcat`, and `MapList` terms. Run each direct AST through the current native `prog_eval` on all four revealed and three held-out rows. Record per-row outputs, traps, term nodes, timing, and exactness. These manually supplied terms are not candidates offered to the P4 learner and do not affect the prior benchmark.

Lock this protocol, audit implementation, suite and generator, prior benchmark capture/lock, P4 evaluator/adapter, native Term/ProgEval sources, extension/build manifest and Cargo lock before execution. Require current native build and stable source hashes. Independently compare direct outputs to each row's frozen expected output.

## Claim boundary

A pass shows only that the exact manually constructed AST executes correctly through the current native evaluator on this finite suite. It does not show that P4 recognizes, generates, retrieves, selects, or verifies the AST. A failure is an implementation/semantic mismatch that must be localized before attributing benchmark gaps to search.
