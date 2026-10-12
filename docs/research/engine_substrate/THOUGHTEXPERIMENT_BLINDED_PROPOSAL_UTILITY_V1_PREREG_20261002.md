# Thoughtexperiment blinded proposal utility v1 — preregistration

**Date:** 2026-10-02  
**Question:** Can the substrate's graph-resident experience-conditioned ranker select useful candidate changes on fresh correction tasks better than fixed, random, and target-specific memoization policies, when task-utility labels are kept outside the candidate-producing process?

## Scope

This is a staged delegation-boundary evaluation. The host continues to enumerate the finite candidate changes using the existing correction candidate generator. The substrate receives only candidate descriptors and prior outcome records, then orders the candidates through its graph-resident ranking Program. An independent parent evaluator computes task utility from held-out task behavior only after the candidate ordering has been emitted. A positive result establishes experience-conditioned selection over a host-enumerated space; it does not establish autonomous candidate generation, oracle discovery, or general self-improvement.

## Fixture admission before capture

Admit at least four independently authored correction-task families. Each family must have:

- a distinct target rule and task specification, with a task-specific held-out continuation oracle implemented outside the substrate worker;
- at least three nonidentical candidates produced by the unchanged `_default_candidates` path, including at least one successful and one unsuccessful candidate under the independent oracle;
- a stable candidate descriptor derived from the proposed rule bundle, not from its measured utility;
- disjoint training and evaluation instances, with evaluation instances generated from a preregistered seed list;
- an explicit mapping from candidate execution to full experiment cost (candidate trials, branch/snapshot time, prediction time, and adoption/verification time).

Before starting the confirmatory panel, record the admitted family names, source hashes, candidate descriptors, seed schedule, and oracle hashes in the lock. If fewer than four families meet these checks, do not reduce the family count silently: report fixture insufficiency and amend this protocol before capture.

## Panel design

Use four fresh worker processes per family and a fixed, interleaved arm schedule. Each worker has a training phase and evaluation phase. The training phase executes every candidate on training instances and sends only typed outcome records to the evaluation worker. Evaluation uses new substrate instances and held-out instances. The evaluator retains the utility oracle and returns no labels until the candidate order is frozen and captured.

Compare these policies on the same evaluation instances:

1. **Experience rank:** the substrate graph-resident rank Program uses outcome records from the other training instances/families; evaluation-family outcome records are excluded.
2. **Frozen rank:** the same Program and graph vocabulary with all outcome counts zero.
3. **Default order:** candidates in the unchanged generator order.
4. **Random order:** a deterministic shuffled candidate order from a preregistered seed, independent of utility.
5. **Target memoization:** reuse the most successful training candidate only when the evaluation target-rule identity matches exactly; otherwise use default order. This bounds a simple lookup baseline without granting cross-family transfer.

### Pre-lock transfer-interface audit

The current `rank_candidates` implementation first looks up records by exact `(target_rule, candidate_label)` and uses an explicit `outcome_class` aggregate when a candidate has one. The admitted fixtures expose a limited, asymmetric transfer surface: shape-axis and recurrence both label `dedup_identity_fix` as `idempotent_mint_guard`; navigation and control-kind candidates have no matching cross-family class, and their target rules are distinct. Thus cross-family experience can affect the idempotence pair, while the graph ranker should remain at its zero-history behavior on navigation and control-kind under this protocol. Preserve these authored class labels as preregistered metadata; do not invent or modify classes after observing policy outcomes. Report per-family effects even if the experience arm is mechanically equivalent to frozen rank for some families.

No arm may receive held-out outputs, evaluation-family labels, or scorer code before its complete candidate order is recorded. Failed experiments remain in the capture and count toward cost. The primary analysis is paired by worker, family, and held-out seed.

## Measures

Report, per arm and family:

- first-candidate utility and full held-out pass rate;
- candidate trials and false-adoption rate;
- total experiment cost, separated into branch creation, prediction, scoring, and adoption/verification;
- transfer distance: whether the training and evaluation target rules, candidate digests, and outcome classes match;
- abstentions, invalid proposals, and unresolved tasks;
- candidate-level provenance linking descriptor, prior record set, emitted rank trace, branch result, and independent oracle score.

Primary contrast: experience rank versus the best of the four controls on paired held-out first-candidate utility and candidate trials. Also report each control separately; do not collapse the controls into a single favorable baseline. Confidence intervals must resample task families as clusters, with worker/seed results nested within each family.

## Integrity and gates

- All family, worker, task, runner, analyzer, protocol, and native-build hashes match the pre-capture lock.
- At least four admitted families and four fresh workers per family complete without source drift.
- Candidate order is captured before the evaluator releases each held-out utility label.
- The independent scorer recomputes every candidate outcome from held-out behavior and matches the recorded task oracle.
- All five policies receive identical evaluation candidates and held-out instances.
- Primary graph state is unchanged by rehearsal; adoption is separately measured and occurs only after an accepted candidate receipt.
- Candidate-level accounting reconciles to family and arm totals, including failed/abstaining runs.
- Every admitted family has at least one successful and one unsuccessful candidate, preventing an uninformative all-easy or all-impossible family.

Any failed gate invalidates the confirmatory claim. Preserve the raw capture and report failed gates; do not remove a family or policy after seeing outcomes.

## Interpretation thresholds

- **Selection signal:** experience rank improves paired first-candidate utility or reduces candidate trials relative to frozen rank and default order, without a higher false-adoption rate.
- **Transfer signal:** that improvement remains when evaluation target rules and candidate digests differ from training records, and beats target memoization.
- **Economic signal:** report the full cost ratio against each control. A reduction in trials is not a cost win if total measured experiment cost rises.
- **No self-improvement claim:** even if all thresholds pass, candidate enumeration remains host-authored and oracle judgments remain evaluator-authored. The next delegation step is to move a bounded candidate-generation operator into the substrate and repeat the same separated scoring protocol.

## Required artifacts

Before capture, add a lock and runner under `evaluation/substrate_capability/`. After capture, preserve raw worker records, independent analysis, and results here. Update the capability map and overall status with both positive and negative results.
