# Batched contract-query partial-domain and operator coverage v1 — preregistration

## Question

Does the sequence-local `TermPredictionMatrix` preserve the ordinary selector's exact behavior when hypotheses use several allowlisted operators and the candidate grid contains partial input records?

## Panel

Use eight distinct pure-Term hypotheses over `x` and optional `y`: identity, increment, decrement, doubling, absolute value, Euclidean remainder by 3, true division by 2, and `x+y`. The 44 candidate inputs cover x=-5…5 with either no y or y in {-2,0,3}. Each target hypothesis is the external oracle in a separate task. Begin with the same labeled row `{x:0,y:1}`. Run each of eight target cases twice, in fresh paired processes, for 32 source/native-locked workers across uncached and matrix arms. The target is analysis-only and is not passed to either selector.

## Gates and measurements

Require exact paired query histories, entropy values, partition counts, ordered predictions (including numeric types), labels, terminal outcomes, and surviving target; independently evaluate every hypothesis/input pair with a closed-form Python oracle; ensure selected queries belong to the locked grid and are never repeated; ensure both partial and complete environments are present in the locked grid; and ensure the matrix arm rejects callback-backed `Holds` Terms before invoking the evaluator. Record query count, whether any selected query omitted y, native evaluator calls, elapsed sequence time, and peak RSS. Preserve failures.

This is a semantic coverage panel, not a speed or natural-task claim. Both methods are expected to converge because each target is a member of the finite supplied set and the grid separates the eight functions. It does not test induction, graph inference, hypothesis adequacy, or unknown operators. A failure blocks using this matrix method for these operator/domain combinations until corrected and rerun.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_contract_query_batched_partial_domain_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_query_batched_partial_domain_v1.py`
- The runner creates a pre-run source/native lock and refuses to overwrite lock or capture files.
