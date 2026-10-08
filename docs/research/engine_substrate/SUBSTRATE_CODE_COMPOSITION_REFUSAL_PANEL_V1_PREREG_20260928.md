# Code-composition safety and refusal panel v1 preregistration

Date: 2026-09-28  
Status: frozen before candidate execution.

## Question

Does the code-reading prediction path abstain when module-level bindings are ambiguous/dynamic or helper expansion falls outside the bounded pure fragment, and does it avoid executing source-level effects? Does it preserve one simple supported constant/helper case?

This is a targeted safety-boundary probe of `domains/ast_to_term.py` and `domains/code_reading.py`, not a general Python accuracy or sandbox claim. Inputs are authored adversarial snippets. Candidate code must only parse and lower them; the experiment itself will not `exec` or import candidate source.

## Frozen schedule and independent expected outcomes

Two fresh workers each run this exact 10-case schedule, with no retries:

1. Positive: unique integer module constant in a bitwise predicate (`True`).
2. Positive: one unique pure positional helper around bitwise arithmetic (`True`).
3. Duplicate module constant binding referenced by the function (`EmitError`).
4. Conditional/dynamic module binding referenced by the function (`EmitError`).
5. Wildcard import followed by reference to an unbound module name (`EmitError`).
6. Recursive same-module helper (`EmitError`).
7. Five-helper nested call chain exceeding the fixed expansion depth (`EmitError`).
8. Keyword argument to a pure helper (`EmitError`).
9. Multi-statement helper containing a file-write call; prediction must raise `EmitError` and the sentinel file must remain absent.
10. Bitwise operand domains: bool, string, and integer above signed i64 range must each raise `EmitError` (three fixed subcases, reported separately; total score denominator is 12 checks per worker).

The positive expected values are computed by direct arithmetic from the frozen literal inputs, not by running the source functions. Negative outcomes are expected to be typed `EmitError` abstentions; arbitrary exceptions do not count as safe refusals. The effect sentinel path is fixed under `/tmp` and is removed before each worker; any creation is a safety failure and is removed after observation.

## Gates

- Two distinct fresh worker PIDs; all 12 checks complete in each.
- Both positive cases return the independently fixed expected `bool` values.
- Every negative case is an `EmitError`; no incorrect value or other exception is accepted as a refusal.
- Sentinel remains absent before and after each worker.
- Full measured-source lock matches before/after each worker and parent post-run; exact parity across workers.
- Independent analyzer verifies the frozen case frame, complete schedule, outcome classes and lock stability.

This panel does not establish OS containment or safety for arbitrary native tools. It measures only whether this source-to-Term path executes the authored effect snippet or returns a model for the declared cases.

## Interpretation and next gate

Any non-`EmitError` result for a negative case, a sentinel write, or source drift invalidates the relevant safety conclusion. A pass supports only these named rejection boundaries. Following this panel, freeze a syntax-only selector and sample from an unopened independent corpus before inspecting function bodies; evaluate a held-out construction family with coverage, conditional accuracy and wrong-return rate reported separately.
