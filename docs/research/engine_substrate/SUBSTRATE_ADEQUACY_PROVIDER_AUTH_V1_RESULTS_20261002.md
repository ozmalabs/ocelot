# Signed provider evidence at code-write adoption v1 — results

All six independent analysis gates pass across 12 fresh full-seed processes (three per case), with unchanged source/native/seed fingerprints. The HMAC envelope binds provider ID, request ID, probe ID, input hash, label ID, expected value, and claimed oracle hash. The verifier checks those fields and the receipt's evidence digest before the existing receipt-required `teach()` path.

| Case | Authenticator | Receipt | Adoption | Held-out result |
|---|---|---|---|---|
| Honest square label against identity | valid | rejected with residual, 3/3 | refused, 3/3 | no candidate emitted |
| Unsigned forged label `2` against identity | refused, 3/3 | core receipt alone would accept, 3/3 | blocked before `teach()`, epoch +0 | no candidate emitted |
| Trusted key signs incorrect label `2` against identity | valid | accepted, 3/3 | adopted, 3/3 | 0/4 exact, 3/3 |
| Correct square candidate and label `4` | valid | accepted, 3/3 | adopted, 3/3 | 4/4 exact, 3/3 |

The 36/36 tamper, cross-request replay, and unregistered-provider controls fail authentication. This demonstrates an effective opt-in boundary against callers who can submit labels but do not hold a trusted provider key. It does not establish label correctness: a configured provider that signs a false value remains authoritative to the system and can cause false adoption. Authentication and semantic adequacy must remain separate gates.

The mechanism uses standard-library HMAC-SHA256 and a verifier-side shared-key mapping. The test key is fixture material, not a deployment secret. The registry is passed explicitly to the wrapper and must be provisioned outside the evidence caller's control. Production deployment still needs a real registry owner, protected key storage, rotation and revocation, provider onboarding, and a key-isolation design. The legacy receipt-only `teach()` entrypoint remains callable; only the new authenticated wrapper enforces signatures. Median full-seed boot is 11.84 s, and the panel makes no selector-performance claim.

Artifacts: [protocol](SUBSTRATE_ADEQUACY_PROVIDER_AUTH_V1_PREREG_20261002.md), [authentication wrapper](../../../domains/adequacy_provider_auth.py), [runner](../../../evaluation/substrate_capability/substrate_adequacy_provider_auth_v1.py), [lock](../../../evaluation/substrate_capability/substrate_adequacy_provider_auth_v1_lock_20261002.json), [independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_provider_auth_v1.py), [raw capture](../../../evaluation/reports/substrate_adequacy_provider_auth_v1_raw_20261002.json), and [analysis](../../../evaluation/reports/substrate_adequacy_provider_auth_v1_analysis_20261002.json).
