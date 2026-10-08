# Cross-family structural induction v1 preregistration

Date: 2026-10-03

## Question

Does one frozen counterexample-driven grammar-expansion policy transfer across distinct numeric relation families, and what accuracy/search cost does it have under a fixed feedback budget?

## Tasks and policy

Five seeded panels per task use four numeric inputs (`ax`, `ay`, `ex`, `ey`) drawn from integers -2 through 2 and three oracle-defined Boolean tasks: (A) exactly one vector axis is opposed; (B) absolute-value equality `abs(ax)==abs(ex)`; and (C) additive equality `ax+ay==ex`. Each worker receives eight balanced labeled training rows and a separately frozen 24-row reserve query pool, with no row overlap. The learner does not receive task names or formulas through its policy interface; labels arrive only through the local oracle callback. The source code necessarily contains evaluator task definitions, so this is harness separation, not a security boundary.

Use one fixed base grammar (`Eq`) and expansion order (`Neg`, `Not`, `Abs`, `Plus`) for every task. After each oracle disagreement, add the next operator before resynthesis; on no-fit, continue expanding in the same order. No task-specific expansion choice is allowed. Each synthesis call has size cap 11, a 2-second timeout, no constants, and returns the first fitting term. Query reserve rows in frozen order, with at most 12 oracle calls. Stop after six consecutive agreements since the last disagreement, reserve exhaustion, no-fit after exhausting the expansion ladder, or budget exhaustion. Freeze the final term before scoring a disjoint fractional grid and a separately frozen integer holdout.

## Measures and gates

Record per-task and per-worker status, expansions, synthesis attempts/timing, queries, agreements, mismatches, final candidate, held-out exactness, and resource cost. Independently replay oracle labels, candidate predictions at queried rows, revealed-example fit, stopping transitions, and holdout scores. Report task families separately; five workers per family are a pilot, not a generalization guarantee. This tests a human-authored grammar menu, order, and policy. It does not test autonomous task discovery, primitive invention, or nonnumeric transfer.
