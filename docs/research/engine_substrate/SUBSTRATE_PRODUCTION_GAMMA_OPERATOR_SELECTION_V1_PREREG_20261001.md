# Production Γ operator selection v1 — preregistration

## Question

Does the production `ensure_program_synthesis → ingest_spec → pump` route use the graph-authored Γ operator selector to choose a registered primitive that enables exact transfer, and how does it behave when the target needs an operator absent from the native `SynthEnumerate` inventory?

This directly measures the production path, including `seeds/program_synthesis_opgrammar.json` and Rust `SynthEnumerate`. The earlier standalone `domains.generator.synthesize` grammar ladder is a different path and is not a substitute for this evaluation.

## Frozen tasks

Both use the generic request “write a function mapping each integer input to its output from examples,” with no operation name in the request and no explicit `ps_enum_ops` supplied.

- **Registered operator, modulo:** `x % 2`, training `x=0,1,2,3`, held-out `x=4..11`. The held primitive `Mod` is present in the Rust operator inventory and is expected to be included by the bare-scalar Γ grammar.
- **Unregistered operation, factorial:** `x!`, training `x=0..5`, held-out `x=6,7,8`. Factorial is absent from the current Rust `SynthEnumerate::OP_TABLE`; this is a negative capability probe, not a claim that finite bounded arithmetic expressions cannot match the examples.

Run five fresh workers per task in a randomized order with seed `20261001`. Use the production native default candidate limit (200,000) and record the exact number tested, source-selected Γ operators, whether Γ supplied the operator list, task result, returned Program IR, and held-out outputs when a Program is accepted. Do not add a Factorial op or alter operator rules during the run. Preserve all worker errors, timeouts, and non-success results.

## Gates and measures

The independent analyzer verifies a current source/native lock; ten scheduled rows and unique PIDs; five workers per task; no explicit message operator list; Γ use in both tasks; `Mod` in the admitted set and returned Program for modulo; exact 8/8 held-out transfer per modulo worker; and a production gap for factorial at the 200,000 candidate limit with no Factorial entry in the inventory. Record wall/CPU time, peak RSS, candidates, Γ list, and all task outcomes.

This separates (a) graph-authored selection among shipped operators from (b) invention of a new primitive. The factorial gap is bounded by current grammar and candidate limit; it does not prove nonrepresentability under arbitrary terms. One scalar family per condition is not a general accuracy or prevalence estimate.

## Reproduction

Create `evaluation/substrate_capability/production_gamma_operator_selection_v1_20261001_lock.json` via `python3 scripts/substrate_production_gamma_operator_selection_v1.py --lock`, run the source-locked runner once, then run `python3 scripts/analyze_substrate_production_gamma_operator_selection_v1.py`.
