# Cumulative learning and scheduled checkpoint contract (P27)

**Version:** P27 scheduled-checkpoint successor v1. **Status:** specification only; no heldout allocation is frozen by this document. **Date:** 2026-10-25.

## P22 disposition and successor decision

The original P22 protocol is **not freeze-ready**. Its preregistration remains `DRAFT — NOT FROZEN`; descendant/checkpoint/resource prerequisites are incomplete, and its approval criteria remain exact candidate-specific decisions. P23 found finite but incomplete search support and unresolved historical attempt detail. P24 required a new version after its v1 analyzer failed; the v2 result establishes bounded common-target learning only. P25 found simulator-specific retention but all arms remained at floor on the unseen task. P26's valid heldout draw failed the registered residual-selection advantage gate and produced no verified search effect, approval, or receipt. These facts do not prove P22 impossible, but they do not repair or satisfy its original gates. No old P22 allocation or outcome is re-entered, rescored, or treated as P27 evidence.

P27 is therefore a **separately versioned scheduled-checkpoint successor**, justified because it can evaluate fixed intervals without requiring a beneficial adoption to occur. It tests measured cumulative state and independent-goal behavior. It is not a continuation or successful completion of P22's recursive-improvement hypothesis.

## Checkpoint identity and estimands

An interval is identified by `(phase, arm, ancestor_checkpoint_id, checkpoint_index, cumulative_charged_primitive_work, cumulative_source_exposure, cumulative_native_rule_steps, cumulative_graph_bytes)`. The scheduled indices are `g0`, `g1`, `g2`, `g3`, with cumulative work markers `[0, 1000, 2000, 4000]` and cumulative task-world access markers `[0, 1, 2, 4]` for this simulator protocol. Readiness is triggered by either fixed charged-work or task-access markers, never by candidate quality, approval, adoption, or a score. Each checkpoint records a content hash of the actual serialized learner state and a parent hash linking it to the prior checkpoint. If no state changed, record the unchanged hash and zero state delta. If search failed, no candidate qualified, or authorization is pending, capture that interval with its actual status and spent resources. Do not synthesize an adoption or approval.

The four frozen arms are: frozen ancestor; evidence-selection only; process-search only; and combined. All use the same primitive/model interface, fixed task/world allocation, per-arm work ceilings and scheduled checkpoint thresholds. Each arm owns its own persistent learner state and ancestry. No state may be copied between arms after g0. Evaluator access is read-only and cannot feed outcomes back into training.

At each checkpoint, evaluate the same sealed common worlds and goals using the actual checkpoint state. At the final checkpoint, also evaluate a separately allocated fresh validation panel. Keep every world, including all-failure, all-success, missing, invalid, no-change, failed-search and authorization-pending records. Missing output is a failure in the score denominator and remains visibly missing. Cluster inference by world and preserve pairing to the frozen ancestor.

The registered capability estimand is paired final success difference for combined versus frozen ancestor; the scheduled trend is the slope over `g0..g3` in that same paired difference. Evaluate the evidence-selection-only and process-search-only component contrasts as preregistered secondary causal claims, with Holm correction across all named family/outcome tests. The P27 phase-level gate remains the plan's declared one: primary final gain at least 0.10 and at least 0.05/checkpoint slope, with one-sided 99% lower bounds above zero after Holm correction. No alternate metric may be selected after results. Any positive result still applies only to the tested finite simulator families.

Efficiency is a separate estimand and is reportable only when arms have matched primitive work, source exposure, native-rule work and memory accounting under the preregistered tolerances. If costs differ, report the difference descriptively and mark efficiency `NOT_ESTABLISHED`; do not normalize away the cost difference.

## Authority, data, and resource boundaries

Scheduled capture and evaluation confer no action authority. An authorization-pending candidate remains pending; it is never executed, adopted, converted into a receipt, or used to satisfy a checkpoint. Existing expression/transition-specific approvals remain unchanged. Heldout/validation worlds and scores are invisible to training, selector, search, and checkpoint readiness logic. Each phase version must list all concrete train, validation, heldout and control seeds and show disjointness from P16–P26 and prior P27 allocations before its preregistration-only freeze.

Every checkpoint preserves complete ancestry, serialized state hash/bytes, cumulative and interval deltas for work, native rules, graph size, source exposure, budget debits, task/world access, proposals, qualifications, approvals, receipts, and missing/pending/error status. Restored branch work is charged cumulatively; restart must not reset counters or schedule. Memory ceilings apply to the complete dynamic graph and serialized snapshot, not just newly added nodes.

## Freeze and interpretation rules

P27.01 is specification only. P27.02 and P27.03 must pass structural and causal integration gates before P27.E2. E2 creates a new runner, analyzer, seed closure, and standalone preregistration commit; all families, tasks, arms, checkpoints, controls, missingness rules, hypotheses, thresholds, resource limits, tests and source/build/runtime hashes must be frozen before access. E3 runs the allocation once and publishes every estimate, interval, stratum, control, resource total, status and artifact hash. An implementation defect after access requires an untouched versioned allocation; it cannot be repaired by rescoring.

No-change and failed intervals are required observations, not grounds to cancel or redraw. Completion of the protocol is not itself evidence of acquired ability. A P27 result cannot erase P20/P21 failures, P25's transfer floor, P26's negative selection result, or P22's draft status. Human equivalence, physical grounding, broad process synthesis, and general capability claims remain outside this contract.
