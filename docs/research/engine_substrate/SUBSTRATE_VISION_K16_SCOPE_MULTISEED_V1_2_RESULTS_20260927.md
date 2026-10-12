# K=16 global versus Retina-root scope: three-seed audited result

**Run:** 2026-09-27. **Fixture:** three independent 4×4 lateral sheets; each seed has an authored global `st_settle` arm and a benchmark-only Retina-root-scoped clone. Every arm used 3,000 retinal-development steps, 2,000 theta-adaptation presentations, full-rescan closure, frozen readout, and `cell_stats(key="rate", period=4, K=16)`.

## Confirmatory checks

The source-locked driver passes all 9 gates across three fresh workers. The independent analyzer passes all 14 checks. It independently recomputes every OSI from the 16×12 tuning matrix, verifies global/root-scoped parity, and checks the complete per-unit `oo_post` weight vectors recorded immediately before and after each readout. The maximum absolute weight delta is exactly zero in all six arms; the independent before/after hashes agree with the runner, and each after-readout hash reconciles with the arm's final weight hash.

| Seed | Global mean OSI | Root-scoped mean OSI | Max tuning delta | Max OSI delta | Max readout weight delta |
|---:|---:|---:|---:|---:|---:|
| 20260931 | 0.225422 | 0.225422 | 0 | 0 | 0 |
| 20260932 | 0.279704 | 0.279704 | 0 | 0 | 0 |
| 20260933 | 0.378932 | 0.378932 | 0 | 0 | 0 |

All three paired tuning arrays and OSI vectors are exactly equal. The seed-to-seed OSI variation remains substantial, so this establishes scope invariance for the tested preparations; it does not establish robust selectivity or broad task competence. Execution mode, preparation, rule bodies apart from the registered scope rewrite, and all readout settings were held fixed.

## Claim boundary

This is a single-sheet 4×4 vision workload, not multi-sheet task evaluation or evidence about the prevalence of cheap cuts. It measures no speedup: each arm still evaluates the full calibrated readout workload, and the reported phase timings are descriptive only. Learned frame discovery, larger validated anatomy, other visual objectives, and non-vision capability families remain open.

The v1 source-snapshot failure and v1.1 source-stable response-only run remain separately preserved; v1.2 is the first capture to satisfy the registered within-readout weight-drift audit.

## Reproduction artifacts

- [Base preregistration](SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_PREREG_20260927.md), [source-snapshot amendment](SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_1_AMENDMENT_20260927.md), and [weight-audit amendment](SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_2_AMENDMENT_20260927.md)
- [Runner](../../../scripts/substrate_vision_k16_scope_multiseed_v1_2.py) and [independent analyzer](../../../scripts/analyze_substrate_vision_k16_scope_multiseed_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/vision_k16_scope_multiseed_v1_2_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/substrate_vision_k16_scope_multiseed_v1_2_20260927.json) and [independent analysis](../../../evaluation/reports/substrate_vision_k16_scope_multiseed_v1_2_analysis_20260927.json)
