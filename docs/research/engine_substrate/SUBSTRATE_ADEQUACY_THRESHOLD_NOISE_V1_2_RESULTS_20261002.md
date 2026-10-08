# Threshold-task signed-evidence and domain-shift v1.2 — results

**Analysis:** 14/14 gates pass across 15 fresh workers. The initial failed pre-capture and v1.1 analyzer diagnostic are retained; see the [v1.1](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_1_AMENDMENT_20261002.md) and [v1.2](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_2_AMENDMENT_20261002.md) amendments.

## Outcomes

The independently implemented oracle is `left + right > limit`. The strict live `WorldAdapter.converse` route was evaluated with a supplied positive candidate and a constant-false alternative. The correct candidate was adopted in 3/3 runs and matched all 100 held-out triples, including values outside the small probe domain. With a broad probe domain, truthful labels rejected the false candidate in 3/3; with an alias-only domain, the receipt accepted the candidate-consistent label but the zero-entropy guard refused adoption in 3/3. Two authenticated providers signing conflicting labels produced `ambiguous` receipts and no adoption in 3/3.

The known epistemic failure reproduced on this new task: a trusted provider signed a false label at the selected discriminating input. The signature and receipt verified, the constant-false candidate was adopted in 3/3, and it matched only 58/100 shifted held-outs (42 errors) in each run. This is an expected failure condition in the preregistration, not a passing correctness outcome. Authentication binds who signed the value; neither HMAC nor probe disagreement establishes that the value is true.

The independent analyzer recomputed the selection, every provider signature, each receipt, and all held-out Term predictions against the separately source-locked oracle. It verified source/native/seed stability, schedule completeness, and 15 distinct worker processes. The positive condition gives bounded evidence that the arithmetic Term transfers outside the probe ranges; it does not establish natural distribution robustness.

## Scope and next work

One authored task, one host, harness-supplied candidates/domains, and test keys limit the result. The adversarial false-label frequency is not a prevalence estimate, and two key holders are not evidence of independent providers. Next evaluate controlled stochastic label noise and shifted intervals over multiple independently authored tasks, compare single-source and genuinely separated oracles, and report false adoption, correct adoption, and refusal rates under fixed label and compute budgets. Do not interpret provider agreement as truth without independent source governance.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_PREREG_20261002.md)
- [Amendments](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_1_AMENDMENT_20261002.md), [analysis amendment](SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_2_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1.py)
- [Independent oracle](../../../evaluation/substrate_capability/independent_threshold_oracle_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_threshold_noise_v1.py)
- [v1.2 lock](../../../evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1_2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_threshold_noise_v1_2_raw_20261002.json) and [analysis](../../../evaluation/reports/substrate_adequacy_threshold_noise_v1_2_analysis_20261002.json)
- Diagnostics: [initial lock](../../../evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1_initial_diagnostic_lock_20261002.json), [v1.1 raw](../../../evaluation/reports/substrate_adequacy_threshold_noise_v1_raw_20261002.json), [v1.1 analysis](../../../evaluation/reports/substrate_adequacy_threshold_noise_v1_analysis_20261002.json)
