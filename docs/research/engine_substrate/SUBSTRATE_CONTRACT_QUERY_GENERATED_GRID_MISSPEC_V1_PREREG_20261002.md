# Generated-pool grid sensitivity and target misspecification v1 — preregistration

## Question

How do candidate-probe coverage and an out-of-grammar target affect generated version spaces, query selection, and held-out correctness as grammar depth rises?

## Frozen task panels

Run three fresh workers for each panel (nine total). All use native `Plus/Times/Minus/Div`, constants `{0,1,2,-1}`, no output constants, 30-second synthesis limit, 10,000-pool cap, and maximum Term size 7. The labeler and target are not passed to synthesis or query selection.

1. **Deep cubic, broad grid:** `f(x)=x³`, knowns `(0,0),(1,1)`, candidates `{-8,-6,-4,-3,-2,2,3,4,5,6,8,10,12}`, held-outs `{-13,-8,8,13}`.
2. **Deep cubic, sparse grid:** same target, knowns, grammar, and held-outs, but only candidate `x=2`. This deliberately tests query resolution when the offered aperture has one point.
3. **Out-of-grammar absolute value:** `f(x)=|x|`, knowns `(-1,1),(0,0),(1,1)`, candidates `{-4,-3,-2,2,3,4}`, held-outs `{-11,-7,7,11}`. The hypothesis grammar omits `Abs` and has only arithmetic Terms, so the exact target is not in the represented operator vocabulary.

Generate each pool using all of that panel's candidate descriptors for behavioral collection/deduplication. Compare uncached and lazy-matrix selectors on the same pool and labels until terminal or candidate exhaustion. Record complete synthesis and selection costs separately and together, query/survivor traces, all survivor held-out predictions, target support, evaluator calls, matrix footprint, and peak RSS.

## Gates and interpretation

Require stable current source/native hashes in lock, worker, and analyzer; all nine workers complete; generated Terms use only the frozen operator set; pool completeness and digests match; every Term is independently evaluated on known/candidate/held-out descriptors; both selector arms have exact trace, entropy, prediction, label, terminal, and survivor parity; and query descriptors never repeat. Recompute all labels with standalone Python target functions. For both cubic panels, require the target to occur in the generated pool and at least one generated survivor to be exact on all held-outs. For absolute value, record target representation and survivor exactness without requiring success: unsupported targets, false singleton, empty version space, or failure to find an informative probe are substantive outcomes, not invalid runs.

The sparse-grid panel is intentionally a stress control and may yield a false singleton; held-out residuals must remain visible and must not be converted into a success claim. Compare the two cubic panels as distinct pools because candidate descriptors participate in behavioral deduplication. These are authored scalar tasks, not an estimate of natural task prevalence or general learner capability.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_contract_query_generated_grid_misspec_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_query_generated_grid_misspec_v1.py`
- The runner writes a source/native lock and raw capture in the capability and report directories.
