# Thoughtexperiment cross-family idempotence transfer v2 — preregistration

**Date:** 2026-10-01  
**Question:** Can outcome transfer correct a measured cold-ranking error when the recurrence task contains multiple due candidates and the smallest edit is under-scoped?

## Task and decision

Train on the actual shape-axis `dedup_identity_fix` outcome, tagged `idempotent_mint_guard`. In a separate recurrence-ledger task, remove only `mrl_offer_due_once`'s candidate-level existence guard and provide two due candidates in one episode. The candidate generator offers (a) `episode_scoped_offer_guard`, which blocks the second candidate after the first offer, and (b) `dedup_identity_fix`, which guards each candidate independently. The task oracle requires exactly one offer for each of the two candidates and zero-progress closure. Thus the episode-scoped option is an explicit under-general repair even if its edit footprint is smaller.

Each of three workers runs the actual training correction followed by cold and transferred-evidence recurrence episodes on fresh graphs. Candidate order is decided by the graph-authored Program. Each candidate is applied only on a full-copy branch; the independent oracle decides whether to continue to the next candidate. Transfer records are derived from candidates actually tried during training and explicitly copied to the recurrence treatment graph.

## Gates

- Three fresh workers, stable source/native fingerprints, and graph-authored rank Programs in both arms.
- Training adopts the axis repair and emits a successful `idempotent_mint_guard` outcome.
- The recurrence candidate generator emits both the episode-scoped and candidate-scoped fixes.
- Cold arm ranks the episode-scoped guard first; its branch fails the two-candidate oracle, then a later candidate passes.
- Transfer arm records at least one cross-target prior success for `idempotent_mint_guard`, ranks the candidate-scoped repair first, and passes in one trial.
- Both arms ultimately pass the same independent oracle, and branch rehearsal leaves each primary unchanged.

## Interpretation limits

This measures whether an explicitly authored outcome class changes ranking under a deliberately discriminating two-candidate oracle. Candidate classes, repairs, and utility labels are authored; transfer transport is host-managed. It is not autonomous invention, natural-task prevalence, or broad learning. If the preregistered cold error does not occur, report the panel as a negative ranking result rather than weakening the gate.
