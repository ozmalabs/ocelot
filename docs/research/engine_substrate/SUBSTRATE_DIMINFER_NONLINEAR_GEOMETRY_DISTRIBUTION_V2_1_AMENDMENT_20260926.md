# DimInfer nonlinear geometry-distribution v2.1 analysis amendment

The v2 capture completed all 576 locked workers with no failures. The first analyzer's only failed integrity check compared the raw `design` object directly to the lock `design`; they encode the same sampled geometries and factorial but intentionally expose different metadata fields, and the analyzer also compared Python tuples directly against JSON arrays without normalizing them (`gen_infer_enabled` in raw versus `arm_pair` in lock). The corrected check compares the shared fields and independently reconstructs all 24 geometries.

Audit also found that the v2 summary collapsed Transform records with no generator (Rung 1 residual explanations) into the `no_transform` category, and omitted `dims`/`deltas` when deciding whether an alternate generator route carried residual work. V2.1 reports these separately as residual-only records, no-record fallthrough, intended-generator routes with residuals, exact alternate-generator routes, and residual-bearing alternate-generator routes.

No raw record, workload, execution, or scoring threshold changed. The initial analysis is retained; v2.1 is the authoritative analysis.
