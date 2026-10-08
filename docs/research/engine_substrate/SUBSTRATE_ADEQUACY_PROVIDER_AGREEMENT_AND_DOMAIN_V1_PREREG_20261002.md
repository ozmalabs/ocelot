# Provider agreement and probe-domain adequacy v1 — preregistration

Date: 2026-10-02

## Question

What do multiple authenticated labels and a challenger-disagreement probe buy at the live code-shape adoption boundary, and what failures remain when provider IDs are correlated or the admissible input domain aliases the hypotheses?

## Conditions

Five source-bound candidate/evidence cases run in three fresh processes each:

1. `honest_single`: square candidate, one trusted provider, probe `x=2`, expected 4.
2. `conflicting_two`: identity candidate, probe `x=2`, one provider says 4 and one says 2; the receipt should be ambiguous and adoption refused.
3. `correlated_wrong_two`: identity candidate, probe `x=2`, two distinct registered provider IDs both sign 2 while the fixed square oracle says 4; the receipt may accept identity, exposing that distinct IDs alone do not prove independent judgment.
4. `aliased_honest_two`: identity candidate, probe only `x=0`, two providers both truthfully return 0; the evidence should authenticate and accept while held-out square checks fail, exposing an uninformative domain.
5. `distinguishing_honest_two`: identity candidate, probe `x=2`, two providers both truthfully return 4; the identity receipt should reject and no shape should be adopted.

Every signature is bound to provider ID, request, probe, input, label, and the square-oracle digest. For each process, verify HMAC status, receipt status, typed code-shape adoption delta, and outputs on `x=3,4,5` against `x*x`. The probe selector is not asked to choose in this panel; the input domains are fixed so the alias and distinguishing controls are explicit and auditable.

## Limits

Providers and keys are fixtures; provider IDs are not evidence of operational independence. The task family is one scalar square/identity contrast on one host. This panel measures the behavior of the current authenticated route and receipt adjudicator, not natural provider correlations, prevalence of aliasing, or a general solution to inductive inference.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_provider_agreement_domain_v1.py
```
