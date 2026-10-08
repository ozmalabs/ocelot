# Stage A disjoint-pair edge overwrite results v1

## Result

All 15 confirmatory cells passed across three fresh worker processes and binding counts 1, 2, 6, 16, and 32. Every cell had exactly one compared drain, zero divergent or unsound drains, and zero runtime conflict fallbacks. Stage A compare and ordinary closure produced identical complete graph dictionaries and progress/terminal results; the derived edge attributes matched the independent per-pair oracle.

This closes one narrow multi-variable case: Stage A derive/undo/compare for independent `(x,y)` bindings that overwrite attributes on pre-existing cross-edges. It does not test contention or establish general multi-variable safety.

## Eligibility boundary

An initial mixed node-write plus edge-overwrite fixture produced no comparisons. Source inspection explains why: the static derivability gate conservatively excludes multi-variable rules that write an attribute on any matched variable, since distinct bindings may share that variable. The admitted probe therefore measures only the edge-overwrite path. This is a scope boundary, not a semantic pass for the excluded rule. The dynamic proposal conflict check was exercised on the admitted disjoint pairs but no conflict was present to trigger fallback.

## Evidence and limits

- Preregistration: [`SUBSTRATE_STAGE_A_DISJOINT_PAIR_PREREG_20260926.md`](SUBSTRATE_STAGE_A_DISJOINT_PAIR_PREREG_20260926.md)
- Runner: [`substrate_stage_a_disjoint_pair_probe_v1.py`](../../../scripts/substrate_stage_a_disjoint_pair_probe_v1.py)
- Independent analyzer: [`analyze_substrate_stage_a_disjoint_pair_v1.py`](../../../scripts/analyze_substrate_stage_a_disjoint_pair_v1.py)
- Lock: [`stage_a_disjoint_pair_v1_lock_20260926.json`](../../../evaluation/substrate_capability/stage_a_disjoint_pair_v1_lock_20260926.json)
- Raw capture: [`substrate_stage_a_disjoint_pair_v1_20260926.json`](../../../evaluation/reports/substrate_stage_a_disjoint_pair_v1_20260926.json)
- Analysis: [`substrate_stage_a_disjoint_pair_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_stage_a_disjoint_pair_v1_analysis_20260926.json)

Source, native extension, and build-manifest hashes were locked at worker start/end. The analyzer passes all nine capture-integrity and semantic gates. The result says nothing about shared hubs, node writes under multi-variable rules, deletion/mint interactions, scheduler completeness, or workload prevalence.
