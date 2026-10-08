# ProblemShape structural key and solver behavior crosswalk v1

This post-hoc evidence join relates two independently analyzed, source-locked panels: unseeded schema acquisition/transfer and BP parameter semantics. It does not rerun either experiment and was not preregistered as a cross-study test. Both upstream analyzers pass (10/10 and 7/7 checks), and worker source-stability gates pass in both reports.

In the transfer panel, four within-worker `max_product`/`sum_product` pairs—two recurrence workers and two mixed-family workers—share the same `ps_has_combine=yes_has_targets_mt=yes` structural key. Both settings end recognized by the same BP schema. This is the intended structural behavior of the codebook.

In the separate BP behavior panel, six pairs over three selected resident networks also share the same key, while every pair returns a different belief map. The maximum absolute per-variable belief difference is 2.0 in all six pairs. `sum_product` converges in all six workers; `max_product` reports nonconvergence in four. These are observable behavior differences, not a judgment that one answer is better.

The combined evidence therefore supports schema recognition and recurrence transfer for a narrow structural class, while showing that the key is not a behavioral-equivalence certificate. The substrate retains the `combine` value on each Goal; any downstream consumer using a recognized `ProblemShape` to select or substitute behavior must still inspect and validate that parameter. No broader false-mint precision estimate follows from this one omitted behavior dimension.

Next gate: on a preregistered held-out solver panel, measure whether downstream consumers preserve behavior-changing Goal parameters when reusing a learned structural key. Include exact-output or independent solver-quality oracles, multiple graph topologies, parameter values, and near-neighbor schemas; separately count correct structural recognition, unsafe behavioral conflation, abstention, and acquisition cost.

Artifacts: [crosswalk analyzer](../../../scripts/analyze_problem_shape_key_behavior_crosswalk_v1.py), [machine-readable join](../../../evaluation/reports/problem_shape_key_behavior_crosswalk_v1_20260928.json), [schema transfer result](SUBSTRATE_PROBLEM_SHAPE_UNSEEDED_SCHEMA_TRANSFER_V1_RESULTS_20260927.md), [BP parameter semantics result](SUBSTRATE_PROBLEM_SHAPE_BP_PARAMETER_SEMANTICS_V1_1_RESULTS_20260927.md).
