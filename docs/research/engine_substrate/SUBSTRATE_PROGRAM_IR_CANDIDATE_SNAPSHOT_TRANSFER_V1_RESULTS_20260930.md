# Program IR candidate-snapshot transfer v1 results

## Result

The source-locked panel completed all ten fresh workers (two clamp tasks × five repetitions), with no worker failures. The independent analyzer passes all 15 checks for the source lock, randomized schedule, unique processes, task reconstruction, exact oracle outputs, branch isolation, and eager/shared-page parity.

All ten synthesis branches accepted one task-specific Program with exactly one graph-resident IR root. The Program executed correctly on every held-out value outside the training range: 60/60 exact outputs, zero accepted false predictions. The eager-copy and shared-graph-page branches produced the same Program presence, IR-root count, outputs/traps, and complete canonical branch-state digest for every worker. The original empty base remained unchanged, and the learned candidate snapshot remained unchanged after both evaluation branches.

The frozen base contains no task-specific Program. The exposure control ingests the same request and six examples but does not run the synthesis pump; it also contains no task-specific Program. These controls report unavailable capability (zero coverage) rather than fabricated numeric predictions. Thus this result establishes acquisition-and-execution from a branch-local synthesized Program, with explicit no-acquisition controls; it does not establish an efficacy difference over another synthesizer or an independent learning algorithm.

## Cost

Across ten workers, median pump wall time is 95.3 ms, median eager candidate validation branch time is 81.6 ms, and median shared-graph-page validation branch time is 70.6 ms. Median process peak RSS is 60,196 KiB. Branch validation time includes branch creation, canonical digesting, and six `ProgEval` calls; it should not be compared directly to the pump-only value. The observed shared-page timing is descriptive: the panel did not preregister a performance superiority hypothesis, timing varies between workers, and this is one host and two fixed task functions.

## Interpretation and limits

This adds evidence from a separate object-level route and representation than GenMint: the standard Rung 3 synthesizer stores an executable Program/IR in the candidate graph, and graph-page branches can execute it with exact parity against eager copies. The result complements GenMint’s acquired `DimensionGenerator` transfer and demonstrates that the branch substrate can carry two distinct learned object types in measured workflows.

The functions are shallow clamps over two bound pairs and a fixed numeric grammar; the operator ontology and oracle are known. Five workers per function measure runtime repeatability, not generalization across functions. There is no out-of-inventory negative function, forgetting test, persistent checkpoint/restart test, natural-task sample, project-held custody, independent host, general CoW performance result, or P3-E1 evidence. No Program is adopted into the baseline.

## Artifacts and reproduction

- [Preregistration](SUBSTRATE_PROGRAM_IR_CANDIDATE_SNAPSHOT_V1_PREREG_20260930.md)
- [Runner](../../../scripts/program_ir_candidate_snapshot_transfer_v1.py)
- [Independent analyzer](../../../scripts/analyze_program_ir_candidate_snapshot_transfer_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/program_ir_candidate_snapshot_transfer_v1_20260930_lock.json)
- [Raw capture](../../../evaluation/reports/program_ir_candidate_snapshot_transfer_v1_20260930_raw.json)
- [Independent analysis](../../../evaluation/reports/program_ir_candidate_snapshot_transfer_v1_analysis_20260930.json)

From the repository root, reproduce with `python3 scripts/program_ir_candidate_snapshot_transfer_v1.py --lock` (compare with the saved lock), `python3 scripts/program_ir_candidate_snapshot_transfer_v1.py`, then `python3 scripts/analyze_program_ir_candidate_snapshot_transfer_v1.py`.
