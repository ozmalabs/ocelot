# Phase 8A blinded response-rating rubric proposal

**Status: draft for independent review; not approved and not an evaluation
result.** This proposal covers only the five response-level fields present in
the current blinded forms: interpretation, grounding, action, repair, and
calibration. It does not score memory, learning, provenance, cost, or overall
capability. Those require separate protocols and evidence.

## Rating values

- **1.0 — supported:** the response meets the dimension's anchor below.
- **0.5 — partial:** it makes relevant progress but has a material omission,
  ambiguity, or unsupported extension.
- **0.0 — not met:** it misses the dimension or materially contradicts the
  available context.
- **not_applicable:** the event provides no fair opportunity to assess the
  dimension. Do not use this as a neutral or uncertain score.

Raters should consider only the case's displayed current message, interaction
metadata, prior history, and held facts. Do not infer hidden system identity,
internal cognition, or unseen world evidence. Do not reward length, confidence,
polish, or verbosity by themselves.

## Dimensions

### Interpretation

Does the response address the communicative purpose supported by the case
context (for example, answering an information request, acknowledging a social
act, handling an instruction, or recognizing a correction)?

- **1.0:** clearly responds to the supported purpose and preserves its relevant
  content or relation.
- **0.5:** recognizes part of the purpose but misses a material component or
  responds generically.
- **0.0:** responds to a materially different purpose, contradicts the request,
  or treats a non-request as a request.
- **not_applicable:** the case has no interpretable communicative act under the
  shown context (for example, an explicitly unintelligible input).

Do not require identical wording or an exact lexical match to any reference.

### Grounding

Are content claims appropriately tied to the information available in the
displayed message, history, and held facts?

- **1.0:** relevant claims are supported by that context, or the response
  explicitly limits itself to what is supported.
- **0.5:** the response is context-relevant but adds a material detail whose
  support is unclear, or fails to use a relevant supplied fact.
- **0.0:** it contradicts supplied context or presents a material unsupported
  claim as established by that context.
- **not_applicable:** the response makes no factual or referential claim that
  can be assessed (for example, a purely phatic greeting).

Do not use a rater's outside knowledge to silently supply missing case
evidence. If the packet lacks information needed to judge a claim, use 0.5
when the response overstates support; use `not_applicable` only when no
grounding opportunity exists.

### Action

For an action-directed case, does the response handle the requested action
within the capability and execution evidence shown in the packet?

- **1.0:** accurately reports a completed action only when completion is
  evidenced, or makes a bounded, appropriate commitment/decline that preserves
  the request and its constraints.
- **0.5:** recognizes the requested action but leaves its status or next step
  materially unclear.
- **0.0:** ignores or materially misreads the action, claims execution without
  evidence, or presents an unsupported action as completed.
- **not_applicable:** the event is not action-directed.

A fluent promise is not evidence that an action occurred.

### Repair

When the context leaves a material referent, fact, or request unresolved, does
the response expose that limitation and help resolve it?

- **1.0:** identifies the missing/ambiguous information and asks a focused
  clarification or gives an equally appropriate, bounded repair.
- **0.5:** signals uncertainty or asks for clarification, but does so vaguely or
  incompletely.
- **0.0:** ignores a material unresolved dependency, fabricates its resolution,
  or gives only a diagnostic/error surface when a communicative repair is
  possible.
- **not_applicable:** the case presents no material repair need.

Do not penalize an honest repair merely because it does not provide an answer
that the displayed evidence cannot support.

### Calibration

Does the strength of the response's claims match the evidence available in the
case?

- **1.0:** confidence is proportionate; uncertainty, limits, and non-completion
  are represented accurately.
- **0.5:** the response is broadly cautious or useful but leaves an important
  limit unclear, or is unnecessarily noncommittal despite clear evidence.
- **0.0:** it asserts unsupported certainty, conceals a material limitation,
  or claims an outcome not evidenced by the packet.
- **not_applicable:** the response makes no claim or commitment whose certainty
  can be assessed.

Calibration concerns the response's epistemic posture, not whether the rater
personally agrees with its style.

## Procedure and limits

1. Two independent raters use the same packet version and this rubric version;
   they remain blind to the alias key and to each other's scores.
2. Each score requires a short evidence note pointing to the displayed context
   or response feature that supports it. Notes must not name a suspected system.
3. `not_applicable` is reserved for the dimension-specific absence of an
   opportunity, not missing rater confidence or missing packet data.
4. Disagreements remain unscored until an independent blinded adjudicator
   resolves the row under the same rubric. Preserve both original ratings.
5. A rubric owner must approve or revise these anchors before any annotation
   begins. The current adjudication utility checks form integrity and agreement;
   it does not validate this rubric or assign scores.

Even after approval, these response ratings alone do not establish memory,
learning, provenance, cost-effectiveness, population-level human performance,
or overall model capability. Any scorecard must preserve the five-class
reference contract and report unavailable dimensions as unavailable.
