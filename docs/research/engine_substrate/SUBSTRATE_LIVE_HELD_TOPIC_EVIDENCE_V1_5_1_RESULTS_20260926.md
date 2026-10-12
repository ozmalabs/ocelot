# Live held-topic same-turn local-miss reuse v1.5.1 (2026-09-26)

## Result

Three fresh source-stable workers passed all **36 gates**. The five positive held-answer prompts and injected local-hit control retain exact answers, evidence and receipt requirements, and the local-hit request supersession checks. On the unknown miss, the inline `ground_topic` call occurs once. It marks the exact GroundRequest with `local_grounding_outcome=miss` and the current inbound id; dispatch consumes that marker, sets the request failed with the existing `no answer` status/error semantics, and does not call `ground_topic` again. The parallel SearchRequest still runs its separate path and fails without a verified candidate. The Goal remains `outcome=unresolved`, and the honest reply remains unchanged with no known-answer leakage.

## Work and comparison limits

The unknown turn's native work counters exactly match v1.4: 67,669 candidate enumerations and 630,849 Term evaluations. This indicates the change removed one grounding invocation without changing the measured native closure work for this fixture. The v1.4 and v1.5.1 runs do not share an identical complete Python source closure because `domains/self_model.py` changed between captures; their wall times are therefore not a causal comparison. V1.4's three unknown calls measured about 171 ms median and v1.5.1's about 163 ms, but the difference cannot be attributed to this edit.

The first v1.5 capture is preserved but excluded: all semantic, reduced-call, and request-marker checks passed, while `domains/self_model.py` changed during worker 2. V1.5.1 changes neither the runner criteria nor the substrate implementation relative to v1.5; it relocks the later stable source state and repeats all controls. The real local Wikipedia corpus is not used by the injected hit, so corpus hit rates and external retrieval quality remain unmeasured.

## Code path and artifacts

`WorldAdapter._answer_topic_reply` records the local-only miss and inbound turn id on the matching requested GroundRequest only after the phrase grounder completed and returned no result. `fetch_dispatch.scan_and_sync_ground` consumes that mark only for `allow_web=False` and an exact active inbound id. It still transitions the request through running to failed and leaves SearchRequest dispatch independent.

- [V1.5.1 amendment](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_5_1_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_live_held_topic_evidence_v1_5_1.py)
- [Source lock](../../../evaluation/substrate_capability/live_held_topic_evidence_v1_5_1_lock_20260926.json)
- [Raw workers](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_5_1_workers_raw_20260926.json)
- [Analysis and gates](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_5_1_20260926.json)
- [Preserved v1.5 drift analysis](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_5_20260926.json)
