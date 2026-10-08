# Numeric residual-to-composer cue v1 preregistration (2026-10-03)

## Question

Can a native rule derive the held `flip_comparison` cue from a numeric outcome
residual without an action-name or opposite-action-pair codebook, and can the
existing composer turn that cue into a useful isolated proposal?

## Design

Reuse the frozen 13-case navigation panel and its target-rule outcome oracle.
Represent observed and expected movement as two-dimensional displacement
components on `OutcomeResidual`. A generic native rule matches only when both
component sums are zero, then writes the fixed held flip cue as a
`CapabilityAxis`. Do not install `OppositeActionPair` nodes or action-pair
edges. Do not put action names, target rule names, or operator labels in the
residual graph or the observation passed to concern induction. Missing and
unknown components remain absent. The cue vocabulary and vector-opposition
formula are authored by this experiment and are source locked.

Fork baseline and candidate branches from the same primary snapshot. The
baseline receives no numeric cue rule. The candidate receives the one generic
native rule, then invokes ordinary concern grounding/composition and scores
positive proposals on fresh held-out task states. Keep the target-absent
condition as a cue-without-proposal control.

## Gates

- Four opposite-direction outcomes derive the cue, select `flip_comparison`
  for `hop_descend_gradient`, and pass held-out scoring.
- Eight negative controls (orthogonal, same direction, unknown, missing,
  zero, and absent-target conditions as specified in the frozen panel) yield no
  cue or false proposal, except target-absent may derive the cue but must not
  build a proposal.
- Baseline never proposes; action-pair ontology nodes/edges are absent; raw
  residual/induction inputs contain no action names or operator/target labels.
- Branch state stays isolated until one compact result receipt is returned;
  the active primary rule and revision remain unchanged.
- Lock, native build, and source hashes remain stable.

## Interpretation boundary

Passing establishes transfer from supplied numeric outcome components through
an authored native relation rule to a held cue and composer proposal. It does
not establish that the substrate invents the opposition relation, derives the
cue vocabulary, learns from examples, or autonomously chooses a repair family.
The action-to-vector encoding is evaluation-side task measurement and is not
credited as substrate learning.
