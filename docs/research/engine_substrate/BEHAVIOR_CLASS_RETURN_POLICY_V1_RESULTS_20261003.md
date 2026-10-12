# Finite behavior-class return policy v1 retrospective results

Date: 2026-10-03

## Policy replay

A deterministic secondary analysis replays a simple choice rule on the source-locked 25-panel query/equivalence capture: after the recorded selection and challenge queries, return all surviving hypotheses as a finite behavior class if they agree on every supplied selection+challenge input; otherwise retain the existing abstention/help behavior. Heldout labels are evaluation-only. No queries, synthesis, or help callbacks were rerun for this analysis.

| Query domain | Panels | Labels used | Single finite class | All class members exact on 6,560 heldout cases | Harmful returns | Existing help calls |
|---|---:|---:|---:|---:|---:|---:|
| Original, nonzero-only | 25 | 45 | 25/25 | 20/25 | 5 | 10 |
| Zero-aware | 25 | 61 | 25/25 | 25/25 | 0 | 5 |

The five harmful original-domain returns are the inequality panels: each survivor set looks like one class on nonzero probes but contains both an exact and a false candidate on the expanded holdout. The zero-aware domain resolves this alias. In the zero-aware opposition panels, four syntactically different survivors form one finite behavior class and all are exact on the expanded holdout. Returning the class would avoid the five Base-family help calls recorded there. Across those calls the recorded help synthesis time totals 6.55 s (median 1.32 s); class construction evaluated 2,560 survivor-probe pairs in the capture, but its elapsed time was not separately measured. The zero-aware policy spends 16 more local labels than original-domain selection across the 25 panels, largely to resolve the inequality aliases, and cuts existing help calls from ten to five. Class return would remove the remaining five opposition hints on this finite capture.

## Interpretation and limits

This is an offline policy replay, not an implemented or deployed decision-maker. It shows a practical distinction between syntactic ambiguity and ambiguity that remains over a declared probe domain, and quantifies a candidate opportunity to replace task-family hints with explicit finite classes. It also demonstrates the safety boundary: a single behavior class is not a universal equivalence certificate. The original-domain inequality control produces five harmful finite-class returns when scored on broader heldout inputs.

Evidence is restricted to five authored numeric relations and five panels each, reused hypotheses and query schedules, a finite 64-input probe pool per domain, and one 6,560-row finite heldout grid. The task-relevant teacher hint is harness supplied. Class-partition cost is reported as term-row work only, not latency. No persistent primitive or rule was added, and no production consumer used a returned class.

## Reproduction

- Upstream preregistration, runner, source lock, capture, and independent analysis are linked in [zero-aware query and equivalence results](PRIMITIVE_SEMANTIC_EQUIVALENCE_V1_RESULTS_20261003.md).
- [Analysis script](../../../evaluation/substrate_capability/analyze_behavior_class_return_policy_v1.py)
- [Machine-readable result](../../../evaluation/reports/behavior_class_return_policy_v1_analysis_20261003.json)
