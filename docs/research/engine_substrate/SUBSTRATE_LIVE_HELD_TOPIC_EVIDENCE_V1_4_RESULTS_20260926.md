# Live held-topic local-hit/miss controls v1.4 (2026-09-26)

## Result

Three fresh full-source-locked workers passed all **35 gates**: the original five held-answer prompts, the unknown-topic negative, and a distinct injected local-hit control. In every worker, the `localhitium` control made one `ground_topic` call, produced a supported HeldAnswer and TopicGroundingEvidence, recorded the answer-topic Goal as `outcome=resolved`, released the exact answer with a matching production receipt, and marked both the same-topic GroundRequest and SearchRequest `superseded`. The unknown `unobtainium` control retained the v1.3 behavior: two calls, both requests ultimately `failed`, Goal outcome `unresolved`, and no known-answer leakage.

## Interpretation

This confirms the intended distinction between the two calls. On a local hit, the inline `_answer_topic_reply` grounding attempt returns usable held evidence, and its existing outcome bookkeeping supersedes both pending requests before dispatch can repeat the local lookup. On a miss, the first inline attempt does not settle the graph request; `_dispatch_pending_io` then fulfills the same GroundRequest through `scan_and_sync_ground`, causing the second local attempt before both graph requests fail.

The local hit is deliberately injected at `topic_grounding._ground_local`; `ground_topic`, its normal `resolve_and_ground` path, `learn_from_teacher`, graph outcome handling, request supersession, comprehension, and production release remain live. It verifies integration and lifecycle semantics, not the installed Wikipedia snapshot's real lookup success rate. The measured full-turn times and native work counts are not compared as a speedup: the turns run after different graph histories and the hit adds learned evidence. No runtime change was made.

This provides a safe next optimization target: when there is a pending same-topic GroundRequest, the inline path may still attempt local grounding once because it can answer immediately; after a miss, the dispatch layer need not repeat that same local probe if it can consume an explicit miss result while preserving the graph-authored request transition and remote SearchRequest path. Before changing code, test the actual `scan_and_sync_ground` local-miss boundary with request-state parity and compare an uncached miss against a same-turn local-result cache. Preserve the current behavior whenever no completed local miss is available.

## Artifacts

- [V1.4 amendment](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_4_AMENDMENT_20260926.md)
- [Runner](../../../scripts/substrate_live_held_topic_evidence_v1_4.py)
- [Full source lock](../../../evaluation/substrate_capability/live_held_topic_evidence_v1_4_lock_20260926.json)
- [Raw workers](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_4_workers_raw_20260926.json)
- [Analysis and gates](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_4_20260926.json)
- [V1.3 call-path diagnostic](SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_2_RESULTS_20260926.md)
