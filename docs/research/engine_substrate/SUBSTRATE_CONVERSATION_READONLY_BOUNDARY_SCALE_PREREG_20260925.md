# Conversation read-only boundary scale preregistration

## Question

Does frame-scoped Phase 4A closure preserve outcomes when adjacent scopes overlap on shared read-only evidence nodes while deliberation and candidate state remain frame-local?

## Design

- Use only `conversation_deliberation_phase4a`, N=1/2/4/8 tasks, three fresh-process replicates, and the existing full versus round-robin scoped closure arms.
- Each task retains its own goal, deliberation, grounded repair, grounded answer, and unsupported answer. For each adjacent pair, add one immutable `SharedGroundingEvidence` node connected by `supports_candidate` edges to the two tasks' local grounded answers; include that evidence node in both Microtheory scopes. Candidate, score, selection, and deliberation nodes are never shared.
- The Phase 4A seed rules match `has_candidate`, `has_selection`, `selects_candidate`, and `about_goal`; they do not read `SharedGroundingEvidence` or `supports_candidate`. Thus this creates overlapping scopes and graph connectivity, but **does not create rule-dependency propagation**. The prior shared-mutable-candidate experiment remains the aliasing negative control.
- Require all 24 reports to reach fixed points, all expected task outcomes, and exact full/scoped normalized projections. Report candidate/Term work, frame turns, wall/CPU time, and RSS descriptively.
- Lock protocol, runner, seed, materializer, binding, scheduler and substrate source hashes before execution; require a current native build.

## Limits

Passing this gate supports only correct settlement with overlapping scopes over untouched shared evidence. It does not support natural frame locality, cross-frame wakeup completeness, inference factorisation, or a scheduler speedup. To test propagation, the native rule path must actually read the shared evidence or an explicit cross-frame rule must be separately preregistered and audited.
