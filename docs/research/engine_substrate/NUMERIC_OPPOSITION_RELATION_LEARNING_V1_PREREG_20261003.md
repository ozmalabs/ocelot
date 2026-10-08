# Numeric opposition relation learning v1 preregistration (2026-10-03)

## Question

Can the substrate's size-ordered term synthesizer infer a numeric opposition
predicate from labeled examples, then generalize the frozen term to unseen
numeric vector pairs without receiving the target relation formula?

## Frozen design

Run five fresh-process replicates. Each receives eight positive and eight
negative training examples sampled from integer vector pairs with a frozen
seed and a declared balancing rule. The input variables are `ax`, `ay`, `ex`,
and `ey`; the binary target is 1 exactly when the expected vector is the
componentwise negative of the actual vector. The learner receives only the
training examples, a fixed grammar (`Neg`, `Eq`, `And`), no constants, maximum
term size 9, and a 12-second synthesis budget. No target formula, relation
name, action labels, or held-out examples enter synthesis.

After synthesis returns, freeze the resulting Term and evaluate it against all
1,296 combinations drawn from the Cartesian product
`{-2.5,-1.5,-0.5,0.5,1.5,2.5}^4`. This held-out grid contains 36 positive and
1,260 negative cases, is disjoint from the integer training domain, and is
scored only after synthesis. Report target-term structure, size, enumerated
term count, wall/CPU time, halt reason, exact held-out confusion counts, and
source/build hashes. A timeout or absent solution is a measured failure, not
an excluded worker.

## Gates

- Exactly five locked workers complete; every source/build hash is stable and
  current.
- Every returned Term fits all 16 training labels and obeys the fixed
  vocabulary/size cap.
- Held-out results are reported per worker and pooled; no post-hoc resynthesis
  on held-out errors.
- Preserve raw training panels, frozen held-out domain, candidate ASTs,
  counters, timing, and analyzer checks.

## Interpretation limits

This is supervised synthesis of one authored numeric relation over a small
fixed grammar. The evaluator supplies correct labels; the grammar already
contains the needed logical/arithmetic primitives. It does not show autonomous
task discovery, vocabulary invention, relation acquisition from unlabeled
experience, or transfer to a different relation family. Five training draws
and one held-out numeric domain are evidence about this relation only.
