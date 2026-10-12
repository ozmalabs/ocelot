# Adaptive factored operator search v1 preregistration

## Question

Can an evidence-guided staged search preserve the exact-candidate coverage of
the fixed four-branch policy while reducing search work, and does a two-label
singleton audit catch false acceptance before adoption?

## Paired inputs and fixed control

Reuse all 20 panels and source-locked results from factored operator search
v1. The v1 capture is the fixed-search control: all four branches run on initial
examples, their unique terms are merged, and the selector uses up to six labels.
The adaptive arm has a three-second timeout for each branch
`Neg/Eq/And + {Plus, Times, Abs, Min}` and 128-solution cap. Operator order is
rotated deterministically from the frozen panel seed, independent of task
identity. Candidate generation gets examples only; the task name is available
to the external oracle/scorer, not used to choose branch order.

After each branch, merge new canonical Terms and request up to two
maximum-entropy labels from the first 24 frozen selection rows. If a unique
candidate remains, request up to two additional audit labels from the reserved
last eight rows. The total audit budget is four labels per panel; each
acceptance attempt requires two distinct matching audit labels for the same
candidate. Accept only if it matches both audit labels. A contradiction
is recorded as a residual; discard inconsistent candidates and search the next
branch using the accumulated labels. Continue until audited singleton,
exhaustion of all four branches, or six active labels. When the active-label
budget is exhausted without an audited singleton, stop branch search and
return `request_help`. Audit labels are allowed acquisition evidence, but all
fractional holdout labels/scores remain sealed until analysis.

## Measures and verification

Lock all source/native hashes and the paired v1 capture before execution.
Independently replay branch order, candidate fit at generation, selector
queries, audit queries, label transitions, help/adoption decision, and
registered holdout scores. Report audited correct resolutions, false
acceptances, help rate, residual-triggered branch expansions, labels, branch
search/wall/CPU and explored-term totals, selector evaluations, and paired
cost/coverage deltas from the fixed control. Include all 20 panels and all
branch timeouts.

## Limits

Four authored operator branches and four numeric task families remain a closed
menu. The work measures early stopping and residual-conditioned staged search,
not open-ended operator invention, natural-task prevalence, or general
self-improvement.
