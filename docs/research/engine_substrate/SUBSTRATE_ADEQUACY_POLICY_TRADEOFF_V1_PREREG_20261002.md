# Offline adequacy policy tradeoff v1 — preregistration

## Question

At identical probe and label budgets, what correct-adoption/false-adoption/refusal tradeoff would unanimity, simple majority, and 80% provider agreement produce on the already source-locked independent and common-mode noise captures?

## Method

This is a preregistered deterministic secondary analysis of the captured trials in `SUBSTRATE_ADEQUACY_STOCHASTIC_NOISE_V1` and `SUBSTRATE_ADEQUACY_CORRELATED_NOISE_V1`; it does not collect new examples or update the substrate. For each captured selected probe, derive the candidate's native prediction and replay its labels/receipt. Compare vote thresholds `q=m`, `q=floor(m/2)+1`, and `q=ceil(0.8m)`. A policy is eligible to accept the candidate only when at least q signed providers match its native prediction and the recorded probe has positive entropy. Every policy uses the same m labels for a row.

Report correct-candidate adoption, wrong-candidate false adoption, and refusal separately by noise process, marginal error p, correlation ρ, and provider count m. Compare empirical rates with the exact binomial/common-mode predictions. Verify both source-locked input captures and all upstream analysis gates before deriving the alternative outcomes.

## Limits

The policies are hypothetical offline vote rules, not implemented substrate policies. Provider quality and common-mode process are simulated. The analysis cannot establish provider independence, truth, field noise rates, or the benefit of a policy under natural tasks. Label counts are matched; policy CPU cost and live mutation are not measured.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_policy_tradeoff_v1.py --lock
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_policy_tradeoff_v1.py
```
