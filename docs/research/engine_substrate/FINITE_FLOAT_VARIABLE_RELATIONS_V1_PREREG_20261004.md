# Finite-float variable relations v1 preregistration

## Question

How often do generated two-variable comparison conjunctions fall outside the clause solver's unary proof fragment, and does it abstain on them? Do the native Terms agree with an independent finite representative-domain satisfiability oracle?

## Frozen cases

Generate 1,024 deterministic conjunctions over `ax` and `ay`, each containing 1–8 `Eq`, `Lt`, `Lte`, `Gt`, or `Gte` atoms and at least one direct variable-to-variable comparison. Numeric constants are finite binary64 values, with an explicit edge pool for signed zero, subnormals, adjacent values, large values, and maximum finite values. Seed `20261005`.

## Reference and gates

For the witness search, form a finite representative set from every literal, up to two adjacent finite floats on each side, signed zero, and the finite extremes. Enumerate all pairs from this set. A found witness proves satisfiability. Failure to find one means only “no representative witness”; it is not by itself an unrestricted unsatisfiability proof. The clause solver is expected to return unresolved for every generated case because each contains a variable-to-variable atom. For found witnesses, evaluate one with the native Term evaluator. Lock cases/sources, verify statuses and native results, and report witness/no-representative-witness counts, representative-domain sizes, work, and time.

## Scope

The oracle covers conjunctions of two-variable equality/order comparisons over finite binary64 values. This does not evaluate arbitrary Boolean Terms, three-or-more-variable order constraints, or natural-task prevalence.
