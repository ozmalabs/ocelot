# Boundary-probe policy comparison v1 preregistration

## Question

Across more than one arithmetic task and several hidden thresholds, how do
candidate-directed boundary probes compare with current fixed coverage, a
wide fixed grid, and safe abstention?

## Frozen tasks, candidates, and arms

Use five frozen additive panels and five frozen product panels, each crossed
with hidden strict upper-bound thresholds `ax < c` for `c ∈ {3.75, 5, 8}`.
For each panel/threshold, supply two structurally distinct equivalent exact
Terms and one restricted near-equivalent candidate:

- additive: `ax + ay == ex + ey`, with a commuted equivalent;
- product: `ax * ay == ex * ey`, with a commuted equivalent;
- restricted control: the exact relation conjoined with `ax < c`.

Compare four responses to the same frozen support. (1) Run the current
coverage-aware policy unchanged. (2) Abstain when the candidate's comparison
threshold lies outside observed `ax` support. (3) Parse the threshold, add
three relation-satisfying probes at `c-0.5, c, c+0.5`, and ask the native
selector. (4) Use a fixed 17-point even-integer grid from -16 through 16,
instantiate task-satisfying examples, and ask the same selector. Selected
probe labels come from the task oracle. All candidate formulas are supplied
by the harness.

## Analysis

Replay policy labels and candidate transitions. Score all arms on the
registered finite holdout and a separately seeded balanced wide-domain set.
Report false-safe returns, exact members retained, abstentions, labels,
candidate/probe evaluations, and selection cost. A safe abstention counts as
no false acceptance but not task success. Independently rescore the restricted
candidate to ensure the wide domain actually exercises each threshold.

## Limits

This is a 30-panel controlled arithmetic study, not natural-task prevalence
or open-ended candidate discovery. Both relation families and all variants
are authored. Numeric literal extraction does not establish a generic
boundary extractor for arbitrary Terms or domains.
