# Shared-substrate multi-sheet visual-task pilot v1.3 — results

## Capture validity

The source-locked run completed global and Retina-root-scoped conditions on one shared 5,969-node, 16,313-edge, 170-rule substrate. Both roots own 16 disjoint SUnits, parameter singleton counts are one, retinal development completed 3,000 steps on both roots, ON/OFF channels were active, the batch input writer matched scalar writes within the preregistered float tolerance, all 6,880 presentation records ended in `fixed_point` or `repeated_graph_state` within the 1.6M cumulative bound, blank replay was exact, and K=16 weights did not drift during readout.

The driver's `pass` bit is false because its topology gate required every seed manifest to have a positive number of rules to tag. `vision_compose` has zero rules with a `match` field and therefore zero executable rules; its zero tag count is correct. The independently source-checked audit verifies that every executable rule in the five manifests was tagged and all other fixture gates passed. The original raw capture is preserved without editing its driver bit.

## Task response

The A-sheet K=16 tuning matrix is exactly unchanged between B-blank and B-grating in both conditions:

| Scope | Max absolute change in A's 16×12 tuning matrix | Mean OSI, all three contexts |
|---|---:|---:|
| Global | 0 | 0.2495275 |
| Retina-root-scoped | 0 | 0.2495275 |

The B grating changed all 128 retinal cell inputs; both B ON/OFF channels were active after preparation. Thus the registered global-scope interference prediction was not observed on this fixture. This is a negative result for the predicted contrast, not evidence that global scope is generally safe. The experiment did not separately read out B's SUnit responses, so a follow-up should add that manipulation check before treating the null contrast as a strong task-level conclusion.

## Runtime and closure work

The matched 2,000-presentation adaptation took 1,580.1 seconds globally and 144.8 seconds root-scoped, a 10.9× difference in this single run. Three probes added 90.1 seconds globally and 83.4 seconds root-scoped. This includes interpreter/runtime overhead and is not a replicated wall-time claim; the difference is consistent with narrowing `st_settle`'s candidate set to each Retina root.

One global adaptation presentation (213) exceeded its first 200,000 progress budget. Resuming the same graph state required an additional 38,132 steps; it then returned `repeated_graph_state`. Its cumulative work was 238,132. No root-scoped presentation needed continuation; its maximum was 868 steps. Intermediate budget hits are retained distinctly from final terminal status in the work ledger. `repeated_graph_state` is not a fixed-point claim.

## Interpretation and next experiment

This single-seed fixture gives useful tractability evidence: root-scoped closure was much cheaper, while the task output did not change under the tested B intervention. Before extending seeds or graph sizes, add a B-side SUnit activity/readout check to establish that B's stimulus propagates through its own visual stack. Then determine whether the null A response follows from genuine independence of the sheets or from an unexercised coupling term. Preserve the current result as the negative task-contrast outcome rather than tuning the stimulus after observing it.

Artifacts: [v1.3 amendment](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_3_AMENDMENT_20260927.md), [runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3.py), [raw capture](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3_20260927.json), [independent audit](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3_audit_20260927.json), [analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3_analysis_20260927.json), and [source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_3_lock_20260927.json).
