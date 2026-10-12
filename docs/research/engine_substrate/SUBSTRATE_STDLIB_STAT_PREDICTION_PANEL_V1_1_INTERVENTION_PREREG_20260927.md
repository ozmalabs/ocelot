# CPython `stat` bounded module-composition intervention v1.1 preregistration

Date: 2026-09-27  
Status: frozen before the v1.1 candidate run.

## Question

Does a bounded AST-graph emitter extension close the measured v1 gap for the frozen CPython file-type predicate frame, while preserving refusal outside a small explicit source fragment and preserving existing arithmetic controls?

This is a targeted engineering intervention on the same inspected family. It cannot establish blind transfer or estimate general code accuracy. The v1 behavior and source are frozen references: raw `0a45d7f3df52630995ca62ed7f3fafe3c419a5983f7f888c26baaf288a77da98`, analysis `1b9b71713dd905056a1c0282e72409d4e823e5b8c0f3d567115fd3b0162a4589`, frame `d1538bb1dec48de2ef8d89252f1afd4f9e8159a0e9768688b29945b1ac5d8bc0`, and lock `446445c9fbefe80a9b0137fbd167e23344a4280b5151786bf189148de46ac03c`.

## Locked intervention fragment

The candidate may add only:

1. A top-level module scope index of unique direct `Name = integer-literal` bindings. Duplicate, ambiguous, augmented, conditional, imported, or dynamic writes invalidate that name; functions/classes/imports are tracked as bindings, not evaluated.
2. Inline expansion of same-module helper calls only when the helper is an undecorated top-level function with required positional parameters, exact positional arity, no keyword/variadic/default arguments, and exactly one Return after an optional docstring. Reject cycles and nesting deeper than four calls. Never execute source Python.
3. AST BitAnd/BitOr/BitXor mappings to existing native Term variants only for exact `int` operands whose concrete values are within signed i64. The candidate refuses absent/non-int/out-of-range concrete binds.

All other ordinary Python calls, dynamic globals, mutations, multiple statements, unsupported operators, and helper shapes remain honest refusals. No change is permitted to the frozen selector, cases, oracle, expected answers, candidate frame, substrate Term evaluator, or native extension.

## Schedule and analysis gates

Replay the same 35 primary cases and two frozen Think Python controls in two fresh workers. Lock the full relevant source tree and all corpus, seed, native, Rust, selector, frame, protocol and baseline artifact hashes before the workers; verify stability before/after. The independent analyzer reconstructs all seven candidates and the 35-case bit-mask oracle, verifies the exact schedule and hashes, scores typed exact outputs and abstentions, compares case-level outcomes with v1, and validates the shared manifest and hashed console capture.

Report candidate exact outputs, coverage, wrong values, controls, worker parity, receipts/mints, wall/cpu cost, boot counts/failures and RSS. Targeted success criterion: each candidate worker returns all 35 exact primary values, both controls pass 2/2, no wrong output, worker parity, stable locks, and every integrity gate passes. A failure or change to an out-of-scope behavior is reported without relaxing the frozen gate.

## Claim boundary and next gate

Even a full pass demonstrates only that this explicitly inspected fragment handles this fixed CPython family. It does not establish general module composition, learning, blind transfer, or tractability. The next transfer panel must be selected and frozen after the candidate implementation is fixed, from a distinct family and source slice, with its own independent oracle and explicit abstention/error scoring.
