# Bounded coupled-quadratic synthesis v1.3 results

## Result

The source/native-locked 30-cell capture passes all ten integrity gates. The linear control acquires and transfers exactly in 10/10 runs. With the coupled quadratic target and `Plus, TupleOf`, the engine finds no candidate in 10/10 runs (median 312 tested; halt reason `max_size`). With `Plus, Times, TupleOf`, it finds a training-consistent term in 10/10 runs (median 1,057 tested; median acquisition 3.29 ms), but all ten candidates fail exact transfer on the six held-out pairs. No reuse timing is reported for those false fits. The canonical training-fit term is the same in all ten repetitions. Peak process RSS is 33.2 MB for this small harness.

The ablation separates representational reach from transfer: adding cross-coordinate multiplication enables a compact training fit, but the current enumerator's first-found consistent term is not the target behavior. The original v1.5 GenInfer path failed to produce a compatible generator; direct `SynthEnumerate` does produce candidates but overfits these labels. These are different routes and grammars, so this comparison does not establish that one subsystem can repair or invoke the other. The salient capability gap is now candidate disambiguation from held-out evidence or active query selection, not merely access to `Times`.

## Claim boundary

This is one authored integer map, one shared train/held-out split, two closed grammars, and a 150,000-candidate cap, in ten repeated fresh substrates. Repetitions verify determinism and capture integrity; they are not independent task samples. The positive control establishes that the route solves this simple task. The result does not estimate natural-task rates, open-ended primitive induction, general program synthesis, or self-improvement. The 3.29 ms acquisition figure is local to this tiny native-call harness and must not be compared to GenInfer v1.5's audit-instrumented closure timings.

## Reproduction

The frozen inputs and source/native hashes are in [the v1.3 lock](../../../evaluation/substrate_capability/synthenumerate_coupled_quadratic_v1_3_20261005_lock.json). Re-run with [the runner](../../../scripts/substrate_synthenumerate_coupled_quadratic_v1_3.py); independently analyze with [the analyzer](../../../scripts/analyze_substrate_synthenumerate_coupled_quadratic_v1_3.py). The [preregistration](SUBSTRATE_SYNTHENUMERATE_COUPLED_QUADRATIC_V1_PREREG_20261005.md), [v1.1 budget amendment](SUBSTRATE_SYNTHENUMERATE_COUPLED_QUADRATIC_V1_1_AMENDMENT_20261005.md), and [v1.2 runner-fix amendment](SUBSTRATE_SYNTHENUMERATE_COUPLED_QUADRATIC_V1_2_AMENDMENT_20261005.md) preserve the design evolution. Raw capture: [JSONL](../../../evaluation/reports/synthenumerate_coupled_quadratic_v1_3_20261005_raw.jsonl); independent analysis: [JSON](../../../evaluation/reports/synthenumerate_coupled_quadratic_v1_3_20261005_analysis.json).
