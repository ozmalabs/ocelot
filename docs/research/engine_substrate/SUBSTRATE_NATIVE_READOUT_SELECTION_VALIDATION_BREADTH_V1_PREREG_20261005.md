# Native readout selection: validation breadth v1 preregistration

## Question

Does increasing the number of distinct labeled validation positions reduce native selector tie abstentions and preserve held-out utility, when fit data, candidate rules, total fit presentations, and final corner sites are held fixed? This is a prospective follow-up to the six-seed v1.1 selector result, which tied and abstained in three seeds with eight validation examples.

## Fixed design

Use fresh seeds 46–51. Keep the same five-pixel centered horizontal/vertical bars, eight fit positions, four original validation positions, and four corner evaluation positions used by v1.1. Add four validation positions `(4,7)`, `(7,4)`, `(7,11)`, and `(11,7)`, each with both labels, for 16 validation examples total. Fit remains 6,400 presentations: 400 presentations per class at each of the eight fit positions. Association state is frozen before validation, selection, and corner evaluation. Corner sites and labels stay sealed from the selector until all selected predictions or tie abstentions are captured.

## Candidate and selector

Keep exactly the v1.1 candidates: raw activation-by-association dot product and squared Euclidean distance from the class activation prototypes. Native rules produce predictions on every validation example, count agreements, and select with `ArgminUnique` over negative validation scores. A unique validation winner is selected; a tie is an explicit abstention. No tie-breaking override is introduced. The host may load inputs and candidate definitions but does not compare scores or set the chosen candidate.

## Gates and reporting

Require source lock, fresh seed IDs, exact disjoint partitions, schedule and association-count reconstruction, one native prediction per candidate per validation example, independently reconstructed candidate scores, correct unique-selection/refusal behavior, frozen learned state, and corner label withholding through capture. Report tie rate, selection coverage, conditional accuracy, unconditional correct/48, abstentions, fixed-candidate accuracy, external nearest-mean and initial-projection controls, fit/selection closure and CPU cost, peak RSS, and per-seed outcomes. Compare tie rates descriptively against v1.1's 3/6 seeds; cohorts are independent and this is not a paired treatment comparison. Do not pool them as if seeds were matched.

## Interpretation boundary

Fewer ties would show that a wider position-validation panel supplies more discriminating evidence for this candidate pair. It would not establish that the substrate invents candidates, learns an unprovided objective, or generalizes beyond this synthetic task. More validation sites may increase selection work; record full cost. A tie or lower transfer accuracy is a valid outcome.

## Reproduction

Use the source-locked v1.2 runner and independent analyzer in `evaluation/substrate_capability`. The earlier v1 failure and v1.1 corrected result remain separate and immutable artifacts.
