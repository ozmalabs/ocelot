# Term deduplication and class-return ablation v1 results

## Results

The 25 frozen candidate pools contain 90 hypothesis rows but only 51 unique
canonical Term JSON values: exact deduplication removes 39 rows (43.3%). All
30 removed rows are in the five opposition panels and three inequality
panels. Each of the five original `behavior_class` decisions contains four
candidate IDs for one canonical Term. The corresponding thoughtexperiment
receipts therefore carry duplicate representations rather than four
structurally distinct hypotheses.

Rerunning the same policy after exact Term deduplication changes all five
opposition outcomes from `behavior_class` to `exact_term`. Across all 25
panels, the deduplicated run ends at `exact_term`, with no false or mixed
survivor set on the declared finite holdout. The deduplicated run uses 70
labels total versus 60 in the original capture; median labels rise from two
to three. Each opposition case uses three labels after deduplication versus
one before, because the singleton path takes two challenge labels. Thus
deduplication removes spurious class ambiguity and preserves finite-domain
correctness, but this policy configuration does not reduce label cost.

## Interpretation and limits

This corrects the earlier interpretation of the five class-return panels.
They show safe handling of duplicate grammar outputs and successful graph
transport of their IDs. They do not establish useful equivalence-class
return among structurally distinct hypotheses. Exact JSON deduplication
cannot merge different Terms with equivalent behavior; broader semantic
deduplication would require its own coverage and soundness study. The result
also exposes a policy tradeoff: the deduplicated singleton challenge rule
spends more labels than returning a finite class containing duplicate IDs.
The upstream generator, five authored numeric tasks, and finite holdout bound
all conclusions.

## Reproduction artifacts

- [Preregistration](TERM_DEDUPLICATION_CLASS_RETURN_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/term_deduplication_class_return_v1.py)
- [Source lock](../../../evaluation/substrate_capability/term_deduplication_class_return_v1_lock_20261004.json)
- [Capture](../../../evaluation/reports/term_deduplication_class_return_v1_20261004.json)
- [Independent replay analyzer](../../../evaluation/substrate_capability/analyze_term_deduplication_class_return_v1.py)
- [Replay analysis](../../../evaluation/reports/term_deduplication_class_return_v1_analysis_20261004.json)
- [Post-capture structural-diversity audit](../../../evaluation/substrate_capability/analyze_term_deduplication_class_return_v1_1.py)
- [Structural-diversity analysis](../../../evaluation/reports/term_deduplication_class_return_v1_1_analysis_20261004.json)
