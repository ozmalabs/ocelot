# Thoughtexperiment deferred RuleEdit attribution v1.1 preregistration

## Amendment

The v1 capture passed producer labeling but falsified the proposed edit: it passed a bare Boolean, which the target rule patch parser rejects as `MalformedClause`. Preserve v1 unchanged. This version supplies the same intended clause as a serialized `Lit(true)` Term tree; all other fixture structure and gates are unchanged.

## Question and gates

Can `SetRuleClause` retain its producer identity through the deferred drain, and can the resulting live rule change and downstream graph effect be independently verified? Run three fresh source-locked workers. Require ordinary, attributed, and exact-snapshot status/progress/pass parity; exactly one deferred event named `edit_target_clause` with `progressed=true`; a changed exported definition for `target_rule`; a graph write by the newly enabled target rule; exact graph delta coverage; aggregate target containment; distinct PIDs; stable fingerprints; and zero dropped events.

The graph target observer cannot itself represent live rule-store state. The exported rule definition/revision is the independent oracle for that state; the exact snapshot is the oracle for graph changes. This single name-addressed case does not establish multi-edit disambiguation, `__mint__` attribution, RulePatch behavior, performance, or autonomous self-modification.

## Reproduction

Build with `PYTHON=python3 scripts/engine_build.sh`, run the v1.1 runner with `--lock` and `--run`, and execute its analyzer. Its lock binds this amendment, runner, analyzer, Rust implementation, Python binding source, and loaded extension.
