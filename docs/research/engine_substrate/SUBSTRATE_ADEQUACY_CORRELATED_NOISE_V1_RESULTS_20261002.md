# Correlated signed-label noise v1 — results

**Status:** 84/84 independent analysis gates pass across 4,320 trials in three fresh processes. The source/native/protocol/runner/analyzer lock remained stable.

## Findings

The panel extends the two-task independent-noise experiment with a common-mode mixture whose pairwise flip-indicator correlation is ρ. It crosses parity and threshold tasks, correct and constant-false candidates, per-provider flip rates 0.1/0.5, 1/3/5 providers, and ρ=0/0.5/1. Every selected probe has nonzero entropy. The analyzer exactly reconstructs each common-mode decision, flip vector, signed label, HMAC, receipt, eligibility result, and held-out score.

With five providers at p=0.1, the wrong-candidate false-eligibility count over the two task families was 0/120 at ρ=0, 5/120 at ρ=0.5, and 6/120 at ρ=1. Corresponding correct-candidate adoption was 61/120, 92/120, and 109/120. At p=0.5, wrong-candidate false eligibility was 4/120, 31/120, and 55/120 as ρ increased; correct-candidate adoption was 2/120, 32/120, and 57/120. The low p=0.1 cells are noisy at 60 trials per task; the raw rates are descriptive and must not be read as calibrated prevalence.

The exact model predicts wrong-candidate eligibility `ρp + (1−ρ)p^m` and correct-candidate eligibility `ρ(1−p) + (1−ρ)(1−p)^m`. Thus at p=0.5 and m=5, eligibility rises from 0.03125 with independent channels to 0.265625 at ρ=0.5 and 0.5 at full common mode, for both candidate qualities. Adding IDs only helps against the independent component. The full-common-mode limit matches the previously observed two-provider shared-false-label failure.

## Scope and next work

This is a stipulated mixture model over two authored tasks, not an estimate of provider correlation. It measures receipt/adoption eligibility, not repeated graph writes, and assumes the providers' marginal error rate is known. The 60-per-task cell size is descriptive. Next measure burst/clustered errors with calibrated quality strata and domain shifts, and compare fail-closed unanimity with a provenance-aware policy under equal label and compute budgets. Do not count IDs as independent evidence without operator/source lineage.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_CORRELATED_NOISE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1.py)
- [Independent-noise base runner](../../../evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_correlated_noise_v1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_correlated_noise_v1_raw_20261002.json) and [analysis](../../../evaluation/reports/substrate_adequacy_correlated_noise_v1_analysis_20261002.json)
