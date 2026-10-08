# Capability-map test-path relevance audit — 2026-09-28

This manually reviews the seven functional-test links with no direct audited
callable-name match in [`substrate_test_reference_triage_20260928.json`](../../../evaluation/reports/substrate_test_reference_triage_20260928.json).
The classification is based on the test code's setup and execution calls, not
on the test's filename or prose alone. It distinguishes functional integration
evidence from exact entrypoint coverage; no test link by itself proves the
whole capability row.

| Capability row | Linked test | Path relevance | What it exercises / what it does not establish |
|---|---|---|---|
| Rule dependency and scheduling | [`test_stage_a_refusal_migrated.py`](../../../tests/test_stage_a_refusal_migrated.py) | Indirect functional integration | Boots a native substrate, installs rules and graph facts, and settles through `tick`; it exercises the Stage A/refusal behavior through orchestration. It does not directly call `rule_access_sets`, nor establish general scheduler completeness. |
| Structural width, frame cuts, hierarchy | [`test_solver_decompose_adapter.py`](../../../tests/test_solver_decompose_adapter.py) | Functional integration | Sends deduction-shaped input through solver-dispatch and decomposition resolvers, then checks candidate projections and bounded refusal. It does not isolate `exact_treewidth` or prove a learned frame hierarchy. |
| Exact/approximate inference and optimization | [`test_solver_dispatch_migrated.py`](../../../tests/test_solver_dispatch_migrated.py) | Functional integration | Creates solve Goals and resolves them through the registered native resolver path, including CAN relax/exact/BP cases. It does not make the Python resolver itself the inference authority or establish inference outside the documented envelope. |
| Vision perception primitives | [`test_vision_change_migrated.py`](../../../tests/test_vision_change_migrated.py) | Adjacent graph-authored mechanism | Loads `vision_waves` and exercises its graph rules over `WaveWorld`. It is relevant vision behavior but does not directly test the row's `WorldAdapter::update_vision`, `evaluate`, or `convolve` entrypoints; those need separate evidence. |
| Program synthesis / induction | [`test_synth_enumerate_migrated.py`](../../../tests/test_synth_enumerate_migrated.py) | Direct native Term path through wrapper | The test wrapper submits `SynthEnumerate` Terms to native substrate evaluation and compares outputs/budgets/refusals. AST callable-name matching misses this because the native implementation is selected by Term dispatch rather than a Python function call. |
| Program synthesis / induction | [`test_prog_synthesis_battery_migrated.py`](../../../tests/test_prog_synthesis_battery_migrated.py) | Mixed measurement and live re-verification | Most cases validate frozen task/result artifacts and derived aggregates; selected cases re-run pinned tasks through the battery adapter and native substrate. It supports task-level reproducibility, not as a direct unit test of every synthesis Term or seed transition. |
| Learning, self-modification, proposals | [`test_vision_growth_migrated.py`](../../../tests/test_vision_growth_migrated.py) | Indirect graph-authored learning path | Loads `vision_growth` and settles graph-authored mint/Oja rules on image-derived patches. It supports selected substrate-native learning, but is not evidence for `GammaLearner`, P3 proposal validation, or source-level proposal installation. |

The three `tests/evaluation/test_p2_*.py` links are separately classified as
evaluation-protocol tests, not functional substrate test links. The two
`tests/evaluation/test_p0a_startup*.py` links are likewise protocol/startup
controls. Their original Markdown citations remain intact as evaluation
evidence. The map therefore has 39 functional-test links and five
evaluation-protocol links; this manual review classifies seven no-name-match
functional links but does not yet review all 39 links or upgrade any row to
fully audited test coverage.
