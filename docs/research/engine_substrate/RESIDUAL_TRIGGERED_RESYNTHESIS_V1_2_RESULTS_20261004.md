# Residual-triggered resynthesis v1.2 — budget diagnostic

The corrected v1.2 source-locked capture passes all six independent gates:
source/upstream binding, paired triggered cohort, first-observed residual
provenance, candidate fit to acquired examples, selector replay, and sealed
holdout rescoring after policy decisions.

V1.1 had timed out all operator branches at 0.5 seconds. V1.2 changes only the
per-operator budget to 2 seconds and repeats the same six triggered panels with
paired original-example and one-residual arms. At this budget, both arms find
at least one holdout-exact candidate in all six panels. Each arm accepts five
exact candidates and requests help on one unresolved panel; neither makes a
false acceptance. Exact-candidate availability and final correctness are
identical between arms. The residual arm has fewer distinct candidates in all
six panels (24→22, 31→11, 21→18, 9→6, 29→16, 18→13) and uses three rather than
four median selection labels. Median synthesis time is 7.79 seconds in the
control and 7.87 seconds with residuals across four two-second branches.

This identifies a budget effect: increasing search time from v1.1's 0.5
seconds to 2 seconds per branch recovers exact candidates in all triggered
panels, including the same exact-candidate coverage in both arms. The one
residual adds no measured heldout-quality gain at equal budget; its candidate
pool reduction and small label saving do not establish an economic advantage
because the search time is unchanged and only six panels are measured. One
panel remains ambiguous after selection and correctly requests help. The
closed grammar, four numeric families, and current candidate support limit
transfer claims; no candidates are installed.

Next increase task-family and support diversity, test whether residuals
provide value under compute-matched search-allocation policies, and measure
end-to-end repeated-task amortization. Keep exactness and false-adoption
outcomes primary over candidate-count reduction.

Artifacts: [original preregistration](RESIDUAL_TRIGGERED_RESYNTHESIS_V1_PREREG_20261004.md), [v1.2 amendment](RESIDUAL_TRIGGERED_RESYNTHESIS_V1_2_AMENDMENT_20261004.md), [runner](../../../evaluation/substrate_capability/residual_triggered_resynthesis_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_residual_triggered_resynthesis_v1_2.py), [source lock](../../../evaluation/substrate_capability/residual_triggered_resynthesis_v1_2_lock_20261004.json), [capture](../../../evaluation/reports/residual_triggered_resynthesis_v1_2_20261004.json), and [analysis](../../../evaluation/reports/residual_triggered_resynthesis_v1_2_analysis_20261004.json).
