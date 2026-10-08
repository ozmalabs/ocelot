# Generic continuous audit v1 — results

The locked 20-panel capture and independent analyzer passed all six gates:
current source and upstream capture binding, panel pairing, deterministic sample
replay and disjointness, native/oracle transcript replay, post-decision sealed
holdout scoring, and help-control presence.

The task-agnostic sampler independently draws four continuous inputs uniformly
from `[-2.4,2.4]` and presents up to 64 oracle labels per candidate. At caps of
4, 16, and 64 labels, outcomes are identical: 12 holdout-correct candidates
accepted, seven false candidates accepted, and one no-candidate panel sent to
help. No sampled point exposed a disagreement in any of the seven candidates,
even with 64 queries each. The cap-64 median is 64 labels; the total is 1,216
labels across 19 candidates. By comparison, the paired task-conditioned audit
accepted the same 12 correct candidates, rejected all seven false candidates
to help, and used 62 labels total (median four when a candidate existed).

This is a negative result for this task-agnostic sampler and these candidate
residuals: random points over the four-dimensional box did not hit the narrow
regions where the incorrect formulas diverged from the target, while targeted
positive/near-miss construction did. More random labels did not compensate
within the measured budget. It is not evidence that uniform sampling cannot
work under other distributions or larger budgets. The result also does not
establish the task-conditioned generator as a deployable policy: it is informed
by task structure. Per-query wall time was not instrumented in this v1 capture;
label count is the complete acquisition-cost measure reported here.

Next compare Term-directed probes extracted from candidate syntax, a broader
random budget, and conservative abstention on held task families. The stronger
learning gate remains end-to-end residual-driven resynthesis, with proposal
quality and all acquisition/search costs measured. No candidate was resynthesized
in this post-search audit.

Artifacts: [preregistration](GENERIC_CONTINUOUS_AUDIT_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/generic_continuous_audit_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_generic_continuous_audit_v1.py), [source lock](../../../evaluation/substrate_capability/generic_continuous_audit_v1_lock_20261004.json), [capture](../../../evaluation/reports/generic_continuous_audit_v1_20261004.json), and [analysis](../../../evaluation/reports/generic_continuous_audit_v1_analysis_20261004.json).
