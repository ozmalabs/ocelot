# Grounded concern-dispatch probe v1.2 results

**Run:** 2026-09-28; four unique fresh full-seed processes, two per condition.  
**Protocol:** [v1.2 preregistration](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_2_PREREG_20260928.md); [amendment history](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_1_AMENDMENT_20260928.md), [v1.2 amendment](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_2_AMENDMENT_20260928.md).  
**Evidence:** [raw capture](../../../evaluation/reports/grounded_concern_dispatch_v1_2_20260928.json), [independent analysis](../../../evaluation/reports/grounded_concern_dispatch_v1_2_analysis_20260928.json), [source/input lock](../../../evaluation/substrate_capability/grounded_concern_dispatch_v1_2_lock_20260928.json), [runner](../../../scripts/substrate_grounded_concern_dispatch_v1_2.py), [analyzer](../../../scripts/analyze_substrate_grounded_concern_dispatch_v1_2.py).

## Result

All 14 independent gates pass. Every worker has stable source/runtime inputs, loads 731 seeds with 11 reported boot failures, invokes the action dispatcher once, and records zero teacher calls.

| Condition | Route | Outcome | Rule delta | Median task wall time |
|---|---|---|---:|---:|
| Preconstructed `compare` instruction with the original text | `concern_authored` (2/2) | Exact repeated concern signature `[['pairwise','PARTS'], ['judge','TRIAL','by','RESULT']]`; new concern minted and grounded as `experiment_rule` | 1 | 2.579 s |
| `walk` instruction, “Walk to the door.” | `goal_only` (2/2) | No concern object; honest no-world/action-space response | 0 | 0.743 ms |

The task timing starts at the `act_on_instruction` call and excludes full-seed boot, though the positive route lazily installs/runs the concern induction path. These four timings are descriptive and not a stable performance estimate. The large positive/control gap is consistent with the added induction and grounding work; it does not isolate which internal operation dominates.

## Interpretation and limits

This confirms that, when supplied a preconstructed instruction whose text and dispatch are already concern-framing, the current route invokes `induce_concern`/`ground_concern` and returns a repeatable teacher-free grounded concern. The goal adds one rule in each positive worker. The natural-language panel fails earlier: it never produces a goal or invokes this action. Therefore the capability map should separate **grounded concern induction: demonstrated on one authored signature** from **natural-language concern-task interpretation: unresolved on the tested wording family**.

V1 is retained as a partial serialization failure: `NodeID` prevented worker results from being encoded. V1.1 captured valid positive rows, but its proposed negative control still contained “Compare” and “judge” in the raw text, so the dispatcher routed both arms to concern authoring; do not use v1.1 to claim route specificity. V1.2 corrected this by using an unrelated `Walk to the door` prompt and passes its positive and negative-control oracles.

The result does not establish correctness of the concern for a real trial, general inductive learning, novel-task transfer, or language comprehension. It uses a manually constructed `Comprehension` object and bypasses parsing, arbitration, and grounding from user text. The next gate should test a grounded trial representation with an independent semantic oracle, then trace the full text-to-action path on task formulations that successfully ground.
