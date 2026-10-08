# Native primitive-family selection transfer v1 results

## Integrity and native responsibility

All ten locked panels (five additive, five product) completed and passed the capture gates. Independent analysis passes all 12 replay checks: it reconstructs the validation/test rows, re-evaluates every native candidate prediction, recomputes validation agreement counts, verifies unique native `ArgminUnique` selection, confirms the target task identity is absent from graph attributes, checks label-after-prediction receipts, and independently scores each sealed grid.

The selection decision is made by a graph rule over two candidate nodes. Candidate formulas, task menu, validation inputs, and validation labels are supplied by the harness; task identity is held only by the scorer. No host code compares candidate scores or writes the chosen family.

## Outcomes

The native selector chooses the correct family in all ten panels with no score ties or abstentions. All five additive panels select additive; all five product panels select product. Each target-family candidate is exact on its 1,296-row evaluation grid in every matching panel. The selected candidate is therefore correct on 12,960/12,960 sealed rows across these panels. The supplied menu includes a useful candidate in every task, so this does not measure refusal when neither candidate applies.

On each validation pool, the target-family candidate scores 32/32. The alternative scores 27–30/32. On additive panels the product alternative accumulates 270 false positives and 400 false negatives over the five grids; on product panels the additive alternative accumulates 400 false positives and 270 false negatives. These exact-grid counts describe two supplied formulas on a finite grid, not arbitrary real-valued inputs.

Median per-panel costs are 0.223 ms for validation prediction closure, 0.095 ms for graph score closure, 0.059 ms for selection commit, and 111.2 ms total worker CPU. Median peak RSS is 44,806 KiB. Test-grid prediction closure and end-to-end wall costs remain in the raw capture for phase-specific inspection; this small graph result is not a scale curve.

## Interpretation boundary

This is a separate input family from the orientation selector and shows that native validation scoring, unique choice, and held-out application can operate on supplied symbolic numeric relations. It is a replication on previously authored panels, with a two-item operator menu and a known useful candidate in every case. It does not demonstrate open-ended primitive invention, task discovery, general numeric reasoning, or self-improvement. In combination with the visual results, it supports bounded cross-domain graph-native model selection; the visual cohort also shows that validation ties and transfer utility depend on task and partition.

## Reproduction artifacts

- [Protocol](SUBSTRATE_NATIVE_PRIMITIVE_FAMILY_SELECTION_TRANSFER_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/native_primitive_family_selection_transfer_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_native_primitive_family_selection_transfer_v1.py)
- [Source lock](../../../evaluation/substrate_capability/native_primitive_family_selection_transfer_v1_lock_20261005.json)
- [Raw capture](../../../evaluation/reports/native_primitive_family_selection_transfer_v1_20261005.json)
- [Analysis](../../../evaluation/reports/native_primitive_family_selection_transfer_v1_analysis_20261005.json)
