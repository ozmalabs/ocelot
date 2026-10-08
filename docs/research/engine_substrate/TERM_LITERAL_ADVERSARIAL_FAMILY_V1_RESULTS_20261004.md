# Term-literal adversarial family v1 results (2026-10-04)

## Findings

The locked six-cell study passes all seven independent replay gates. The
edge-only policy accepts all six false candidates without labels. Adding
pairwise direct-literal probes rejects both two-variable controls with one
oracle label each. It does not reject either three-variable or either
four-variable guard: the false candidates remain in accepted behavior
classes, and their locked witnesses remain unqueried. For the two-variable
point guard, the witness itself is queried and rejects the candidate; it is
not reused as holdout data. The interval panels retain a separate interior
holdout witness and one mismatch among 3,088 holdout rows.

| Guard | Edge-only | Edge + literal | Native Term evaluations (edge / literal) | Wall time (edge / literal) |
|---|---:|---:|---:|---:|
| Interval, 2 variables | false accepted, 0 labels | rejected, 1 label | 212 / 189 | 2.00 / 1.69 ms |
| Point, 2 variables | false accepted, 0 labels | rejected, 1 label | 212 / 171 | 1.63 / 1.42 ms |
| Interval, 3 variables | false accepted, 0 labels | false accepted, 0 labels | 212 / 308 | 2.24 / 3.25 ms |
| Point, 3 variables | false accepted, 0 labels | false accepted, 0 labels | 212 / 236 | 1.81 / 2.00 ms |
| Interval, 4 variables | false accepted, 0 labels | false accepted, 0 labels | 396 / 588 | 4.70 / 7.36 ms |
| Point, 4 variables | false accepted, 0 labels | false accepted, 0 labels | 396 / 444 | 3.71 / 4.14 ms |

The times are single-run, sub-millisecond-to-millisecond policy measurements
and should be treated as descriptive. The extra proposal cost grows with the
number of literal-boundary combinations, while pairwise proposals cannot
populate three or four guard variables simultaneously. That is the observed
mechanistic source of the misses.

## Interpretation

Literal-directed probes repair a low-arity boundary failure but do not scale
to conjunctions whose exception requires more coordinates than the query
generator varies together. Candidate structure reveals the constants but
the proposal policy does not compose them across all relevant variables.
Next measure targeted multi-variable query generation against the same
locked family, with a proposal budget and cost accounting, then expand to
unselected-variable guards and nested Boolean structure. These six authored
cells are a stress test, not an estimate of natural-task false-acceptance
rates. Finite probe agreement still is not a proof of equivalence.

## Reproduction and artifacts

The preregistered family, source lock, upstream binding, raw capture, and
independent replay are available here:

- [Protocol](TERM_LITERAL_ADVERSARIAL_FAMILY_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/term_literal_adversarial_family_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_term_literal_adversarial_family_v1.py)
- [Lock](../../../evaluation/substrate_capability/term_literal_adversarial_family_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/term_literal_adversarial_family_v1_20261004.json)
- [Analysis](../../../evaluation/reports/term_literal_adversarial_family_v1_analysis_20261004.json)
