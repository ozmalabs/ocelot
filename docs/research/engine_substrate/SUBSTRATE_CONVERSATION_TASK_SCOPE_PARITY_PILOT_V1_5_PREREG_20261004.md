# Conversation task-scope parity pilot v1.5 preregistration

Date: 2026-10-04

## Question

Where does scoped closure spend matching work: on raw successful bindings, rejecting bindings outside the declared ownership set, duplicate suppression, or applying each distinct in-scope binding?

## Workload and controls

Repeat the source-locked v1.4 comparison unchanged: three fresh workers; authored concurrent-goal cases at 2, 4, and 8 frames plus the four-frame common-ground stress case; monolithic closure paired with globally reswept Microtheory scopes. Scope roots and unchecked ownership edges remain symmetric measurement annotations. Preserve exact graph, checkpoint, goal-state, and quiescence gates. V1.4 protocol, runner, analyzer, lock, capture, and independent analysis are pinned as prior evidence.

## Added measurement

The native scoped matcher emits separate work events for: successful raw binding callbacks before scope filtering; bindings retained by `binding_touches_scope`; bindings rejected by that scope filter; duplicate in-scope bindings skipped by canonical-key deduplication; and distinct bindings passed to `apply_rule_full`. These are counts at explicit code boundaries. Candidate-pair and Term-evaluation scale counters remain the comparable search counters across monolithic and scoped modes. Event subjects use the stable per-process active rule vector index; operation IDs and graph scopes identify each run.

The analyzer must independently check, for each scoped checkpoint and in aggregate:

- raw matched bindings = in-scope bindings + out-of-scope bindings;
- in-scope bindings = duplicate bindings + apply attempts;
- event kind coverage, row shape, operation identity, zero dropped events, source stability, and exact state parity.

## Gates

1. Provenance-current native engine. Direct lock includes the runner, analyzer, protocol, v1.4 source artifacts, panel, materializer, seed, fixtures, native extension/build manifest, and relevant Rust sources.
2. Three distinct worker processes cover exactly the preregistered workload matrix, and locked inputs are unchanged after capture.
3. All monolithic/scoped final graphs, every checkpoint graph, goal statuses, and fixed-point outcomes match.
4. Each partition scope reaches zero-progress quiescence with no deferred effects; report notification completeness without treating false as complete.
5. No dropped work rows. Binding-count conservation equations pass per checkpoint and in aggregate; no binding volume is inferred from wall time.
6. Independent analysis recomputes integrity, state digests, binding conservation, and work summaries from retained capture.

## Interpretation boundary

This measures the current scoped matching funnel on explicitly annotated authored conversation fixtures. It does not prove dependency completeness, learned or natural frames, equivalence of the scoped and monolithic algorithms, lower cost, or prevalence across natural tasks. A successful binding callback is not a raw graph candidate count: matcher candidate scans remain represented by scale counters.
