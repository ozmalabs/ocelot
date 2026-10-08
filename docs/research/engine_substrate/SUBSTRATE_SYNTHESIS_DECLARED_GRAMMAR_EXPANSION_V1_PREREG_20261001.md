# Declared grammar expansion v1 — preregistration

## Question

When the target function needs an operator excluded from the declared synthesis grammar, does bounded synthesis report no fit, and can the same route recover and transfer the target after that operator is supplied? What is the measured difference in candidate work and runtime?

This is a test of grammar coverage and externally directed rung-three escalation. It does not test whether the substrate can invent or select a missing primitive.

## Frozen task and conditions

The target is `f(x) = x / 2`, evaluated with the substrate DSL's division semantics. Both conditions receive the same examples `x ∈ {0,2,4,6}` with analytic labels `x/2`, constants `(0,1,2,-1)`, maximum term size 5, no output-derived constants, and saturation disabled (`saturate_k=999999`). Held-out inputs are `{-5,-3,-1,1,3,5,9}` and are scored only after synthesis.

- **Declared grammar, operator absent:** `Plus, Times, Minus, Min, Max, Abs, Neg`.
- **Expanded grammar:** the same operators plus `Div`.

Each condition runs in five fresh worker processes. Randomize the ten-worker order with seed `20261001`. Per-worker synthesis timeout is 5 seconds; parent timeout is 12 seconds. Preserve all failures and timeouts. A no-fit outcome is called complete only when synthesis reports `max_size`; timeout or any other halt reason is incomplete.

## Captures and gates

Record the task/examples, grammar, term-size limit, explored terms, distinct training signatures, halt reason, returned term, training fit, held-out predictions and exactness, wall/CPU time, PID, native/source provenance, and full schedule. The independent analyzer must verify source/native lock stability, all ten rows, five workers per condition, unique PIDs, exact locked schedule, completion semantics, no fit under the declared operator-absent grammar, and exact held-out transfer under the expanded grammar.

Primary costs are explored candidate terms and synthesis wall/CPU time. Candidate count is not a universal work measure across operators; the comparison is local to this fixed task/size panel. Do not infer asymptotic complexity, natural-task frequency, or autonomous primitive invention from this result.

## Reproduction

Create the source lock with `python3 scripts/substrate_synthesis_declared_grammar_expansion_v1.py --lock` and save it to `evaluation/substrate_capability/synthesis_declared_grammar_expansion_v1_20261001_lock.json`. Run the runner once; it refuses to overwrite the raw capture. Then run `python3 scripts/analyze_substrate_synthesis_declared_grammar_expansion_v1.py`.
