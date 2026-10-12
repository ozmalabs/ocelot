# Native string-composition execution audit v1 results

Date: 2026-10-03

## Results

The source-locked audit passed. All six human-constructed compositions executed exactly through the current native ProgEval path on all 18 tasks: 126 example and held-out rows, zero traps/evaluator errors, and 18/18 tasks exact including holdouts. The independent analyzer re-evaluated every saved IR against the frozen fixture and independently recomputed each expected value from the registered task formula; it found no mismatches.

This localizes the fresh string-composition benchmark gap: the current evaluator semantics can run the intended operators and compositions on this fixture, while the P4 acquisition path usually fails to produce or accept the correct program. It does not establish that P4 can recognize, retrieve, generate, select, or verify these compositions, because ASTs were supplied directly by the audit. Nor does it demonstrate autonomous operator invention or broad string reasoning.

## Artifacts

- [Preregistration](STRING_COMPOSITION_NATIVE_EXECUTION_AUDIT_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/audit_string_composition_native_execution_v1.py) and [independent analyzer](../../../evaluation/substrate_capability/analyze_string_composition_native_execution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/string_composition_native_execution_v1_lock_20261003.json), [capture](../../../evaluation/reports/string_composition_native_execution_v1_20261003.json), and [analysis](../../../evaluation/reports/string_composition_native_execution_v1_analysis_20261003.json)
