# MetaShape downstream categorisation utility preregistration (2026-09-26)

## Downstream decision

Measure the actual `domains.teach.categorise_by_shape` output used by `teach()` when no explicit category/categoriser determines filing. The decision is a MetaShape filing label or `None` (abstain). The gold label is fixed by the generated example's declared family and control status; it is not inferred from the system's output.

## Paired protocol

Use one fresh adapter with `shape_vocabulary` and `meta_shape_growth` loaded. Before training, record the classifier output for every locked query. Then submit the eight training items (two per family) through `teach()` with explicit isolated training category, allowing the shape observer/growth rules to operate. Identify the three newly minted support-2 family shapes; MotionRule is a prior-only positive control expected to use the existing `spatial_dynamics` label. Run the identical query list through `categorise_by_shape` again, with no graph mutation from queries.

Families/input values match the fixed-value sensitivity protocol. Five queries per family:

1. Positive new values with fixed field preserved: expected label is that family's minted MetaShape; for MotionRule, `spatial_dynamics`.
2. Fixed-value mismatch: expected `None` for FrameBinding/ResourceTransfer/GoalTrace; `spatial_dynamics` for MotionRule (the declared family is unchanged).
3. Missing fixed field: expected `None` for the three minted families; `spatial_dynamics` for MotionRule.
4. Extra `unexpected_slot="noise"` with other fields preserved: expected the family label (new MetaShape or `spatial_dynamics`), since the structural matching rung is open to added relations.
5. Same values under a `*Distractor` type: expected `None` for all families because the declared item type changes.

Thus the gold vector contains 3 × (family, abstain, abstain, family, abstain) for newly minted families and (spatial_dynamics, spatial_dynamics, spatial_dynamics, spatial_dynamics, abstain) for MotionRule. Query order is family order from the prior sensitivity protocol, then the five query classes above.

## Metrics and gates

Report paired exact accuracy, coverage, abstention precision/recall, per-class/per-family confusion, and transitions baseline→trained. Count source-lock and input-count integrity as admission gates; do not require the classifier to pass an accuracy threshold. Keep `None`, minted-structure labels, and prior labels distinct. Seed persistence is disabled; training writes, if any, go to a temporary directory.

This is a 20-query synthetic schema-classification benchmark. It measures utility of a real consumer on this authored label oracle only; it does not establish natural teaching quality or broad concept semantics.
