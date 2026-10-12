# Held-topic global versus per-area settlement parity v1: results

Date: 2026-10-05  
Status: historical v1 capture; its exact digest is ID-sensitive. The corrected v1.2 semantic comparison supersedes its inconclusive graph-parity result.

## Findings

The source-locked capture contains all nine workers (three per arm), seven turns per worker, and stable source fingerprints. Each barrier/live-area settlement call reached zero residual without hitting its round cap. Their per-area work reports repeat across workers. The global arm also completed its normal closure calls.

Conversation replies agree across all three arms at all seven turn positions. Node and edge counts agree at every position: from 25,068 nodes / 11,507 edges after turn one to 25,388 / 12,262 after turn seven. These are useful invariants, but they do not prove graph equality.

The protocol called its graph digest canonical, but the implementation sorts graph records while retaining numeric node IDs and edge endpoints. The global digest is repeatable on the first turn but changes on later turns across workers; the barrier and async digests also differ from global on turn one despite matching counts and replies. This is consistent with ID allocation/order differences, but the capture lacks graph records needed to test that explanation. The analyzer correctly fails its declared exact digest gate; that failure is not evidence of semantic graph divergence.

## Interpretation

At the time, this run established settlement, reply, and cardinality agreement but could not establish graph parity. The later v1.2 run resolves that measurement issue with a reference-aware semantic fingerprint and reports per-turn parity. The held-topic utility limitation remains: the copper clarification prompt still asks for more information.

## Next gate

Run a versioned follow-up that captures enough post-turn graph structure to compare states independently of node IDs. Preserve v1 and its failed exact-digest result. The follow-up must define and validate an ID-independent equivalence check, retain multiplicities and typed directed edges, test it against deliberately changed node attributes and edges, and only then compare global, barrier, and async arms. If the comparison detects differences, report the smallest differing typed records and investigate scheduling order effects. If it passes, proceed to a separate response-priority/residual-continuation experiment; full-settlement parity alone does not validate deferral.

Artifacts: [protocol](SUBSTRATE_HELD_TOPIC_AREA_SETTLEMENT_PARITY_V1_PREREG_20261005.md), [capture](../../../evaluation/reports/held_topic_area_settlement_parity_v1_20261005/capture.json.gz), [analysis](../../../evaluation/reports/held_topic_area_settlement_parity_v1_analysis_20261005.json).
