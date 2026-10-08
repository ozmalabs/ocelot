# DimInfer nonlinear geometry-distribution results

## Capture and analysis

The locked experiment completed 576 fresh workers: 24 sampled geometries × eight transform families × three replicates. Each worker ran independent intact and generator-ablated full-seed states, with GenInfer disabled. There were no worker failures, all PIDs were unique, the exact geometry sample and inputs reconstructed, and all 16 v2.1 checks passed, including semantic determinism across the three repeats for every family × geometry × arm cell. The 24 geometries—not the 72 repeated workers per family—are the geometry-level sampling units.

The first v2 analyzer failed its design-equality check because it compared Python tuples with JSON arrays and expected raw and lock metadata objects to have identical fields. Its route summary also counted Transform records with no generator as “no transform” and ignored `dims`/`deltas` residuals. Both issues are disclosed in the v2.1 amendment; the initial analysis remains available. V2.1 normalizes array representations and separates generator routes, residual-bearing routes, Rung 1 residual-only records, and no-record fallthrough. It changes no raw data or workload.

## Geometry-level route rates

| Family | Intact route across 24 geometries | Ablated route across 24 geometries |
|---|---|---|
| `rotation90` | Intended exact: 24/24 | No Transform record; novelty mint: 24/24 |
| `reflection_r` | Intended exact: 24/24 | Exact alternate: 10/24; alternate with residual shifts: 14/24 |
| `reflection_c` | Intended exact: 24/24 | Exact alternate: 24/24 |
| `scale2` | Intended exact: 24/24 | No Transform record; novelty mint: 24/24 |
| `cycle4` | Intended exact: 24/24 | Alternate `reflection_r` plus local shifts: 6/24; mint: 18/24 |
| `rotation90 → cycle4` | Intended exact: 21/24; `rotation90` plus residual shift: 3/24 | Mint: 24/24 |
| `reflection_r → cycle4` | Intended exact: 12/24; `cycle4(k=2)` plus residuals: 6/24; Rung 1 residual-only: 6/24 | Rung 1 residual-only: 6/24; mint: 18/24 |
| `rotation90 → scale2` | Intended exact: 24/24 | Mint: 24/24 |

The reflection result separates an invariant ambiguity from geometry-dependent alternatives. `reflection_r` is algebraically identical to `reflection_c → rotation90(k=2)` (and vice versa) for every bounded point set. The engine selected that exact alternate for all 24 `reflection_c` ablations and 10 `reflection_r` ablations; on the other 14 `reflection_r` geometries, it preferred a one-generator route plus predicate-local shifts. No point geometry can make the algebraically identical paths identifiable from endpoint coordinates alone.

The non-exact aliases do vary with geometry. Removing `cycle4` produced `reflection_r` plus predicate-specific residuals on 6/24 geometries; the other 18 had no Transform record and minted a quantum. For `reflection_r → cycle4`, 6/24 intact geometries were explained by `cycle4(k=2)` plus residuals, and another 6/24 by Rung 1 residuals with no DimInfer generator. Thus the route mix is a property of the geometry distribution and rung ordering, not just the operator inventory.

Across all intact calls, status is `recognized_transformed` and no CapabilityAxis quanta are added. Ablation adds one quantum on 396/576 worker arms (132/192 geometry-level family/arm cells), while other ablations remain recognized through exact alternate, residual-bearing alternate, or Rung 1 explanations. This again shows that terminal status is not an acquisition or route metric.

## Cost and limits

Median closure times are about 0.71–0.74 ms for primitive families and 1.35–1.62 ms for compositions. These are small full-seed closure times on the measured host, excluding boot and fixture construction; paired differences are descriptive. The geometry population is uniformly rejection-sampled from a bounded 4×4 lattice with conditions chosen to exercise the modulo boundary. It is not a natural-task distribution, does not test generator induction, and cannot resolve exact algebraic aliases.

Next report exact D4 identities as equivalence classes and evaluate sequence identification only with history, intervention, or another independent signal. Expand the geometry distribution beyond the 4×4 lattice for residual-alias rates, and measure induction of a genuinely novel nonlinear operator separately; the current GenInfer path is linear-only.

## Artifacts

- [Preregistration](SUBSTRATE_DIMINFER_NONLINEAR_GEOMETRY_DISTRIBUTION_V2_PREREG_20260926.md)
- [V2.1 analysis amendment](SUBSTRATE_DIMINFER_NONLINEAR_GEOMETRY_DISTRIBUTION_V2_1_AMENDMENT_20260926.md)
- [Source/design lock](../../../evaluation/substrate_capability/diminfer_nonlinear_geometry_distribution_v2_lock_20260926.json)
- [Runner](../../../scripts/substrate_diminfer_nonlinear_geometry_distribution_v2.py)
- [Initial analyzer](../../../scripts/analyze_substrate_diminfer_nonlinear_geometry_distribution_v2.py)
- [Amended analyzer](../../../scripts/analyze_substrate_diminfer_nonlinear_geometry_distribution_v2_1.py)
- [Raw capture](../../../evaluation/reports/substrate_diminfer_nonlinear_geometry_distribution_v2_20260926.json)
- [Initial analysis](../../../evaluation/reports/substrate_diminfer_nonlinear_geometry_distribution_v2_analysis_20260926.json)
- [V2.1 analysis](../../../evaluation/reports/substrate_diminfer_nonlinear_geometry_distribution_v2_1_analysis_20260926.json)
