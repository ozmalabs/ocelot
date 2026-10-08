# Offline evidence-policy tradeoff v1 — results

**Status:** 327/327 analysis gates pass. This deterministic secondary analysis replays 6,480 locked source trials under three hypothetical vote rules, yielding 19,440 policy decisions. It does not change the substrate or collect new labels.

## Main result

For each row, unanimity, simple majority, and 80% agreement receive the same signed labels and use the same nonzero-entropy probe. Under the independent p=0.1, five-provider input, correct-candidate eligibility was 72/120 for unanimity, 113/120 for 80% agreement, and 119/120 for majority. Wrong-candidate false eligibility was 0/120, 2/120, and 6/120 respectively. The empirical majority false-accept count is higher than its exact model expectation (about 1/120); with only 120 examples, treat all empirical rates as descriptive and use the preregistered exact-model probabilities for the mechanism comparison.

At p=0.5 with five providers and independent errors, empirical correct eligibility was 5/120 under unanimity, 23/120 under 80% agreement, and 63/120 under majority; wrong-candidate false eligibility was 4/120, 20/120, and 56/120. The exact model gives the same probability to a correct acceptance and a false acceptance at p=0.5, making majority uninformative absent calibrated provider quality.

Common-mode errors narrow the advantage of relaxed voting. With p=0.5, five providers, and ρ=0.5, exact eligibility for correct candidates is 0.34375 under 80% agreement and 0.5 under majority; false eligibility has the same values for wrong candidates. At ρ=1 all three rules reduce to the one-source behavior because every provider shares the same label. Thus a threshold can trade refusals for false adoption only under assumptions about source quality and dependence.

## Interpretation and limits

The comparison confirms a policy frontier, not a universally superior rule. Under the same label budget, unanimity requires stronger agreement and refuses many correct candidates under independent noise. Majority improves coverage under low independent noise but becomes uninformative at 50% error and does not withstand common-mode corruption. The 80% rule is an intermediate operating point in these simulations. The exercise uses stipulated synthetic providers, two Boolean tasks, and 60 samples per task/cell; it measures neither CPU cost nor repeated live graph writes, and it does not estimate natural provider reliability. No production policy change is justified by this analysis alone.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_POLICY_TRADEOFF_V1_PREREG_20261002.md)
- [Analysis script](../../../evaluation/substrate_capability/analyze_substrate_adequacy_policy_tradeoff_v1.py)
- [Input-source lock](../../../evaluation/substrate_capability/substrate_adequacy_policy_tradeoff_v1_lock_20261002.json)
- [Derived analysis](../../../evaluation/reports/substrate_adequacy_policy_tradeoff_v1_analysis_20261002.json)
- Source captures: [independent noise](../../../evaluation/reports/substrate_adequacy_stochastic_noise_v1_raw_20261002.json), [common-mode noise](../../../evaluation/reports/substrate_adequacy_correlated_noise_v1_raw_20261002.json)
