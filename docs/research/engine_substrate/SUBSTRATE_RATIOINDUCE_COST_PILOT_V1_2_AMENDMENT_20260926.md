# RatioInduce cost pilot v1.2 amendment — 2026-09-26

The v1.1 capture is retained, not overwritten. Only its four-dimensional cells passed. Its codebook declared four coordinate dimensions for every factor stratum, while the 2-D and 3-D populations contain only their declared lower-dimensional tuples. `RatioInduce` correctly refused those malformed schema/population combinations (`explained=false`, `checked=0` or partial checks); this is another fixture error, not cost evidence for those cells.

Before the v1.2 rerun, change the runner to create a matching `ShapeSignature.dim_types` schema for each D stratum. N/P sweeps use D=2; dimension sweep cells each use their own D-matched schema. All factor levels, population generation, repetitions, metrics, and acceptance conditions remain unchanged. The original v1 and v1.1 records remain separate and excluded from the v1.2 summaries.
