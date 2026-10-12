# Same-addressee Goal identity scaling v4 results

**Run:** 2026-09-26. **Grade:** locked generated task diagnostic at 2, 4, and 8 concurrent Goals (15 fresh workers total). This is not a natural-task sample or production integration.

## Task semantics

All Goals share one addressee. Each task has its own selection, execution, and result events, with an explicit `event -> for_goal -> Goal` link. Temporal-only lifecycle rules assign every Goal to the first operation sequence. A shared-addressee guard does the same and cannot separate tasks. The explicit event-to-goal rule variant matches the frozen task oracle for every Goal at all three scales.

The explicit variant therefore handles one failure that addressee matching cannot. It relies on the benchmark-supplied identity edge; the current production event producers have not been shown to emit it. This is a candidate representation, not a production fix or proof that the link is sufficient for all task types.

## Scoped closure

With explicit links, the owner queue matches full closure at all 8, 16, and 32 checkpoints for 2, 4, and 8 goals respectively. Remote goal-origin owners are reported at every result. Suppressing those notifications makes the graph stale from the first result sequence at each size; one final global closure restores exact graph parity. All scoped calls finish without budget exits or deferred effects. The independent analyzer recomputes every size gate and the operation counters.

The queue costs more than full closure in these small workloads. Candidate-pair counts are 1.38×, 1.33×, and 1.30× full closure; Term evaluations are 1.43×, 1.32×, and 1.26×. Single-run aggregate wall ratios are 2.39×, 2.41×, and 2.35×. These short timings are descriptive only. Peak RSS remains around 37–40 MiB including the interpreter and substrate import floor, so this probe does not isolate graph memory growth. Operation counts increase faster than goal count over this narrow 2–8 interval; larger sizes and repeated workers are needed before interpreting the trend.

## Claim boundary and next gate

This shows exact explicit-identity consumption and owner-notification parity on one generated connected task family. It does not establish automatic ownership, a production event schema, broad workload locality, useful-scale tractability, or a speed benefit. The next gate should validate task/action identity links on an independently authored workload and extend the scale envelope beyond eight concurrent goals before any runtime integration decision. See the [preregistration](SUBSTRATE_DISCOURSE_GOAL_IDENTITY_SCALE_V4_PREREG_20260926.md), [runner](../../../scripts/substrate_discourse_goal_identity_scale_v4.py), [independent analyzer](../../../scripts/analyze_substrate_discourse_goal_identity_scale_v4.py), [input lock](../../../evaluation/substrate_capability/discourse_goal_identity_scale_v4_lock_20260926.json), [raw report](../../../evaluation/reports/substrate_discourse_goal_identity_scale_v4_20260926.json), and [analysis](../../../evaluation/reports/substrate_discourse_goal_identity_scale_v4_analysis_20260926.json).
