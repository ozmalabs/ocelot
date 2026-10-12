# Term-literal joint proposals v1 results (2026-10-04)

## Result

The six-cell locked comparison passes all seven independent analyzer gates.
Adding the full Cartesian assignments of direct literal values across all
literal-bearing variables removes the four higher-arity false acceptances
from the preceding study. Each is rejected by one oracle label. The two
arity-2 controls are unchanged. No joint proposal slate exceeded 16 new rows;
the preregistered maximum was 64.

| Guard | New joint rows | Labels, pairwise → joint | Native evaluations, pairwise → joint | Wall time, pairwise → joint |
|---|---:|---:|---:|---:|
| Interval, 2 variables | 0 | 1 → 1 | 189 → 189 | 1.61 → 1.62 ms |
| Point, 2 variables | 0 | 1 → 1 | 171 → 171 | 1.36 → 1.36 ms |
| Interval, 3 variables | 8 | 0 → 1 | 308 → 261 | 3.41 → 2.55 ms |
| Point, 3 variables | 1 | 0 → 1 | 236 → 186 | 2.01 → 1.56 ms |
| Interval, 4 variables | 16 | 0 → 1 | 588 → 495 | 7.66 → 5.44 ms |
| Point, 4 variables | 1 | 0 → 1 | 444 → 342 | 4.50 → 3.26 ms |

The additional rows are small relative to the pairwise slate because some
joint assignments overlap existing proposals and are deduplicated. The
observed native evaluation counts and wall time decrease in the repaired
cases because the selector finds and consumes a distinguishing query sooner.
These timings are one capture per cell, not stable speed estimates.

## Interpretation and limits

Joint literal products restore coverage for this finite family. The cost of
constructing the product is multiplicative in the number of literal values
per participating variable: the interval family already grows from 8 new
rows at arity 3 to 16 at arity 4. The 64-row cap is a fail-closed bound for
this experiment, not a general complexity guarantee. More values, unrelated
guards, nested disjunctions, or many candidate Terms can make the slate
explode. The next gate is adaptive subset/variable selection with an explicit
proposal-work budget, tested on broader generated guards; track any missed
counterexample as a false acceptance and abstain when the budget leaves a
class unresolved. This does not establish unrestricted semantic equivalence
or natural-task prevalence.

## Reproduction

- [Protocol](TERM_LITERAL_JOINT_PROPOSALS_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/term_literal_joint_proposals_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_term_literal_joint_proposals_v1.py)
- [Lock](../../../evaluation/substrate_capability/term_literal_joint_proposals_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/term_literal_joint_proposals_v1_20261004.json)
- [Analysis](../../../evaluation/reports/term_literal_joint_proposals_v1_analysis_20261004.json)
