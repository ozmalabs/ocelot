# Perceptual numerosity contract v1

Status: semantic freeze for P7.04–P7.E3. This contract specifies perceptual inputs and uncertainty outcomes. It does not claim that a perceptual numerosity implementation or evaluation exists. The symbolic `NumberWorld` remains a separate task and comparator.

## 1. Input boundary and evidence

A perceptual scene arrives as a source-bound `NumerosityObservation` with owner, scene/event ID, source/model/frame epochs, sensor modality, visible region, and acquisition status. It contains either individually segmented visible objects for the small-set route or aggregate sensor measurements for the larger-set route. It never contains the hidden exact count, a target answer, a ratio label, or a scoring annotation. Those remain in a detached evaluator record.

The observation boundary may mechanically ingest a sensor grid or a set of measured regions. It may compute bounded aggregate measurements such as occupied area, local density, spacing distribution, visible fraction, and occlusion. It cannot count the underlying objects and then publish that count as an aggregate feature. Missing, occluded, stale, ambiguous, or out-of-frame measurements remain explicit uncertainty. Each measurement retains the exact scene/frame source reference and cannot combine across owners or epochs.

## 2. Individuated small sets and aggregate larger sets

When at most four objects can be independently individuated, perception may create one source-bound token per visible object and compare cardinalities by one-to-one matching. The decision rule is bounded by the fixed small-set limit; it cannot enumerate an unbounded scene. If individuation is uncertain, the result is a range or `UNKNOWN`, not a guessed exact count.

For larger scenes, no per-object token list or exact cardinality is available to the decision graph. The ingestion adapter supplies aggregate visual measurements whose work is bounded separately: sensor reading and aggregation may be O(n) in input pixels/regions, while graph decision work and graph growth have fixed declared caps independent of the hidden object count. Exact count may appear only in detached scoring data.

## 3. Uncertainty, comparison and abstention

A numerosity estimate is a bounded distribution or interval with its sensor evidence and uncertainty. Comparison returns `LESS`, `SAME_WITHIN_RESOLUTION`, `MORE`, or `UNKNOWN`; it does not force a binary answer when evidence overlaps. Invalid or stale evidence, unresolved occlusion, or conflicting cues produce `UNKNOWN` and no world-changing commitment.

Area, density, spacing, object size, contrast, viewpoint, occlusion, and container boundaries can confound one another. When independent cues conflict beyond the frozen tolerance, the mechanism must abstain. It cannot resolve conflict by reading hidden count. Probabilities and confidence must come from the observed sensor evidence or a separately learned model; an answer-shaped hand-coded Weber curve is prohibited.

Ratio judgments preserve scale: scenes with equal ratios at different absolute magnitudes should produce comparable distributions after accounting for sensor resolution. If uncertainty intervals overlap such that the ratio ordering is not identified, return `UNKNOWN`. Decision cost is separately bounded from ingestion cost and the budget request must be approved before any optional refinement or additional sensing.

## 4. Controls and acceptance

The evaluator retains exact counts and labels outside the graph. It may use these only to score. Input fixtures cover: small sets 0–4 with independently shuffled layouts; larger sets with controlled density/area/spacing; equal ratios at different scales; crossed area-density cues; occlusion and missing regions; stale frame/source epochs; and label/metadata leakage probes.

The frozen target criteria from the build plan remain proposed: at least 95% exact accuracy for unambiguous small sets, at least 75% on ratio comparisons at ratios ≥1.5, and no more than a 10-point accuracy difference between equal-ratio scale conditions. Report all abstentions and coverage alongside accuracy; a high score from answering only easy scenes does not pass. These are evaluation criteria, not human-performance claims.

Acceptance tests:

- `test_small_sets_exact`: independently individuated clear sets up to four are exactly matched by bounded one-to-one token comparison.
- `test_hidden_count_not_visible`: graph input and derived nodes contain no exact count, target class, or scorer label for the aggregate route.
- `test_area_density_conflict_abstains`: crossed cues beyond the frozen tolerance return `UNKNOWN` without a committed comparison.
- `test_equal_ratio_scale_contract`: equal ratios at different scales have comparable uncertainty-aware outputs within the frozen tolerance.

Controls also verify stale epochs, missing/occluded evidence, bounded graph growth, bounded decision work, and detached scorer isolation. No test may turn missing evidence into a positive comparison.
