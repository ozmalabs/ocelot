# Vision settle root-scoped mean probe

**Run:** 2026-09-25. **Evidence:** native semantic probe with an independent arithmetic and provenance audit. Production seed and engine source were not modified.

## Finding
The benchmark-only DSL variant replaces both global `NodesOfType(SUnit)` sources in `st_settle`'s competition mean with `Neighbours(r, has_sunit)`, where `r` is the matched World. It loads and runs natively. On the paired two-World/two-unit fixture, the authored global arm returns A `[0.5,0.5]` when B is `[0,0]`, and `[0,0]` when B is `[1,1]`. The root-scoped arm returns A `[0,0]` under both B states, as predicted by the corrected equation: A's local neighbor mean and its own World mean are both 1. All four calls progressed once and completed below the cap. The independent audit passed all arithmetic, invariance, progress, and provenance checks.

The initial v1 preregistration incorrectly predicted `[0.5,0.5]` for the scoped arm. Its raw output and failed prediction are retained at `evaluation/reports/substrate_vision_settle_root_scope_probe_20260925.json`; the corrected v1.1 amendment and run are separately recorded. This was a prediction error, not an engine or DSL failure.

## Evidence
- Protocol: [`v1 preregistration`](SUBSTRATE_VISION_SETTLE_ROOT_SCOPE_PROBE_PREREG_20260925.md), [`v1.1 correction`](SUBSTRATE_VISION_SETTLE_ROOT_SCOPE_PROBE_V1_1_AMENDMENT_20260925.md)
- Runner: [`substrate_vision_settle_root_scope_probe.py`](../../../scripts/substrate_vision_settle_root_scope_probe.py)
- Independent analyzer: [`analyze_substrate_vision_settle_root_scope_probe_v1_1.py`](../../../scripts/analyze_substrate_vision_settle_root_scope_probe_v1_1.py)
- Raw and analysis: [`raw JSON`](../../../evaluation/reports/substrate_vision_settle_root_scope_probe_v1_1_20260925.json), [`analysis JSON`](../../../evaluation/reports/substrate_vision_settle_root_scope_probe_v1_1_analysis_20260925.json)
- Lock: [`v1.1 lock`](../../../evaluation/substrate_capability/vision_settle_root_scope_probe_v1_1_lock_20260925.json)

## Scope and next gate
This demonstrates that root scoping is expressible and removes cross-World dependence on this minimal fixture. It does not establish full-sheet fidelity, task/orientation quality, fixed-point behavior with `st_commit`, or performance. Next run global and root-scoped cloned rules on matched full `build_sheet` workloads with the complete settling/commit cycle and downstream orientation readout; quantify task-quality deltas and work before considering a seed change. Keep the authored seed untouched until that gate passes.
