# Held-topic area-settlement semantic parity v1.2: results

Date: 2026-10-06  
Status: all preregistered checks passed; bounded semantic-structure parity established under the v1.2 WL invariant.

## Result

The source-locked panel completed nine fresh workers (three global, three barrier-area, three async-area), each running the same seven-turn held-topic workload with `PYTHONHASHSEED=0`. Capture integrity and fixture checks passed. At every turn, normalized fingerprints, replies, and node/edge counts matched across workers and arms. Final normalized graph fingerprints also matched across all arms.

The per-area arms used explicit assignments for the traced lexicon, curiosity, residual, and ShapeDecode rules. All 48 recorded settlement calls reached zero residual without hitting their round cap. The scheduler work reports repeated across workers. Final graph size grew from 25,068 nodes / 11,507 edges after turn one to 25,388 / 12,262 after turn seven.

The corrected fingerprint normalizes serialized NodeID references as labeled reference relationships and excludes `SystemModel.ts` and `SystemModel.runtime_s`, which vary as wall-clock and execution-time metadata. Its fixtures pass ID-renumbering and timing-metadata invariance, plus mutations of node attributes, edge direction/type/attributes, and edge multiplicity. The previous raw digest failures are therefore measurement artifacts. The WL invariant is not a complete graph-isomorphism decision procedure, so this result is stated at that equivalence level.

## Capability and limits

This establishes that the existing opt-in area scheduler can reach the same measured graph structure and conversation outputs as global closure on one authored held-topic workload, with all rules retained. It does not show faster response release: the v1.2 arms settle without a finite priority budget, and `WorldAdapter.comprehend()` still uses global `run_rules()`. It does not establish natural-task prevalence or tractability of learning new structure. Task utility remains bounded by the known clarification failure on “Can you tell me about copper?”.

## Next gate

Prototype a response-priority scheduler interface that can settle designated request-critical rules while carrying ambient residual work. Preserve graph read/write wakeups and the same full rule set. Compare against global closure at a common quiescent checkpoint, using the v1.2 semantic fingerprint and reply/task-outcome parity; separately measure response-critical work, residual size, continuation cost, and mutation wakeup completeness. Include cold and warm sessions and the existing positive/negative locality controls. A parity pass at full settlement does not predetermine this finite-budget result.

Artifacts: [protocol](SUBSTRATE_HELD_TOPIC_AREA_SETTLEMENT_PARITY_V1_2_PREREG_20261006.md), [runner](../../../scripts/substrate_held_topic_area_settlement_parity_v1_2.py), [analyzer](../../../scripts/analyze_held_topic_area_settlement_parity_v1_2.py), [fingerprint implementation](../../../scripts/substrate_graph_semantic_fingerprint.py), [capture](../../../evaluation/reports/held_topic_area_settlement_parity_v1_2_20261006/capture.json.gz), [analysis](../../../evaluation/reports/held_topic_area_settlement_parity_v1_2_analysis_20261006.json).
