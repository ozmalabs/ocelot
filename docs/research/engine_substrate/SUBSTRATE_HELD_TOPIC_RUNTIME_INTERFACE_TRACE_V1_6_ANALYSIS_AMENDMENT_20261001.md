# Held-topic runtime interface trace v1.6 analysis amendment (2026-10-01)

## Reason

The preregistered v1.7 analyzer compared work rows grouped into per-scope profiles after renumbering pointer scopes. That gate fails: the number and grouping of raw scope pointers varies across fresh workers even though every turn's operation IDs, producer RuleUIDs, work kinds, queue subjects, and unit counts match exactly. Scope IDs are raw addresses of `TypedGraph` instances, and short-lived graph objects can be freed and their addresses reused. Pointer-group cardinality is therefore not a stable worker-level identity.

## Correction

Preserve v1.7 raw data and analyzer. The amended independent analysis compares operation-work rows as a multiset of `(operation_id, producer_rule_uid, kind, subject, units)`, omitting the process-local pointer scope field. It continues to require positive scope IDs per raw row and reports per-turn scope-pointer counts by worker as a diagnostic, but does not gate equality of those counts. It still requires zero dropped rows and exactly one supported operation-kind marker for each `(scope, operation_id)` group. This retains the attribution detail within each process while avoiding a cross-process address-identity claim.

## Evidence and limits

Across all 21 worker-turns, the operation-level row multisets are identical across the three workers; summed work units also match per turn. This supports repeatable operation-level scheduler/deferred-work counts on this route. It does not prove stable graph-scope ownership across object lifetimes. The per-scope pointer rows remain process-local and cannot be joined to task frames or compared as persistent scope identities without a stable native scope token.
