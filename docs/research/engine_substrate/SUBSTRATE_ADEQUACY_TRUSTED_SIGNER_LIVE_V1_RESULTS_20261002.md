# Trusted signer live-route adequacy test v1 — results

Date: 2026-10-02

## Result

All 7 independent checks pass across six fresh, source/native/seed-locked workers with no source drift.

| Condition | Provider authentication | Core receipt | Adoption | Held-out square cases |
|---|---:|---:|---:|---:|
| Correct square candidate; correct signed label | 3/3 | accepted 3/3 | adopted 3/3 | 9/9 correct |
| Identity candidate; trusted provider signs identity's wrong answer at `x=2` | 3/3 | accepted 3/3 | falsely adopted 3/3 | 0/9 correct |

The false label is HMAC-valid, request-bound, candidate-bound, and consistent with the identity Term at the single requested probe. The signed envelope also carries the square-oracle identifier, but that identifier is only a signed claim; the adapter does not execute or independently verify the oracle. This is a live end-to-end demonstration that provider authentication establishes possession of a configured key, not truth or adequacy. Median `converse` times were 172.73 ms for the truthful arm and 178.07 ms for the false-label arm; three observations per arm are descriptive only.

The result supports an independent-provider agreement / probe-adequacy gate as the next experiment. Distinct provider IDs alone will not prove independence: registry ownership and provider correlation must be part of the evaluation. Multi-probe selection also has a known limit: if the admissible probe domain aliases the hypotheses, no finite check over that domain can distinguish them.

## Scope

One authored scalar task family, one host, one test-only key, and a deliberately adversarial trusted label. This measures the existence of a failure mode; it does not estimate how often natural providers err or predict real-world false-adoption rates.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_TRUSTED_SIGNER_LIVE_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_trusted_signer_live_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/substrate_adequacy_trusted_signer_live_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_trusted_signer_live_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_trusted_signer_live_v1_analysis_20261002.json)
