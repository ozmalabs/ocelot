# Cross-family ranker null-transfer probe v1 — preregistration

**Date:** 2026-10-02  
**Question:** Does the production graph-resident ranker remain unchanged when given real typed outcomes from a different correction family with no shared target or outcome class?

## Design

Three fresh workers construct the faulted `classify_kind_family` candidate set and compose the actual `self_correct_rank_*` Program. Each captures the production ranker's order with zero prior outcomes. The worker then receives the complete per-candidate training outcome records from the source-locked recurrence candidate-admission capture, and ranks a fresh copy of the same control-kind candidate set. The recurrence records contain the target `mrl_offer_due_once`, the `idempotent_mint_guard` and `episode_scoped_idempotence` classes, and their measured training utilities. Control-kind uses target `classify_kind_family` and has no candidate outcome classes.

Workers capture both orders and candidate digests before the independent analyzer joins the order to control-kind held-out utility. The recurrence capture is input data only; the worker does not read or receive control-kind held-out results. Measure order equality, per-candidate prior counts, first-candidate utility after the join, and rank-call elapsed time. This is an interface-boundary probe, not the four-family confirmatory panel.

## Interpretation

The prediction from the ranker's current exact-target/shared-class matching implementation is that every control-kind candidate receives zero prior successes and failures, so experience order equals cold graph rank. If observed, this validates the negative transfer boundary while also showing that the substrate cannot exploit cross-family outcomes for these descriptors under the current label schema. Do not assign a shared class after this result. The separate confirmatory panel must retain the null cases and report them by family.
