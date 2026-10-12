# Held-topic runtime interface trace v1 (2026-10-01)

## Capture and integrity

Three fresh full-profile workers replayed the seven frozen held-topic turns. All source fingerprints remained stable; each worker recorded seven turns; native runtime tracing dropped zero events; all observed rule UIDs mapped to event-time static read/write metadata; and the analyzer independently reconciled event scope, access-class/resource totals, node sets, and attribute-schema counts. The task-cut edge structures and dynamic traces repeat exactly across workers. The compressed capture is 3.36 MB.

This capture adds native read/write-like event traces and attribute schemas to the existing protocol-declared task projections. These are observational traces, not proof that unseen dependencies are absent. The cuts remain authored operational ownership. Attribute value hashes identify repeat changes without storing all boundary values: `Interlocutor.believed_concepts` changes across worker instances on all seven turns, while its schema is stable. This external boundary field is mutable shared context, not a fixed task-local dimension.

## Measurements

The whole runtime state contains 25,387 nodes and 12,262 typed edges. Per-turn operational frames contain 10–13 owned nodes, 40–51 direct boundary incidences, and 27–34 distinct external nodes. The deterministic min-fill widths in the original protocol concern only the induced owned-node graph and do not bound full rule dependencies.

| Turn | Owned nodes | Boundary incidences | External nodes | Dynamic native access events | Inside or direct-boundary access events | Outside-cut access events |
|---|---:|---:|---:|---:|---:|---:|
| Copper meta | 11 | 42 | 28 | 315,449 | 9,750 | 309,410 |
| Basalt meta | 11 | 43 | 29 | 117,844 | 6,935 | 111,849 |
| Hexagon meta | 11 | 43 | 29 | 125,101 | 7,293 | 118,993 |
| Copper table | 11 | 42 | 27 | 131,960 | 7,272 | 125,972 |
| Copper honest-capability | 12 | 51 | 34 | 129,249 | 8,618 | 122,482 |
| Unobtainium unknown | 10 | 40 | 29 | 149,648 | 8,871 | 142,697 |
| Localhitium injected source | 13 | 43 | 29 | 159,203 | 8,380 | 152,906 |

The scope categories can overlap when one event touches multiple node roles; node-free/global events are reported separately in raw data. The large outside-cut counts show that these small answer-lifecycle projections do not capture most observed native closure activity. They do not show those accesses are necessary to the answer, nor that the current closure can safely omit them.

The frozen task-quality oracle passes 18/21 worker-turns. All three current-source workers ask for clarification on “Can you tell me about copper?” instead of returning the known held answer; its route remains `honest_capability`. The other six turns per worker meet their frozen task checks. This is a reproduced quality failure, not a trace-integrity failure. Historical v1.6 reports a pass for that turn under a different source lock; this run is current-source evidence and does not attribute the change to a single edit.

## Interpretation and limits

This result supplies one concrete runtime interface profile with full typed cuts, external-node attribute schemas, static declarations for observed rules, and dynamic native access events. It confirms that the declared answer frame is much smaller than the active native operation footprint. Access tracing remains limited to native instrumented events inside `converse`; host operations, scheduler work outside those hooks, and unexecuted dependency branches are not proven complete. No partitioned execution was attempted, and the failed quality gate is retained. This does not estimate cheap-cut prevalence or establish natural-task tractability.

## Artifacts

- [Preregistration](SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_PREREG_20261001.md)
- [Analysis correction amendment](SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_ANALYSIS_AMENDMENT_20261001.md)
- [Runner](../../../scripts/substrate_held_topic_runtime_interface_trace_v1.py)
- [Corrected analyzer v1.1](../../../scripts/analyze_substrate_held_topic_runtime_interface_trace_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/held_topic_runtime_interface_trace_v1_20261001_lock.json)
- [Compressed capture](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_20261001/capture.json.gz)
- [Analysis v1.1](../../../evaluation/reports/held_topic_runtime_interface_trace_v1_20261001/analysis_v1_1.json)
