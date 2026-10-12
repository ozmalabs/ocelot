# Term-directed floating-point edge probes v1.2 — results

The v1/v1.1 captures are diagnostic: v1's analyzer referenced a missing
holdout constant; v1.1 compared a full finite score object against the
runner's compact result schema. The corrected, newly locked v1.2 capture
passes all eight independent checks, including upstream/current-source
binding, paired survivor identity, task-blind proposal replay, prior-pool
class replay, oracle/selector/behavior-class replay, strict-abstention control,
wide-holdout scoring, and cost accounting.

On both the no-residual and one-residual arms, the prior selection pool places
all three Terms in one observed behavior class. The Term-directed generator
extracts `ax` and `ex` from their syntax and proposes IEEE edge assignments.
The native selector chooses `(ax,ex)=(1e-200,2e-200)`; the oracle label is false.
The squared candidate `ax*ax == ex*ex` predicts true because both products
underflow to zero, so one label removes it. The two remaining Terms form one
binary behavior class on the probe slate and are accepted as a class; strict
syntactic-singleton control would request help. Policy cost is 221 native Term
evaluations and 2.09 ms wall time for the no-residual arm, and 218 evaluations
and 1.72 ms for the residual arm. Each policy uses one oracle label.

All three candidates score exact on the earlier 1,296-point ordinary-scale
holdout, so that holdout missed the numerical defect. On the separate 4,096
case seeded log-scale/ULP holdout, the squared candidate disagrees 520 times;
the two absolute-value candidates have zero disagreements and zero invalid
outputs. The holdout is finite and cannot prove universal equivalence. The
result demonstrates a narrow but concrete improvement: syntax-derived edge
probes expose a floating-point false candidate that the existing query pool
and ordinary-scale audit miss, while behavior-class return retains two exact
survivors. This is one authored task family and a harness-authored probe
policy, not generic float correctness or autonomous self-improvement.

Next transfer this probe construction to other candidate operators and
independently authored domains; include signed zero, NaN/infinity policy,
subnormal boundaries, and arithmetic-specific adversarial cases. Measure
false-class acceptance and query/search cost, and distinguish raw Term output
identity from the substrate's binary classification contract.

Artifacts: [preregistration](TERM_DIRECTED_FLOAT_EDGE_PROBES_V1_PREREG_20261004.md), [v1.1 amendment](TERM_DIRECTED_FLOAT_EDGE_PROBES_V1_1_AMENDMENT_20261004.md), [v1.2 amendment](TERM_DIRECTED_FLOAT_EDGE_PROBES_V1_2_AMENDMENT_20261004.md), [runner](../../../evaluation/substrate_capability/term_directed_float_edge_probes_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_term_directed_float_edge_probes_v1_2.py), [source lock](../../../evaluation/substrate_capability/term_directed_float_edge_probes_v1_2_lock_20261004.json), [capture](../../../evaluation/reports/term_directed_float_edge_probes_v1_2_20261004.json), and [analysis](../../../evaluation/reports/term_directed_float_edge_probes_v1_2_analysis_20261004.json).
