# Describe-scene selective seed profile results (2026-09-27)

## Controlled profiles

Both probes use stable locks with identical source closure, native extension, and build manifest to the passing full-seed v2.4/timing runs. Profile v1 requests only the `conversation` root; the loader selects four of the 742 indexed seeds. Profile v2 freezes four explicit roots (`conversation`, `comprehend_instruction`, `communication_intent_arbitration`, `jabberwock_identity`) and selects their eight-seed dependency closure.

| Profile | Seeds selected | Current RSS after seed boot | Current RSS after two requests | Process peak RSS | Scene-description capability |
|---|---:|---:|---:|---:|---|
| Full seed reference | 742 indexed corpus entries | 1.342 GiB | 0.352 GiB | 2.508 GiB | Passes expected reply and request Goal lifecycle |
| Conversation only | 4 | 0.050 GiB | 0.080 GiB | 0.129 GiB | Fails: no substrate identity grounded; no resolved Goals |
| Conversation + instruction + identity | 8 | 0.048 GiB | 0.081 GiB | 0.129 GiB | Fails: replies only “I am Jabberwock”; no resolved Goals |

The reduced profiles use about 19.5× less peak RSS than the full-seed reference, but neither preserves the measured task capability. The loader declares selection complete and reports no failed manifests in either profile; missing behavior is therefore a capability loss from the frozen selection, not a loader integrity failure. Do not treat these profiles as viable lightweight deployments.

This shows that declared dependency closure for the selected roots is not sufficient to preserve the full-seed conversation behavior. The next experiment must identify the runtime rule/seed dependencies actually used by the successful full profile, then make a new frozen selection from that evidence and rerun held-out prompts to guard against one-stimulus overfitting.

## Evidence boundaries

The full profile's current RSS values are from one phase-sampled worker; its 2.508 GiB peak is a five-process median independently confirmed by GNU `time -v`. Each selective profile has one worker. All three use the same source/native hashes, but the reduced-profile memory values should be replicated before being treated as a distribution.

- [combined independent profile analysis](../../../evaluation/reports/describe_scene_selective_seed_profiles_v1_analysis_20260927.json)
- [conversation-only raw report](../../../evaluation/reports/describe_scene_selective_seed_profile_v1_20260927.json)
- [instruction/identity raw report](../../../evaluation/reports/describe_scene_selective_seed_profile_v2_20260927.json)
- [full-profile memory correction](SUBSTRATE_DESCRIBE_SCENE_BOOT_MEMORY_PROFILE_V1_RESULTS_20260927.md)
