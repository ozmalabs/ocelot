# Operator-shape selection transfer v1.1.1 — results

**Date:** 2026-09-29. **Question:** can the production request route use the existing graph-authored greater-than operator-shape selector on unseen scalar piecewise-scaling instances, and what happens when its trigger wording is removed?

## Protocol and integrity

Two fixed functions were used: `3*x` above threshold 5 and `2*x` otherwise; `4*x` above threshold 7 and `2*x` otherwise. Each has six training values, six disjoint holdouts, and five fresh workers in each of two semantically equivalent wording conditions. The trigger condition contained the registered greater-threshold tokens; the lexical ablation preserved the same constants and examples while omitting every token in that shape's trigger list. No operator list was supplied by the runner. The probe used the normal `ensure_program_synthesis` → `ingest_spec` → `pump` path and executed accepted reflected Programs on heldout points through `ProgEval`.

V1 and v1.1 are preserved but excluded: v1's analyzer rebuilt schedule order from sorted JSON maps instead of the runner's declaration order; v1.1 added explicit order lists to the lock but its copied analyzer still ignored them. V1.1.1 corrects the analyzer and repeats the panel. Its independent analysis passes all eight capture-integrity checks and all ten behavioral gates, including exact schedule, complete/unique matrix, current source/native hashes, stable workers, selector facts, terminal outcomes, and accepted-program holdout readbacks ([v1 preregistration](SUBSTRATE_SYNTHESIS_OPERATOR_SHAPE_TRANSFER_V1_PREREG_20260929.md), [analysis correction amendment](SUBSTRATE_SYNTHESIS_OPERATOR_SHAPE_TRANSFER_V1_1_AMENDMENT_20260929.md), [final amendment](SUBSTRATE_SYNTHESIS_OPERATOR_SHAPE_TRANSFER_V1_1_1_AMENDMENT_20260929.md)).

## Results

| Task | Wording | Selector outcome | Accepted / exact transfer | Candidate tests | Median pump wall time |
|---|---|---|---:|---:|---:|
| Threshold 5, factors 3/2 | Trigger | `thresholded_greater_branch`; `Times/Gt/IfThenElse` | 5/5; 30/30 points | 102,862 | 234.5 ms |
| Threshold 5, factors 3/2 | Lexical ablation | No shape; empty explicit list, broad default Gamma set | 0/5; no candidate | 200,000 cap | 282.8 ms |
| Threshold 7, factors 4/2 | Trigger | `thresholded_greater_branch`; `Times/Gt/IfThenElse` | 5/5; 30/30 points | 105,413 | 235.3 ms |
| Threshold 7, factors 4/2 | Lexical ablation | No shape; empty explicit list, broad default Gamma set | 0/5; no candidate | 200,000 cap | 218.2 ms |

The selected shape and exact operator list are written to the graph by the ordinary rule route. All ten triggered workers transfer exactly with zero false accepts. Both ablation tasks hit the candidate cap in 5/5 runs. Candidate work falls by 1.94× and 1.90× under trigger wording. Complete `pump` latency varies: threshold 5 is faster with selection, while threshold 7 is slightly slower despite using fewer candidate tests. Thus the selected grammar reduces enumerator candidate work reliably, but these timings do not establish a wall-time speedup. Peak RSS is available per worker in the [raw capture](../../../evaluation/reports/synthesis_operator_shape_transfer_v1_1_1_20260929_raw.jsonl); all per-cell timing and gate details are in the [analysis](../../../evaluation/reports/synthesis_operator_shape_transfer_v1_1_1_20260929_analysis.json), with full provenance in the [lock](../../../evaluation/substrate_capability/synthesis_operator_shape_transfer_v1_1_1_20260929_lock.json).

## Interpretation and next measurement

This is current-source evidence that one existing graph-authored operator-shape rule can transfer across two parameterizations and value splits of a scalar piecewise-scaling task, select its registered operators without harness injection, and support exact holdout performance. The paired lexical ablation shows that example evidence and numeric constants alone do not cause the broad default grammar to solve these cases within the current cap; selector wording changes the selected candidate set. The evidence is restricted to a rule whose tokens and operators were explicitly authored for greater-threshold programs. It does not establish that the system learns new shape rules, that these trigger tokens are robust language understanding, or that the result extends to other operator families.

Next evaluate the existing `thresholded_lower_branch` selector on a separately preregistered below-threshold task with fresh constants, neutral-wording ablation, disjoint holdouts, and the same controls. After both directions, test a task family that does not match either authored shape to measure selector refusal and the default grammar's cost. Do not extrapolate the two-family study to general grammar induction ([runner](../../../scripts/substrate_synthesis_operator_shape_transfer_v1_1_1.py), [analyzer](../../../scripts/analyze_substrate_synthesis_operator_shape_transfer_v1_1_1.py)).
