# GenInfer 2-D search scaling results

**Run date:** 2026-09-26  
**Protocol:** [`SUBSTRATE_GENINFER_SCALE_PREREG_20260926.md`](SUBSTRATE_GENINFER_SCALE_PREREG_20260926.md)  
**Engine:** `24073a9be843`  
**Evidence grade:** three-bound direct evaluator timing; five repetitions per bound; all semantic and provenance checks pass

## Result

The fixed four-cell L fixture recovers the expected matrix at every scale. The exhaustive candidate count follows `(2B+1)^4 - 1`; median direct-call time and candidate throughput are:

| Bound B | Expected matrix | Candidate matrices | Median time | Min–max | Median candidates/s |
|---:|---|---:|---:|---:|---:|
| 4 | `[2,1,1,1]` | 6,560 | 7.398 ms | 7.302–10.918 ms | 886,748 |
| 8 | `[4,2,2,2]` | 83,520 | 93.812 ms | 92.206–95.931 ms | 890,293 |
| 12 | `[6,3,3,3]` | 390,624 | 437.723 ms | 434.183–458.635 ms | 892,400 |

Median time ratios relative to B=4 are 12.68× at B=8 and 59.17× at B=12. Candidate-count ratios are 12.73× and 59.55×. The near-constant median candidate throughput is consistent with time being dominated by the exhaustive candidate loop for this fixed fixture and range.

## Interpretation and limits

This is direct `GenInfer` evaluator time on one immutable graph and one positive shape family. It excludes process startup, graph construction, the separate `checked` read, full rule closure, generator insertion, and follow-up decode. It supports the local statement “roughly 0.89 million tested matrices per second at B=4–12 for this four-relation example on this engine and machine.” It does not prove an asymptotic runtime law, constant per-candidate cost across input sizes, a general CPU capacity estimate, or natural-task tractability. Only three bounds and five samples per bound were measured; B=4 has visible timing spread. Higher dimensions remain skipped by the evaluator, and the next required performance work is to vary relation count and task family while retaining the bound sweep.

## Reproducibility artifacts

- Preregistration: [`SUBSTRATE_GENINFER_SCALE_PREREG_20260926.md`](SUBSTRATE_GENINFER_SCALE_PREREG_20260926.md)
- Runner: [`geninfer_scale_probe_v1.py`](../../../scripts/geninfer_scale_probe_v1.py)
- Independent analyzer: [`analyze_substrate_geninfer_scale_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_scale_probe_v1.py)
- Raw capture: [`substrate_geninfer_scale_probe_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_scale_probe_v1_20260926.json)
- Analysis: [`substrate_geninfer_scale_probe_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_scale_probe_v1_analysis_20260926.json)
