# Thoughtexperiment deferred RuleEdit attribution v1 preregistration

## Question

Can a `SetRuleClause` request retain its producer identity through the deferred drain, and can the resulting live rule change and downstream graph effect be independently verified?

## Change under evaluation

The pending RuleEdit tuple carries the producer's rule symbol. During drain, an attributed deferred event wraps the existing edit/mint handling. Queue ordering and rule-edit semantics remain unchanged. Graph write targets alone cannot expose a live rule-store mutation, so the fixture also captures the target rule's serialized definition before and after closure.

## Protocol and gates

Three fresh source-locked workers each install one gated producer, a target rule initially disabled by a false `where`, and one graph fact that matches that target. The producer queues one `where=true` edit and sets its own one-shot gate. Compare ordinary, attributed, and exact-snapshot settlement. Require status/progress/pass parity; exactly one `deferred=true` event named `edit_target_clause`; an actual target-rule definition change; execution of the newly enabled target rule; exact graph-delta coverage; aggregate target containment; distinct worker processes; stable source/native fingerprints; and no dropped events.

The analyzer validates both evidence channels. This is one name-addressed RuleEdit case and does not establish multi-edit disambiguation, `__mint__` provenance, rule-patch behavior, performance, or autonomous self-modification.

## Reproduction

Build with `PYTHON=python3 scripts/engine_build.sh`, run the runner with `--lock` and `--run`, then run its analyzer. The source lock binds the preregistration, runner, analyzer, Rust queue/drain implementation, Python binding source, and loaded native extension.
