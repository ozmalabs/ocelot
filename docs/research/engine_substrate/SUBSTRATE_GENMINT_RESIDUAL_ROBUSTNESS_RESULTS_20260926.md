# Full-seed GenInfer residual-robustness results (2026-09-26)

## Protocol result

The production `shape_decode_loop` ran 240 fresh-core sequences (3 layouts × 2 identity modes × 4 first-member conditions × 2 GenInfer settings × 5 repeats), with two full closure calls per sequence. All nine integrity/provenance gates pass. Every observation settles, the GenInfer-disabled arm mints no linear generators, and semantic outcomes are repeat-stable. The experiment body took 16.279 s including boot/setup; this is one machine/build run.

## Main observations

- **Positive control:** all 30 GenInfer-enabled first members end `recognized_transformed`. Twenty mint the exact `[1,1,0,2]` generator; ten paired-square cases are handled by an earlier held transform and mint no linear generator.
- **Corrupted first member:** across 90 enabled cases, 35 finish the first closure as `recognized_transformed` and 55 as `minted`. A linear generator appears after the first observation in 25 cases: five are the generating matrix and 20 are alternatives. The remaining 65 cases split into ten held-transform recognitions with no new linear generator and 55 quantum mints. This differs from the direct evaluator because earlier held rungs can intercept a case before GenInfer; the enabled flag does not force GenInfer to run.
- **Later clean `M²(base)`:** all 120 enabled sequences end `recognized_transformed`, including cases where the first minted generator was an alternative. In exactly the 20 alternative-first cases, the clean member causes an additional linear generator to be present by sequence end. Reuse succeeds, with extra codebook growth.
- **GenInfer-disabled comparison:** 80/120 downstream clean members end `minted`; the other 40 paired-square cases are already handled by the held transform in both arms. Across the 120 sequences, enabled closure mints 55 CapabilityAxis quanta versus 180 with GenInfer disabled (69.4% fewer). This count is specific to this two-observation sequence and does not include a description-length cost for generator nodes.

## Cost envelope

Per-closure medians were 1.482 ms (enabled first member), 0.572 ms (enabled clean M²), 0.494 ms (disabled first), and 0.371 ms (disabled clean M²). The enabled clean-M² p90 was 221.757 ms, with a 252.208 ms maximum, consistent with occasional repeated induction/search work in a tiny four-relation fixture. These timings are descriptive, not a stable benchmark claim; they show that rare branches can dominate the tail even when the median operating path stays small.

## Interpretation and limits

The substrate's held-basis order materially conditions the direct GenInfer result: some positive and corrupted cases are handled upstream and never mint a matrix. Where wrong matrices are minted, later clean observations can recover by adding another generator; this preserves recognition but incurs extra structure. Thus end-to-end capability should track route, exact generator recovery, alternative minting, later recognition, additional mint count, quanta, and latency separately. A success status alone hides both the extra acquisition and long-tail cost.

This remains one authored map, three four-relation layouts, three coordinate perturbation magnitudes, and the current seed. It does not estimate natural-task noise, learning accuracy, broad resource use, or the frequency of these paths in deployment.

## Artifacts

Protocol: [`SUBSTRATE_GENMINT_RESIDUAL_ROBUSTNESS_PREREG_20260926.md`](SUBSTRATE_GENMINT_RESIDUAL_ROBUSTNESS_PREREG_20260926.md). Runner/analyzer: [`genmint_residual_robustness_probe_v1.py`](../../../scripts/genmint_residual_robustness_probe_v1.py), [`analyze_substrate_genmint_residual_robustness_probe_v1.py`](../../../scripts/analyze_substrate_genmint_residual_robustness_probe_v1.py). Raw capture: [`substrate_genmint_residual_robustness_v1_20260926.json`](../../../evaluation/reports/substrate_genmint_residual_robustness_v1_20260926.json). Analysis: [`substrate_genmint_residual_robustness_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_genmint_residual_robustness_v1_analysis_20260926.json).
