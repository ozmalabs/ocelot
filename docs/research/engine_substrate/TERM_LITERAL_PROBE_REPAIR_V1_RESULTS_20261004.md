# Term-literal probe repair v1 results (2026-10-04)

## Result

The locked paired comparison passes all seven independent analysis gates.
Across three numeric panels, edge-only and edge-plus-literal agree on the
absolute-square underflow and signed-zero division cases. On the targeted
structured interval panel, edge-only accepts the false interval-alias Term
with zero labels. Adding direct variable/literal comparison-boundary
assignments queries one boundary, rejects the alias, and retains the exact
identity Term. The false candidate has one mismatch among 4,094 disjoint
holdout rows; the identity has none. Policy work is 88 native Term
evaluations without literal probes and 96 with them, with one oracle label
added and sub-millisecond measured policy time in both arms.

The other two panels retain their earlier results: the absolute-square
underflow false Term is rejected at one label and two exact behavior-class
survivors remain; the quotient-equality Term is rejected at signed zero while
identity remains. Literal probes do not add labels there. Across all panels,
the additional proposal cost is bounded in this small slate; timings are
single-process descriptive measurements, not a scaling estimate.

## Interpretation and limits

This is evidence that extracting direct `Var`/`Lit` comparison boundaries
repairs this harness-authored false-acceptance case. It does not establish
complete extraction of Term conditions, safe behavior-class acceptance, or
unrestricted semantic equivalence. A different false candidate can place its
exception outside every proposed boundary. Acceptance therefore remains a
finite-domain policy decision without a bounded-domain proof. The next useful
step is a prospective adversarial family varying literal operators,
interval widths, conjunction depth, and guards on variables not in the
selected pair; report miss rate, abstention, proposal cost, and label cost.

## Reproduction

The preregistration, runner, analyzer, immutable input lock, raw capture, and
analysis are linked below. Re-run from the repository root:

```sh
python3 evaluation/substrate_capability/term_literal_probe_repair_v1.py --run
python3 evaluation/substrate_capability/analyze_term_literal_probe_repair_v1.py
```

The lock was created with `--lock` before capture and binds the sources,
upstream v2 capture, panels, and policy settings.

- [Protocol](TERM_LITERAL_PROBE_REPAIR_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/term_literal_probe_repair_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_term_literal_probe_repair_v1.py)
- [Lock](../../../evaluation/substrate_capability/term_literal_probe_repair_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/term_literal_probe_repair_v1_20261004.json)
- [Analysis](../../../evaluation/reports/term_literal_probe_repair_v1_analysis_20261004.json)
