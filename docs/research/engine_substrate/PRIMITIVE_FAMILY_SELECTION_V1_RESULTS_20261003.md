# Primitive-family selection v1 results

## Result

The source-locked experiment covers all five additive and all five product
panels from adequacy audit v1.1. Independent analysis passes all six gates,
including input replay, entropy/fixed-order transcript replay, candidate and
final holdout rescoring, and source/capture binding.

Both candidate operator families (Plus and Times) were synthesized in every
panel. The maximum-entropy policy reaches an exact singleton in the correct
family in 5/5 additive and 5/5 product panels, using median two oracle labels
per task. The fixed-order policy reaches an exact singleton in 3/5 panels per
task and remains ambiguous in 2/5 per task; median label count is five for
additive and six for product. Neither policy ends in an empty or false
singleton in these panels. Median synthesis wall time is 2.10 seconds for the
Plus family and 1.75 seconds for Times; the local oracle supplies all labels.

## What this measures

This is evidence that, given a two-family operator menu and a usable pool of
input/output examples, active query selection can distinguish the useful
primitive family on these ten numeric panels. It progresses beyond a
harness-selected primitive hint: the two candidate families are both searched,
and the task label is not passed to either query policy. It does not establish
open-ended primitive discovery. The menu contains only Plus and Times, targets
are two closely related authored numeric relations, and the local harness
provides labels without measuring real-oracle economics. The 1,296-case grid
scores outcomes after the policy stops and is not exposed during selection.

A useful next step is to broaden the primitive menu and add task families that
require different arities, compositions, or nonnumeric operators. Include a
help-request action with an explicit cost, operator families that are
irrelevant or harmful, and hidden task identity. Measure family-selection
accuracy, exact held-out transfer, false singleton, empty/ambiguous outcomes,
labels, search cost, and end-to-end decision cost. Keep widening and help
selection distinguished from autonomous self-modification.

## Reproduction artifacts

- [Preregistration](PRIMITIVE_FAMILY_SELECTION_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/primitive_family_selection_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_primitive_family_selection_v1.py)
- [Source and input lock](../../../evaluation/substrate_capability/primitive_family_selection_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/primitive_family_selection_v1_20261003.json)
- [Independent analysis](../../../evaluation/reports/primitive_family_selection_v1_analysis_20261003.json)
