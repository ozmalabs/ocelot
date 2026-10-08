# Resynthesis selector-budget extension v1 preregistration

## Question

For the higher-budget resynthesis candidates that remain ambiguous after eight labels, does using more of the already-declared disjoint selection pool resolve the version space, and does the selected singleton generalize to the sealed holdout?

## Design

Freeze both candidate pools and all first-eight-or-fewer selection events from residual resynthesis v1.2. Replay each arm's recorded labels, then continue the same native maximum-disagreement selector over the remaining preregistered selection rows, querying the same task oracle. Stop at singleton, selector failure, or exhaustion of the pool. Report cumulative outcomes at 8, 16, 32, and the full available pool. Do not change candidate generation or search. Holdout scoring occurs only after each policy decision; request help if ambiguity remains.

## Measures and validity

Lock v1.2 source/capture/analysis hashes, candidate identities, panel data, and query pool. Independently verify source binding, label replay, query disjointness, selector decisions, stop conditions, and 1,296-point holdout scores. Report exact/false singleton, help, labels, and candidate-set size at each cap, including every panel.

## Limits

This isolates query budget on an inherited candidate pool; it cannot establish that the candidates are complete or that additional labels improve synthesis. The small numeric task set and sealed finite holdout remain the evaluation boundary.
