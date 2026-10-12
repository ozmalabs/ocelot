# Live conversation capability panel v1.1 complete-runtime replication results

## Question and amendment

This is a replication of the fixed five-task/two-worker live conversation panel, with an explicit runtime-closure amendment. The original panel lock did not include Python helpers under `scripts/` or reference assets under `data/slabs/`; both are now hashed alongside the existing `domains/`, `substrate/`, native Python package, seed, native extension, and build-manifest closure. The isolated source tree is `/tmp/ocelot_live_capability_panel_v1_1_snapshot_20260927` from the full-runtime route-contrast snapshot. The new lock contains 3,359 Python script hashes and 36 slab-file hashes. The worktree itself was changing during capture, so this is a result for that isolated snapshot, not a claim about the current worktree.

## Integrity and outcomes

Ten unique fresh processes completed the preregistered schedule. Every worker reports the same pre/post runtime locks; parent lock stability, worker uniqueness, per-condition replication counts, and full-seed boot integrity pass. Full seed boot loads 731 manifests and reports 11 failures in every worker. Independent analysis passes all provenance/integrity gates. The task contracts pass in 8/10 workers, with outcomes separated by task as required:

| Task | Pass | Median request wall | Outcome |
|---|---:|---:|---|
| Scene description | 2/2 | 10.954 s | Exact expected description and resolved `describe_scene` Goal with selection, execution, and action-result events. Public reply has no matching graph-linked outbound Message in either replicate. |
| Held self-knowledge answer | 2/2 | 0.260 s | Returns an organisation answer rather than a question; outbound content matches. |
| Self-report action | 2/2 | 0.287 s | Selects `self_report`, resolves `report_self` through all lifecycle events, and returns the held organisation inventory. |
| Unknown-word clarification | 2/2 | 0.194 s | Asks what `quorplezap` means with graph-linked clarification evidence. |
| Concern authoring | 0/2 | 0.234 s | Returns `I don't know 'two' — what does it mean?`; neither worker reaches the concern-authoring action route. |

The failed concern route and scene output-channel mismatch are distinct failures: one is task completion/route selection, the other is provenance alignment between returned text and graph-visible communication. These results do not pool into a general success rate: the five tasks are selected repository-contract probes from one modality and only two workers each. Cold full-seed process boot and small replicate count also preclude a population or resource-scaling claim.

## Interpretation and next work

The corrected runtime closure does not change the qualitative v1 result on this snapshot: four selected conversation contracts pass and the concern-authoring route fails. It does repair the evidence boundary by ensuring the action helpers and slab data are present and hashed. Next, evaluate the two failures separately: (1) route the concern prompt to authoring only when its required concepts are actually resolved, without masking genuine unknown-word clarification; (2) align scene-description public replies with graph-linked outbound messages. Then broaden capability measurement across independent modalities and task families (inference/CAN, vision, memory, and held-out program synthesis), each with its own task oracle and resource envelope. Do not average these unlike families into a single score.

## Artifacts

- [v1.1 amendment](SUBSTRATE_LIVE_CONVERSATION_CAPABILITY_PANEL_V1_1_AMENDMENT_20260927.md)
- [Executed driver snapshot](../../../scripts/substrate_live_conversation_capability_panel_v1_1_snapshot_driver.py)
- [Complete runtime lock](../../../evaluation/substrate_capability/live_conversation_capability_panel_v1_1_lock_20260927.json)
- [Raw worker report](../../../evaluation/reports/live_conversation_capability_panel_v1_1_20260927.json)
- [Independent analysis](../../../evaluation/reports/live_conversation_capability_panel_v1_1_analysis_20260927.json)
