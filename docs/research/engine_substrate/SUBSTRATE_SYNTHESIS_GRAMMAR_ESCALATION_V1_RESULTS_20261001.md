# Bounded grammar escalation v1 results (2026-10-01)

## Result

The confirmatory capture completed ten fresh workers without errors. The independent analyzer passes all 10/10 gates, including the source/native lock, exact randomized schedule, unique PIDs, bounded completion, expected stage order, and held-out checks.

For `x / 2`, the arithmetic grammar completes size 5 without a fit in 5/5 workers (median 500 explored terms, 13.2 ms). The caller then supplies the numeric grammar containing `Div`; all five searches return `(x / 2)` and predict all seven odd/negative held-outs exactly (35/35), after a median 94 terms and 2.12 ms. Median total search wall per worker is 15.3 ms.

For `x % 3`, all three grammars passed to the standalone `domains.generator.synthesize` helper omit `Mod`. Every worker completes the size-5 search without a fit at every stage. Median stage costs are 500 terms/22.8 ms for arithmetic, 1,701/68.2 ms for numeric, and 3,655/120.1 ms for full; median total wall is 215 ms. This is a clean bounded gap report for that helper, not for the production Rust synthesis route.

## Interpretation and limits

The results separate held-operator application from acquisition in this helper. The system recovers division only after the caller includes `Div`. The tested Python helper grammars omit `Mod`, but the production Rust operator inventory and graph-authored Gamma rule do include it, as established by the separate [production-path study](SUBSTRATE_PRODUCTION_GAMMA_OPERATOR_SELECTION_V1_RESULTS_20261001.md). The Python-helper no-fit does not establish substrate-wide operator absence. Within the helper, finite bounded no-fit also does not prove that a larger composition could never fit these examples. Escalation was scripted by the experimenter.

See the [scope amendment](SUBSTRATE_SYNTHESIS_GRAMMAR_ESCALATION_V1_SCOPE_AMENDMENT_20261001.md) for this correction.

The panel measures one scalar task family on one host, with one term-size ceiling and five workers per target. Candidate counts are local to this grammar and not a universal work metric. The result does not establish general induction tractability or natural-task rates.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_SYNTHESIS_GRAMMAR_ESCALATION_V1_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_synthesis_grammar_escalation_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_synthesis_grammar_escalation_v1.py)
- [Source lock](../../../evaluation/substrate_capability/synthesis_grammar_escalation_v1_20261001_lock.json)
- [Raw capture](../../../evaluation/reports/synthesis_grammar_escalation_v1_20261001_raw.json)
- [Analysis](../../../evaluation/reports/synthesis_grammar_escalation_v1_20261001_analysis.json)

## Next gate

Evaluate a substrate-authored proposal for a primitive absent from the native operator table (such as factorial) against a blinded task-utility oracle. The proposal route must identify the unsupported operation and propose or request an extension; charge proposal generation and all rejected searches. Keep caller-supplied grammar changes as controls, and separately score fit, held-out transfer, false acceptance, refusal, and total cost. Until that route is measured, the evidence supports bounded gap reporting, not self-directed structure acquisition.
