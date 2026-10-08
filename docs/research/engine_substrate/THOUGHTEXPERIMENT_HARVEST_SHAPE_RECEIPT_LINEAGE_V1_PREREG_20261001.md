# Harvest-shape receipt lineage v1 preregistration

**Question.** Does Direct versus receipt adoption change the selected `scale_cancellation` shape's source Microtheory metadata for the corpus-derived `batch_normalization` homonym?

## Fixture and comparison

In three fresh workers, full-boot the frozen seed corpus. Select the `has_concept` name `batch_normalization`, requiring exactly two target nodes and two owner Microtheories; expected full-boot identities are recorded by the preceding census-derived probe. Fork one immutable snapshot into Direct and receipt branches. Both remove the selected name's original ownership rows and add the same rewired rows in higher-owner-ID-first order. Direct state is evaluated directly; the receipt branch's journal delta is adopted into the unchanged primary at the captured revision. Run `harvest_shapes()` on Direct and adopted primary, and record the `scale_cancellation` shape plus complete selected shape signatures.

## Gates

Require three fresh PIDs, exact fixture shape, stable source/seed fingerprints, exact canonical whole-graph equality between Direct and adopted primary, identical selected shape identities/content excluding `source_mt` and `source_mt_id`, and a changed `scale_cancellation` owner attribution matching one of the two fixture owners. Collect no timings.

## Limits

The ownership rewire is controlled, not a natural task. A changed shape metadata result proves propagation from receipt edge ordering into the active harvester output. It does not by itself prove changed postulate firing or task performance. Such a claim requires a separately gated applicability continuation.
