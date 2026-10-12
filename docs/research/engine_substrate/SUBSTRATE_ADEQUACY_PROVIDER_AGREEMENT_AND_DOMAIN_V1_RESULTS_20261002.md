# Provider agreement and probe-domain adequacy v1 — results

Date: 2026-10-02

## Result

The source/native/seed-locked panel completed 15 fresh processes without source drift; all 10 independent checks pass.

| Condition | Authenticated labels | Receipt | Adoption | Held-out score |
|---|---:|---|---:|---:|
| Truthful square, one provider, distinguishing `x=2` | 1 | accepted | 3/3 | 9/9 |
| Identity, one correct and one false provider at `x=2` | 2 | ambiguous | 0/3 | not adopted |
| Identity, two distinct IDs agree on false `2` at `x=2` | 2 | accepted | 3/3 | 0/9 |
| Identity, two truthful providers on alias-only `x=0` | 2 | accepted | 3/3 | 0/9 |
| Identity, two truthful providers on distinguishing `x=2` | 2 | rejected | 0/3 | not adopted |

The existing receipt adjudicator correctly rejects conflicting labels as ambiguous and rejects unanimous truthful labels that contradict the candidate. However, the provider-authenticated live route accepts a false candidate when two different registered IDs agree on a false label, and also accepts a false candidate when the only fresh probe aliases it with the target. The two failures are distinct: provider correlation defeats a naïve ID-count quorum; an inadequate admissible domain defeats even truthful providers.

The API has a deterministic maximum-entropy challenger selector, but this experiment deliberately fixes the domain and does not connect that selector to live adoption. Even a selector can only distinguish hypotheses represented in its challenger set and within its admissible domain. The current strict adapter route validates signed evidence and receipt binding but does not attest provider independence, require a minimum number of distinct providers, or verify target-blind probe-selection provenance.

## Scope

One authored square/identity contrast, one host, fixture provider keys, and three repetitions per condition. This identifies failure modes; it does not estimate natural provider correlation or alias-domain prevalence. The IDs `oracle-a` and `oracle-b` are deliberately not evidence that two independent operators exist.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_PROVIDER_AGREEMENT_AND_DOMAIN_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_provider_agreement_domain_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_adequacy_provider_agreement_domain_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_provider_agreement_domain_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_provider_agreement_domain_v1_analysis_20261002.json)
