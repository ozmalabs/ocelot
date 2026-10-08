# Contract query scaling and misspecification v1 — preregistration

## Questions

1. How do native Term evaluations and wall time for maximum-entropy input selection change as the finite hypothesis set and expression depth grow?
2. Does the selector report when no supplied hypothesis fits, and can it distinguish a unique finite-set survivor from the true target when the target is observationally aliased on selected probes?

## Scaling design

Build binary-coded hypothesis families at H=8, 32, and 128 (two fresh workers each). Each hypothesis is a nested `IfThenElse` Term of depth K=log2(H), encoding one bit at each of K special integer inputs. All hypotheses agree on the initial observation x=0. Candidate inputs contain the K informative points plus 3K decoys. A hidden candidate target is labeled only after the selector proposes an input. The selector receives Terms, previous observations, and candidate inputs, but not the target ID or labels in advance. Compare 2,000 seeded random query orders at every size.

## Misspecification design

At H=32, run two fresh workers with the same version space:

- **Observational alias:** the external target matches a supplied coded hypothesis on all K informative probes and initial input, but differs by +100 at the last decoy. Measure whether the finite-set selector reaches a singleton and whether an independent held-out check exposes the error.
- **Initial contradiction:** the external task label for x=0 is 1 while every supplied hypothesis predicts 0. Measure whether the selector returns an empty consistent set instead of a candidate.

The misspecification target and independent output oracle are harness-side; the query selector sees only candidate Terms and the observations returned after each query.

## Measures and gates

Record source/runtime hashes, fresh process IDs, expression depth, candidate count, input count, selector native-evaluation call count, query count, per-call and total elapsed time, and RSS. Independently reproduce maximum entropy, target labels, model consistency, and random baselines. Require exact selection of the expected K informative queries at each scale, target identification for closed-set cases, empty-set refusal for the direct contradiction, and explicit disclosure of false singleton confidence under the observational alias. This is a finite synthetic scaling study, not an asymptotic theorem or natural-task estimate.
