# Stage A overlap-triggered fallback results v1

## Result

All 15 cells passed across three fresh workers at hub fanouts 1, 2, 6, 16, and 32. At fanout 1, Stage A reported no conflict fallback. At every fanout ≥2, it reported exactly one fallback per run. Stage A enabled and ordinary closure produced identical full graph dictionaries, progress values, terminal behavior, and oracle-correct edge attributes. The control arm reported no Stage A fallbacks.

This demonstrates the measured runtime overlap guard routes shared-hub proposals through the ordinary sequential path without changing outcomes. Since every proposal pair touches the same hub node, the current conservative node-level relation declines Stage A batching even though these particular target-edge writes are semantically independent. This is a correctness result and an observed lost opportunity for parallel/apply batching, not a performance result.

## Evidence and limits

- Preregistration: [`SUBSTRATE_STAGE_A_OVERLAP_FALLBACK_PREREG_20260926.md`](SUBSTRATE_STAGE_A_OVERLAP_FALLBACK_PREREG_20260926.md)
- Runner: [`substrate_stage_a_overlap_fallback_probe_v1.py`](../../../scripts/substrate_stage_a_overlap_fallback_probe_v1.py)
- Independent analyzer: [`analyze_substrate_stage_a_overlap_fallback_v1.py`](../../../scripts/analyze_substrate_stage_a_overlap_fallback_v1.py)
- Lock: [`stage_a_overlap_fallback_v1_lock_20260926.json`](../../../evaluation/substrate_capability/stage_a_overlap_fallback_v1_lock_20260926.json)
- Raw capture: [`substrate_stage_a_overlap_fallback_v1_20260926.json`](../../../evaluation/reports/substrate_stage_a_overlap_fallback_v1_20260926.json)
- Analysis: [`substrate_stage_a_overlap_fallback_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_stage_a_overlap_fallback_v1_analysis_20260926.json)

All ten independent integrity and semantic checks pass. This covers shared-source edge writes with target-local reads and the listed fanouts only. It does not prove the overlap detector sound for all effects, test node-write rules excluded statically, cover deletes/mints, or establish the prevalence of this shape in workload distributions. No timing or speedup was measured.
