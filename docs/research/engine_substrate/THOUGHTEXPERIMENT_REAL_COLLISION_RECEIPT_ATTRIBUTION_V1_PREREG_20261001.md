# Real-collision receipt attribution v1 preregistration

**Question.** Does receipt edge ordering change source attribution for a multiply-owned concept name already present in the full seed corpus?

## Fixture selection

Each fresh worker performs the full seed boot. From the resulting graph, select the lexicographically first `has_concept` name with exactly two distinct target node IDs and exactly two distinct owning Microtheory IDs, where both source nodes are Microtheories. Record the name, both target IDs, both owner IDs/names, and original ownership rows. Selection is deterministic from sorted graph data.

## Comparison

Fork the same immutable full-boot snapshot into Direct and receipt branches. In both, remove the selected name's two original ownership rows, then add the same two rewired owner-target rows in reverse source order (higher owner ID first). Read `_owning_mt_map()` from the Direct branch. For the receipt arm, capture the `conclusions` journal delta and atomically apply it to the unchanged full-boot primary at its captured revision, then read the same helper. Compare complete canonical graph facts between Direct and adopted primary, selected name attribution, and receipt addition order.

## Gates

Use three fresh workers. Require full boot completion to return, source/native/seed fingerprints stable before and after, the selected collision meet the stated shape, Direct and adopted-primary canonical graph facts match exactly, receipt additions are sorted by edge key, and owner-map attribution differs. No timings are collected.

## Limits

The operation deliberately rewires two corpus-derived ownership rows to isolate ordering behavior; it is not a naturally occurring task trace or a proposed semantic mutation. It demonstrates whether the consumer result is sensitive to receipt ordering on real corpus identities and names, not whether that changed attribution is desirable. The full-boot seed failures are recorded.
