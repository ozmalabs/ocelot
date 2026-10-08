# Generated cubic finite-grid alias control v1 — preregistration

## Question

Can behavioral pool collection and the entropy query selector detect that a supplied finite candidate grid aliases a wrong model with the target, or can the process return a false singleton?

## Frozen task

Target: `x³`, independently labeled with integer arithmetic. Known rows: `0→0`, `1→1`. Candidate grid: only `x=−1`. Held-outs: `x∈{−9,−5,5,9}`. Generate the version space with `Plus/Times/Minus/Div`, constants `{0,1,2,−1}`, maximum Term size 7, only the frozen candidate grid for behavioral pool collection, a 30-second ceiling, and a 10,000-solution cap. Run three fresh workers. The target and labels are not passed to synthesis or selector.

The grid is an intentional alias control: on all provided known and candidate inputs, `x³` and `x` agree. The pool collector may therefore retain only a representative of that shared observed behavior, depending on generation order.

## Arms and measurements

Compare uncached and lazy-matrix query selection on each identical generated pool, using the frozen external labels. Record pool completeness/size/hash, whether any retained hypothesis matches the target on every held-out, query traces and terminal reason, final survivors' held-out predictions, selector calls/time, synthesis time, and peak RSS.

## Validity gates and outcomes

Require current source/native hashes to match before/after and at analysis, all three workers to complete, pool digests and completeness to match, all Terms to use only the frozen operator vocabulary and independently evaluate on known/candidate/held-out rows, exact paired query/entropy/prediction/label/terminal/survivor parity, and no repeated queries. Independently recompute labels and predictions. Do not require target support or held-out success: an empty version space, multiple held-out-divergent survivors, or a false singleton is the substantive result. The primary diagnostic is whether the finite grid leaves a wrong model indistinguishable from the target and whether the harness exposes that residual on held-outs.

This is one constructed counterexample condition, not a rate estimate. It demonstrates a known logical limit of finite version spaces if it occurs; it does not estimate how often natural tasks alias in this way.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_contract_query_generated_cubic_alias_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_query_generated_cubic_alias_v1.py`
- The runner writes a source/native lock and raw capture in the capability and report directories.
