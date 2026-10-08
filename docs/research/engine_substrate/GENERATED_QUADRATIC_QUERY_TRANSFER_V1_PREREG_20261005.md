# Generated quadratic query-transfer v1 preregistration

## Question

Can the current synthesis and native finite-query selector work in sequence on a misspecification boundary already observed in direct `SynthEnumerate`: preserve a held-out-correct hypothesis among fitting candidates, select an informative input, use its label to eliminate the training-fit shortcut, and retain an exact held-out survivor?

## Task and fixed inputs

Two scalar components of the coupled map are measured separately: `r+r*c` and `c+r*r`. Both use the six training pairs `(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)`. The synthesis grammar is `Plus, Times`, no constants, size 5, timeout 15 seconds, max 1,000 distinct solutions, and `include_output_constants=False`. Synthesis uses a fixed 6×6 probe grid with each coordinate in `{-2,-1,0,1,2,3}` to preserve behaviorally distinct programs. Query selection receives the generated Terms, candidate inputs, and training labels; it never receives the target ID or future labels. The 20 repetitions permute the same grid under a fixed seed. The three policies are maximum entropy, first in the permuted order, and a separate seeded random order. The oracle label is calculated only after each policy selects an input. Six fixed held-out points score survivors after query selection.

## Measures and admission

Record generation wall/CPU time, explored and distinct counts, pool size and halt reason; per-policy queries, prediction-evaluation counts, selector and total decision time; whether a held-out-exact hypothesis is in the pool before querying and uniquely survives afterward. The analyzer independently replays terms, decisions, labels, survivors, and holdout transfer. Admission requires stable source/native fingerprints, exact train/candidate/held-out definitions, complete two-task by 20-repetition by three-policy coverage, at least two generated fitting behaviors per task, a held-out-exact target in each version space, complete decision replay, and no false exact-survivor attribution. Any failed gate remains a result and is not silently excluded.

## Claim boundary

This is a two-function, fixed integer grammar and finite synthetic oracle. It tests integration of existing synthesis and query components; it does not establish natural-task prevalence, open-ended dimension induction, autonomous grammar choice, or source-level self-improvement. Query counts and compute costs are reported together, and repeated grid permutations are not independent task samples.

## Reproduction

Create the source lock with `python3 scripts/substrate_generated_quadratic_query_transfer_v1.py --lock`, capture with the same script without arguments, and analyze with `python3 scripts/analyze_generated_quadratic_query_transfer_v1.py`.
