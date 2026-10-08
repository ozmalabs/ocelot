# K=16 global versus Retina-root scope: three-seed result

**Run:** 2026-09-27. **Fixture:** three independent 4×4 lateral sheets, each with an authored global `st_settle` arm and a benchmark-only Retina-root-scoped clone. All arms used 3,000 retinal-development steps, 2,000 theta-adaptation presentations, frozen readout, and `cell_stats(key="rate", period=4, K=16)` under unfiltered full-rescan closure.

## Response result

The corrected v1.1 capture passes all seven driver gates and the independent analyzer passes all twelve implemented checks. Source fingerprints are stable at worker start/end and after the run; each seed ran in a fresh worker. The independent analyzer recomputed every OSI from the tuning arrays. For each seed, the 16×12 tuning arrays and 16 per-unit OSIs are exactly equal between scope arms (maximum absolute deltas 0).

| Seed | Global mean OSI | Root-scoped mean OSI | Max tuning delta | Max per-unit OSI delta |
|---:|---:|---:|---:|---:|
| 20260931 | 0.225422 | 0.225422 | 0 | 0 |
| 20260932 | 0.279704 | 0.279704 | 0 | 0 |
| 20260933 | 0.378932 | 0.378932 | 0 | 0 |

Per-seed adaptation and probe fixed-point/repeated-state counts match between scope arms. Final weight hashes match within each seed. The OSI variation across these three initializations is notable; the result is paired scope invariance on the tested preparations, not evidence that the sheet has high or robust selectivity.

## Preregistration discrepancy and claim boundary

The preregistration required a direct before/after readout weight-drift check. The inherited `cell_stats` harness records final weights but does not retain a pre-readout weight hash, so that requirement was not measured. The capture and analyzer gates therefore establish the response-parity result above but do **not** satisfy the entire preregistered gate. Final weight-hash equality across scope arms is not a substitute for a within-arm drift check. Add that audit before claiming a full confirmatory pass.

This is a single-sheet, 4×4, three-seed workload. It does not test multi-sheet task outcomes, global-factor prevalence, a speedup, learned frames, or general vision capability. Full-rescan timing is descriptive and excludes no causal cost claim.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_PREREG_20260927.md) and [harness amendment](SUBSTRATE_VISION_K16_SCOPE_MULTISEED_V1_1_AMENDMENT_20260927.md)
- [Runner](../../../scripts/substrate_vision_k16_scope_multiseed_v1_1.py) and [independent analyzer](../../../scripts/analyze_substrate_vision_k16_scope_multiseed_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/vision_k16_scope_multiseed_v1_1_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/substrate_vision_k16_scope_multiseed_v1_1_20260927.json), [independent analysis](../../../evaluation/reports/substrate_vision_k16_scope_multiseed_v1_1_analysis_20260927.json), and [failed v1 source-snapshot capture](../../../evaluation/reports/substrate_vision_k16_scope_multiseed_v1_20260927.json)
