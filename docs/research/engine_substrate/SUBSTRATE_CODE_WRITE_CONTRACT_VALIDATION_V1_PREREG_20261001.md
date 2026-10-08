# Code-write contract validation v1 — preregistration

## Question

Can independent request-level input/output examples prevent semantic-mismatch codebook growth while still admitting an aligned example?

## Intervention

The opt-in `contract_examples` path to `teach_write_shape_from_example` accepts rows of the exact form `{inputs: {argument: value, ...}, expected: value}`. Before grounding identifiers or teaching a ShapeSignature, it must require a non-empty list, exact argument-key agreement, and exact type/value agreement from both native Term evaluation and emitted Python for every row. Any invalid or mismatching row refuses acquisition. The legacy no-contract path remains available and is explicitly outside this gate.

## Locked panel

Run four fresh full-seed workers in randomized order, two each:

- **Aligned parity:** parity source, parity request, and five independent contract rows.
- **Mismatched parity-as-square:** same one-argument parity source, square request, and five square contract rows. Keeping the arity identical ensures the gate is exercised on behavior, not merely rejected by an argument-shape check.

The analyzer independently computes parity and square expectations and checks acquisition outcome, selected construction, codebook growth, exact native/Python agreement, source stability, process uniqueness, and the captured lock. The task oracles do not enter the substrate worker. For mismatch refusal, require no new `taught_parity` ShapeSignature and an explicit output-contract failure. For aligned acquisition, require exactly the expected taught shape and successful Term/Python transfer on the contract rows.

## Scope

This is a mechanism result for two small integer functions and caller-supplied contract observations. It does not establish that the observations themselves are correct, that the contract covers all task semantics, or that request meaning can be inferred without an evaluator. All source/native/seed-manifest inputs and harness files are locked before the worker panel; preserve every worker outcome and report startup, acquisition, and memory cost separately.
