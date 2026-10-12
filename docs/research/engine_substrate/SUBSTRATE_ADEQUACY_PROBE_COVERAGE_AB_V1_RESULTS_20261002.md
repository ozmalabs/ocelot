# Adequacy-probe coverage and gated/ungated comparison v1 results

All 29 analysis checks pass across three matched repetitions. Within each
narrow or broad gated/ungated pair, the candidate, acquisition example,
selected probes, oracle labels, request ID, and receipt hash are identical.

| Probe domain | Receipt | Strict gate | Ungated control | Held-out result |
|---|---|---|---|---|
| Narrow `{x=1}` | Accepted: identity and square agree at the only fresh probe | Adopts the false identity candidate in 3/3 runs | Adopts in 3/3 runs | Both arms score 0/4 on `x={2,3,4,5}` |
| Distinguishing `{x=1,2,3,4}` | Rejected: fresh probes expose residuals | Refuses adoption in 3/3 runs | Adopts the same false candidate in 3/3 runs | Ungated arms score 0/4; gated arms abstain |

The narrow-domain false acceptance is the key result: the receipt proves
agreement over the caller-declared finite probe set, not semantic adequacy
outside it. When the same candidate receives distinguishing probes, the gate
prevents the incorrect codebook growth that occurs in the ungated control.
This demonstrates a useful conditional guard and its coverage limit in the
actual `teach()` path.

Median full-seed boot was 12.16 s. Teach-call medians were 10.8 ms for strict
gating and 18.9 ms for ungated adoption in this small panel; the arms differ in
outcome and should not be interpreted as a speed comparison. The probe domain,
candidate, and oracle are deliberately authored adversarially. Three runs do
not estimate how often real caller-supplied domains omit discriminating cases,
or how a domain generator should choose them.

Artifacts:

- [Preregistration](SUBSTRATE_ADEQUACY_PROBE_COVERAGE_AB_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_probe_coverage_ab_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_probe_coverage_ab_v1_lock_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_probe_coverage_ab_v1.py)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_probe_coverage_ab_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_probe_coverage_ab_v1_analysis_20261002.json)
