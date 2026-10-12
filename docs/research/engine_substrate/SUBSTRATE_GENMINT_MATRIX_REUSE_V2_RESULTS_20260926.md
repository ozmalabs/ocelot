# Full-seed GenMint extended-horizon reuse results

## Capture and analysis provenance

The v2 preregistered run completed all 540 fresh-process workers across 3 matrices × 3 predicate layouts × 2 induction arms × 6 reuse prefixes × 5 replicates, with no worker failures and unique PIDs. Exact source, native artifact, and lock hashes are stored in the raw record. The first analysis was invalidated by its own denominator error: it expected 90 design cells where the locked factorial has 108. That initial output is preserved. Amendment v2.1 corrects the cell count only, keeps the raw capture and locked runner unchanged, and the independent corrected analysis passes all 16 gates, including the exact randomized schedule, 108 balanced cells, all inputs/targets, repeated outcomes, route classification, and provenance checks.

The 16 held-out bases are deterministic, asymmetric four-point integer shapes generated from the preregistered seed. Across all enabled training arms, the same acquisition pattern recurs: the expected matrix is acquired in 40/45 cases per K prefix, with the `shearB × adjacent_01` cell missing in all five replicates. In the 8/9 successful matrix/layout cells, every application routed through the training-acquired matrix exactly predicts all held-out rows: 1,240 application calls and 4,960/4,960 rows across the full experiment. Across all K values, 25 calls mint a generator during application, 130 later reuse an application-minted generator, and 1,395 have no selected generator transform. These routes are retained separately from training transfer.

## Stage-separated paired costs

The table gives medians across 45 matched matrix/layout/replicate pairs at each K. Costs are sums of measured full native rule-closure calls; process startup, seed boot, and input graph construction are excluded. “Application-only” sums the heldout closure calls and excludes the training closure. Process RSS is the fresh worker high-water mark.

| K | Enabled train ms | Disabled train ms | Enabled applications ms | Disabled applications ms | Enabled total ms | Disabled total ms | Enabled faster pairs | Median quanta enabled/disabled |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3.802 | 0.875 | 0 | 0 | 3.802 | 0.875 | 4/45 | 0 / 1 |
| 1 | 3.851 | 0.887 | 0.735 | 0.833 | 5.028 | 1.727 | 0/45 | 0 / 2 |
| 2 | 3.794 | 0.881 | 1.543 | 1.910 | 6.064 | 2.817 | 0/45 | 0 / 3 |
| 4 | 3.888 | 0.883 | 3.651 | 4.802 | 8.445 | 5.693 | 0/45 | 0 / 5 |
| 8 | 3.911 | 0.884 | 9.394 | 13.368 | 14.624 | 14.272 | 21/45 | 0 / 9 |
| 16 | 3.800 | 0.875 | 27.438 | 41.951 | 32.194 | 42.816 | 25/45 | 0 / 17 |

The median paired enabled-minus-disabled total-cost difference first becomes negative at K=16 in the pooled intention-to-treat comparison (−9.94 ms). Conditional on training acquiring the expected matrix, it crosses at K=8 (median paired difference −0.21 ms; 21/40 pairs faster), and at K=16 the conditional median difference is −10.78 ms (25/40 pairs faster). This conditional view is descriptive and post-stratified by the measured acquisition outcome; it does not replace the pooled result. At K=16, median application-only cost is about 14.5 ms lower in the enabled arm, offsetting its roughly 2.9 ms higher training closure cost. Disabled arms use one CapabilityAxis quantum at training and one on each held-out application; enabled arms use zero median quanta across the sequence when acquisition succeeds.

The successful `shearA` layouts and `shearB` layouts that acquire during training reach their first stratum median crossover at K=8. No prior-matrix layout crosses through K=16 in this run, so the pooled result hides matrix-specific economics. The persistent `shearB × adjacent_01` miss is a serious tail: training ends recognized with no linear generator, then its first heldout task takes 548–595 ms in the enabled arm while minting `genlin_[1,1,0,1]`. Later heldout tasks reuse that generator in about 0.8–1.6 ms each. This pattern reproduces across K prefixes and shows that delaying induction until heldout failure can create a large single-call latency spike. The nominal tiny K=0 speed difference in this stratum is noise around sub-millisecond calls and is not a meaningful crossover.

Peak process RSS remains around 42 MiB with no useful arm distinction at this scale. These measurements do not isolate the internal GenInfer evaluator from full rule closure and do not include seed boot in the economic curve.

## What this establishes and what remains open

This experiment strengthens the case for an economic operating profile: in the successful authored matrix/layout cells, training cost is higher and held-structure application is cheaper; savings accumulate and outweigh the training premium by K=8 conditionally and K=16 overall on this capture. It also identifies a severe latency-tail case when the training view is insufficient to mint the needed structure. The evidence is limited to three matrices, three predicate layouts, 16 generated clean shapes, one full-seed path, one host, and K≤16. It does not establish natural-task acquisition frequency, general capability, stable break-even across matrices, commodity-scale performance, or asymptotic tractability.

Next: broaden to independently authored transform families and geometries, measure the probability and latency of deferred acquisition on a preregistered layout distribution, and collect internal stage attribution or direct-evaluator controls. The substrate-wide cheap-cut premise remains a separate open requirement: measure separator/boundary width and execution factorisation on preregistered representative workloads, including a known globally coupled counterexample.

## Reproduction artifacts

- [v2 preregistration](SUBSTRATE_GENMINT_MATRIX_REUSE_V2_PREREG_20260926.md)
- [v2.1 analysis amendment](SUBSTRATE_GENMINT_MATRIX_REUSE_V2_1_AMENDMENT_20260926.md)
- [source/design lock](../../../evaluation/substrate_capability/genmint_matrix_reuse_v2_lock_20260926.json)
- [runner](../../../scripts/genmint_matrix_reuse_probe_v2.py)
- [initial analyzer](../../../scripts/analyze_genmint_matrix_reuse_probe_v2.py)
- [corrected analyzer](../../../scripts/analyze_genmint_matrix_reuse_probe_v2_1.py)
- [raw capture](../../../evaluation/reports/substrate_genmint_matrix_reuse_v2_20260926.json)
- [initial failed analysis](../../../evaluation/reports/substrate_genmint_matrix_reuse_v2_analysis_20260926.json)
- [corrected analysis](../../../evaluation/reports/substrate_genmint_matrix_reuse_v2_1_analysis_20260926.json)
