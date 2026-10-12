# Operator-hint blinding v1 — results

The source-locked study completed all ten panels and three arms per panel.
Both expanded grammars were synthesized from the same initial examples. The
joint policy received the union of generated candidates without a task-specific
operator hint and used the native maximum-entropy selector with task-oracle
labels. Independent replay passed all five gates: source/panel binding,
revealed-example fit, query/label/survivor replay, exhaustive registered
holdout rescoring, and complete arm coverage.

For the joint `Plus`+`Times` candidate pool, an exact model survived and was
returned on all five additive and all five product panels. The joint policy
resolved each panel as a singleton after 1–5 oracle labels (medians 2 for
additive, 2 for product). In every panel the survivor came from the task-
appropriate grammar family. The matched single-expansion controls show why
the hint matters: Plus-only resolves all additive panels but yields five false
singletons on product; Times-only resolves all product panels, while additive
has two empty sets and two false singletons. Joint synthesis costs a median
3.83–3.90 seconds per panel on this host, versus 1.73–2.12 seconds for a
single expansion. Candidate selection itself uses a median 158/253
candidate-input evaluations for additive/product joint pools.

This is the first bounded evidence here that examples and oracle-selected
queries can choose between two experimenter-declared primitive families when
task identity is withheld from candidate search. The expansion vocabulary is
only `Plus` versus `Times`; synthesis, task formulas, examples, and oracle are
still controlled. The joint route costs roughly twice a single grammar and
does not establish open-ended primitive invention, transfer outside these two
numeric families, or production self-improvement.

Artifacts: [preregistration](OPERATOR_HINT_BLINDING_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/operator_hint_blinding_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_operator_hint_blinding_v1.py), [source lock](../../../evaluation/substrate_capability/operator_hint_blinding_v1_lock_20261004.json), [capture](../../../evaluation/reports/operator_hint_blinding_v1_20261004.json), and [analysis](../../../evaluation/reports/operator_hint_blinding_v1_analysis_20261004.json).
