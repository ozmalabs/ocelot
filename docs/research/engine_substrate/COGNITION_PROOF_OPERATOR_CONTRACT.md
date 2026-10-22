# Proof and invention-operator contract

**Status:** P14.01 specification, frozen 2026-10-22 before implementation. This contract constrains later P14 work; it does not claim that the current engine proves process laws.

## Law vocabulary and boundary

A law statement is a typed predicate over a declared process family. It names the exact family/model identity, state and transition representation, quantified variables and domains, and explicit assumptions. Quantification is finite and bounded unless a separately reviewed proof backend declares a stronger supported fragment. A checker may return `checked`, `rejected` with a counterexample, or `unsupported`; timeout, missing assumptions, and finite observations never count as a proof.

An **empirical invariant** is a regularity observed in a bounded set of traces, with source identities and sample bounds. It can guide experiments and be recorded as a conjecture, but it is not a theorem and cannot satisfy a proof obligation. A **conjecture** is a law candidate with its assumptions and evidence attached, but no accepted machine proof. A **checked theorem** is a conjecture for which the declared checker validates the exact statement under the exact assumptions and process-family identity. A counterexample rejects or downgrades that candidate; it does not silently edit the law or its assumptions.

Proof references bind the statement digest, assumption digest, checker/version, family/model digest, and relevant process/model/frame epochs. Any change to a bound input invalidates the proof reference. The checker must fail closed on unsupported syntax, unbounded domains outside its declared fragment, missing assumptions, stale epochs, and mismatched family identity. P14.02's only checked inference is the graph-resident structural rule for an exact permutation commutator constructor with same-family active arguments and the parity-homomorphism assumptions. This rule checks exact constructed parameters; it does not introduce a general theorem prover. P14's finite fixtures establish only this declared finite fragment. No general law follows from absence of a sampled counterexample.

## Operator authorship and immutable boundaries

An authored invention operator is data describing a bounded combinator over the held process algebra. It carries author/provenance, source process identities, a content digest, declared preconditions/effects, resource caps, development-split measurements, proof obligations, and a full parent/rollback lineage. Candidates run in a sandbox under the same transition semantics, resource limits, criteria and proof obligations as held operators. A candidate cannot write the verifier, checker, evaluation harness, held-out allocation or labels, criteria, approval records, or another candidate's immutable evidence.

Candidate selection uses only the development split. Promotion is a separate lifecycle transition and requires the existing human approval gate where the existing authorship/criterion policy requires it. A measured positive development yield is necessary but insufficient: invariant checks cannot regress, held-out results remain untouched until the registered evaluation, and failed or rejected candidates retain their evidence and lineage. No model-authored source code or direct engine mutation is part of this interface.

Law and operator-authorship policies remain disabled by default. Explicit cognition-on registration may enable bounded candidate/proof work after focused validation. Proof establishes mathematical behavior only within the declared model; it does not authorize an external action, adoption into an unregistered domain, or a capability-level claim. Existing action/manifold authorization and adoption gates remain independent.

## Phase ordering and acceptance

P14.01 freezes this vocabulary and boundary before implementation. P14.02 may add checked finite-family laws while retaining unsupported and false candidates as non-theorems. P14.03 may require checked proofs only for explicitly registered proof-admitting domains and must retain separate action authorization. P14.04 may propose bounded graph-authored combinators under frozen criteria and the existing human gate. P14.E2 must register the development and untouched evaluation splits before any held-out run.
