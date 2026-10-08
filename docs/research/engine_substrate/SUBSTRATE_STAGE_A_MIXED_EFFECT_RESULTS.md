# Stage A mixed attribute/edge effect probe (2026-09-25)

## Result

Stage A compare admitted one mixed rule containing both `SetAttr` and `AddEdge` effects over six independent self-loop bindings, each with a single matched variable. The expected attribute values and corresponding derived-edge attributes were preserved. The run recorded one compared drain, zero divergence, zero unsound drains, and zero terminal progress. The [raw report](../../../evaluation/reports/substrate_stage_a_mixed_effect_probe_20260925.json) includes the full graph, exact inputs, checks, and source/native provenance.

## Boundary

This shows that a mixed effect shape can enter Stage A when bindings are one-variable and independent. It does not show admission or correctness for the previously measured multi-variable reader/writer shape: that shape writes matched targets across multiple variables and is conservatively excluded by the current contention check. It also does not exercise concurrent attribute mutation inside the mixed-effect drain. Keep these cases distinct in future scheduler claims.
