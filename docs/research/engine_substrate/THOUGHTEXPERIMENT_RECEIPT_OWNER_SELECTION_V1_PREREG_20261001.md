# Receipt owner-selection diagnostic v1 preregistration

**Question.** Can the existing receipt diff/apply path change the output of `implication_harvester._owning_mt_map()` relative to direct execution of identical edge writes, while preserving the same canonical graph facts?

## Frozen fixture and comparison

In each fresh worker, create a base substrate with node IDs 0=`Microtheory(mt_a)`, 1=`Microtheory(mt_b)`, and 2=`Concept(shared_concept)`. From one immutable snapshot, create a Direct branch and a receipt branch. In both branches, add `mt_b --has_concept--> shared_concept` followed by `mt_a --has_concept--> shared_concept`. Direct readout calls `_owning_mt_map()` on the Direct branch. Receipt readout captures the branch's `conclusions` journal delta, applies it to the unchanged primary at its expected revision, and calls `_owning_mt_map()` on the adopted primary.

## Gates

Run eight fresh worker processes. Require the same two added edge facts and exact canonical edge-key parity between Direct and adopted primary. Record direct and adopted helper outputs and require source/native fingerprints stable before and after. This is a mechanism diagnostic, not a benchmark; exclude timings.

## Limits

The fixture deliberately includes two distinct target nodes with the same name and two owners to make the helper's name-keyed ambiguity observable. It proves the receipt path can alter this helper's result under that condition. It does not show that natural task execution creates this exact ambiguity or that all consumers should use this helper's choice. See the separate full-seed [ownership census](THOUGHTEXPERIMENT_OWNERSHIP_ORDER_CENSUS_V1_RESULTS_20261001.md) for corpus prevalence.
