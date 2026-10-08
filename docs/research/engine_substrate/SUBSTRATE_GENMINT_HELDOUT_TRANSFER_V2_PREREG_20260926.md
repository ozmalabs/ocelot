# Full-seed GenMint four-relation held-out transfer preregistration v2

**Lock date:** 2026-09-26, before confirmatory capture. **Question:** does production GenInfer acquire a new linear generator from six training relations and reuse it on a four-relation held-out pattern that is less ambiguous with the seed's existing generators?

## Fixture and disclosure

Use matrix `[1,1,0,2]` over ten 2-D integer points: `(0,0),(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2),(3,1),(1,3)`. Three predicate assignments each label five rows p0 and five p1:

| Layout | p0 relation indices | Training indices | Held-out indices |
|---|---|---|---|
| adjacent_01 | 0,1,4,6,8 | 0–5 | 6–9 |
| opposite_03 | 0,3,4,7,8 | 0–5 | 6–9 |
| adjacent_12 | 1,2,5,6,8 | 0–5 | 6–9 |

The first six training rows are the same in the earlier direct held-out study; four additional points enlarge the held-out pattern to two p0 and two p1 relations. A disclosed, unarchived clean-arm fixture-selection pilot observed training acquisition and held-out selection of the linear map in all three layouts, while the induction-disabled training arms minted a quantum. This pilot selected the protocol geometry and is not confirmatory evidence. The full preregistered factorial below tests noise, held-out variants, paired controls, repeats, cost, and route attribution.

## Arms

Cross three training conditions (clean; uniform +1 on p0 coordinate slot 1; inconsistent +1/+2 on the first two p0 training rows) with clean or uniform +1 p0 held-out targets, GenInfer enabled/disabled, and five repetitions. Each fresh full-seed substrate first receives exactly the six training base rows and one training observation; after closure, the four held-out base rows are introduced as a new ShapeSignature and their target as a separate observation. Total: 180 independent sequences. Assignment order is shuffled with the declared runner seed.

Capture statuses, residuals, all Transform nodes, graph-resident generators, CapabilityAxis quanta, graph size, closure latency, input rows, native/source hashes, and engine provenance. Independently score the held-out Transform only when it references a linear generator newly minted during the training stage. Apply its matrix under the engine's per-signature origin normalization and then the returned residual transforms. Separately classify transforms that select another held generator or have no generator transform; do not count these as learned-linear transfer or as incorrect predictions from that matrix.

## Gates and reporting

Primary positive gate: in each clean-training/clean-heldout layout, all five GenInfer-enabled sequences mint the expected matrix during training, re-decode training with zero quantum, select that newly acquired matrix on the held-out observation, and independently predict all four held-out rows exactly. The paired disabled arm must acquire no copy of the expected matrix. Across all cells require input partition integrity, exact 6/4 train/held-out sizes, five repeats per cell, deterministic within-cell outcomes, and source/native provenance. All perturbed outcomes are descriptive; report acquisition/reuse counts separately from alternative held-dimension routes and all resource costs.

The protocol studies an authored 2-D integer-linear family only. It does not estimate natural task prevalence, broad generalization, or asymptotic search complexity. Reproduction: `PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_heldout_transfer_probe_v2.py` and `python3 scripts/analyze_genmint_heldout_transfer_probe_v2.py`.
