# GenInfer pattern-structure probe results (2026-09-26)

## Result

The preregistered 4-shape × 3-predicate-grouping probe passes all 10 independent checks. Across 12 cells and five calls per cell, all 60 calls recover `[2,1,1,1]`; all cells have exactly four base/goal relations, independently derived B=4, and 6,560 checked matrices. Native/source hashes, deterministic shuffled schedule, and finite positive timing samples verify.

## Descriptive cost pattern

Median direct-call latency by predicate grouping, summarized as the median of the four shape-specific medians, is:

| Predicate grouping | Median latency | Range over four shapes |
|---|---:|---:|
| Shared label | 7.40 ms | 7.26–7.53 ms |
| Two labels, two relations each | 7.59 ms | 7.42–7.90 ms |
| Four unique labels | 11.50 ms | 11.30–11.74 ms |

In this fixture, unique predicates cost about 1.55× shared predicates despite the same relation count, bound, candidate count, and recovered transform. Geometry has a smaller measured spread within each grouping: about 3.8% for shared, 6.5% for paired, and 3.9% for unique labels from fastest to slowest shape. These are five-repeat descriptive ratios without inferential intervals; treat them as hypotheses for a confirmatory run, not stable cost factors.

## Claim boundary and next work

This expands the positive 2-D evaluator evidence from copied copies of one L motif to four asymmetric point sets and three predicate-multiplicity patterns. It does not cover a new transformation family, noisy or negative cases, dimensions above two, larger B, automatic mint/closure, or natural tasks. The predicate effect may reflect the current matching/canonicalization path and should be confirmed with more repeats, plus one negative shape-preserving control and a separate task family. Continue acquisition-cost evaluation at the full seed path; direct evaluator time alone is not rung-3 learning cost.

## Reproduction

- Protocol: [preregistration](SUBSTRATE_GENINFER_PATTERN_STRUCTURE_PREREG_20260926.md)
- Runner: [capture script](../../../scripts/geninfer_pattern_structure_probe_v1.py)
- Independent analyzer: [analysis script](../../../scripts/analyze_substrate_geninfer_pattern_structure_probe_v1.py)
- Raw: [JSON](../../../evaluation/reports/substrate_geninfer_pattern_structure_v1_20260926.json)
- Analysis: [JSON](../../../evaluation/reports/substrate_geninfer_pattern_structure_v1_analysis_20260926.json)
