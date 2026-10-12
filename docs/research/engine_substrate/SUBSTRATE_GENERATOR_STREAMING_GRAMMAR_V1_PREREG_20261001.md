# Streaming generator with conditional grammar v1

## Question

Does the opt-in cohort-streaming path preserve exact bounded-pool results and allocation behavior when enumeration includes comparison and ternary conditional operators?

## Design

Use the frozen triangular, square, and Euler task adapters from the prior generated-pool studies. Compare eager and streaming modes in each paired worker with randomized order, two repetitions, fixed five-input probe prefixes, and a grammar containing `Plus`, `Times`, `Minus`, `Div`, `Lt`, `Gt`, `Eq`, and `IfThenElse`. Size ceilings are triangular/square 5 and 6, Euler 4 and 5 (12 paired workers total). Keep constants `(0,1,2,-1)`, output-constant expansion disabled, 10,000 solution cap, saturation disabled, and an eight-second synthesis timeout. Do not retry or replace timeout, error, incomplete-pool, or semantic-mismatch outcomes.

Record per-arm halt reason, ordered behavior signatures, pool size, explored/distinct counts, held-out target support, wall/CPU time, and Python-traced peak allocation. Streaming is useful only if it preserves the full bounded pool; timeouts are failures, not parity. The parent process caps each arm at 12 seconds to retain pathological generation failures.

## Limits

This is a small synthetic grammar-width stress study with two repetitions, not a broad induction estimate. Python allocation tracing excludes native allocations and perturbs elapsed time. The conditional operators are added to the arithmetic grammar to exercise the ternary cohort construction path; this does not cover all DSL productions or type-directed synthesis.

## Reproduction

Write `evaluation/substrate_capability/substrate_generator_streaming_grammar_v1_20261001_lock.json` using the runner's `--lock` command, run the runner, then run its independent analyzer.
