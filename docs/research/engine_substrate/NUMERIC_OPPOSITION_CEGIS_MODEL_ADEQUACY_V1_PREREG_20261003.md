# CEGIS model adequacy and transfer v1 preregistration

Date: 2026-10-03

## Question and design

Does counterexample-guided resynthesis distinguish a target expressible in its fixed grammar from a target outside it? Run five paired panels on the existing frozen numeric query pools. Each panel has two target oracles: (A) componentwise opposition, the in-grammar control; and (B) exactly one coordinate is opposed, the XOR of the two componentwise opposition predicates, which is not expressible with the learner's `Neg`/`Eq`/`And` grammar. Recompute the four initial labels for each target; query inputs, order, and budget are shared within panel. Learner gets rows and labels only, not target identity/formula. After each active query it reruns synthesis from all revealed examples, with no constants, max term size 9, 12 seconds per round, at most 128 candidates, and at most six oracle calls.

Freeze the final state at singleton, no-fit, selector abstention, pool exhaustion, or budget exhaustion. Score all final candidates only after freeze on the 1,296-case fractional grid. The oracle is a local deterministic evaluator. Record search cost by round and count whether a false singleton, no-fit, unresolved ambiguity, or exact singleton occurred. A no-fit status is not evidence of correct model-adequacy detection unless the paired in-grammar controls solve under the same panel and the out-of-grammar training examples themselves are consistent.

## Integrity gates and limits

Lock protocol, source/build hashes, upstream pool, derived labels, and analyzer before capture. Independently replay oracle labels, candidate fit on revealed examples, query uniqueness and maximum-entropy choices, and final holdout scores. Report all workers and statuses. This is a diagnostic on two related numeric targets and one bounded grammar; it does not establish reliable model selection, transfer to unrelated domains, or self-improvement.
