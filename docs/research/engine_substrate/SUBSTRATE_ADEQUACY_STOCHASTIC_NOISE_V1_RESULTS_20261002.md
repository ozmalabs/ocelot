# Stochastic label-noise dose response v1 — results

**Status:** 48/48 independent analysis gates pass across 2,160 trials in three fresh processes. The initial manifest mismatch was detected before any worker ran; its diagnostic lock is retained and the confirmatory run uses the amended v1.1 lock.

## Findings

The panel crosses parity and three-input threshold tasks, correct and constant-false candidate models, label-flip probabilities 0/0.1/0.5, and 1/3/5 simulated signed providers. Each cell has 60 deterministic but separately seeded trials. The analyzer independently reproduces 2,160 probe selections, noise draws, label values, HMAC signatures, receipts, and held-out oracle checks; all source/native hashes remain stable.

The observed acceptance/refusal pattern follows the fail-closed rule. At a distinguishing probe, a correct candidate is eligible for adoption only when every provider returns the uncorrupted label, with theoretical probability `(1-p)^m`. A wrong candidate can be falsely eligible only when all providers flip to its value, with theoretical probability `p^m`; conflicting values become ambiguous. At `p=0.1`, increasing providers from one to five moves the theoretical correct-acceptance probability from 0.90 to 0.590 and false-acceptance probability from 0.10 to 0.00001. At `p=0.5`, the corresponding probabilities are 0.50/0.50 with one provider and 0.03125/0.03125 with five. Empirical rates across each pair of task families tracked these predictions descriptively, with 60 observations per family/cell.

This is a sharp reliability tradeoff: fail-closed exact agreement can suppress false adoption under independent noise, but it turns any disagreement into refusal. It does not identify the truthful source, estimate real-world noise, or infer a majority as truth. The p=0.5 symmetry shows that more signatures do not help when provider correctness is uncalibrated. The separately measured trusted-false-signer condition remains outside this independent-noise model and still defeats adoption checks.

## Limits and next work

These are two authored Boolean tasks, simulated independent provider channels, one host, and mechanism-level eligibility rather than 2,160 graph writes. Provider independence and each flip probability are stipulated by the harness. Next test correlated and burst errors, domain-shifted probes, and a calibrated evidence-quality policy across more independently authored tasks; report correct adoption, false adoption, refusal, and label/compute cost together. Do not infer deployment noise rates from this panel.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_STOCHASTIC_NOISE_V1_PREREG_20261002.md)
- [v1.1 pre-capture amendment](SUBSTRATE_ADEQUACY_STOCHASTIC_NOISE_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py)
- [Independent oracles](../../../evaluation/substrate_capability/independent_adequacy_noise_oracles_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_stochastic_noise_v1.py)
- [Confirmatory lock](../../../evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_stochastic_noise_v1_raw_20261002.json) and [analysis](../../../evaluation/reports/substrate_adequacy_stochastic_noise_v1_analysis_20261002.json)
- [Initial diagnostic lock](../../../evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1_lock_20261002.json)
