# Held-topic trace semantic-parity replay v1.1 amendment

Date: 2026-09-28  
Applies to: [v1.1 preregistration](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_PREREG_20260928.md)

## Correction to the v1 status

The v1 full-trace capture and its analyzer passed capture-integrity checks, but those checks did not compare the traced worker to a contemporaneous uninstrumented worker. After v1 completed, the current worktree's `substrate/world_adapter.py` changed. A post-change baseline run with the same locked native wheel answers the three “What do you know about …?” held-answer prompts, the table question, the unknown-topic control, and the injected local-hit control; “Can you tell me about copper?” still asks for information needed to ground the answer. A development five-arm run on the post-change source produced identical semantic signatures for baseline, access tracing, per-rule counters, all-scope work tracing, and the combined trace wrapper in one process.

Accordingly, v1 remains valid only as a capture of its isolated snapshot. Its six query-oracle failures are not evidence about current-worktree capability. A later v1.1 paired replay also passed baseline/trace semantic parity on that snapshot, but reproduced the old failures in both arms. Comparing final graph counts showed the snapshot booted 52 fewer nodes and 119 fewer edges than the actual workspace; the runner's “complete source closure” did not include the root `data/` tree or other local runtime assets. The workspace's uninstrumented control with the same native wheel answers six of seven query cases, while the snapshot control answers only one. Thus v1/v1.1-snapshot trace reconciliation remains useful as instrumentation evidence for that snapshot, but its capability outcomes and its application to the current runtime are invalid.

The v1.1 preregistration now includes a full content hash of the 3.9 GB `data/` tree before and after execution. The paired run completed from the actual workspace with its local assets present, retained the fixed workload and oracle, and passed source/data stability checks. Current capability conclusions rely on that workspace capture, not v1 or the isolated v1.1 replay.

## Analyzer field-path correction

The actual-workspace capture completed with stable source and data hashes, but the preregistered analyzer raised `KeyError` while reading `base_fingerprint` from the old, un-nested lock shape. The paired raw already stores it under `locked_inputs.source_lock.base_fingerprint`. The original analyzer was preserved and its hash remains in the capture lock. A separate [v1.1.1 corrected analyzer](../../../scripts/analyze_substrate_held_topic_trace_semantic_parity_v1_1_1.py) changes that field lookup and output path only; it independently rechecks semantic signatures, trace accounting, frame schemas, oracle outcomes, and worker locks. Its analysis passes all 24 checks. This correction affects adjudication only; it does not alter captured inputs or worker execution.
