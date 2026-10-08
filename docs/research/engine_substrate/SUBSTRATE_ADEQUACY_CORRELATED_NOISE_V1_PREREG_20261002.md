# Correlated signed-label noise v1 — preregistration

## Question

How does common-mode provider error change the false-adoption/refusal tradeoff measured under independent label noise?

## Design

Reuse the source-locked parity and threshold tasks, correct and constant-false candidate conditions, independent per-provider flip rates `p ∈ {0.1, 0.5}`, provider counts `m ∈ {1,3,5}`, and add common-mode mixture weight `ρ ∈ {0,0.5,1}`. Each task × candidate quality × p × ρ × m cell receives 60 deterministic trials across three fresh workers (4,320 trials total). On each trial, with probability ρ all providers share one Bernoulli(p) flip; otherwise each provider receives an independent Bernoulli(p) flip. This mixture has pairwise flip-indicator correlation ρ and preserves marginal error probability p.

At the selected distinguishing probe, the receipt accepts unanimous labels matching the candidate, rejects unanimous labels contradicting it, and marks any disagreement ambiguous. For a correct candidate, theoretical adoption eligibility is `ρ(1-p) + (1-ρ)(1-p)^m`. For a wrong candidate, theoretical false eligibility is `ρp + (1-ρ)p^m`. All process/source selection, signature, receipt and held-out checks from the independent-noise panel remain in force.

## Interpretation limits

The provider errors are simulated; the model stipulates one simple common-mode mixture and does not estimate natural correlation or represent every dependence structure. Provider IDs and fixture keys do not establish actual independent operators. The measured result is mechanism-level adoption eligibility, not repeated graph mutation or a task-prevalence estimate.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_correlated_noise_v1.py
```
