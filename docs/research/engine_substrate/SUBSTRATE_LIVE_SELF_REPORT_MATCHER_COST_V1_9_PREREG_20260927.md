# Live self-report matcher cost v1.9 preregistration

Date: 2026-09-27 local

## Question

Does the matcher-attribution instrumentation validated on the attached-scene `describe_scene` workload also conserve exact candidate tests on the independent live `self_report` route?

## Workload

Use the existing full-seed current-source self-report fixture: `report your organisation`, followed by the known `describe who you are` route-selection shortfall. The first prompt is the measured task. Its native producer hook must emit Goal-bound `selection`, `execution`, and `action_result` events. The second prompt is retained as a route negative/control and is not included in producer-work totals when it produces no lifecycle events. Preserve the existing five explicit owner-link/failure controls.

Measure three fresh processes. Reset global and per-rule counters immediately before each producer event; enable the audit only over that event closure. Capture global candidate tests, per-rule counts, per-clause counts, native matcher metadata including ambiguity status, and Term-evaluation totals.

## Gates

1. Three distinct PIDs and stable current-source/native fingerprints at start, finish, and post-run.
2. The first prompt reaches the self-report route and resolves its own Goal through exactly selection/execution/result; the second prompt’s no-lifecycle route outcome reproduces as separately classified behavior.
3. All five established identity and faculty-failure controls pass.
4. In every producer-event interval, `cand_tested = attributed + cand_tested_unattributed`; verified per-rule and in-arity per-clause sums each equal the attributed count.
5. Every attributed audit ID maps to captured native metadata; ambiguous IDs have no residual attributed rows; every clause position is below matcher arity.
6. Term-evaluation counters reconcile between per-rule and global snapshots.
7. Candidate and attribution profiles reproduce across workers; any mismatch is reported as a failed repeatability gate, not averaged away.

## Interpretation boundary

This is one current-source self-report task route and one route-selection control. It can test whether exact matcher attribution transfers across a second live topology. It does not establish natural-task frequency, semantic accuracy, general learning capability, asymptotic scaling, uninstrumented runtime, or tractability on commodity hardware. The known second-prompt route shortfall remains an independent capability issue.
