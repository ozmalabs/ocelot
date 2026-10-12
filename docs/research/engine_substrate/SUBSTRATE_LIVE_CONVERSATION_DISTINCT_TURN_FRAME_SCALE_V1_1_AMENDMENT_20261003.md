# Live conversation distinct-turn frame scale v1.1 amendment

Date: 2026-10-03  
Status: post-capture semantic-replicate analysis; v1 raw capture and v1 analysis are preserved.

The preregistered exact graph digest parity gate fails for both sequence arms. Pairwise inspection of each arm's three workers finds graph node-array order and directed typed edge topology identical. The only varying fields are `runtime_s` and `ts` on generated `SystemModel` nodes. V1.1 therefore retains each raw digest and adds a semantic digest after mapping node IDs to array positions and excluding only those two fields on `SystemModel` records. All other node attrs and fields, graph array order, and edge endpoints/types are compared exactly. This is not general graph isomorphism, and it does not retroactively pass the failed raw digest gate.

Analyzer: [v1.1 independent analyzer](../../../evaluation/substrate_capability/analyze_live_conversation_distinct_turn_frame_scale_v1_1.py). Capture is unchanged: [raw JSONL capture](../../../evaluation/reports/live_conversation_distinct_turn_frame_scale_v1_20261003.jsonl.gz).
