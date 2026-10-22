# Independent-goal improvement contract

**Scope:** P22.01 specification. It governs claims about improvement across independently generated tasks and generations. The P21 retention and curriculum effects both failed at ceiling; neither is treated as a learning benefit or used to tune this protocol. P15's operator-aligned result remains bounded to its declared finite family.

## Independent goals, splits and checkpoints

Task-world identity is generated from a frozen family generator, a split namespace, and a world seed. Generation/checkpoint index never enters the goal, world dynamics, scoring key, or held-out label. Every checkpoint is evaluated on the same sealed world IDs, and every paired arm receives a fresh isolated copy of each world. Training, curriculum selection, development qualification, validation, and sealed evaluation use disjoint seed blocks. Candidate names, operator powers, and expected improvement cannot influence goal generation. A family is claimed only after the same world adapter produces real outcomes for all matched arms in development.

The frozen ancestor is copied from the declared starting checkpoint for every world and generation. It does not receive candidate updates. Adaptive checkpoints are immutable snapshots with parent digest, candidate expression digests, active portfolio, task provenance, approval events, proof/adoption/grounding records, cumulative work, memory, and rollback disposition. A failed, stale, timed-out, rejected, or rolled-back generation remains in the lineage and denominator. Human edits invalidate autonomous-generation attribution.

## Arms and equal resources

The primary arms are unchanged ancestor, adaptive curriculum with the ancestor portfolio, and full improvement with native proposal/verification/promotion. They start from independent copies of the same ancestor and share identical task worlds, primitive interfaces, model-query opportunities, action ceilings, and cumulative primitive-work budgets. Curriculum and invention costs count against those budgets. Each agent uses one shared ThinkingBudget; denial, retrieval, proof search, approval, rollback and failed work are recorded. A success comparison at unequal work remains a capability outcome only; no efficiency claim is made unless paired work is equal within the prespecified tolerance.

Existing approval is candidate-specific. The historical P15 approvals for `commutator_square_v1`, `commutator_cube_v2`, and `commutator_fourth_v3` apply only to those expressions and their frozen criteria digest. Any different expression, parameter, guard, domain, or criteria digest that reaches a world-action path requires a new exact approval event. The evaluator may test an unapproved candidate in a non-actionable verification world, but cannot grant its approval.

## Estimands and inference

For each family, world ID, and generation, record paired bounded scores for the full checkpoint and unchanged ancestor on the same world. The generation-specific effect is the mean of candidate-minus-ancestor paired score differences. The primary final effect is the generation-3 paired mean, which must be at least `+0.10`. The trend estimand is the ordinary least-squares slope of the per-generation paired means over ordered generations 1–3; its one-sided 99% lower bound must exceed zero. A claimed family must satisfy both criteria. Holm correction controls the one-sided family-level tests at `α=.01` across all claimed families.

Inference resamples whole world IDs as clusters, preserving that world's repeated checkpoints and arms. Use 10,000 deterministic bootstrap resamples with the seed fixed in the preregistration. Report paired differences, per-checkpoint rates, Wilson intervals, exact McNemar tests, the slope, and corrected bounds. For all-success, all-failure, or flat paired scores, the paired effect and slope are exactly zero; the result is a valid no-improvement outcome, not an undefined model fit. Missing pairs, duplicate world-arm rows, or inconsistent world identity make the affected estimate `NOT_ESTABLISHED`.

At least three promoted generations are needed for a recursive-improvement claim. Each claimed family and generation must have at least 200 common sealed worlds, plus at least 200 fresh validation worlds, with the same task identities across arms and checkpoints. Use the same sealed evaluation panel at each checkpoint; do not fit on it. Report all families, checkpoints, failures, approval costs, wall time, primitive work, native steps, model calls, graph/memory footprint, and rollback events. A positive score trend does not establish efficiency or human-relative performance.

## Safety, provenance and claim boundaries

Proof bindings, expression digests, adoption events, source/model/frame epochs, independent action receipts and grounding checks must pass for every external transition. Any false proof, stale binding, unauthorized action, label leak, world-state mismatch, or rollback failure is a zero-tolerance phase failure. Revocation suspends dependent tasks. Unknown adapters are `UNSUPPORTED`; missing outcomes are `NOT_RUN`; timeouts remain failures or unknowns and cannot be replaced. No human baseline exists for this task family until a protocol-matched source is cited or a prospective procedure is frozen.

No capability level closes from a finite task family. P22.04 must map each L-level to demonstrated input breadth, exact native consumers and held-out evidence, retaining unsupported raw perception, irregular-time handling, opaque motor skills and general language as open where no evidence exists.
