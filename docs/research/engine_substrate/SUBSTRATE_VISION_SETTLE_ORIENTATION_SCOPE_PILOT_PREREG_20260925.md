# Orientation-response scope pilot preregistration

Date: 2026-09-25. Benchmark-only root-scoped clone; no production seed/engine changes.

## Question
Does root-scoping `vision_settle` preserve orientation-response quality on a complete single-sheet workload when evaluated through the existing `complex_cells.cell_stats` stimulus/readout code?

## Paired pilot
Build global and root-scoped `settle_lib.build_sheet` arms for `(n_side, seed)=(3,20260925),(4,20260926)`, channels=`lateral`, connectivity=8, settle=1, bubble=0. Patch only the benchmark process's loaded `vision_settle` manifest as documented in the prior scope probe. Freeze learning (`oo_eta=0`, `frozen=1`, homeo=0, lateral frozen) and use identical construction seeds. Measure `cell_stats(key="rate", period=4, K=4)`, retaining the established 12 orientation values and using the standard four-phase grid as a pilot. Record per-unit and mean OSI, tuning arrays, alive counts, elapsed probe time, root membership, and native provenance. No training or adaptation occurs.

## Criteria
For each pair, report exact tuning-array/state parity and absolute OSI delta. A pair is task-quality-equivalent for this pilot iff max absolute tuning difference <=1e-10 and mean OSI delta <=1e-10. Report all caps/omitted measurements. Timing is exploratory only: no speedup inference from two arms or two seeds.

## Scope
K=4 is a pilot resolution, not the committed K=16 confirmatory instrument. If parity holds and cost is practical, a separate preregistered K=16 confirmation can follow. This does not test multi-sheet full anatomy, learning, or scaling.
