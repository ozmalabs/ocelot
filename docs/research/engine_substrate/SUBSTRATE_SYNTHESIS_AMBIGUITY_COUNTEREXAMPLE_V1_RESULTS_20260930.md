# Rung 3 ambiguity and counterexample response v1 results

## Results

The source-locked panel completed 15/15 fresh workers (five per arm), with no failures. The independent analyzer passes all 15 integrity, label-reconstruction, isolation, and backend-parity checks.

| Arm | Accepted | Exact training points | Exact held-out points | Median candidates | Median pump wall |
|---|---:|---:|---:|---:|---:|
| Sparse examples, default grammar | 5/5 | 30/30 | 0/30 | 121,536 | 1,635 ms |
| Add one counterexample, default grammar | 0/5 (gapped) | no accepted Program | no candidate | 200,000 (cap) | 2,074 ms |
| Add counterexample, oracle grammar | 5/5 | 35/35 | 30/30 | 58,824 | 767 ms |

Under sparse training, every worker accepts the predicate shortcut `r + (c > 1)` in the first output coordinate. It exactly fits all six examples per worker but is wrong on every held-out point: 30/30 accepted false predictions. Adding the known distinguishing example `(0,3) -> (2,3)` removes this false fit. With the default broad grammar, all five searches then exhaust the 200,000-candidate cap and gap; no wrong candidate is accepted. With the same examples and the externally supplied operator inventory `Plus, Minus, Max, TupleOf`, all five workers find an exact program, and all 30 held-out predictions are correct.

Each accepted candidate was stored inside a shared-graph-page training branch and evaluated from both eager-copy and shared-page children. Training/evaluation outputs, status, IR root counts, and complete post-evaluation graph/grammar/rule digests match exactly across backends. The primary graph and candidate snapshots remain unchanged. This demonstrates the branch contract carrying both an overfit Program and an exact corrected Program in a synthesis workload.

## Interpretation

One externally selected example is enough to eliminate this specific false hypothesis, but it is not enough to make default search tractable. The engine moves from false acceptance to honest gap under the broad grammar; the compact grammar recovers exact transfer with about 3.4× fewer candidates than the corrected/default cap and about 2.7× lower median pump wall time. The grammar is injected by the experimenter, so its result is an upper bound using task knowledge, not autonomous ambiguity resolution. The substrate did not select or request the counterexample.

The cost tradeoff is visible: corrected/default search spends the full 200,000-candidate budget and takes about 2.07 s median; the sparse false-fit takes 1.64 s; the corrected/oracle-grammar path takes 0.77 s. These are one-host full-pump measurements for this fixed task. There are no distribution-level confidence claims.

## Limits

This is one authored hinge function, one known counterexample, and one oracle grammar. It does not estimate false acceptance across task families, discover which query to ask, compare learned grammar selection, or establish general program-learning or tractability claims. No program is adopted. Broader ambiguous functions, delayed/noisy feedback, candidate ranking, explicit refusal/query behavior, independent task selection, and held-out grammar transfer remain open.

## Artifacts and reproduction

- [Preregistration and pilot disclosure](SUBSTRATE_SYNTHESIS_AMBIGUITY_COUNTEREXAMPLE_V1_PREREG_20260930.md)
- [Runner](../../../scripts/synthesis_ambiguity_counterexample_v1.py)
- [Independent analyzer](../../../scripts/analyze_synthesis_ambiguity_counterexample_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/synthesis_ambiguity_counterexample_v1_20260930_lock.json)
- [Raw capture](../../../evaluation/reports/synthesis_ambiguity_counterexample_v1_20260930_raw.json)
- [Independent analysis](../../../evaluation/reports/synthesis_ambiguity_counterexample_v1_analysis_20260930.json)

From the repository root, reproduce with `python3 scripts/synthesis_ambiguity_counterexample_v1.py --lock` (compare with the saved lock), `python3 scripts/synthesis_ambiguity_counterexample_v1.py`, then `python3 scripts/analyze_synthesis_ambiguity_counterexample_v1.py`.
