# Adequacy label-provider spoof at adoption v1 — results

All six independent analysis gates pass across six fresh full-seed workers. The honest and forged arms use the same identity candidate, request ID, distinguishing probe `x=2`, source ID, and declared oracle SHA-256. The analytic square oracle says 4; the forged label says 2, matching the candidate.

| Evidence arm | Receipt | Strict `teach()` | Codebook change | Held-out result |
|---|---|---|---|---|
| Honest square label (`4`) | rejected with residual, 3/3 | refused, 3/3 | epoch +0, 3/3 | no candidate emitted |
| Forged label (`2`) under the same provider ID/hash | accepted, 3/3 | adopted, 3/3 | epoch +1, 3/3 | 0/4 exact, 3/3 |

The accepted spoof receipt also passes `verify_accepted_receipt`: its digest and candidate binding are internally consistent. The failure is upstream of receipt integrity. `source_id`, `oracle_sha256`, `label_id`, and `expected` are caller-supplied fields; the adjudicator does not verify a provider signature or recompute the label from the named oracle. Copying the true oracle hash does not prove that the oracle produced the value. A strict adoption gate therefore blocks a bad candidate only when its input evidence is trustworthy.

This is a controlled caller-spoof attack, not evidence about accidental error rates or the compromise of a real provider. It identifies an implementation requirement before any security claim: a trusted key registry, signed request-bound labels, key lifecycle/revocation, and a clear trust boundary for who supplies the registry. The current study does not implement those features. Median full-seed boot was 11.83 s; no performance conclusion is drawn.

Artifacts: [protocol](SUBSTRATE_ADEQUACY_PROVIDER_SPOOF_V1_PREREG_20261002.md), [runner](../../../evaluation/substrate_capability/substrate_adequacy_provider_spoof_v1.py), [lock](../../../evaluation/substrate_capability/substrate_adequacy_provider_spoof_v1_lock_20261002.json), [independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_provider_spoof_v1.py), [raw capture](../../../evaluation/reports/substrate_adequacy_provider_spoof_v1_raw_20261002.json), and [analysis](../../../evaluation/reports/substrate_adequacy_provider_spoof_v1_analysis_20261002.json).
