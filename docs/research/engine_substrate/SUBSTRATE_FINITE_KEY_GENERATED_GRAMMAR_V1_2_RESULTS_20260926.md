# Finite-key generated grammar v1.2 results

**Run date:** 2026-09-26  
**Evidence grade:** locked grammar/runtime comparison; all 25 registered cases and 12 independent checks pass.

## Outcomes

The panel covers 15 admitted programs and 10 expected refusals. Admitted cases vary finite literal key values (`null`, booleans, positive/negative integers, strings including Unicode), empty and multiple key attributes, reuse of an existing matching witness, one/two/three-edge joins, repeated variables, minted endpoints, and two interacting rules. All 15 pass the checker, parse and run in the native engine, report `fixed_point`, stay within their analyzer progress bound, and exactly match the independently interpreted terminal node and edge graphs. All ten negative cases are refused by the checker, including malformed fields, computed keys, fresh minting, invalid endpoints/order, output-edge attrs, unsupported effects, and attributed-edge write conflicts.

The v1 raw capture reported one apparent graph mismatch (24/25 passes). The runner's interpreter had not encoded the engine's injective binding semantics. `runners/dsl/src/rewrite.rs::extend_each` explicitly rejects a completed binding when two distinct variable names resolve to the same `NodeID`. Thus `x -link-> y` does not match a self-loop, while a repeated variable pattern `x -loop-> x` can. V1.2 applies this condition in its independent oracle. No engine semantic change was retained; the release artifact was rebuilt from the restored source before v1.2.

## Provenance and limits

The v1.2 pre-run lock covers the fixture runner, independent analyzer, finite-key checker, protocol/amendment, native parser/effect/runtime sources, build manifest, and loaded native library. Its shared manifest records current build freshness and a nonempty parent console log. The independent analyzer passes 12 checks for the full fixture inventory, outcomes, terminal graph parity, bounds, source lock, manifest, native artifact, and log.

This is representative syntax coverage, not exhaustive grammar equivalence. It exercises the declared finite-key fragment only and does not cover every JSON scalar edge case, every ordering/interleaving, large joins, malformed runtime metadata, or nonmonotone effects. The finite fact bound establishes termination for the admitted fragment under its stated assumptions; this panel checks selected runtime realizations of that fragment, not a wall-time theorem.

## Artifacts

- Base protocol: [`SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_PROTOCOL_20260926.md`](SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_PROTOCOL_20260926.md)
- v1.2 amendment: [`SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_2_AMENDMENT_20260926.md`](SUBSTRATE_FINITE_KEY_GENERATED_GRAMMAR_V1_2_AMENDMENT_20260926.md)
- Runner and independent analyzer: [`verify_mint_termination_generated_grammar_v1_2.py`](../../../scripts/verify_mint_termination_generated_grammar_v1_2.py), [`analyze_mint_termination_generated_grammar_v1_2.py`](../../../scripts/analyze_mint_termination_generated_grammar_v1_2.py)
- Lock: [`mint_termination_generated_grammar_v1_2_lock_20260926.json`](../../../evaluation/substrate_capability/mint_termination_generated_grammar_v1_2_lock_20260926.json)
- Raw capture and analysis: [`raw`](../../../evaluation/reports/mint_termination_generated_grammar_v1_2_20260926.json), [`analysis`](../../../evaluation/reports/mint_termination_generated_grammar_v1_2_analysis_20260926.json)
- Console log: [`mint-termination-generated-grammar-v1-2-20260926.stdout_stderr.log`](../../../evaluation/run_logs/mint-termination-generated-grammar-v1-2-20260926.stdout_stderr.log)
