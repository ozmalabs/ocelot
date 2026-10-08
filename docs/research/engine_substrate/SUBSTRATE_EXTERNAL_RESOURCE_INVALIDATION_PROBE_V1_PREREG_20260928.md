# External resource invalidation probe v1

## Question

When a `UseTool` predicate reads a mutable external resource, does a resource-only change cause an already-matched rule to be reconsidered? Does a later graph event cause a new match to observe the changed resource?

## Protocol

- Lock `term.rs`, `rewrite.rs`, Python bindings, native extension, build manifest, and probe code before workers start.
- Three independent processes each create a fresh substrate and a temporary file-backed tool handler. The callback logs the file value for every invocation and returns that value.
- Install one rule matching `trigger` edges, with `where = Eq(UseTool("resource_value", [Lit("resource")]), Lit("1"))` and an effect setting `accepted=1` on the matched target.
- Phase A: resource contains `0`; run closure and capture calls, graph, progress, and access declaration.
- Phase B: change only the file to `1`; run closure without any graph mutation and capture the same measures.
- Phase C: change the file back to `0`, add a second matching edge, run closure, and capture both target attributes and calls.
- Record per-phase bytes/hash and callback return values. No network or persistent files are used.

## Gates and claim limits

Integrity gates require three fresh successful workers with identical source/native locks and phase shapes. Behavioral outputs are reported, not assumed. This synthetic probe distinguishes resource-only reevaluation from graph-triggered evaluation; it does not establish behavior for every Term, a watcher/invalidation mechanism, effect retraction, or production workload prevalence. `UseTool` already has a wildcard graph read declaration, so Phase C also characterizes the current graph-trigger path, not only a specific edge dependency.
