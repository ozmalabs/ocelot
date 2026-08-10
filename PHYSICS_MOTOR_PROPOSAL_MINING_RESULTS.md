# Physics and analogy driven motor proposal mining — results

## Outcome

The residual-to-motor-proposal seam is now implemented as a general graph
faculty in `embodied_physics_proposal`.

A failed learning-plan prediction can now:

1. open an `EmbodiedPhysicsQuestion` over a categorical, body-relative desired
   state change;
2. retrieve partially overlapping output-null motor-plan stages with
   `ShapeDecode`;
3. recruit the existing arbitrary-order, receipt-verified program trajectory
   search;
4. either publish a viable known path or synthesize a previously unseen,
   arbitrary-width compound from one receipt-learned command per independent
   effector group;
5. forward-project that compound as a testable six-coordinate integer Pareto
   point while it still has no output authority;
6. let curiosity choose one surviving experiment without granting actuator
   authority;
7. expose one selected compound outcome to the existing motor collapse only
   after the dynamic structural-envelope check; and
8. use the ordinary physical receipt to promote a reusable shape memory or
   retain a body-contextual counterexample.

The developmental adapter now routes by the capability's requested observable
evidence and body-state signature. Goal labels are not consulted when choosing
commands or assembling a compound. A supported half-turn can therefore be
expressed through relations among support topology, orientation, angular
momentum, compound effector coupling, and rising/falling height energy without
joint names, a pose, a token sequence, or an authored motor command.

## Guardrails

- All new cognitive values are integer quanta. The generated faculty and its
  recursive term tree contain no floating point values.
- The Pareto point keeps predicted evidence, discrimination, novelty, energy,
  peak load, and recoverability separate. `scalarized=0` is explicit.
- Analogy nodes, questions, proposals, and retained memories all have
  `output_authority=0`.
- A novel compound may be proposed from receipt-grounded components, but its
  predicted consequence is explicitly distinct from physical verification.
  Dynamic structural limits are rechecked by the existing motor-release guard;
  proposal selection cannot bypass it.
- A failed receipt disables only that proposal in its observed body/question
  context and stores the counterexample. It does not create a global taboo.
- Successful proposal memories remain hints and require local verification on
  another body.
- Positive proposal shapes, body-relative shape evidence, and contextual
  counterexamples survive the version-12 motor-library round trip as
  output-null integer graph facts.

## Verification

`tests/test_embodied_physics_proposal_migrated.py` covers:

- recursive integer-only manifest validation;
- the rolling body-state relation contract;
- residual-to-question creation and transitive faculty loading;
- retrieval from the real motor-plan hint library;
- complete six-coordinate proposal construction from a verified two-step
  trajectory;
- output-null curiosity selection;
- physical-success promotion and residual closure; and
- agent-level, dual-shape warm recall across a structurally overlapping body;
  and
- physical-failure contextual negative memory retained at agent level.
- unseen three-effector synthesis, forward projection, Pareto selection, and
  single-outcome release without a recognized goal label; and
- durable positive and negative proposal knowledge across lifetimes.

Focused graph result: **27 passed, 1 optional PyBullet test skipped**.

The real PyBullet developmental smoke run also completed from the declared
supine fixture with the Rust graph owning policy. It generated receipt-grounded
consequence evidence across the 43 opaque actuator commands, advanced three
developmental stages, and produced four support alternations. This is an
end-to-end adapter/physics check, not a claim that the short smoke curriculum
reached independent walking: it remained non-upright at the end. The run is in
`results/humanoid_counterfactual_physics_smoke.json`.

The 360-action curriculum run is recorded in
`results/humanoid_counterfactual_physics_curriculum.json`. It closed 360
physical developmental receipts, advanced five stages to the body-relative
side-lying transition, and observed 48 support alternations. It did not yet
create the rolling learning-plan residual needed to invoke the new physics
question naturally. The synthesis/release seam is therefore demonstrated by
the deterministic graph integration test, while the longer run separately
validates that its learned integer inputs originate in the real simulator. A
claim of autonomous physical rolling would be premature.
