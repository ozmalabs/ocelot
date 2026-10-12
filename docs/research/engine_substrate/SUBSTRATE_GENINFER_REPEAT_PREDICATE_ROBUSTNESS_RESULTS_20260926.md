# GenInfer repeated-predicate recovery robustness results (2026-09-26)

## Outcome

All eight integrity/determinism gates pass for 60 observations (three layouts × four conditions × five repeats). All 15 positive observations recover `[1,1,0,2]` without residuals. Across 45 corrupted observations, 20 are accepted, 25 refused, and only 5 return the generating matrix. The remaining 15 accepted cases return a different matrix.

The response is strongly geometry-dependent and non-monotonic in corruption magnitude:

| Layout | Corruption | Accepted | Generating matrix recovered | Returned matrix when accepted | Candidate count |
|---|---:|---:|---:|---|---:|
| Original | +1 | 5/5 | 0/5 | `[0,0,0,2]` | 6,560 |
| Original | +2 | 5/5 | 5/5 | `[1,1,0,2]` | 6,560 |
| Original | +3 | 5/5 | 0/5 | `[-2,-2,0,2]` | 6,560 |
| Orthogonal pairs | +1 | 0/5 | 0/5 | refused | 624 |
| Orthogonal pairs | +2 | 0/5 | 0/5 | refused | 624 |
| Orthogonal pairs | +3 | 0/5 | 0/5 | refused | 624 |
| Paired square | +1 | 0/5 | 0/5 | refused | 624 |
| Paired square | +2 | 5/5 | 0/5 | `[-1,0,0,2]` | 624 |
| Paired square | +3 | 0/5 | 0/5 | refused | 624 |

The original geometry's alternative matrices carry predicate-local shifts; the paired-square +2 case returns the alternate matrix with one global +2 row shift. Every outcome was identical across the five repeats in its cell. The orthogonal-pair and paired-square layouts require only 624 candidate matrices, versus 6,560 for the original layout, due to their smaller data-derived bound.

## Source-linked mechanism audit

The candidate-bound explanation is ruled out for these fixtures: `624=(2·2+1)^4−1` gives B=2, and `6,560=(2·4+1)^4−1` gives B=4. The generating matrix's maximum coefficient is 2, so it is inside the enumerated domain in every cell. This is independently checked in the analyzer.

The more direct mechanism is canonical positional alignment. `eval_gen_infer` sorts the observation at [shape_decode.rs:3031–3032](../../../runners/dsl/src/shape_decode.rs); `build_candidate` separately sorts each transformed held signature at [shape_decode.rs:2015–2016](../../../runners/dsl/src/shape_decode.rs) and then zips the two sequences at [shape_decode.rs:2039](../../../runners/dsl/src/shape_decode.rs). There is no persistent relation identity key beyond the relation tuple values. Repeated predicates therefore leave within-predicate rows to be paired by sorted coordinate order. In the original layout the two p0 outputs from the generating matrix begin at row coordinates `[0,1]`: adding +1 to the first makes `[1,1]` (aligned deltas `[+1,0]`, inconsistent within p0); adding +2 gives sorted `[1,2]` (aligned deltas `[+1,+1]`, consistent); adding +3 gives `[1,3]` (aligned deltas `[+1,+2]`, inconsistent). This directly predicts why the generating matrix is eligible at +2 but not +1/+3 under the predicate-local uniformity rule ([shape_decode.rs:2156–2180](../../../runners/dsl/src/shape_decode.rs)).

Where multiple matrix/residual decompositions remain eligible, the code chooses fewest residual entries, then smallest coefficient L1 sum, then lexicographic matrix ([shape_decode.rs:3132–3147](../../../runners/dsl/src/shape_decode.rs)). In paired-square +2, the reported alternative has one residual entry and matrix L1=3, while the known generating matrix has L1=4 with one residual entry; this ranking therefore favors the alternative. The source audit makes canonical pairing and the Occam tie-break plausible causes of the observed outcome. It is not an exhaustive proof that no other candidate-ranking interaction contributes.

## Interpretation

This is evidence that geometry changes both search size and the recognition boundary. The measured corruption response is not a simple monotonic threshold: a larger perturbation can be accepted where a smaller one is refused, and the generating matrix can be recovered at +2 while not recovered at +1 or +3 for the original geometry. Therefore a single noise control, a single bound, or `explained` alone is inadequate for a GenInfer learning-accuracy claim. Report candidate count, geometry, decomposition acceptance, exact generating-matrix recovery, and residual form separately.

## Limits

Three synthetic arrangements, one integer matrix, one relation-local row-coordinate corruption, and five repetitions per cell. This does not estimate natural-noise rates, generalize to other generator families, or include full closure, mint, or reuse.

## Artifacts

Protocol: [`SUBSTRATE_GENINFER_REPEAT_PREDICATE_ROBUSTNESS_PREREG_20260926.md`](SUBSTRATE_GENINFER_REPEAT_PREDICATE_ROBUSTNESS_PREREG_20260926.md). Runner/analyzer: [`geninfer_repeat_predicate_robustness_probe_v1.py`](../../../scripts/geninfer_repeat_predicate_robustness_probe_v1.py), [`analyze_substrate_geninfer_repeat_predicate_robustness_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_repeat_predicate_robustness_probe_v1.py). Raw data: [`substrate_geninfer_repeat_predicate_robustness_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_20260926.json). Analysis: [`substrate_geninfer_repeat_predicate_robustness_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_analysis_20260926.json).
