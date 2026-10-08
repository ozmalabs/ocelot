# Declared scope-anchor matcher v2.0 preregistration

Date: 2026-10-03
Status: preregistered before implementation; exploratory engine evaluation.

## Question

Can a declared single owner anchor plus a conservative co-ownership proof reduce the repeated enumeration measured in v1.6–v1.9 while preserving scoped closure behavior and match/effect order?

## Hypothesis and implementation contract

Four discourse lifecycle rules carry `match_type: Goal`, bind a `goal` variable, and contain the pattern edge `event for_goal goal`. Add opt-in rule metadata naming the anchor variable and the ownership-link pattern edge. For these rules, enumerate only scope-owned Goal anchor values and move the anchor-adjacent match edge to the front of candidate expansion. Restore the original rule-clause order with the live-index rank key measured in v1.9 before applying effects.

The fast path is admissible only when every owned Event has exactly one outgoing `for_goal` edge to an owned Goal, the rule contains the corresponding `event for_goal goal` pattern edge, and an owned Goal cannot occupy another matched variable role in that rule. Other owned nodes (including the scope root itself) are admissible only when no edge in the rule pattern is incident to them. Any violation, missing anchor, or malformed metadata takes full matcher plus the existing `binding_touches_scope` filter. This condition is necessary because generic scope semantics currently mean “any bound node is owned”; anchor-only matching is sound only when non-anchor owned Events are co-owned with the anchor and no other owned node types can occur in the pattern.

## Arms and workload

1. **Fallback control:** metadata absent; full-match/filter for multi-edge rules.
2. **Declared anchor:** anchor and link metadata present; validated anchor path for eligible rules; fallback otherwise.

Run the v1.6 authored matrix (2, 4, 8 concurrent goals and four-frame common-ground stress) under ascending, descending, and outside-in scope schedules, with three fresh workers per schedule. For this v2 pilot, ownership annotations include Goals and Events with an explicit `for_goal` edge; origin and ambient events remain shared/unowned because they do not carry that direct owner edge. Add two ownership controls: (a) a `for_goal` Event is owned by a different frame from its linked Goal; (b) a `for_goal` Event links to a Goal with no frame owner. The proof guard must route unsafe frame scopes to fallback. Each arm uses the same annotation and matched initial graph state; the fallback arm strips the performance metadata during rule loading, while authored rule behavior is otherwise identical. Capture source and native hashes.

## Gates

- Source lock stable before and after all nine fresh workers.
- Exact final, checkpoint, and goal-lifecycle parity between fallback and anchor arms for every workload and ownership control.
- Ordered binding/effect trace parity for each anchored rule, or an independently checked canonical sequence digest before effect application.
- Cross-frame and orphan-owner controls demonstrate that the runtime proof guard selects fallback where anchor ownership alone cannot represent generic `touches-owned` semantics.
- Analyzer independently verifies path counters, guard/fallback counts, case/order coverage, and state comparisons.
- Candidate visits and Term evaluations are reported by rule and by path. The anchor path is a performance success only if both are lower than the same-source fallback control; otherwise report it as a semantic result without adoption. Wall-time is secondary and requires paired, source-identical measurements.

## Exclusions

Passing this panel does not establish general scope correctness, natural-task frame locality, computational factorization, self-improvement, or broad tractability. The `Goal`/`Event` ownership proof is specific to the declared relation contract; other ownership shapes remain on fallback until separately specified and evaluated.

## Provenance

- Prior path attribution and decision: [v1.8 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_PATH_ATTRIBUTION_V1_8_RESULTS_20261003.md), [v1.9 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_DELETION_SAFE_ORDER_V1_9_RESULTS_20261003.md)
- Matcher and metadata seam: [`match_rule_each_for_scope`](../../../runners/dsl/src/rewrite.rs), [`RewriteRule`](../../../runners/dsl/src/rewrite.rs)
- Conversation lifecycle rule set: [conversation_discourse_state.json](../../../seeds/conversation_discourse_state.json)

## Amendment — 2026-10-03, before confirmatory rerun

The first source-locked nine-worker capture completed state and trace parity, but the declared-anchor path was rejected on every aligned case by an overly conservative role-adjacency implementation. Its failed capture is retained at `evaluation/reports/conversation_task_scope_anchor_pilot_v2_0_20261003.json`; it is not evidence of performance. The matcher check now evaluates adjacency once per distinct pattern edge type. An owned Event may occupy a non-owner role only when the pattern edge connects that role directly to the declared anchor and every such runtime neighbor is an owned Goal; this covers the lifecycle `origin` role while preserving fallback for cross-frame and orphan ownership. A second diagnostic found that scoped ownership includes the Microtheory root; it is now allowed only when it has no incident edge type from the match pattern. The ownership contract, workloads, success gates, and comparison arms remain unchanged. The amended capture and lock use the `_v2_0_1_` suffix; report both runs, and treat the first as a failed implementation attempt.

### Amendment — 2026-10-03, semantic-edge work attribution

The v2.0.1 independent analysis passes semantic gates but finds identical aggregate Candidate and Term counts for anchor and fallback. Before changing the matcher again, the follow-up capture adds expansion-call and candidate-pair counts keyed by `(rule, source variable, edge type, target variable)`. This key is invariant to clause reordering, unlike the existing positional clause counter. Capture the same 54-case workload and controls under a new source lock with `_v2_0_2_` filenames. These measurements are diagnostic: they do not relax exact-state/guard gates and do not change the performance success rule (both aggregate Candidate and Term totals must decrease). This is a measurement instrumentation amendment only; no task, control, schedule, or success threshold changes.

### Amendment — 2026-10-03, fallback-arm patching defect

Post-run source inspection found that the runner changed `substrate.seed_loader.manifest_for`, while `substrate.boot_core` had already imported its own module-level reference. Therefore, the arms called `partition_fallback` retained the declared-anchor metadata. The v2.0.1 and v2.0.2 captures remain valid for anchor-versus-monolithic state parity and the anchor proof-guard observations, but neither is a valid anchor-versus-full-fallback work comparison. Withdraw the v2.0 performance conclusions, including the v2.0.2 claim that the semantic-edge search tree was identical under generic fallback and anchor matching. The follow-up [v2.1 selectivity protocol](SUBSTRATE_CONVERSATION_TASK_SCOPE_SELECTIVITY_V2_1_PREREG_20261003.md) patches both references and gates on zero anchor-path counters in every fallback checkpoint.
