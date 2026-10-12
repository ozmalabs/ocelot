# Term external-dependency replay/order probe v1.3 results

Date: 2026-09-28

## Results

The locked panel passed all 10 independent checks across three fresh processes and both insertion orders. With one shared handler that returns true only on its first call:

- The first inserted rule is the only one that writes its marker. Reversing rule order reverses the winning marker.
- Each first settle makes three callbacks: two for the first rule (true, then false) and one false callback for the second rule. The first settle reports one progress step.
- After the first settle, the runner resets only the handler's local state. The graph is unchanged. A second `run_rules` call performs zero progress, invokes no callback, and emits no trace events.
- Both rules report `reads_any=true` and a finite `edge:trigger` read. No trace events are dropped, and callback, native-fire, and trace counts match.

This confirms an order-sensitive, stateful predicate outcome in the exact synthetic fixture. It also demonstrates that changing callback-local external state does not itself wake a settled graph rule: a second settle does not reevaluate the predicate in this schedule. This is consistent with graph-only notification semantics, not a general scheduler guarantee.

## Interpretation

Rule predicates that enter `UseTool` do not have ordinary pure-predicate semantics. A callback's changing result can make rule order determine which effects commit, and later external-state changes can remain invisible until some graph event causes reevaluation. This supports treating dynamic callbacks as declared effects with explicit invalidation/idempotency behavior, or excluding them from match predicates. The probe does not choose between those design options.

## Reproduction

The raw writer refuses to overwrite an existing capture; use a new `--output` path for another run. Artifacts: [preregistration](SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_3_PREREG_20260928.md), [source/native lock](../../../evaluation/substrate_capability/term_external_dependency_probe_v1_3_lock_20260928.json), [runner](../../../scripts/substrate_term_external_dependency_probe_v1_3.py), [raw capture](../../../evaluation/reports/term_external_dependency_probe_v1_3_20260928.json), [independent analyzer](../../../scripts/analyze_term_external_dependency_probe_v1_3.py), and [analysis](../../../evaluation/reports/term_external_dependency_probe_v1_3_analysis_20260928.json).
