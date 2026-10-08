# Live conversation capability panel v1 results (2026-09-27)

## Integrity

Ten unique full-seed workers (two for each of five tasks) pass source-lock stability, process uniqueness, and seed-boot integrity. The independent analyzer confirms all ten raw records join to the registered lock. The pooled task-contract gate fails because the live concern-authoring task does not reach the expected self-authoring route. Per-task analysis separates this one failure from the four passing contracts.

## Per-task results

| Task | Contract result | Median request wall (range) | Median peak RSS | Evidence |
|---|---:|---:|---:|---|
| Scene description | 2/2 pass | 10.354 s (10.249–10.459) | 1.784 GiB | Exact expected three-percept reply; one resolved `describe_scene` Goal with selection/execution/action-result. The public reply has no matching graph-linked outbound Message in either worker. |
| Held self-knowledge answer | 2/2 pass | 0.250 s (0.240–0.259) | 1.673 GiB | “How are you organised?” returns an organisation answer, not a question; matching outbound answer Message exists. |
| Self-report action | 2/2 pass | 0.279 s (0.261–0.298) | 1.674 GiB | `report your organisation` selects `self_report`, resolves one `report_self` Goal through all three lifecycle events, and has matching outbound content. |
| Unknown-word clarification | 2/2 pass | 0.205 s (0.202–0.208) | 1.674 GiB | `quorplezap the door` produces a graph-linked clarification asking about `quorplezap`, marked `expects_response`. |
| Concern authoring | 0/2 pass | 0.235 s (0.226–0.244) | 1.674 GiB | The live sentence is comprehended as an instruction, but native interpretation selects repair on `typed_unresolved_action_dependency`; the action bridge is not called, and the agent asks what “two” means. No concern is authored. |

Across all ten fresh processes, full-seed boot has median wall/CPU of 12.044/12.827 s (ranges 11.831–12.838/12.542–13.583). Every non-scene task adds six native rules during ordinary request closure. Scene description adds 24 total, with `_ensure_describe` accounting for 18. Request process CPU is recorded but includes process-wide concurrent activity; no per-thread CPU attribution was attempted in this sequential panel.

## Interpretation

Four of five selected task contracts pass in both replicates, but this is not a general capability rate. It shows sharply different live costs: four routes complete in roughly 0.2–0.3 s wall time on this fixture, while scene description includes an approximately 10 s first-use faculty build. The separate concern-authoring source test proves only the direct action bridge; it does not imply the natural-language live route reaches that bridge. The live conversation front door instead lets typed unresolved-action repair preempt the self-authoring route.

The scene task also reproduces the known output-channel mismatch: `WorldAdapter.converse` returns the correct description, but no graph-linked outbound Message contains it. Public text, graph provenance, and Goal success must therefore be separate capability dimensions. The 1.67–1.78 GiB peak RSS values are cold-process measurements for one full-seed configuration, not memory scaling estimates.

## Next evaluation

Prioritize the live concern route and scene reply alignment as separate repair/evaluation targets. Then repeat the same locked panel on current source, retaining the original prompts and contracts; add a second independently sourced concern and answer task before broadening any success claim. In parallel, continue structural and learner evaluations already catalogued in the capability map rather than inferring tractability from conversation routes.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_CONVERSATION_CAPABILITY_PANEL_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_live_conversation_capability_panel_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_live_conversation_capability_panel_v1.py)
- [Source lock](../../../evaluation/substrate_capability/live_conversation_capability_panel_v1_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/live_conversation_capability_panel_v1_20260927.json)
- [Analysis](../../../evaluation/reports/live_conversation_capability_panel_v1_analysis_20260927.json)
