# CEGIS query order sensitivity v1 preregistration

## Question

The current `cegis_synthesize` policy adds the first disagreement in its caller-supplied candidate-family order. Does changing only that order change query sequence, synthesis outcome, heldout transfer, or oracle work on a fixed finite task?

## Task and arms

Use the existing grounded triangular-number task, `T(n)=sum(0..n)`, with its existing descriptor, oracle, known row `n=1`, grammar, candidate family `n=2..12`, and independent heldout values `17,23,50,99,100,250`. Compare five fresh-process paired replicates of:

1. `fixed_order`: the task's existing ascending family order.
2. `seeded_permutation`: a deterministic permutation generated from preregistered seed plus replicate index.

Everything else (code, initial state, grammar, search cap, timeout, and heldout set) is identical. The main randomized worker schedule is also fixed from the registered seed. This is a sensitivity probe of the implemented policy, not a comparison against an information-gain selector or a claim of label-sealed active learning.

## Measures and gates

Record exact candidate order, selected counterexample sequence, every oracle call, round recipes, final synthesis status, heldout predictions, CPU/wall time, and fresh worker PIDs. The independent analyzer must reconstruct orders and oracle labels, reconcile selected queries to observed calls, verify the heldout labels and results, and report paired changes. Preserve all workers and failures. The run is interpretable only if all ten workers complete, PIDs are unique, lock and schedule match, and all labels reconstruct exactly.

Report results descriptively; do not claim one ordering is better from five pairs. If outcomes vary by order, register a follow-up that contrasts the current scan with query strategies under a sealed oracle and charges query-selection work. If they do not vary, treat this as a null for this one task and expand to additional functions before any broader conclusion.

## Claim boundary

This benchmark changes only family order on one authored function. It does not establish query-policy superiority, natural-task generality, or substrate-owned task/family construction. The current policy may call the oracle on candidate inputs before selecting which label is added; all such calls are counted but this protocol does not conceal them.
