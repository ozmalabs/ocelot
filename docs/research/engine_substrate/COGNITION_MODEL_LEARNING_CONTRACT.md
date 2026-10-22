# Observed process learning contract v1

Status: semantic freeze for P8.01–P8.E3. It defines what transition evidence can support. It does not claim that a learned model, latent-state mechanism, informative experiment policy, or external-world adapter exists yet.

## 1. Observation and transition identity

A `TransitionObservation` is an append-only source record with owner, episode/event IDs, source/model/frame epochs, sequence index, typed pre-state facts, the actually emitted action and sink receipt, and the subsequently observed post-state facts and outcome receipt. Its identity is `(owner, episode, event, source_epoch, model_epoch, frame_epoch)`. Predictions, recalled episodes, asserted labels, imagined states and unreceipted results cannot be used as observed transition support.

Bindings are typed and source-bound. A candidate effect may refer to a variable only when the trace contains the same observed object reference in pre-state and action context. Object identity can be abstracted to a declared type only after the same relation is witnessed on at least two distinct objects. The learner cannot invent unobserved parameters, silently coerce types, or use a hidden task answer.

## 2. Candidate portfolios and evidence

Induction enumerates only the finite supported effect templates: add/remove/set a typed feature, or a declared finite relation change. Every candidate retains its exact supporting transition IDs, counterexamples, owner and epoch tuple. Candidates consistent with all evidence remain in a portfolio; the learner cannot choose one favored model when observations do not identify it. Empirical frequencies are distributions with support and unknown mass, not exact deterministic laws. A complete finite-state proof or a complete separating probe set is required before marking an exact law.

A counterexample appends evidence and revises confidence/support; it never edits the historical trace. A candidate with a contradicted effect becomes `DISPUTED`, while other consistent candidates remain available. An update to source/model/frame epoch invalidates current views and plans but retains historical observations. Missing evidence or observationally indistinguishable candidates yields `UNKNOWN`/`NOT_IDENTIFIED`.

## 3. Identity, transfer and invalidation

A learned schema separates action identity from parameter binding and effect. It may apply to an untouched object only when its declared type/feature binding is present and the learned effect is independent of object identity across the witnessed instances. Prediction output is marked `predicted`, never `observed`. Only a matching source-bound outcome can verify or refute it.

An old plan or cached process view is current only for the exact model and source epochs it names. A counterexample or model-epoch change marks dependent artifacts stale; host action authorization remains outside the learner and may veto any consequence.

## 4. Bounds and funding

The disabled-by-default `ModelLearningPolicy` bounds live hypotheses to 32 per owner/domain, event references examined per request to 200, candidate templates to the frozen finite set, induction rule work to 2,000 steps, and retained transition evidence to a declared ring/window policy without deleting provenance references. Any optional portfolio expansion, latent search, or intervention refinement is requested through the shared ThinkingBudget before computation. A debit is unique by owner, operation, source epoch, and evidence key. Exhaustion and expiry end as `UNKNOWN`/`TIMEOUT`; they do not promote a partial candidate.

The base ingestion of a real world event is mechanical adapter work. Python may validate the wire schema, append source records, tick native rules under a bound and read graph outcomes. It cannot infer an effect, select a hypothesis, repair a prediction, or choose the experiment.

## 5. Acceptance and controls

- `test_effect_learned_from_trace`: a repeated observed action/pre/post trace mints a typed candidate with every source witness.
- `test_unseen_object_binding`: a candidate supported on two objects predicts on a third object with the same declared type, without mutating the observation.
- `test_counterexample_revises_model`: contradictory receipt appends counterevidence, disputes the contradicted candidate and preserves alternatives/history.
- `test_indistinguishable_hypotheses_retained`: observations that do not distinguish two effects preserve both and report `NOT_IDENTIFIED`.

Implementation controls cover no trace, imagined-only trace, duplicate IDs, stale or cross-owner receipts, changed object type, missing action sink receipt, model-epoch invalidation, interrupted funding, and restart without double debit. Evaluation separates exact supported finite laws from empirical/distributional fit; a finite training fit alone never claims a general law.
