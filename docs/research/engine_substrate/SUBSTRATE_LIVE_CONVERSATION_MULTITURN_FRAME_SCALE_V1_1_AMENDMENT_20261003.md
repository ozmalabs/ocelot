# Live conversation multi-turn frame scaling v1.1 amendment

Date: 2026-10-03  
Status: post-capture analyzer amendment; the v1 capture and v1 analysis are preserved.

## Reason

The locked v1 analysis correctly failed its raw exact-digest replicate gate at N=2, 4, and 8. Inspection of the three fresh workers at each size found identical graph node-array order and edge topology, with all stable node fields equal. The only observed node-field differences were generated `SystemModel.attrs.runtime_s` and `SystemModel.attrs.ts` values, which encode execution time. Raw graph digests remain distinct and are retained unchanged.

## Amended comparison

The v1.1 independent analyzer compares a second, semantic graph digest. It maps node IDs to their graph-array positions, compares the complete ordered node records, and compares every directed, typed edge after endpoint remapping. The only excluded fields are `runtime_s` and `ts` on nodes whose type is exactly `SystemModel`. This exclusion is narrow and justified by the measured variation. It does not alter captures, ownership reconstruction, per-turn task gates, or the v1 raw digest check. The v1.1 gate requires all three semantic digests at each N to match.

This amendment does not retroactively make the raw-digest v1 gate pass. It tests whether graph structure and stable state replicate after removing the two observed generated timing fields. The comparison remains sensitive to graph array ordering and is not a general graph-isomorphism test.

## Artifact

Amended analyzer: [analyze_live_conversation_multiturn_frame_scale_v1_1.py](../../../evaluation/substrate_capability/analyze_live_conversation_multiturn_frame_scale_v1_1.py). The raw v1 capture is unchanged: [live conversation multi-turn frame-scale capture](../../../evaluation/reports/live_conversation_multiturn_frame_scale_v1_20261003.jsonl.gz).
