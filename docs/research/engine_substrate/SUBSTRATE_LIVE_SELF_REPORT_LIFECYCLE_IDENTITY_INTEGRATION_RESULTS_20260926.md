# Live self-report lifecycle identity integration results

## Current full-seed work attribution v1.7

V1.7 repeats the two-turn live self-report route and five semantic controls under a full source-closure lock covering all loaded seed JSON manifests and relevant Python source trees. Three fresh workers pass all lifecycle, reply, source-stability, and control gates; a separate analyzer passes ten checks including per-rule/global counter conservation and exact helper-work replication. The six `_record_live_goal_event` calls per worker use 49,888 candidate pairs and 528,489 Term evaluations total. Across two calls per event kind, selection uses 16,682 pairs/178,869 Terms, execution 16,606/174,824, and result 16,600/174,796. Median helper-call times are 13.56, 12.84, and 13.46 ms respectively. These counters cover the full active rule set and event setup plus native closure; they are not just lifecycle-rule costs.

This remains two sequential requests in one held organization-report task family. A same-source comparison with the threaded `describe_scene` capture gives 6.77× candidate pairs and 3.19× Terms for that particular scene schedule, but route content, graph history, and schedule differ, so the ratios are descriptive. See the [v1.7 amendment](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_7_AMENDMENT_20260926.md), [full source lock](../../../evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_7_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_20260926.json), and [independent work analysis](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_analysis_20260926.json).

## Prior confirmatory v1.6

After the discourse seed added the native single-owner guard, three fresh source-stable full-seed processes reran the self-report route. All turns preserve Goal-bound selection/execution/result identity and terminal closure. Correct-link, omitted-link, swapped-link, duplicate-result, and faculty-failure controls all pass. The independent analyzer verifies current source/seed locks and worker/post-run stability. Median boot was 11.82 s and median turn time was 1.98 s.

V1.5 remains valid for its own prior seed state; v1.6 is current confirmation after the shared lifecycle-rule change.

## Prior confirmatory v1.5

Three fresh, source-stable full-seed processes each ran two identical `report your organisation` instructions to the same recipient. Every turn selected the production `self_report` route, returned an organisation-grounded response, and produced one `report_self` Goal linked to its own inbound Message and origin event. Each Goal emitted exactly one identity-linked `selection`, `execution`, and `action_result` event in order. Native rules recorded the same transitions, resolved and closed the Goals, and left them absent from `has_active_goal`. All five semantic controls passed: correct link, omitted link, swapped link, duplicate result idempotence, and faculty failure closure. The independent analyzer confirms current lock equality, source stability at worker start/end and post-run, three distinct PIDs, event identity, and all control gates.

Median full-seed boot was 11.93 s and median per-turn time was 1.99 s. These timings are descriptive, not scaling evidence.

V1.4 passed the same gates against its then-current source state. The later describe-scene integration changed shared action and rule-authoring sources, so v1.4 is retained as historical evidence; v1.5 is current confirmation.

## Prior confirmatory v1.4

Three fresh, source-stable full-seed processes each ran two identical `report your organisation` instructions to the same recipient. Every turn selected the production `self_report` route, returned a response with organisation evidence, and produced one `report_self` Goal linked to its own inbound Message and origin event. For each Goal the live producer emitted exactly one identity-linked `selection`, `execution`, and `action_result` event in that order. The native rules recorded the same ordered `transitioned_by` events, resolved the Goal, added it to `has_closed_goal`, and left it absent from `has_active_goal`. Each event had exactly its owning Goal in `for_goal`; Goal, origin Message, and origin event identities were distinct across turns.

All five preregistered controls passed:

- Correct link: only the linked Goal selected.
- Missing link: neither Goal selected.
- Swapped link: the explicit edge, not the declared payload target or event time, determined which Goal selected.
- Duplicate result: two result events produced one terminal transition sequence and one closed Goal.
- Faculty failure: selection and execution were followed by `action_failure`, and the Goal became blocked and closed with no action-result event.

The independent analyzer reconstructed every gate from the raw capture and matched the lock against the current source, native build, worker-start, worker-end, and post-run fingerprints. Median full-seed boot time was 12.30 s and median per-turn time was 2.11 s; timings are descriptive, not scaling evidence.

V1.3 passed the same gates against its locked source state, but `world_adapter.py` changed after that capture completed. Its capture remains valid for the earlier hash and is preserved. V1.4 and v1.5 are preserved against their source snapshots; v1.6 is current confirmation after the native owner-uniqueness guard.

## Failed attempts retained

The earlier attempts are retained and excluded from confirmation:

1. **v1:** event identity controls and transitions worked, but native terminal rules left Goals in `has_active_goal` while also placing them in `has_closed_goal`; positive lifecycle gates failed.
2. **v1.1:** attempted the Python API spelling `remove_edge` in seed rule effects. The seed loader rejected that effect and skipped the terminal rules. The failure was disclosed before correction.
3. **v1.2:** used the engine-supported `del_edge` effect and the direct fixture controls passed, but the live adapter's `_bind_live_goals_and_deliberation` subsequently re-added terminal Goals to `has_active_goal`. The live projection exposed this reactivation.

V1.3 fixed both terminal-state paths: the native rules use `del_edge`, and adapter rebinding now preserves terminal membership by removing active membership and ensuring closed membership. V1.4 reconfirms those semantics against the later workspace source state.

## Claim boundary and next gate

This establishes production event ownership for the held self-report branch of `conversation_action.act_on_instruction`, and shows native Goal identity matching, omission rejection, mislink handling, duplicate-result idempotence, and faculty-failure closure on the tested graph vocabulary. It does not establish lifecycle event production for other scene actions, planning, external I/O, or other instruction routes; it does not certify external-effect authorization or receipt durability; and it does not demonstrate concurrent execution because the two live requests are sequential. Two sequential action routes are now confirmed. Native interleaving and owner uniqueness are separately confirmed on a fixture; test actual overlapping live requests before generalizing the owner contract.

## Artifacts

- Protocol: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_PREREG_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_PREREG_20260926.md)
- V1.1 amendment: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_1_AMENDMENT_20260926.md)
- V1.2 amendment: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_2_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_2_AMENDMENT_20260926.md)
- V1.3 amendment: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_3_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_3_AMENDMENT_20260926.md)
- V1.4 source-current amendment: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_4_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_V1_4_AMENDMENT_20260926.md)
- V1.6 amendment after native owner-uniqueness guard: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_6_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_6_AMENDMENT_20260926.md)
- V1.5 source-current amendment after describe-scene integration: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_5_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_5_AMENDMENT_20260926.md)
- Current v1.6 runner: [`substrate_live_self_report_lifecycle_identity_integration_v1_6.py`](../../../scripts/substrate_live_self_report_lifecycle_identity_integration_v1_6.py)
- Current independent analyzer: [`analyze_substrate_live_self_report_lifecycle_identity_integration_v1_6.py`](../../../scripts/analyze_substrate_live_self_report_lifecycle_identity_integration_v1_6.py)
- Prior v1.5 runner: [`substrate_live_self_report_lifecycle_identity_integration_v1_5.py`](../../../scripts/substrate_live_self_report_lifecycle_identity_integration_v1_5.py)
- Prior independent analyzer: [`analyze_substrate_live_self_report_lifecycle_identity_integration_v1_5.py`](../../../scripts/analyze_substrate_live_self_report_lifecycle_identity_integration_v1_5.py)
- Original runner and analyzer remain linked by the preserved v1.4 capture's lock.
- V1.6 current confirmatory lock: [`live_self_report_lifecycle_identity_integration_v1_6_lock_20260926.json`](../../../evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_6_lock_20260926.json)
- V1.6 current raw capture: [`substrate_live_self_report_lifecycle_identity_integration_v1_6_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_6_20260926.json)
- V1.6 current analysis: [`substrate_live_self_report_lifecycle_identity_integration_v1_6_analysis_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_6_analysis_20260926.json)
- V1.5 prior confirmatory lock: [`live_self_report_lifecycle_identity_integration_v1_5_lock_20260926.json`](../../../evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_5_lock_20260926.json)
- V1.5 prior raw capture: [`substrate_live_self_report_lifecycle_identity_integration_v1_5_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_5_20260926.json)
- V1.5 prior analysis: [`substrate_live_self_report_lifecycle_identity_integration_v1_5_analysis_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_5_analysis_20260926.json)
- Preserved v1.3 source-state capture: [`lock`](../../../evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_3_lock_20260926.json), [`raw`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_3_20260926.json), [`analysis`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_3_analysis_20260926.json)
- Preserved failed captures: v1 [`raw`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_20260926.json), v1.1 [`raw`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_1_20260926.json), v1.2 [`raw`](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_2_20260926.json)
