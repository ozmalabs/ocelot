# Thoughtexperiment deferred RulePatch attribution v1 preregistration

## Question

Can a graph-native RulePatch preserve every producer identity when several rules queue the same patch, while retaining the existing deduplicated, single-commit behavior?

## Change under evaluation

The transient queue associates each patch node with an ordered set of unique producer rule symbols. Duplicate submissions still produce one queue item and one CAS transaction. The deferred event carries the complete origin set; its legacy `rule_name` is only the first origin and must not be read as a unique cause. Exact graph changes are checked separately from the target rule's exported definition/revision.

## Protocol and gates

Three fresh workers each create one unprotected target rule at revision zero, one valid RulePatch node proposing `where=true`, and two distinct one-shot producer rules sharing the same patch edge. Both producers queue the same node before the drain. Require ordinary/attributed/exact settlement parity; one committed deferred event containing both producer identities; exactly one target-rule revision advance; a durable `committed` patch receipt; exact graph-delta coverage including the patch node; aggregate target containment; distinct PIDs; stable source/native fingerprints; and no event drops.

This tests the previously ambiguous deduplicated multi-producer case. It does not prove which producer was causally necessary, and it is not a performance or autonomous self-repair result.

## Reproduction

Build with `PYTHON=python3 scripts/engine_build.sh`, run the runner with `--lock` and `--run`, then run the analyzer. The source lock binds the rule-write event schema, queue/enqueue/drain implementation, binding serializer, protocol, runner, analyzer, and loaded extension.
