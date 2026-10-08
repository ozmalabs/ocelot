# H06_C / 180° transform alias audit

**Date:** 2026-09-29. **Purpose:** resolve the repeated canonical-key miss in the held-out polyomino transfer capture without changing engine rules, adapter behavior, or winner selection.

## Evidence

The source-locked capture contains the `H06_C_rotate_2` clean example with base cells

```text
{(0,0), (0,1), (1,1), (2,1), (2,2), (3,1)}
```

and target cells

```text
{(0,1), (1,0), (1,1), (2,1), (3,1), (3,2)}.
```

An independent replay through `worlds.arc_ls20_scenario._recognise_sigs` yields adapter output `None`. Rebuilding the same `Observation` and running the native rules gives `status=recognized_transformed`, `covered_by=sym`, and a `has_transform` whose generator is `cycle4`, `k=1`, and `source=dim_infer`; the graph also contains `latent:cycle4`.

The held `cycle4` generator is a row increment modulo four. Applying `(r,c) -> ((r+1) mod 4,c)` to the six base cells yields exactly the six target cells. The intended half-turn `(r,c) -> (3-r,2-c)` also yields exactly that same set. Therefore the observation is ambiguous between two held operators for this shape, despite the expected task label being `rot90:2`.

The adapter in `worlds/arc_ls20_scenario.py::recognise_required_key` maps `rotation90`, `reflection_r`, `reflection_c`, substitution, and shift transforms to task keys. It has no `cycle4` mapping, so it returns `None` after the graph-level recognition. No source behavior was modified for this audit.

## Consequence for the v1 result

The 71/72, 284/288, and 273/288 figures remain valid **canonical-key return rates at the adapter boundary**. They are not graph-level recognition rates. The H06_C/180° row is an adapter label miss caused by a genuine transform alias, not an engine refusal. Graph-level status was replayed only for this clean case and its exact adapter-level noise repeats; the remaining sigma-12 canonical-key misses and the negative controls were not audited at graph level. The v1 “all errors are refusals” statement must not be used as a substrate-level result.

## Next measurement requirement

Future transfer captures must record, per observation, graph `status`, selected generator and parameters, graph transform explanation, exact transformed-signature equality, and adapter output. Score adapter compatibility separately from graph recognition, measure transform equivalence classes, and report canonical-label accuracy only on cases where the intended operator is identifiable from the held vocabulary. Preserve aliased cases as a separate result group.
