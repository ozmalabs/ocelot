# Generic continuous singleton audit v1 preregistration

## Question

Does post-search false-singleton detection persist when audit inputs are drawn by a task-agnostic sampler, without task-conditioned positive/near-miss templates?

## Design

Freeze the 20 panels, candidate identities, and candidate Terms from the source-locked adaptive factored search. The tested policy samples each of `ax`, `ay`, `ex`, and `ey` independently and uniformly from the continuous interval `[-2.4, 2.4]`, using a deterministic per-panel seed. It has no task-family input and does not inspect candidate Terms when proposing rows. Exclude any row exactly present in training, selection, or the sealed fractional holdout set. Query the task oracle for each sampled row, compare its label with the candidate prediction, and request help at the first mismatch. If no mismatch appears by the budget, provisionally accept. Report results at cumulative caps of 4, 16, and 64 oracle labels; later caps reuse the same ordered sample stream. A fixed help control always abstains.

The oracle labels use the held task definition only to score an input, as in ordinary supervised interaction. The policy receives no task name or oracle formula. This is a post-search audit only: it neither resynthesizes from mismatches nor changes candidate generation.

## Measures and gates

Lock source/native hashes, upstream candidate capture, exact panel mapping, sampler interval, seeds, and caps before execution. An independent analyzer must replay every sampled row and oracle label, verify distribution bounds and disjointness, recompute candidate predictions and first-mismatch stopping, and score acceptance against the sealed 1,296-point holdout only after policy decisions. Report correct/false acceptance, help, labels, wall time, and per-task results at each cap, alongside the earlier task-conditioned and integer audits. The run is valid only if all 20 panels are paired and all provenance and transcript checks pass.

## Limits

Uniform four-dimensional sampling may have low power against rare or narrow residual regions; failure to detect a false candidate is not evidence of equivalence. Conversely, this assay does not establish generic task learning, active probe design, or residual-driven repair. The task family and candidate pool remain the four authored numeric families from the upstream study.
