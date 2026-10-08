# Declared grammar expansion v1 results (2026-10-01)

## Result

The confirmatory source-locked panel completed ten fresh-process workers with no errors. The independent analyzer passes all 10/10 gates, including current source/native lock, the randomized schedule, distinct PIDs, bounded no-fit semantics, and held-out transfer.

With `Div` excluded from the declared grammar, all five searches reach the size-5 ceiling with no fitting term (`halt_reason=max_size`). Median explored work is 1,116 terms; median synthesis wall time is 29.4 ms. After adding `Div`, all five workers return `(x / 2)`; the seven odd and negative held-outs are exact in all cases (35/35). Median explored work is 94 terms and median wall time is 2.02 ms. Both conditions use the same four even-valued training examples and declared size/fuel settings.

## Interpretation and limits

This panel measures the standalone `domains.generator.synthesize` helper, not the production Rust `SynthEnumerate` route. It is a crisp bounded demonstration that this helper's synthesis result depends on which primitives the caller makes available. The no-fit arm establishes absence only within the declared grammar through size 5. The expansion arm applies an existing division primitive; it does not discover, implement, or autonomously select that primitive. This is therefore evidence for grammar-conditioned program induction and a concrete escalation boundary, not open-ended concept invention. Candidate counts are useful within this fixed comparison but are not a cross-operator universal cost unit. One scalar task, one host, and five repetitions do not establish natural-task prevalence or general tractability.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_SYNTHESIS_DECLARED_GRAMMAR_EXPANSION_V1_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_synthesis_declared_grammar_expansion_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_synthesis_declared_grammar_expansion_v1.py)
- [Source lock](../../../evaluation/substrate_capability/synthesis_declared_grammar_expansion_v1_20261001_lock.json)
- [Raw capture](../../../evaluation/reports/synthesis_declared_grammar_expansion_v1_20261001_raw.json)
- [Analysis](../../../evaluation/reports/synthesis_declared_grammar_expansion_v1_20261001_analysis.json)

## Next gate

The helper-level escalation follow-up is recorded in [bounded grammar escalation v1](SUBSTRATE_SYNTHESIS_GRAMMAR_ESCALATION_V1_RESULTS_20261001.md). The production route is separately measured in [production Γ operator selection v1](SUBSTRATE_PRODUCTION_GAMMA_OPERATOR_SELECTION_V1_RESULTS_20261001.md), which tests its actual finite inventory and shows the remaining gap on factorial. The next open gate is a substrate-authored proposal for a primitive absent from the native inventory, scored against blinded task utility and charged for proposal generation plus every search attempt.
