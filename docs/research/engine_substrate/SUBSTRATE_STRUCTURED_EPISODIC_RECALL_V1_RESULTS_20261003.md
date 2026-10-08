# Structured episodic recall v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_STRUCTURED_EPISODIC_RECALL_V1_PREREG_20261003.md)  
Implementation source: [episodic memory seed](../../../seeds/episodic_working_memory_core.json)  
Fixture precedent: [existing migrated memory tests](../../../tests/test_episodic_working_memory_migrated.py)

## Result

Nine fresh isolated workers completed (three each for known value 14, known value 29, and unknown cue). Source, complete-record, unique PID, exact graph digest, and semantic gates all pass. Every behavioral gate passes: each known cue yields exactly one RecallCandidate linked to its Episode and reconstructing the correct observed event; the unknown cue yields no RecallCandidate and exactly one `insufficient_information` RecallOutcome.

| Condition | Passes | Median nodes / edges | Median bind tick | Median retrieval tick | Peak RSS |
|---|---:|---:|---:|---:|---:|
| Known value 14 | 3/3 | 18 / 27 | 0.523 ms | 0.234 ms | 147.9 MiB |
| Known value 29 | 3/3 | 18 / 27 | 0.509 ms | 0.207 ms | 148.5 MiB |
| Unknown cue | 3/3 | 17 / 22 | 0.536 ms | 0.180 ms | 148.4 MiB |

The positive RecallCandidates carry `provenance_kind=recalled`, `observation_status=not_observed`, confidence 0.85, and uncertainty 0.15. The unknown-cue result carries `provenance_kind=retrieval_failure`, `observation_status=not_observed`, and uncertainty 1.0. This is bounded uncertain retrieval, not a claim that reconstructed content is a new observation. Rule binding/retrieval occur via substrate graph ticks; Python only creates typed input nodes/edges and reads back result nodes.

Paired with the prior [live value-recall result](SUBSTRATE_LIVE_COUNTERBALANCED_VALUE_RECALL_V1_RESULTS_20261003.md), this gives a specific capability boundary: the structured episodic path binds and retrieves when explicit event, context, schema, and cue graph facts are supplied; the tested `WorldAdapter.converse` route did not translate plain statements into a usable memory event or generate an answer. The reproducible [cross-capture audit](../../../evaluation/reports/live_structured_memory_boundary_v1_audit_20261003.json) confirms zero `EpisodicEvent`, `MemoryContext`, `MemorySchema`, `MemoryRetrievalRequest`, `RecallCandidate`, or `RecallOutcome` nodes in all nine prior live workers. The 1–2 `Episode` nodes present are not `episodic_working_memory_v1` Episodes. The same audit shows asymmetric parsing: the `14` assertion has an object value, but the `29` assertion does not; both lack relation support and remain unresolved. The identical question parses as `table:know`, yet no retrieval request is created. Thus this route never invoked the structured retrieval path. The two measurements use different seed footprints and task interfaces, so their memory and timing figures are not directly comparable. This does not imply that all conversational memory paths fail or that this structured fixture represents natural language.

## Next gate

The structured API has now passed while the live route shows no structured memory nodes. Next specify the smallest explicit language-to-event bridge contract: map a supported, unambiguous assertion to an observed event, context, and schema; create a cue request from a follow-up; preserve source, uncertainty, and `not_observed` recall provenance; then render an answer only from the recall candidate. First measure bridge activation and exact value grounding on counterbalanced values with ambiguous/no-fact controls. Do not infer a bridge from legacy message episodes.

Artifacts: [raw capture](../../../evaluation/reports/structured_episodic_recall_v1_20261003.jsonl.gz), [analysis](../../../evaluation/reports/structured_episodic_recall_v1_analysis_20261003.json), [runner](../../../evaluation/substrate_capability/structured_episodic_recall_v1.py), [analyzer](../../../evaluation/substrate_capability/analyze_structured_episodic_recall_v1.py), and [source lock](../../../evaluation/substrate_capability/structured_episodic_recall_v1_lock_20261003.json).
