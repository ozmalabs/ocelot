# Live held-topic complete boundary audit v1.6 (2026-09-26)

## Result

Three fresh full-source-locked workers passed the semantic, request-lifecycle, route-repeat, and full-boundary-structure gates. The structural signatures repeat across workers for all six turns. After each conversation's timed/native-work window, the runner serializes the complete graph and computes every typed edge incident to a declared operational task-owned set: inbound message, same-event goals, held answers, supporting evidence, same-topic SearchRequest/GroundRequest nodes, production receipts, and outbound replies. It counts induced edges, crossing incidences, unique external neighbors, and a deterministic min-fill elimination-width upper bound on the induced owned subgraph.

| Turn family | Owned nodes | Internal edges | All-type boundary incidences | Unique external nodes | Induced-width upper bound |
|---|---:|---:|---:|---:|---:|
| Copper meta | 11 | 11 | 41 | 27 | 2 |
| Basalt meta | 11 | 11 | 42 | 28 | 2 |
| Hexagon meta | 11 | 11 | 42 | 28 | 2 |
| Copper table | 11 | 11 | 41 | 26 | 2 |
| Copper honest-capability | 11 | 11 | 46 | 30 | 2 |
| Unobtainium unknown | 10 | 10 | 39 | 28 | 1 |
| Localhitium injected hit | 13 | 13 | 42 | 28 | 2 |

The seven rows list six task turns plus the added local-hit control (seven total). The positive held-answer turns have 4.1–4.6 times as many crossing incidences as the earlier v1.2 projection's 9–10 counted incidences, which used a fixed subset of edge types. This shows the earlier boundary number understated the complete direct cut. It does not show that the new 26–30 unique neighbors are independent dimensions: the external types include shared graph hubs such as Agent, Channel, Interlocutor, DiscourseState, and repeated Intent/Mention nodes. A useful decomposition must retain these shared structures rather than equate incidence count with separator width.

## Interpretation and limits

The selected task-owned projections are sparse (10–13 nodes, 10–13 internal edges) and have min-fill upper bounds 1–2. This width is only for the induced subgraph on manually declared answer-lifecycle nodes. It omits dependencies mediated through external boundary nodes and is neither exact treewidth of the full rule/factor dependency graph nor a learned frame boundary. The crossing-edge count is exact for this vertex set and complete serialized runtime graph; the task ownership choice is operational, not a claim that the system learned these frames.

The final whole graph in worker 0 grows from 24,962 nodes/11,471 edges after copper meta to 25,277 nodes/12,233 edges after the injected local-hit control. Full graph serialization runs after the query timer and is excluded from turn work and latency. The experiment measures one authored held-evidence family and its controls; it is not a natural-task distribution or CPU-scale estimate.

## Artifacts

- [V1.6 amendment](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_6_AMENDMENT_20260926.md)
- [Source-locked runner](../../../scripts/substrate_live_held_topic_evidence_v1_6.py)
- [Source lock](../../../evaluation/substrate_capability/live_held_topic_evidence_v1_6_lock_20260926.json)
- [Raw workers and incident edges](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_6_workers_raw_20260926.json)
- [Analysis and gates](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_6_20260926.json)
