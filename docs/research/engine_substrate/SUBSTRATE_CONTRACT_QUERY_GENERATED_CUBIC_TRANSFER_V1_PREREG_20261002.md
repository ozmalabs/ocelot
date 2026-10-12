# Generated cubic pool lazy-query transfer v1 — preregistration

## Question

Does the lazy survivor-first prediction matrix preserve query decisions and reduce evaluation work when the bounded substrate synthesizer generates a deeper cubic hypothesis pool for a task family not used in the preceding transfer panel?

## Frozen task and arms

The target is the scalar function `f(x)=x³`, independently labeled by integer arithmetic. The descriptor is `{x: float(x)}`. Known rows are `x=0→0` and `x=1→1`; candidate probes are `x∈{-4,-3,-2,2,3,4,5,6,7,8,9}`; held-outs are `x∈{10,12,15,19,23}`. Synthesize once per fresh worker using `Plus/Times/Minus/Div`, constants `{0,1,2,-1}`, maximum Term size 5, full candidate probes for behavior deduplication, a 30-second ceiling, and a 10,000-solution cap. The labeler and x³ target are never passed to synthesis or query selection.

Compare uncached and lazy-matrix selection on the exact same generated pool, known rows, candidate grid, and labels. Run three fresh workers. Both selectors query until singleton, candidate exhaustion, or unanimous predictions; evaluate final survivors on all held-outs. Report pool size/completeness/hash, explored Terms, synthesis wall/CPU time, query sequence, selector wall/CPU time, native calls, matrix cells/bytes, held-out accuracy, and peak RSS.

## Validity gates and outcomes

Require current source/native hashes to match the frozen lock before and after capture and for every worker; all three workers must complete; pools must be complete, nonempty, contain at least two hypotheses, and include at least one hypothesis correct on all held-outs; every generated Term must be independently evaluated on all known/candidate/held-out descriptors; both arms must have exact query, entropy, prediction, label, terminal, and survivor parity; no query descriptor may repeat; all survivor outputs and target-oracle labels are recomputed independently. A failed pool-completeness, target-support, parity, or held-out gate is a measured negative result, not a reason to change the task or rerun with different examples.

The target family is new relative to the preceding triangular/square/Euler transfer panel, but remains a small arithmetic task authored for this protocol. This measures selector transfer on a deeper generated pool. It is not a natural-task prevalence estimate, proof of generalization, or end-to-end learning advantage; synthesis and selection costs must be interpreted together.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_contract_query_generated_cubic_transfer_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_query_generated_cubic_transfer_v1.py`
- The runner writes a source/native lock and raw capture in the capability and report directories.
