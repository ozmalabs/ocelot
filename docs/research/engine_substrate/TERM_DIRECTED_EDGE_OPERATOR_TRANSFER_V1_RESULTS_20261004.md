# Term-directed edge-probe operator transfer v1 — results

The locked capture passes all seven independent checks: source/upstream
binding, two-panel coverage, candidate fit to training, task-blind probe
replay and disjointness, selector/class replay, separate wide-holdout scoring,
and cost accounting.

The same task-blind variable-pair stress generator finds one oracle-labeled
counterexample in both operator families. In the inherited Abs/Times panel,
`ax*ax == ex*ex` is rejected at `(1e-200, 2e-200)` due to underflow; the two
remaining candidates form one binary behavior class. On the separate
4,096-case holdout, the squared candidate has 879 disagreements and the two
survivors have zero. In the new Div/Eq panel, `(ax/ex)==1` agrees with the
target `ax==ex` on all eight ordinary prior selection rows and all training
examples. The edge selector chooses `(ax,ex)=(0,0)`; division-by-zero returns
zero, rejecting the quotient candidate while preserving the identity
candidate. The separate 4,096-case holdout has zero disagreements for both
identity and quotient Terms because it deliberately excludes the queried
zero/zero point; the query transcript is the evidence that falsifies the
quotient candidate. The policy performs one oracle query per panel, with 216
and 63 native Term evaluations and about 1.00 ms and 0.52 ms policy time,
respectively.

This transfers the probe construction from an Abs/Times underflow failure to
a Div/Eq zero-denominator failure. It does not show that the finite holdout
alone validates the quotient Term, nor that two authored arithmetic tasks
establish general operator transfer. No Term is installed. Next test other
operator families and independently selected task forms, ensure holdout
supports include nearby but disjoint arithmetic edge cases, and measure
false-class acceptance across structured nulls.

Artifacts: [preregistration](TERM_DIRECTED_EDGE_OPERATOR_TRANSFER_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/term_directed_edge_operator_transfer_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_term_directed_edge_operator_transfer_v1.py), [source lock](../../../evaluation/substrate_capability/term_directed_edge_operator_transfer_v1_lock_20261004.json), [capture](../../../evaluation/reports/term_directed_edge_operator_transfer_v1_20261004.json), and [analysis](../../../evaluation/reports/term_directed_edge_operator_transfer_v1_analysis_20261004.json).
