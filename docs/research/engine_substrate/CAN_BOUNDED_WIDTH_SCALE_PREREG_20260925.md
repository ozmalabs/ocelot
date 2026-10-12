# Preregistration: bounded-width exact inference scale check

**Question.** Does the current graph extraction plus exact junction-tree MAP path retain exactness and acceptable measured cost as a width-one runtime graph grows from 32 to 2,048 variables?

**Frozen design.** Run [`can_bounded_width_scale.py`](../../../scripts/can_bounded_width_scale.py) in isolated Python worker processes for path graphs of 32, 64, 128, 256, 512, 1,024, and 2,048 variables, three deterministic replicates each. Each graph is built in a fresh native substrate with two-state unary fields and pairwise couplings generated from the predeclared seed formula in the script, extracted through `can_network_from_mt`, and solved by the current `junction_tree_map` using the min-fill order. A separately implemented two-state chain dynamic program and an independent energy scorer are the exactness oracle.

**Primary measures.** Runtime extraction time, min-fill ordering time, junction-tree MAP time, Python traced peak during MAP, worker process peak RSS, width, bag size, and exact energy gap. Raw per-run results are retained. Wall times are descriptive host measurements; use scaling by size and replicate spread, not commodity-hardware extrapolation.

**Pass criteria.** All extracted models equal their generated factors; all graphs have upper bound 1 and maximum bag size 2; MAP energy matches independent DP and scoring at every point; all three workers complete at every size. A budget failure, width growth, model mismatch, or energy disagreement is a failed gate and remains in the record. No timing threshold is used for the correctness gate.

**Limits.** This is a synthetic path family and a solver envelope, not a natural-task or learned-frame result. It does not test frame discovery, separator maintenance, marginal inference, native allocation totals, concurrent execution, or higher width. Do not generalize beyond the measured path workload.

**Lock.** `evaluation/substrate_capability/can_bounded_width_scale_lock_20260925.json` captures benchmark/protocol and solver/build inputs before execution.

## Transparent harness amendment before scored rerun

The first worker invocation failed before producing a result because the harness converted unordered factor keys to ordered tuples, while `junction_tree_map` consumes `frozenset` keys. A direct inspection confirmed that the graph extraction matched the generated factors; the failure was in the benchmark adapter. The adapter now converts the extracted keys back to `frozenset` for the solver call. The lock is amended to the corrected harness and this note before the scored rerun. The suite, seeds, primary measures, oracle, and pass criteria are unchanged. The failed diagnostic invocation is not included as a scored observation.
