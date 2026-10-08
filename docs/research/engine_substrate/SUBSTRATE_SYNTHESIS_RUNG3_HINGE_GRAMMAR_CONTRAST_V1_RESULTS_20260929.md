# Rung 3 hinge-map grammar contrast v1 — results

**Date:** 2026-09-29. **Question:** does a small operator inventory make the integrated Rung 3 route tractable on a hinge task with examples that distinguish a threshold shortcut from the intended piecewise rule?

## Protocol

Five fresh workers per arm use the same eight training pairs, six disjoint heldout pairs, source/runtime, request, 200,000 default candidate cap, and `ensure_program_synthesis` → `ingest_spec` → graph-authored `pump` path. The default arm leaves operator selection to the substrate. The oracle arm injects the existing `ps_enum_ops` fact with `Plus`, `Minus`, `Max`, and `TupleOf` before pumping. This is a known-task grammar intervention; it supplies task-relevant information and is not autonomous selection. One earlier exploratory pair found the same search outcomes, but those data are excluded; the current five-per-arm result is the locked repeat ([preregistration](SUBSTRATE_SYNTHESIS_RUNG3_HINGE_GRAMMAR_CONTRAST_V1_PREREG_20260929.md)).

The independent analyzer passes all eight integrity gates. Both arms reach Rung 3 and terminate in all five workers; current source/native hashes match, worker source state remains stable, and every accepted Program has exactly one reflected IR root and six independent holdout readbacks.

## Results

| Arm | Accepted | Exact holdout transfer | Median candidates | Median pump wall time | Median pump CPU time | Peak RSS |
|---|---:|---:|---:|---:|---:|---:|
| Default broad selection | 0/5 | 0/5 | 200,000 (cap) | 1,804 ms | 1,799 ms | 79.3 MB |
| Oracle-supplied grammar | 5/5 | 5/5 (30/30 points) | 61,384 | 650 ms | 650 ms | 63.2 MB |

The default arm reaches the candidate ceiling and gaps in every repetition. The oracle arm returns the same accepted Program in all five runs; it computes `r + max(c-1,0)` in the first coordinate and transfers to all six heldout points each time. Median candidate work is 3.26 times lower and median `pump` wall time is 2.78 times lower under the oracle grammar. These are complete `pump` costs, including graph-rule and adapter overhead, on one local machine/build; they do not isolate native enumerator time.

Full checks and per-worker outcomes are in the [analysis](../../../evaluation/reports/synthesis_rung3_hinge_grammar_contrast_v1_20260929_analysis.json), [raw capture](../../../evaluation/reports/synthesis_rung3_hinge_grammar_contrast_v1_20260929_raw.jsonl), and [source/input lock](../../../evaluation/substrate_capability/synthesis_rung3_hinge_grammar_contrast_v1_20260929_lock.json). All preregistered contrast thresholds pass: oracle exact transfer ≥4/5, default cap exhaustion ≥4/5, and median candidate reduction ≥3×.

## Interpretation and limits

This is strong causal evidence on this fixed task that narrowing the candidate grammar can change the production route from capped failure to exact heldout transfer at lower cost. It explains the earlier accepted hinge false generalization: with sparse training and a broad grammar, the first fitting candidate is a Boolean threshold shortcut; with balanced training, broad search cannot finish within budget; with the correct grammar supplied, the intended max-based program is found and transfers.

The oracle arm injects the correct operators from outside the learning path. No result here demonstrates how the substrate could infer that inventory from a residual, choose it without task leakage, or distinguish the correct grammar from alternatives on unseen natural tasks. The narrow conclusion is that grammar selection is a critical missing capability and a measurable tractability lever for this Rung 3 workload. Next test a preregistered operator-shape selection rule on tasks not used to construct it, with heldout negatives, broad-default and oracle-upper-bound controls, plus per-family false acceptance and budget outcomes.
