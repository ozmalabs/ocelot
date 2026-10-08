# Thoughtexperiment automatic outcome persistence transfer v1 — preregistration

**Date:** 2026-10-01  
**Question:** Do outcomes written by the production `scan_and_self_correct` path persist in the primary graph and influence a later thoughtexperiment branch without host construction or transport of outcome rows?

## Design

Each of three fresh workers prepares the graph-authored shape-axis correction task through the ordinary collapse watch and self-correction gate. Before correction, it forks a cold control graph. The primary then calls `scan_and_self_correct`, which must adopt the shape-axis fix and write typed `CorrectionOutcome` nodes itself. Fork a second graph only after this operation so it inherits those records.

Both branches receive the same held-out recurrence task. Its faulted `mrl_offer_due_once` rule is tested against an episode-scoped guard and a candidate-scoped repair using the v2 staged-arrival oracle. Candidate repairs are applied only to full-copy trial branches; task inputs and source state in the two evaluation graphs are paired. No `CorrectionOutcome` nodes are manually constructed or transported by the runner.

## Gates

- Three fresh workers, stable sources/native, and graph-authored correction policies.
- Normal `scan_and_self_correct` adopts `dedup_identity_fix` and persists typed positive and negative outcome rows.
- Cold fork contains zero `CorrectionOutcome` nodes; the post-training fork inherits the exact primary records.
- Both held-out task graphs emit a graph-authored rank Program and the same recurrence candidate set.
- Cold ranking selects the smaller episode-scoped guard, fails the `[1, 0]` offer-count oracle, then repairs successfully.
- Inherited success ranks the candidate-scoped repair first; it passes the `[1, 1]` oracle in one trial.
- All candidate rehearsals preserve each task graph's primary graph and rules.

## Interpretation limits

This tests automatic outcome persistence within one substrate and inheritance through a native full-copy branch. Task-family labels, repair classes, and utility scoring are authored; this is not autonomous concept formation, policy invention, or natural-task generalization. The cold control is forked from the same prepared training graph before correction, and the treatment from its post-correction primary.
