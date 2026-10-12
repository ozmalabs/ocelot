# Live self-identity route probe v1 (2026-09-26)

## Result

Three fresh full-source-locked workers evaluated four nearby phrasings with `speech_act="instruction"`. All route signatures repeated and source fingerprints remained stable. The earlier v1.8 result correctly observed no self-report Goal for `describe who you are`, but its expected lifecycle target was not selected by the running system.

| Prompt | Selected comprehension | Live route | Event-bound Goals | Reply |
|---|---|---|---:|---|
| `describe who you are` | question, held table (`meta`) | no action route | 0 | `I am Jabberwock.` |
| `describe yourself` | instruction | `self_report` | 2 | `I am Jabberwock.` |
| `who are you` | question, direct meta (`self_identity`) | no action route | 0 | `I am Jabberwock.` |
| `tell me about yourself` | instruction | `self_report` | 2 | `I am Jabberwock.` |

For each action phrasing, one Goal has `self_target=self_identity` and a complete identity-bound selection→execution→action_result lifecycle. A second event-bound `report_self` Goal has no target or transitions. Source inspection identifies the competing producer: `seeds/conversation_self_reply.json::instruction_self_report_identity` mints a generic `report_self` Goal and reply for the reflexive instruction, while the live Python action faculty mints a second, targeted Goal and records its lifecycle. The graph-authored Goal is left unresolved when the action path owns the actual answer. This is a concrete duplicate-commitment/ownership gap, with an identified rule producer. The two question phrasings answer through question/meta routing and are not expected to emit an action lifecycle.

## Interpretation and limits

The apparent v1.8 dispatch failure is resolved as a measurement expectation mismatch: `describe who you are` is parsed as a grounded meta question rather than a self-report instruction. The self-identity capability is reached by other tested phrasings, through two distinct paths: question/meta readback and action/self-report. Same-sentence output across routes is not evidence that the routes share a producer or lifecycle.

This four-item, fixed-order probe estimates neither natural-language coverage nor answer quality. All four prompts were authored for diagnosis; all use one speaker and one live adapter per worker. It measures route selection and Goal structure only, not frame locality or tractability. The next implementation gate should establish a single Goal/reply owner for reflexive self-report, then confirm that the non-owning producer no longer leaves an unresolved duplicate and retain route-negative controls for external report objects.

## Artifacts

- Runner: [`substrate_live_self_identity_route_probe_v1.py`](../../../scripts/substrate_live_self_identity_route_probe_v1.py)
- Source lock: [full source closure](../../../evaluation/substrate_capability/live_self_identity_route_probe_v1_lock_20260926.json)
- Raw capture: [three workers](../../../evaluation/reports/substrate_live_self_identity_route_probe_v1_20260926.json)
- Prior v1.8 shortfall capture: [results and limits](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_8_RESULTS_20260926.md)
