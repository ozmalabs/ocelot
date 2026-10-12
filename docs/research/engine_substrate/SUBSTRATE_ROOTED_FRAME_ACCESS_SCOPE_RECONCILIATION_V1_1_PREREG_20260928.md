# Rooted-frame access-scope reconciliation v1.1 preregistration

Date: 2026-09-28
Status: preregistered after diagnosing process-global trace contamination and before the corrected three-worker replay

## Motivation and instrumentation correction

The v1 trace used one process-global event map, enable flag, and thread-local rule UID, although node IDs, rule UIDs, and symbol IDs belong to individual substrate instances. The v1 capture recorded `edge:is_a` under UID 1 although that substrate's UID 1 rule matched `committed_goal`. A direct cross-instance probe enabled tracing on an empty substrate, executed a separate populated `WorldAdapter`, and panicked when the empty substrate snapshot resolved a foreign symbol ID. This establishes trace contamination, not a rule-access declaration defect.

The native trace is now scoped by the address identity of the substrate's owned graph. A rule guard carries this scope through nested instrumented reads; the recorder accepts events only from the substrate selected by its instance method, and snapshot returns only that scope. The release extension was rebuilt from the modified Rust source. Semantic task behavior must remain aligned with the accepted v1.1 proposal-panel capture; trace rows are expected to differ and are not required to match the old global trace.

## Frozen workload and baseline

Replay the same two prompts, seed construction, and three fresh worker schedule from rooted-frame proposal panel v1.1. Preserve the accepted panel's raw and lock hashes in the new lock. Do not alter prompts, graph construction, or proposal definitions. Capture per-request rule-scoped access rows and post-request static access records, including exact exported match-edge triples, derived read/write keys, and rule UID/index mapping.

## Registered analyses

1. **Scope isolation:** positive arm traces a workload on its own substrate and captures nonzero events; negative arm enables trace on a distinct empty substrate during the populated workload and must capture zero rows without panic. This is a process-level isolation control, not a concurrency guarantee.
2. **Replay integrity:** three fresh PIDs; stable per-worker and post-run source locks; exact semantic graph digest, reply presence, route, goal count, and lifecycle outcome parity against the corresponding accepted v1.1 replicate. Compare corrected trace rows exactly across the three corrected workers, not against the contaminated v1 trace.
3. **Static-key concordance:** map supported trace kinds using v1 analyzer rules and compare each observed access to post-request static keys. Preserve mismatches by event identity. A mismatch is an unresolved source/schema issue, not automatically an engine semantic failure.
4. **Concrete identity refinement:** report observed read/write identity intersections and static possible dependency pairs. Absence of observed overlap is not independence.
5. **Cost counters:** report per-rule and aggregate fields descriptively. The v1 equations are not integrity gates: missing per-rule rows and uncalibrated equations must remain explicit. Any future equation requires source-backed event-boundary semantics before capture.

## Integrity gates

- Three distinct worker PIDs and stable corrected source locks.
- Scope positive and negative controls pass.
- Semantic/task parity with accepted v1.1 baseline; exact trace parity among corrected workers.
- Zero trace drops and weighted counts equal the sum of event-row counts.
- Independent offline analyzer reproduces scope isolation, static key mapping, identity intersections, and replay parity from raw capture.

## Claim boundary

This tests instrumentation isolation and selected access-scope behavior on one authored two-prompt task pair. It does not establish trace completeness, natural-task prevalence, learned frame locality, causal necessity, scaling, or a general complexity bound.
