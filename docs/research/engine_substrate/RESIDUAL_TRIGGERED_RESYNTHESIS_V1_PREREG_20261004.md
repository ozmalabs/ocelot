# Residual-triggered resynthesis v1 preregistration

## Question

When a task-blind Term-conditioned audit finds a prediction/oracle mismatch, does adding that residual to the training examples improve bounded substrate search and acquired-label selection, relative to spending the same search budget on the original examples?

## Cohort and arms

Use only panels where the locked Term-conditioned audit produces a mismatch within its first 64 labels. Selection into this cohort is determined by the observable audit transcript, never by sealed holdout correctness. For each such panel, run two paired arms over the same four factored operator branches (`Plus`, `Times`, `Abs`, `Min`):

- **No-residual control:** original training examples only.
- **Residual arm:** original training examples plus the first audit mismatch row and its oracle label.

Each branch receives a 0.5 second native synthesis budget, size cap 7, no output-derived constants, up to 64 distinct fitting solutions, and the same preregistered probe inputs. Merge canonical Terms across branches. A task-blind native discriminating-input selector then uses at most eight oracle labels from a disjoint selection pool to reduce the version space; abstain if no unique candidate remains. Score selected and remaining candidates against the sealed 1,296-point holdout only after both policies finish. Report branch wall/CPU time, explored counts, candidate counts, selector time, labels, and holdout outcomes. No candidate is installed into the primary substrate.

## Validity checks

Lock current engine/source hashes, both upstream captures and locks, exact panel/candidate/mismatch mapping, operator order, budgets, selection rows, and candidate Terms. Independent analysis replays residual labels from raw audit events, confirms paired budgets and oracle transcripts, verifies no training/selection/holdout leakage, recomputes candidate predictions and final holdout scores, and checks primary-state isolation. Report every triggered panel and the excluded panels with no residual; do not generalize beyond this selected cohort.

## Limits

This is a harness-orchestrated, closed four-operator, synthetic numeric repair assay. It measures substrate synthesis and candidate selection after a supplied residual. It is not autonomous discrepancy discovery, open-ended concept invention, persistent rule adoption, or general self-improvement. A single counterexample need not make the true rule identifiable.
