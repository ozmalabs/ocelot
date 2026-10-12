# Stage A mixed overwrite compare results v1

## Result

All 15 confirmatory cells passed across three fresh processes and 1, 2, 6, 16, and 32 independent bindings. The rule combines `SetAttr(x, observed, Attr(x, watched))` with `AddEdge(x, derived, x, {value: Attr(x, watched)})` over pre-existing nodes and pre-existing edges, so its undo path must restore both an existing node attribute and existing edge attributes. At every size, Stage A compare admitted exactly one drain and reported zero divergent and zero unsound drains. The candidate and control had identical complete graph dictionaries, progress count (one progressing drain), and zero-work terminal result; every output matched the independent oracle.

This closes one precise B1 subgap: mixed node-attribute and existing-edge-attribute overwrite under Stage A derive/undo comparison for independent one-variable bindings. It does not close mixed contended/multi-variable rollback, deletion/mint interactions, or general Stage A correctness. Compare mode is diagnostic; this result does not enable Stage A execution by default.

## Evidence and limits

- Preregistration: [`SUBSTRATE_STAGE_A_MIXED_OVERWRITE_PREREG_20260926.md`](SUBSTRATE_STAGE_A_MIXED_OVERWRITE_PREREG_20260926.md)
- Runner: [`substrate_stage_a_mixed_overwrite_probe_v1.py`](../../../scripts/substrate_stage_a_mixed_overwrite_probe_v1.py)
- Independent analyzer: [`analyze_substrate_stage_a_mixed_overwrite_v1.py`](../../../scripts/analyze_substrate_stage_a_mixed_overwrite_v1.py)
- Lock: [`stage_a_mixed_overwrite_v1_lock_20260926.json`](../../../evaluation/substrate_capability/stage_a_mixed_overwrite_v1_lock_20260926.json)
- Raw capture: [`substrate_stage_a_mixed_overwrite_v1_20260926.json`](../../../evaluation/reports/substrate_stage_a_mixed_overwrite_v1_20260926.json)
- Analysis: [`substrate_stage_a_mixed_overwrite_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_stage_a_mixed_overwrite_v1_analysis_20260926.json)

The restricted fixture excludes bindings that may write shared targets. It does not establish correctness for contention, arbitrary effects, changing match sets, concurrent mutation, or application workloads.
