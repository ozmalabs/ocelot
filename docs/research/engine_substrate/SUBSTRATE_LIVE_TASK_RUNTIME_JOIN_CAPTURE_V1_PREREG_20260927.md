# Live task runtime join-work capture v1 preregistration

Date: 2026-09-27 local

## Question

Which active multi-edge native rules incur candidate work during the current `describe_scene` conversational task, and what is the exact runtime graph state immediately before a representative task transition?

## Capture

Reuse the source-locked threaded `describe_scene` task harness, its two-request serialized schedule, frozen scene and expected replies, goal identity/lifecycle gates, and complete graph signature. Run three fresh processes on the current worktree with native per-rule counters already enabled at the producer event closures. After loading the selected full seed profile, export each active rule's installed match pattern. Join the per-event `candidate_tests` counter rows by stable RuleIdx to these patterns. Record all matched multi-edge rule/event pairs, along with event kind, rule match clauses, candidate tests, candidate pairs, and term-evaluation work.

Before request B's `action_result` event enters the event/closure path, capture the complete graph once (replicate 0) and record node/edge counts and its canonical byte digest in all three workers. The first pre-action graph is retained as a separate machine-readable snapshot. The graph is an observation from runtime task construction and earlier closures; no fixture graph edges are injected by this capture.

## Gates

- Three fresh PIDs, stable current source/native inputs at worker start/end and after run.
- Existing request serialization, event order, reply parity, identity, lifecycle, task boundary, and terminal semantic graph gates all pass.
- Active rule table is aligned by RuleIdx with native `rule_access_sets`; active match patterns are serialized from `export_rules()`.
- Per-event per-rule candidate work maps only to a present active RuleIdx; report candidate work for every rule with match arity ≥3 and candidate_tests >0.
- Exact graph snapshot hash matches the representative worker's recorded pre-action digest; node/edge counts match its runtime metadata.

## Scope boundary

This is three repeats of one authored concurrent conversation fixture on the current full-seed profile. Candidate counters are collected around selected goal-event closures, not every internal native call in `converse`; the full selected graph has far more activity than these producer intervals. The snapshot is one pre-action state, not a representative natural-distribution sample. Do not infer population frequency, complete work attribution, or general tractability.
