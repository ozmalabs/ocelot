# Executable seed cache-operator census v1 preregistration

## Question

Which shipped executable seed rules contain `Argmax` or `Holds` terms, and in which rule sections do they occur?

## Method

Lock every JSON seed manifest, this runner, the operator-census protocol, and `engine_rules_only`. Exclude declarative principles using the same seed-loader helper used by native boot. Recursively count operator term nodes in each executable rule's match, where, and effects sections. Emit seed/rule-level counts and corpus totals, then verify all locked inputs remain unchanged.

## Acceptance and limits

Require a current source lock, nonempty corpus, and source stability. This is a static census of authored executable rules. It does not establish that a rule fires, that a cache entry is populated, or how often a workload uses the operator. Use it to select source-linked runtime fixtures for the next cache-transfer gate.
