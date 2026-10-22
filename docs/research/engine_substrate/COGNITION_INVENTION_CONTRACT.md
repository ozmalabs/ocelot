# Process invention and effect evidence contract v1

Status: semantic freeze for P9.01–P9.E3. Existing process operators and seed files are implementation inputs, not claims that every operator passes the contracts below. Invention policies remain opt-in.

## 1. Exact algebra and operator boundaries

A permutation maps the content at index `i` to index `p[i]`; `compose(a,b)` means apply `a` then `b`, so `c[i] = b[a[i]]`. A matrix acts on integer column vectors and composition is `B·A`. A matrix inverse is exact only when the integer matrix is unimodular (`det = ±1`). Integer deltas have exact inverse by negation. Sequences preserve application order; identity and inverse are exact only when every child is supported and exact.

The finite operator set is inverse, compose, conjugate, commutator, power-2 and power-3, plus bounded square-root search. Every candidate records operator, parent IDs, cost, type, source/model/frame epochs, effect evaluation and verification receipt. Search is bounded by operator pairs, process depth/root candidates, probes and approved round budget. A restart uses the same unique round/debit identity and cannot spend again.

## 2. Equivalence, novelty and adoption

Exact equality is available only for fully represented supported process values and complete effect fingerprints. A finite incomplete probe set yields `probe_equivalent`, never exact identity. Collisions preserve both candidates and request a separating probe; they cannot deduplicate a candidate or establish a law. Adoption requires declared-domain verification on fresh states and exact matching source/model/frame epochs. The cheapest verified representative may be selected only inside one exact equivalence class.

Composition order, inverse law, conjugation and commutator are checked against native effects, not operator names or templates. Conjugation closure terminates only when every bounded supported conjugate is either exactly known or explicitly unresolved; the root/pair/depth cap cannot be exceeded to force closure.

## 3. Repair and irreversible effects

Repair-to-equivalence is a separate candidate type from an inverse. Its contract names a goal predicate/equivalence relation, allowed initial-state domain and terminal evidence. A repair may be many-to-one or irreversible; it must never be advertised as an exact inverse. It requires actual detached evaluation and fresh-state re-verification before adoption. No external action is emitted by the evaluator.

## 4. Finite stochastic outcomes

A supported stochastic effect is a finite distribution `[(outcome, p)]` with unique typed outcomes, finite probabilities in `[0,1]`, total support at most one, and explicit unknown mass `1 - Σp`. Exact distributional equality requires complete support from the declared finite model. Empirical frequencies retain sample count, confidence method and unknown mass; they are not promoted to exact laws. Insufficient samples, omitted outcomes, or unsupported probability terms produce `UNKNOWN`, not a point estimate or deterministic fingerprint.

## 5. Invariants and walls

A complete algebraic proof over a declared representation is `proven`; evidence from a finite sample is only `witnessed`. Parity, conserved counts/sums and determinant tests must specify the domain and supported action family. A wall explanation ties the target mismatch to a proven or explicitly witnessed invariant. A breaker must change the required invariant and pass fresh effect verification. Partial probes cannot prove impossibility or equivalence; absent breakers yield an honest impasse.

## 6. Acceptance and controls

- `test_compose_order`: native sequential effects match the frozen order for permutations, matrices and process sequences.
- `test_noninvertible_no_inverse`: singular/non-bijective processes return no exact inverse.
- `test_repair_not_exact_inverse`: a verified goal-equivalent repair remains a repair record and never enters inverse identity.
- `test_finite_probe_collision_not_law`: equal fingerprints on an incomplete probe set retain both processes as unresolved.
- P9.02 additionally checks all six core operators, 3-cycle/dihedral closure, precise conjugation law, round-budget debit uniqueness and restart bounds.
- P9.03 checks parity walls, invariant-changing breakers, partial-probe nonproof and honest impasse.
- P9.04 checks fresh repair verification, exact-inverse refusal, distribution support/unknown mass and epoch invalidation.

Controls include malformed terms, aliases with distinct exact effects, stale receipts, duplicate requests, denied/expired budget, tampered verification criteria, noninvertible transforms and truncated distributions. A missing evaluator or verifier remains unsupported and cannot be substituted with `None`, identity or zero cost.
