# Self-directed learning-plan result

The developmental curriculum is now a constraint graph, not an externally
ordered schedule. Jabberwock instantiates and maintains its own persistent
`LearningPlan` over the situated capability DAG.

For every planning epoch it:

1. derives ready and blocked plan steps from mastered prerequisites;
2. derives an evidence budget from the body's evidence window and dependency
   structure;
3. publishes every ready experiment as a complete integer Pareto candidate;
4. compares information gap, prerequisite unlocking, retention urgency,
   transferable overlap, and experiment/reset cost without scalarization;
5. selects one frontier experiment and exposes only its capability goal to the
   motor graph;
6. updates the plan from the causally closed action receipt;
7. replans, changes scenario, extends a budget from observed progress, or
   records an honest deferment.

Completed Pareto alternatives remain in cold graph history. They leave the hot
comparison edge after selection so historical decisions do not consume the
current System 2 budget.

## Physical assay

Protocol: `protocols/humanoid_developmental_floor_v1.json`

Result: `results/humanoid_self_managed_learning_plan_v2.json`

- 244 of 244 developmental receipts were retained.
- The plan made 161 objective selections and 160 subsequent replans.
- It made 17 explicit evidence-budget revisions.
- No selected step exceeded its revised evidence budget.
- It requested and completed eight body/scenario re-instantiations.
- It selected the side-orientation fixture twice while investigating the
  `side_lying_transition` capability.
- Five capabilities reached retained mastery in the fixed 160-action
  evaluation; the plan remained actively investigating `side_lying_transition`.
- No caregiver protection supplied learning evidence.

This establishes self-management and bounded adaptation, not a performance
gain claim. The earlier scalar-frontier run reached six mastered capabilities
in the same nominal action horizon. The new system deliberately exposes the
allocation decision and its tradeoffs; improving that Pareto basis is now an
empirical planning question rather than a hidden curriculum constant.

The host does not select objectives, budgets, revisions, or scenarios. It
publishes declared simulator possibilities, mechanically enacts the single
graph-selected act, and returns receipts.

## Persistent autonomous learning assay

The motor-library boundary now also retains unfinished developmental evidence.
At an explicit lifetime boundary, graph rules mint an output-null, structural
body-shape-indexed experience memory together with the distinct causal contexts
in which it succeeded. A fresh body can recall the integer evidence counts, but
the memory cannot issue motor output or assert mastery. A capability at the
retention boundary still requires a fresh successful physical receipt.

The assay used one persistent v9 library across fresh PyBullet bodies:

- `results/learning_epochs/humanoid_autonomous_epoch_01.json`: cold start;
  five mastered capabilities.
- `results/learning_epochs/humanoid_autonomous_epoch_02_persistent.json`: the
  five mastered memories were reverified; side-lying reached 9 successes in
  five contexts and was consolidated as unfinished `retention_due` evidence.
- `results/learning_epochs/humanoid_autonomous_epoch_03.json`: the new body
  recalled that evidence, earned the required fresh success, and mastered
  side-lying after 11 selections. Mastery rose from five to six, and the graph
  redirected the remaining epoch to rolling and prone support.
- `results/learning_epochs/humanoid_autonomous_epoch_04.json`: prone-support
  evidence improved from 2 successes in two contexts to 6 successes in five
  contexts. Rolling remained at zero successes after 259 cumulative attempts.

The final library is
`results/learning_epochs/humanoid_autonomous_motor_library_v1.json`. It holds
six mastered capability memories, 18 learned somatomotor coupling motifs, and
two unfinished output-null memories: rolling and prone support.

This demonstrates cumulative learning across reinstantiation rather than
repeated cold rehearsal. It also exposes the next planning limit honestly:
the current Pareto frontier continues to allocate too much evidence to the
zero-yield rolling basin while a parallel support route is productive. That is
an objective-selection problem, not a persistence failure or a missing reset.

That exposed limit is now addressed by the order-N metacognitive learning-plan
faculty. Its design and physical follow-up are reported in
`METACOGNITIVE_LEARNING_RESULTS.md`.
