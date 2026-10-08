# Thoughtexperiment A8 proposal bridge v1 — preregistration

**Question:** Can the live graph-resident A8 structural composer emit a useful candidate for the navigation polarity task through the thoughtexperiment branch evaluator, and how does that proposal compare with the unchanged host candidate generator on the same held-out cases?

## Scope and hypothesis

This is a responsibility-boundary bridge for the existing chosen-action-rule composer. It does not extend the composer to arbitrary rules. Four fresh workers each receive a faulted `hop_descend_gradient` rule and the same held-out directions (`down`, `right`) used by the blinded proposal-utility v1.2 adapter.

The primary prompted arm adds a graph-resident `CapabilityAxis` whose residual includes `flip`, `comparison`, and `gate`, calls the production `ground_concern` path, and uses only the rule variant emitted by the graph composer. It must not use or fall back to `_default_candidates` to fill a missing proposal. The unprompted control supplies only the common `test/send/judge/structure/gradient` residual and records whether the composer honestly abstains. The unchanged `_default_candidates` list is evaluated as a reference set and default-order policy, not as a source for the graph proposal.

Predictions registered before capture:

1. The prompted path is served by the graph composer, selects `flip_comparison`, and emits one variant of the faulted target.
2. The graph proposal digest matches the host list's `flip_comparison` candidate modulo the generated rule name and passes both held-out directions.
3. All host candidates are scored on the held-out split; exactly the graph proposal and the host `flip_comparison` candidate pass.
4. The unprompted composer abstains because no applicable EditOp has positive keyword overlap.
5. The target rule is unchanged by composition and every evaluation branch preserves its source context and verifies its receipt.

Any failed prediction is retained and reported. Do not change the cue, target rule, or operator set after viewing results.

## Staged protocol

Before capturing orders or outcomes, lock the runner, analyzer, adapter, navigation fixture and preregistration, A8 composer/rule sources, task seeds and dependencies, native build inputs, and loaded binary. The order stage captures the faulted source rule, complete host reference candidate list and descriptors, prompted graph proposal, unprompted proposal/abstention, target-rule before/after evidence, and timing components. It contains no held-out utility outcomes. Inspect that capture for complete workers, graph-served composition, candidate identities, cue separation, source stability, and absence of scores before scoring.

The separate scoring stage evaluates every host candidate once with `adapters.score` on a fresh held-out context. A graph proposal identical by normalized digest to a host candidate reuses that exact held-out outcome row; if it is a distinct valid proposal, score it once on an isolated branch. The scorer also recomputes source and fault controls and records direct task cases, receipt verification, and primary preservation. It does not return any label to the proposal/order stage.

## Measures and cost

Report per worker:

- graph route, selected operator, exact target and proposal digest;
- candidate-set digest inclusion and full candidate-level held-out utility;
- prompted and unprompted proposal behavior, including invalid outputs and abstentions;
- host candidate default-order first-success prefix and graph single-candidate outcome;
- target-rule preservation, primary branch isolation, receipt validity, and task cases;
- candidate enumeration, full `ground_concern`/composer time, measured A8 applicability precompute time, common task setup, branch creation, patch, task scoring, and receipt verification costs.

Report common task construction once and separate it from host enumeration, graph composition, and attempted candidate evaluation. Report exhaustive reference-scoring cost separately from the host default-order's operational prefix. The graph arm's operational search includes composition plus its one candidate trial. No production adoption or open-ended learning cost is measured.

## Interpretation boundary

A pass establishes a prompted graph-composed rule variant as a useful thoughtexperiment candidate on one authored task family. It does not establish autonomous target diagnosis, candidate diversity, extension beyond chosen-action rules, natural-task prevalence, general capability, or self-improvement. Host applicability extraction and adapter orchestration remain explicit residual responsibilities.

## Required artifacts

Source lock, blind order capture, held-out capture, and analyzer output must be written under `evaluation/`. The analyzer hash is part of the pre-capture lock. Preserve failed runs and report every preregistered prediction and integrity gate.
