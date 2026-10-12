# Stage A overlap-triggered fallback preregistration

## Question

When an admitted multi-variable rule produces proposals that touch a shared hub, does Stage A detect the overlap, fall back to sequential committed execution, and preserve ordinary closure's exact graph and progress behavior?

## Fixture and contrast

For fanouts 1, 2, 6, 16, and 32, construct a hub `x` with one `trigger` edge to each distinct target `y_i`. Each target has `watched=i+10`; each pre-existing `derived` edge `x -> y_i` starts with `{value:-1, marker:i}`. The rule matches `(x, trigger, y)` and applies `AddEdge(x, derived, y, {value:Attr(y, watched)})`. Its reads are target-local and writes share the hub, so the rule is statically admitted while Stage A's runtime touched-node relation should detect proposal overlap for fanout ≥2. Compare fresh ordinary-closure and Stage A-enabled executions.

## Gates

Across three fresh workers and every fanout require exact whole-graph equality, exact target-value oracle, exact edge count, and progress/terminal parity. Require zero unsupported compare expectations; for fanout 1 require zero conflict fallback, and for each fanout ≥2 require a positive fallback count. Lock protocol, runner, Rust sources, native extension/manifest, and commit at worker start/end.

## Claim boundary

This tests shared-source edge writes that are independently safe semantically but conservatively overlap under the current node-level relation. It does not establish detection of every harmful dependency, behavior for node-attribute writes (statically excluded for multi-variable rules), deletion/mint effects, concurrent mutation, or natural workload prevalence.
