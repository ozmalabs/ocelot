# Conversation scoped owner-wakeup probe results

**Run:** 2026-09-26. **Grade:** preregistered mechanism diagnostic on one authored ten-event conversation fixture; not a scheduler benchmark or natural-task locality estimate.

Four caller-assigned operation-phase Microtheory frames were used. Each arm incrementally constructed the same discourse and settled after each event. The full global-closure arm is the oracle. A second arm seeded the current event frame and followed native affected-Microtheory reports until its queue emptied. A control ignored those reports and ran global closure only after the last checkpoint.

## Result

The owner queue matched the full graph digest at all 10 checkpoints. Both remote goal-origin frames were notified during resolution: frame 1 to frame 0 across events 1–3, and frame 3 to frame 2 across events 6–8. The downstream receipt rule ran in those origin frames; owner-queue final goal provenance, receipts, and common-ground state matched full closure.

When owner wakeups were omitted, the first task became stale at event 3 and the second at event 8. Receipt divergence persisted in later checkpoints; three of ten checkpoints happened to remain equal. One final global closure restored the exact full-arm graph digest. All scoped calls completed without budget exits or deferred effects, and every reported owner mapped to a caller-declared frame.

## Cost and limits

This small correctness fixture does not show a speedup. The caller queue made multiple scoped calls per checkpoint, and its measured settlement times exceeded full closure in this run; setup and single-run timings are descriptive. Frame creation and queue policy remain caller-side. The result establishes that the current scoped API can report remote owners for this particular connected conversation pattern and that following those reports preserves exact closure here. It does not establish automatic scheduling, complete dependency discovery, realistic learned partitions, or a general cheap-cut distribution.

All 11 runner gates and nine independently recomputed checks pass. See the [preregistration](SUBSTRATE_CONVERSATION_SCOPED_OWNER_WAKEUP_PREREG_20260926.md), [runner](../../../scripts/substrate_conversation_scoped_owner_wakeup_v1.py), [independent analyzer](../../../scripts/analyze_substrate_conversation_scoped_owner_wakeup_v1.py), [input lock](../../../evaluation/substrate_capability/conversation_scoped_owner_wakeup_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_conversation_scoped_owner_wakeup_v1_20260926.json), and [analysis](../../../evaluation/reports/substrate_conversation_scoped_owner_wakeup_v1_analysis_20260926.json).
