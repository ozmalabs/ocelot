# Generated Version Space and Label Blind Query Selection v1

Status: preregistered confirmatory pilot. This follows an explicitly exploratory `n=1..5` triangular-number probe; those observations are not included in the confirmatory anchors.

## Question

Can the substrate's enumerative synthesizer produce a bounded hypothesis pool from one labeled example, and can its finite-pool entropy selector choose a label-blind query that improves identification over fixed-first and seeded-random selection?

## Task and split

- Task: triangular number `T(n) = 0 + ... + n`, labeled by the existing grounded slow summation oracle in `scripts/cegis_faculty_on_sum_of_n.py`.
- Training anchors: `n = 6, 7, 8, 9, 10`, each evaluated as a separate condition with one known label.
- Candidate query pool: values `n=2..12` excluding that condition's anchor. These inputs are supplied without labels to generation and ranking.
- Held-out evaluation: `n=13..20`; heldout labels are computed only after selecting and receiving the query response.
- Candidate grammar: `Plus`, `Times`, `Minus`, `Div`; literals `(0, 1, 2, -1)`; max term size 7; 10-second synthesis cap; max 10,000 fitting behaviors; output-derived constants disabled.

## Policies

For each anchor, compare: (1) fixed-first query, (2) seeded-random query with 10 preregistered seeds, (3) maximum predictive entropy over the generated pool, with existing tie breaks, and (4) an oracle-best diagnostic that labels every candidate and chooses the query leaving the fewest consistent hypotheses. The oracle-best arm is an upper bound and its full oracle-call cost must be charged.

## Measures and decision rules

Record generation elapsed wall and CPU time, terms explored, distinct behaviors, returned pool size, halt reason, selected query, every oracle query input and response, survivor count, whether the pool contains a hypothesis matching the slow oracle on all heldout inputs, and the fraction of survivors that match the oracle on heldout inputs. The entropy selector is only credited with unique identification when exactly one survivor remains and it is correct on every heldout input. Only `max_size` is treated as a complete pool under the bounded grammar; timeout, saturation, and the solution cap are partial pools. Compare policy rates over anchors and random seeds; do not generalize beyond this task family.

The claim boundary is a bounded generated-pool active-query pilot. It does not establish automatic hypothesis-space construction in general, CEGIS integration, general capability, or broad tractability. The next independent task family is population variance; its current exploratory run timed out at 20 seconds, so pool completeness and search cost are explicit outcomes there.

## Reproduction

Run `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_generated_version_space_v1.py --lock` to inspect the expected source and engine lock. Save the lock to `evaluation/substrate_capability/substrate_generated_version_space_v1_20260930_lock.json`, then run the script without `--lock`; it refuses stale locks and refuses to overwrite a prior raw capture.
