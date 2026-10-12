# Blind structural repair relation evidence v1 (preregistration)

## Question

Can the syntax-only proposal generator use local training-graph relation
evidence to propose a missing match edge, while retaining the prior v2
candidate pool and withholding target rules and case labels from generation?

## Inputs and policy boundary

For each case, the policy receives the faulted rule, a current match binding
from rule variables to graph node IDs, and graph edge triples from the exposed
training neighborhood. It derives extension signatures only for observed
edges that touch an already-bound node and lead to an as-yet-unbound node.
The candidate generator receives those signatures, not the target rule,
fault-family label, canary examples, or final oracle. The evaluation layer
uses alpha-equivalent variable canonicalization when comparing the generated
pool to target rules, since a fresh variable name is not semantically fixed.

The five fault/target pairs are reused from proposal coverage v1. Each
training neighborhood contains the same two relation types (`has_context` and
`has_tag`) at an output node. For four cases those neighbors are already bound
by the faulted rule; for the dropped-edge case they are unbound and can be
offered as extensions. The `has_tag` relation is a distractor. This is a
controlled proposal-generation probe, not a realistic data distribution.

## Procedure and gates

Three fresh workers run the same panel. The runner freezes the generator,
runner, analyzer, protocol, both fixtures, and v2 comparison analysis. The
analyzer requires exact candidate-ID, count, and coverage agreement across
workers; source-lock integrity; no truncation; and consistent proposal and
deduplication counts. It reports per-case proposal coverage, number of
relation-derived candidates, candidate pool sizes, and enumeration timing.

The registered outcome is whether the missing-edge target enters the
candidate pool and what distractor proposals are added. A pass means only
that the relation evidence is translated into a syntactically appropriate
candidate. It does not establish that the relation is necessary, that graph
selection chooses it, or that the repair passes behavioral holdouts. The same
fixture and fault forms have informed the prior operator changes, so this is
another engineering probe, not independent generalization evidence.
