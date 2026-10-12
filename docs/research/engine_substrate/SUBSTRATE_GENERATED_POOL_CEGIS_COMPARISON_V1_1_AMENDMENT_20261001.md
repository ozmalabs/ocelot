# Generated-pool active query versus iterative resynthesis v1.1 amendment

The first preregistered invocation failed before task setup or measurement. All 12 scheduled workers raised `AttributeError` because the runner referenced `euler.HELDOUT`, a constant absent from the imported Euler task module. The failed capture is retained at [`initial_failure`](../../../evaluation/reports/substrate_generated_pool_cegis_comparison_v1_20261001_raw.json); it contains no benchmark evidence.

Correction: declare the six already preregistered held-out complexes directly in the comparison runner and lock that declaration. No task, grammar, arm, budget, stop rule, or success gate changes. The corrected replay uses a distinct `v1_1` lock and raw-capture path; the initial failure remains untouched. The runner also continues to require complete generated pools before selector outcomes count.
