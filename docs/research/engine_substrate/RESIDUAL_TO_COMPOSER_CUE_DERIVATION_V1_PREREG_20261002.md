# Residual-to-composer cue derivation v1 preregistration

## Question

Can the system convert an outcome residual into an operator-level composer cue using task state and a small, explicit action geometry, while abstaining when the residual does not identify a safe edit? The preceding raw-residual boundary result is the baseline: generic `actual`/`expected` fields mint an axis but do not ground it; the authored A8 cue composes successfully.

This is a bounded mechanism experiment, not a claim of open-ended self-improvement. The cue derivation is an explicit candidate mechanism. It must not use the expected target rule, a `name_hint`, or a supplied edit/operator label. It may read the task's declared action-to-displacement vocabulary and the observed state/action record.

## Candidate mechanism

For each action, obtain its displacement vector from the preregistered four-direction action table. Compare the observed action vector with the expected action vector. If the vectors are exact opposites on one axis, emit the existing A8 cue predicates `test`, `send`, `judge`, `structure`, `gradient`, `flip`, `comparison`, and `gate`; otherwise abstain. Preserve the raw residual alongside the derived predicates. The action table and cue schema are explicit authored inputs to this candidate decoder. The mechanism does not select a target rule: `ground_concern` must still find the applicable held relation. A proposal remains isolated and is scored before any primary-graph adoption.

## Preregistered panel

- Four navigation directions with a deliberately inverted action rule: Up/Down and Left/Right residuals. Use fresh workers and held-out positions/distances from the A8 panel.
- Four valid, non-inverted synthetic action discrepancies (orthogonal or same-direction wrong actions). These must abstain.
- Four underdetermined or malformed synthetic residuals (missing expected action, unknown action token, or zero displacement). These must abstain.
- Positive control: the existing authored A8 cue on a fresh matched context.
- Negative grounding control: derived cue against an unrelated target rule/context; it must not emit a proposal.

## Gates and measurements

Report per-cell cue, abstention, grounding, proposal target/operator/site, primary-rule preservation, and held-out task score. Require all inverted cases to derive the cue and compose the preregistered `flip_comparison` proposal; require zero proposals in all ambiguity, non-inversion, and unrelated-target controls. Positive control must pass. Record derivation, grounding, scoring, and total wall time separately. Source fingerprints cover the runner, protocol, task vocabulary, composer/reflective sources, seed closure, and loaded native binary. Any source drift invalidates the run.

Failure is informative: a missed inverted case, any false proposal, target leakage, or rule mutation fails the candidate. Passing establishes only a small, authored task-family bridge from residual geometry to an existing operator class. It does not establish learning of new operator semantics, broad transfer, or utility outside the measured panel.

## Baseline and next implementation

- Baseline capture and analyzer: [raw residual grounding boundary v1](../../../evaluation/reports/residual_to_composer_grounding_boundary_v1_20261002.json), [analyzer](../../../evaluation/substrate_capability/analyze_residual_to_composer_grounding_boundary_v1.py).
- Candidate implementation is not yet measured. Build a source-locked runner and independent analyzer against the gates above before drawing a capability conclusion.
