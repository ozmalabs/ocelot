# Thoughtexperiment polar-conflict guard v1 protocol (2026-10-03)

## Question

Can the existing Rust CoW snapshot/fork path isolate a candidate rule, preserve the baseline behavior, and return only an explicitly selected candidate graph residual to the primary substrate?

## Design

For each of seven fixed query/claim conditions, create a fresh primary graph and fork two children from the same snapshot. The baseline child receives the current `communication_intent_arbitration` seed. The candidate child receives the same seed plus a hand-authored rule at priority −100. It detects two evidenced, accepted unary propositions with the same predicate and selected subject but opposite polarities. For a conflict it marks the interpretation as conflicted, creates a `PolarConflictOutcome`, and suppresses the ordinary answer plan.

The seven conditions are one affirmed claim, one negated claim, contradictory accepted claims in both insertion orders, an accepted claim paired with a retracted opposite claim, an accepted claim paired with a proposed opposite claim, and accepted opposite claims about different subjects. Each condition is repeated three times, giving 21 rows. Expected candidate and baseline outcomes are encoded in the runner.

## Gates

1. The source lock matches before and after the run; native build freshness is clean.
2. Baseline output matches the current behavior oracle in every row.
3. Candidate behavior preserves unique positive/negative answers and ignores non-accepted or different-subject controls, while producing no answer plan and exactly one conflict outcome for accepted contradictions.
4. Primary graph and rule state remain unchanged before explicit residual return; experiment rules never leak into primary.
5. A conflict residual is returned once to primary using the captured graph/rule revision; returned nodes match the candidate branch. No residual is returned for control cases.

## Provenance note

This protocol follows an exploratory inline proof that exposed the conflict case. The fixed runner and source lock define the measured replay; the result should not be described as preregistered blind confirmation. The rule is authored for this fixture, not discovered by the substrate. A passing result measures the experiment substrate's branch isolation and residual-return mechanism, not production answer safety, conflict-rule generalization, trusted claim lineage, or autonomous self-improvement.
