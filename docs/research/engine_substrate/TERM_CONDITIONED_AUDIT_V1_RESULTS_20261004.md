# Term-conditioned audit v1 — results

The source-locked capture and independent analyzer pass all seven gates,
including current source/upstream binding, paired candidates, deterministic
Term-conditioned proposal replay, balanced candidate-prediction classes,
disjointness, native/oracle transcript replay, post-decision sealed holdout
scoring, help control, and nonnegative timing records.

The task-blind policy uses candidate predictions to collect up to 32
predicted-true and 32 predicted-false inputs from a 25-value quarter-step
support, then checks them with the task oracle. Across 20 fixed candidates,
there are 12 holdout-exact and seven false candidates, plus one panel without
an accepted candidate. At 4 labels, the policy accepts 12 exact and six false
candidates and helps on two; at 16 labels, it accepts 12 exact and four false
candidates and helps on four; at 64 labels, it accepts 12 exact and one false
candidate and helps on seven. The remaining false acceptance is an absolute-
value panel whose incorrect Term agrees with all sampled support points.

At the 64-label cap, it rejects six of seven false candidates while preserving
all 12 correct candidates. The policy uses 21,039 native candidate-Term
evaluations total (median 731.5 per panel; median proposal-generation wall time
6.36 ms and CPU time 6.36 ms). The paired uniform continuous sampler found no
false candidate in 64 oracle labels each. The task-conditioned audit rejected
all seven false candidates with 62 labels total, but uses task-aware templates.
Thus candidate-conditioned proposals improve error detection over uniform
sampling on this fixture, but cost many Term evaluations and still miss a
false candidate. Results do not generalize beyond these four authored task
families and the specified support. The policy is candidate aware, does not
use the task label to propose, and does not resynthesize from residuals.
Passing this finite audit cannot certify equivalence.

Next vary independently authored task families and support shape, add
adversarial finite-support aliases, and feed mismatches into residual-driven
resynthesis with total proposal/query/search cost and final adoption quality
measured. Per-query label cost and proposal-generation cost must remain
separate in those comparisons.

Artifacts: [preregistration](TERM_CONDITIONED_AUDIT_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/term_conditioned_audit_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_term_conditioned_audit_v1.py), [source lock](../../../evaluation/substrate_capability/term_conditioned_audit_v1_lock_20261004.json), [capture](../../../evaluation/reports/term_conditioned_audit_v1_20261004.json), and [analysis](../../../evaluation/reports/term_conditioned_audit_v1_analysis_20261004.json).
