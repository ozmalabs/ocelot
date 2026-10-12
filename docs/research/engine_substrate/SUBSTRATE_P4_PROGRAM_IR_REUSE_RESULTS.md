# P4 Program IR verification, retention, and reuse results

**Status:** the registered semantic/round-trip gates pass for one generated, known-success task. The route uses exemplar retrieval; this does not measure novel induction.

## Acquisition and execution

Three fresh `Substrate` instances in one process accepted the same `contrast_reverse_string_01` IR (identical SHA-256), and ProgEval matched all four revealed and three held-out rows before and after graph export/restore. Median boot/seed setup was 29.75 ms wall / 29.88 ms process CPU; the synthesis route was 16.00 ms wall / 54.04 ms process CPU. The route used `construction=retrieved_exemplar`; codebook, descent, exact, and enumeration rungs were not used. Together, boot plus route took 45.48 ms wall / 81.83 ms process CPU. Independent seven-row verification took 0.432 ms wall.

The reflected IR occupied 161 JSON bytes and added five graph nodes. Export took 7.59 µs median, restore 21.49 µs, and restored verification 0.349 ms. After a 100-call warm-up, ProgEval application cost medians were 48.95 µs/call (100 calls), 47.75 µs/call (1,000), and 49.82 µs/call (10,000). These timings include Python/native call overhead and describe this one short reverse-string Program IR.

## Retained-subgraph lifecycle finding

Removing the reflected root reduced the graph by only one node: four child Term nodes remained. Repeating add-root/remove-root cycles retained exactly four additional nodes per cycle in all three acquisitions: +4 after one cycle, +40 after ten, and +400 after one hundred. Compact serialization of the whole P4 graph grew by 316, 3,160, and 31,600 bytes at those points, from a 545,973-byte / 3,397-node baseline. This is direct graph-state growth for this concrete term representation.

Current RSS did not give a stable corresponding curve: after 100 cycles the observed deltas were 0, 0, and +304 KiB across the three runs, so this small experiment cannot attribute a reliable RSS cost. No unrelated graph node pointed to the temporary IR nodes in this probe. It did not test intentionally shared children or external references; a cleanup implementation must preserve such references.

The finding is relevant to existing helper patterns that add a term subgraph and then call `remove_node(root)`, including `domains/prog_synthesis.py::_eval_ir_on` and the temporary round-trip root in `eval_and_record`. Those call sites may accumulate unreferenced term children. The probe establishes the mechanism and graph-byte growth for one term, not application-level memory impact. A follow-up should exercise owned/unowned references, then add ownership-aware cleanup (or explicit caller cleanup) and rerun graph-state and semantic checks.

Protocol: [preregistration](SUBSTRATE_P4_PROGRAM_IR_REUSE_PREREG_20260925.md). Runner: [P4 IR reuse measurement](../../../scripts/substrate_p4_program_ir_reuse.py). Frozen inputs: [lock](../../../evaluation/substrate_capability/p4_program_ir_reuse_lock_20260925.json). Raw results: [JSON](../../../evaluation/reports/substrate_p4_program_ir_reuse_20260925.json).

## Scope

This is one known successful task from a generated contrast suite. It measures a P4 route whose accepted result came from exemplar retrieval, not held-out induction capability. It does not cover production durability, full-adapter checkpointing, external shared-subgraph references, or a diverse natural task mix. The direct-PBE F3 probe remains separate because it measures Term `evaluate`, not Program IR through ProgEval.
