# Substrate synthesis off-support ambiguity v1 — preregistration

## Question

Does the standard graph-resident program-synthesis route distinguish a uniquely supported square function from a simpler program that matches an underdetermined sample, and does it refuse an inconsistent example set?

## Design

Use three neutral, request-text-matched tasks through the current production route `ensure_program_synthesis` → `ingest_spec` → `pump`. All examples bind the same field, `value`; no task name or request contains the word “square”, an operator list, or a grammar hint. Each cell runs in five fresh processes (15 total), with execution order randomized from the locked seed.

1. **Off-support ambiguous:** training examples `(0,0),(1,1)`, with the hidden evaluation target `y=x²` and heldouts `[-3,-2,2,3]`. The identity and square Programs both fit the supplied rows; the independent oracle makes their off-support difference explicit.
2. **Disambiguated positive control:** training examples `(-2,4),(-1,1),(0,0),(1,1),(2,4)`, heldouts `[-4,-3,3,4]`, target `y=x²`.
3. **Contradictory negative control:** training examples `(0,0),(0,1),(1,1)`, same hidden target and heldouts `[-1,2]`. No deterministic function can satisfy both labels at input 0; a refusal/gap is required.

The independent task oracle is the analytic square function. Read each accepted graph-resident Program back through `ProgEval`; do not rely on the learner's own acceptance flag as evidence of generalization. Record chosen Program structure, candidate counts, status/gap, wall/CPU time, peak RSS, every heldout prediction, source/native hashes, and exact example/request payloads. Use the existing 200,000-candidate limit without tuning it after observing results.

## Gates

- Fifteen distinct fresh workers; exactly five repetitions per task; randomized schedule matches the preregistered seed.
- Source, seed, native binary, and task payload match the pre-run lock and remain unchanged in workers.
- Disambiguated square is accepted and exactly predicts all four heldouts in every repetition.
- Ambiguous square is reported separately from the positive control, with candidate structure and all four independent-oracle outcomes captured; do not count fit on the two training rows as task success.
- Contradictory labels reach the fixed candidate cap and return `gapped` with no accepted Program in every repetition; any acceptance fails the refusal gate.
- Independent analyzer recomputes the square oracle and reconciles every worker, schedule, source hash, and captured status.

## Interpretation limits

This is one scalar function family with tiny authored datasets on one host. The ambiguous arm intentionally identifies a specification/identifiability limit: without a bias or more examples, no learner can infer the hidden intent from those two points. An identity answer is therefore a false generalization against the external target, but a valid fit to the supplied evidence. The contradictory arm tests one deterministic inconsistency form. Neither arm estimates natural-task ambiguity, broad synthesis generality, or new-operator invention. Any stronger residual-triggered selection policy requires a separate preregistered comparison and must pay its proposal, verification, and application costs.
