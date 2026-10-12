# Thoughtexperiment blinded proposal utility v1.1 — arm information boundaries

**Date:** 2026-10-02  
**Status:** protocol clarification before panel lock or capture  
**Supersedes:** no v1 outcomes; v1 has no four-family panel capture.

## Reason for amendment

The v1 description says experience rank must exclude evaluation-family outcomes, but does not say whether target memoization may read that family's disjoint training outcomes. Treating the controls as if they shared one information boundary would make the target-memo arm either unavailable or a duplicate of default order. This amendment fixes the information sets before the confirmatory lock. No panel candidate orders or held-out utility outcomes have been captured.

## Frozen information sets

For evaluation family `f`, each of its four workers has a train split and a disjoint held-out split. Candidate enumeration, the train/held-out task instances, candidate descriptors, and scorer implementations are fixed in the panel lock. Rank orders are emitted and persisted before the separate scoring stage is allowed to load held-out labels.

| Arm | Permitted outcomes at order time | Policy |
|---|---|---|
| Experience rank | Training outcomes from the other three families only; no outcomes from `f` | Actual graph-resident `rank_candidates` program with those typed records |
| Frozen rank | No prior outcomes | Same graph-resident program and candidates |
| Default | None | Unchanged `_default_candidates` order |
| Random | None | Uniform deterministic permutation from a family/worker seed fixed in the lock |
| Target memoization | Training outcomes from `f` only | Pick the best observed candidate for the exact target identity; ties use unchanged generator order; if no positive candidate exists, use default order |

Target memoization is deliberately the only arm that reads evaluation-family **training** outcomes. It is a within-family lookup control, not a source of evidence for cross-family transfer. No arm sees held-out outcomes or the scoring code before all orders are frozen. The primary experience-versus-control comparisons therefore test whether cross-family records help beyond a zero-history graph ranker, fixed order, random order, and a stronger same-target training lookup.

## Cost and accounting clarification

For every family, worker, arm, and candidate, record wall-clock nanoseconds for candidate enumeration, rank/order generation, branch or snapshot creation, task execution/scoring, and adoption verification separately. Candidate branch cost is measured in the independent scoring stage; rank-order cost excludes process boot but process boot is reported separately. Report both attempted-candidate count and end-to-end elapsed time. If the implementation cannot isolate one of these costs, mark it unavailable and do not claim an economic advantage. Failed and invalid candidate runs remain in the denominator.

Training-label production is measured and reported separately from evaluation cost. A cost comparison may not treat externally computed training labels as free. The five policy orders must use identical descriptors and held-out instances, and the analyzer must reconcile every cost row to its raw worker record.

## Required pre-capture checks

The panel lock must include hashes for this amendment, v1 protocol, fixture audit, all task/oracle sources, the ranker and candidate generator, runner and analyzer, native engine binary/build identity, task seeds, random seeds, and the full candidate-descriptor matrix. The lock must state all four family worker IDs, policy information sets above, and the complete cost schema. Capture remains no-go until the audit verifies these fields and each family's disjoint train/held-out instances.

If any family cannot supply a disjoint task split or complete candidate-level utility oracle, preserve the failed admission result and amend before any panel capture. Do not drop the family or reinterpret an existing utility capture as a blinded panel.
