# Production Γ operator selection v1 results (2026-10-01)

## Result

Ten source/native-locked fresh workers completed with no errors. The independent analyzer passes 12/12 gates, covering source/native stability, schedule, unique workers, lack of explicit operator lists, Gamma use, operator availability, held-out predictions, and factorial gap semantics.

On the modulo task, Γ supplies its graph-authored bare-scalar operator list, including `Mod`; the caller supplied no `ps_enum_ops`. All five production runs accept a Program whose return expression is `value % 2`. The eight held-out values are exact in every run (40/40 total). Median search work is 257 candidates, pump wall 18.14 ms, pump CPU 18.06 ms, and peak RSS 41.31 MiB.

On factorial, Γ again supplies the same 14-operator bare-scalar list, but `Factorial` is absent from the Rust `SynthEnumerate::OP_TABLE`. All five workers return `enumerate_failed` at the native 200,000-candidate limit with no Program. Median pump wall is 373.60 ms, CPU 370.53 ms, and peak RSS 68.63 MiB.

## Interpretation

This confirms a real but bounded substrate-authored capability: graph-authored Γ rules select an operator set from a finite shipped `SynthOp` inventory based on example-shape evidence, and the production synthesis route can compose an admitted `Mod` operator and transfer on a held-out continuation. Γ did not invent `Mod`, which was already present in the Rust operator table and added to its static `SynthOp` vocabulary. The factorial result is a genuine ontology boundary for this route: the current finite inventory does not include that primitive, and the bounded search returns a gap rather than a Program.

The factorial no-fit is bounded by the current operator table, the 200,000 candidate cap, and the task examples; it does not prove no larger program using existing operators could fit them. The study covers two scalar tasks, one host, and five repetitions per task. It does not establish general operator-selection accuracy, natural-task prevalence, or open-ended primitive invention.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_PRODUCTION_GAMMA_OPERATOR_SELECTION_V1_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_production_gamma_operator_selection_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_production_gamma_operator_selection_v1.py)
- [Source lock](../../../evaluation/substrate_capability/production_gamma_operator_selection_v1_20261001_lock.json)
- [Raw capture](../../../evaluation/reports/production_gamma_operator_selection_v1_20261001_raw.json)
- [Analysis](../../../evaluation/reports/production_gamma_operator_selection_v1_20261001_analysis.json)

## Scope clarification for the standalone grammar ladder

The separate [declared grammar expansion v1](SUBSTRATE_SYNTHESIS_DECLARED_GRAMMAR_EXPANSION_V1_RESULTS_20261001.md) and [grammar escalation v1](SUBSTRATE_SYNTHESIS_GRAMMAR_ESCALATION_V1_RESULTS_20261001.md) call `domains.generator.synthesize`, a standalone Python helper whose local `_op_table` omits `Mod`. Their modulo no-fit is correct for that helper's declared grammars. It must not be generalized to the production Rust synthesizer or the substrate as a whole. See the [scope amendment](SUBSTRATE_SYNTHESIS_GRAMMAR_ESCALATION_V1_SCOPE_AMENDMENT_20261001.md).
