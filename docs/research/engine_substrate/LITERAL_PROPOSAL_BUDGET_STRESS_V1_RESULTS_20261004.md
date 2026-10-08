# Literal proposal budget stress v1 results (2026-10-04)

## Result

The source-locked experiment passes all seven independent replay gates. The
noise-padded candidate exposes four direct literal values on each of four
variables, yielding 256 Cartesian rows. The exhaustive arm includes all 256,
queries the separating assignment once, and removes the false candidate. The
64-row arm processes the same 273-row edge/pairwise base slate but truncates
the extra Cartesian rows before the first separating assignment. Its
underlying finite-class logic would accept the false candidate; the
incomplete-slate guard converts that outcome to `request_help` with zero
oracle labels.

| Policy | New Cartesian rows | Oracle labels | Final decision | False acceptance | Native Term evaluations | Policy time |
|---|---:|---:|---|---:|---:|---:|
| Exhaustive | 256 | 1 | Accept surviving identity | No | 1,605 | 27.7 ms |
| Budgeted | 64 of 256 | 0 | Request help | No | 1,364 | 29.2 ms |

Both timings are from one capture and include policy selection, not a stable
benchmark of proposal construction or end-to-end learning. The 64-row arm's
holdout includes one mismatch for the false candidate among 3,089 rows; the
exhaustive arm's oracle label is disjoint from that holdout.

## Interpretation

The combination space grows quickly even for a four-variable guard when
irrelevant literal comparisons enlarge each variable's menu. A hard cap plus
explicit completeness tracking preserves safety by abstaining when a
truncated proposal slate leaves a false class unresolved. It does not make
the search itself cheap: the exhaustive arm processes four times as many
joint rows, and the budgeted arm still spends 1,364 native Term evaluations
across its larger base slate and policy accounting. The next capability step
is structure-aware clause proposals or adaptive variable subsets that locate
a useful counterexample without enumerating the full product; compare them
against exhaustive labels, work, miss/abstention, and false acceptance on
larger generated families. This single authored stress case is neither a
natural-task rate nor a general tractability result.

## Reproduction

- [Protocol](LITERAL_PROPOSAL_BUDGET_STRESS_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/literal_proposal_budget_stress_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_literal_proposal_budget_stress_v1.py)
- [Lock](../../../evaluation/substrate_capability/literal_proposal_budget_stress_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/literal_proposal_budget_stress_v1_20261004.json)
- [Analysis](../../../evaluation/reports/literal_proposal_budget_stress_v1_analysis_20261004.json)
