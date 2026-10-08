# Live conversation distinct-turn frame scaling v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_LIVE_CONVERSATION_DISTINCT_TURN_FRAME_SCALE_V1_PREREG_20261003.md)  
Digest amendment: [v1.1](SUBSTRATE_LIVE_CONVERSATION_DISTINCT_TURN_FRAME_SCALE_V1_1_AMENDMENT_20261003.md)

## Integrity and outcomes

Six fresh source-locked workers completed, three for each exact three-turn sequence. All source checks and worker records pass. The preregistered raw graph digest parity gate fails in both arms. Inspection finds identical graph array order and typed directed topology across the three replicates in each arm; only generated `SystemModel.attrs.runtime_s` and `ts` vary. The separately amended v1.1 semantic digest gate excludes only these fields and passes. No worker was removed based on route outcome.

| Arm | Median nodes / edges | Owned task Goals | Unowned Goals | Incident boundary nodes | Direct cross-frame edges | Interaction edges | Treewidth | Peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Independent prompts | 25,134 / 11,690 | 1 | 3 | 52 | 4 | 3 | 2 | 1,721.0 MiB |
| Context-dependent follow-ups | 25,166 / 11,780 | 3 | 3 | 72 | 3 | 3 | 2 | 1,721.0 MiB |

The independent sequence is `How are you organised?` → `quorplezap the door` → `report your organisation`. All three inbound Messages are distinct roots, but only the final self-report Goal is linked to its own prompt; the first two `communicate` Goals are not owned by their Messages under the strict identity rule. The held-knowledge answer and clarification replies occur, while the last prompt takes the `self_report` route.

The follow-up sequence is `report your organisation` → `Can you explain that in simpler terms?` → `What part of your organisation is most important?`. All three prompts have explicit request-linked Goals. The first resolves as `report_self`; the follow-up Goals are `answer_topic` and remain active. The first follow-up asks what information it should use; the second says the system does not hold the “most important” fact. Thus explicit frame identity does not imply task completion or grounded follow-up capability.

Both sequences yield a complete three-frame interaction graph (all three frame pairs are connected; treewidth 2). Boundary-mediated interactions add broad coupling in both arms. The independent arm's incomplete task ownership weakens the interpretation of its three roots as three fully represented task frames. With only three frames, treewidth has little scaling resolution. Peak RSS is the full-seed process footprint, not per-frame memory. This is a small authored diagnostic, not a natural conversation sample.

## Next gate

The follow-up sequence exposes two distinct issues: prompt-to-Goal ownership varies by route, and follow-up Goals can persist without resolving. Next, measure whether a follow-up can use the specific prior reply: preregister contrastive context controls (same follow-up after different prior answers, plus the same follow-up as a fresh first turn), retain current identity rules, and score answer grounding against the earlier turn. Expand to more independently authored sequences only after route-level ownership labels are reviewed. Do not infer locality from the three-frame width result.

Artifacts: [capture](../../../evaluation/reports/live_conversation_distinct_turn_frame_scale_v1_20261003.jsonl.gz), [original v1 analysis with raw digest failures](../../../evaluation/reports/live_conversation_distinct_turn_frame_scale_v1_analysis_20261003.json), [amended v1.1 analysis](../../../evaluation/reports/live_conversation_distinct_turn_frame_scale_v1_1_analysis_20261003.json), [runner](../../../evaluation/substrate_capability/live_conversation_distinct_turn_frame_scale_v1.py), [amended analyzer](../../../evaluation/substrate_capability/analyze_live_conversation_distinct_turn_frame_scale_v1_1.py), and [source lock](../../../evaluation/substrate_capability/live_conversation_distinct_turn_frame_scale_v1_lock_20261003.json).
