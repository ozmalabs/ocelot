# Thoughtexperiment blinded proposal utility v1.2 — randomization and cost semantics

**Date:** 2026-10-02  
**Status:** clarification before full-panel lock and capture; no four-family orders or held-out scores exist.

## Random order seeds

The five-policy panel uses a fixed seed for every family/worker pair:

- shape-axis: 420001–420004
- recurrence: 420101–420104
- navigation: 420201–420204
- control-kind: 420301–420304

Seed mapping is `420001 + 100 * family_index + worker_index`, with family order `[shape_axis, recurrence, navigation, control_kind]` and zero-based workers `[0,1,2,3]`. The lock and every order record preserve the actual seed. Shuffling uses Python's deterministic `random.Random(seed).shuffle` over the unchanged generator order.

## Cost schema

Every task setup and candidate evaluation records nanoseconds for:

- context setup and candidate enumeration (separate fields; setup excludes the measured generator call);
- policy-order construction, including ranker graph setup, record insertion, rank evaluation, or the applicable baseline-order operation;
- isolated branch creation, candidate patch application, task-oracle scoring, and receipt verification;
- per-candidate total and per-policy sum.

Training-label production is measured separately. Report experience's required other-family training cost and target memoization's same-family training cost; do not count either as free. Also report the common experimental acquisition burden separately from per-policy costs.

The task graph remains unchanged. Candidate trial branches use the native full-copy fork, except shape-axis, which uses the existing thoughtexperiment snapshot path; both branch types and their setup costs are explicitly labeled. Receipt verification checks that the candidate rule bundle was applied to that isolated branch and that the direct task oracle passed. The panel does not commit candidate rules to the primary graph, so production adoption/commit time is outside this selection experiment and must not be included in a claim about production end-to-end savings.

If any phase cannot be timed or reconciled, preserve it as unavailable, fail the economic gate, and still report the utility/order result at its narrower scope. The analyzer must reconcile each policy total to setup, order, training acquisition where required, and its actual attempted candidate branches.
