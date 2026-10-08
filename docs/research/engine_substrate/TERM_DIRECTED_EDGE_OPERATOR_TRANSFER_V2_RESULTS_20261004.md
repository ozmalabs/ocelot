# Term-directed edge-probe operator transfer v2 — results

The locked capture passes all nine independent gates, including provenance,
three-panel pairing, training-example fit, bitwise float disjointness, probe
and selector replay, holdout replay, cost accounting, the signed-zero control,
and the structured false-class control.

The Abs/Times panel rejects the squared-equality candidate with one label;
its 4,096-case heldout error count is 877, while both remaining Terms score
zero errors. The Div/Eq panel rejects `(ax/ex)==1` with one label at positive
zero/zero. Its disjoint holdout includes negative-zero cases, where the
quotient candidate disagrees six times; the exact identity has zero errors.
This confirms the bitwise-distinct signed-zero holdout catches the same
zero-denominator failure without reusing the query row.

The structured literal-alias control exposes a policy failure. The candidate
`(ax==ex) OR ((ax==0.125) AND (ex==0.25))` agrees with the identity on every
registered probe, so the finite behavior-class policy accepts both Terms
without an oracle label. The sealed holdout contains the literal pair and
records two mismatches for the candidate. The exact identity has zero. This
shows that variable-pair edge agreement does not justify accepting a finite
behavior class: hidden literal guards can remain untested. Strict syntactic
singleton acceptance would abstain on this panel. Policy costs are 223 native
Term evaluations/1.05 ms for Abs/Times, 63/0.38 ms for Div/Eq, and 88/1.03 ms
for the structured control; oracle labels are 1, 1, and 0.

The result establishes narrow transfer and a concrete false-class risk, not a
safe acceptance rule. The next repair is to add task-blind Term-literal
proposals, compare them against edge-only probes on this locked alias control,
and retain help/abstention where the syntax-directed slate cannot separate
survivors. More generally, no finite sampled class should be described as
universally equivalent without a proof or a stated bounded domain.

Artifacts: [preregistration](TERM_DIRECTED_EDGE_OPERATOR_TRANSFER_V2_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/term_directed_edge_operator_transfer_v2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_term_directed_edge_operator_transfer_v2.py), [source lock](../../../evaluation/substrate_capability/term_directed_edge_operator_transfer_v2_lock_20261004.json), [capture](../../../evaluation/reports/term_directed_edge_operator_transfer_v2_20261004.json), and [analysis](../../../evaluation/reports/term_directed_edge_operator_transfer_v2_analysis_20261004.json).
