# Interleaved two-goal owner-wakeup probe v2 results

**Run:** 2026-09-26. **Grade:** locked diagnostic on one authored ten-event conversation fixture with a caller-assigned four-frame partition.

## Closure and notification result

The owner-queue arm matched global closure's complete graph at all 10 event checkpoints. The omitted-notification arm first diverged at event 6 when the remote receipt consumers needed to run; its receipts stayed stale through events 7–9. A final full closure restored exact graph parity. At event 6 the native write report mapped changed Goal nodes to both remote origin frames (frame 0 and frame 1). All scoped calls completed without deferred effects or progress-budget exits. The independent analyzer recomputed all 12 gates.

This confirms that the scoped report can fan a write out to multiple caller-owned frames in this connected, interleaved fixture. The caller queue was slower than global closure in this one small timing capture; no performance benefit follows.

## Semantic capability gap exposed

The fixture encodes two intended sequences: origin 0 followed by operation events 4–6, and origin 3 followed by events 7–9. In this benchmark, the explicitly loaded experimental `conversation_discourse_state` seed guards transitions by event kind and temporal order, not by task identity or addressee. Consequently both open Goals transition on events 4, 5, and 6; event 6 resolves the later-origin Goal as well. A source audit found the domain's host `transition_goal(agent, goal, target, event=...)` helper but no call sites from domain modules. Thus this is a limitation of the benchmark-loaded native seed rules, not evidence that an active production path currently misassigns the task. The scheduling arms match because they use the same native closure semantics.

This separates two conclusions: owner notification preserves current seed-rule semantics across frames here, while those rules do not preserve the fixture's intended multi-goal assignment. A later locked candidate-rule probe tests a shared-addressee guard without changing the production seed.

## Claim boundary

One authored conversation fixture and manually declared frames do not estimate natural locality, automatic scheduling, or general tractability. This is a correctness diagnostic plus a concrete multi-goal semantic counterexample, not a broad capability pass. See the [preregistration](SUBSTRATE_CONVERSATION_SCOPED_OWNER_WAKEUP_V2_PREREG_20260926.md), [runner](../../../scripts/substrate_conversation_scoped_owner_wakeup_v2.py), [independent analyzer](../../../scripts/analyze_substrate_conversation_scoped_owner_wakeup_v2.py), [lock](../../../evaluation/substrate_capability/conversation_scoped_owner_wakeup_v2_lock_20260926.json), [raw report](../../../evaluation/reports/substrate_conversation_scoped_owner_wakeup_v2_20260926.json), and [analysis](../../../evaluation/reports/substrate_conversation_scoped_owner_wakeup_v2_analysis_20260926.json).
