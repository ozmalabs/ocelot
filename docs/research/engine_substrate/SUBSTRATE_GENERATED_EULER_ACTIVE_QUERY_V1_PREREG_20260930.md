# Generated Euler Version Space Active Query v1

Status: preregistered confirmatory benchmark. Earlier one-query probes were exploratory and are not confirmatory evidence.

## Question

When the substrate generates a finite hypothesis pool from one labeled structural example, does iterative predictive-entropy query selection identify the held-out-correct behavior with fewer oracle calls than fixed-first or seeded-random selection?

## Task, pool, and holdout

- Task: Euler characteristic for finite simplicial complexes of dimension at most two, labeled by the existing grounded slow closure-and-alternating-sum oracle.
- Training conditions: point, edge, and filled triangle, one anchor per condition (each has Euler characteristic 1).
- Candidate query pool: the 12 named examples from `jabberwock_closes_the_euler_tie.py::_family()`. Their labels are withheld from policy code until the input is selected.
- Independent evaluation holdout: pentagon loop; two disjoint hollow triangles; two disjoint filled triangles; two loops joined at one vertex; a three-triangle edge-sharing chain; and two disjoint tetrahedral boundaries. None is a query candidate or a hypothesis-generation probe.
- Hypothesis grammar: `Plus`, `Times`, `Minus`, and `Div`, literals `(0, 1, 2, -1)`, max size 5, 15-second generation cap, at most 10,000 fitting hypotheses, and output-derived constants disabled. Candidate query descriptors are unlabeled probes for behavior deduplication.

## Policies and budgets

For each anchor, compare iterative entropy ranking, fixed-first ordering, and 20 seeded-random query orders. After each response, filter the current pool and repeat until one hypothesis remains or candidates are exhausted. The query budget is 12 oracle calls. Heldout labels are used only by the evaluator and never influence ranking or stopping. Record exact oracle calls, prediction/evaluation count, selector wall and CPU time, synthesis wall and CPU time, terms explored, pool size, halt reason, heldout accuracy of the final survivor set, and whether the true behavior was present before querying.

Entropy uses the current survivors with equal weights and ranks only remaining candidates; ties follow the existing selector's distinct-prediction and candidate-order rules. Fixed-first consumes candidates in declared order. Random uses `random.Random(20260930 + anchor_index*100 + replicate)` and samples without replacement. A policy is a success only if it ends with one hypothesis and that hypothesis matches the slow oracle on all six heldout cases.

## Interpretation limits

The result is limited to a bounded arithmetic grammar over authored Euler descriptors and these finite complex families. The known family and holdout are synthetic; this does not establish generated-version-space generality or natural-task tractability. A timeout, saturation, or solution-cap stop is a partial hypothesis pool and is analyzed separately from `max_size` completion. Selector benefit must be reported together with generation and selection compute costs.

## Reproduction

Run `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_generated_euler_active_query_v1.py --lock` and save the output to `evaluation/substrate_capability/substrate_generated_euler_active_query_v1_20260930_lock.json`. Run the runner without `--lock`, then run `python3 scripts/analyze_substrate_generated_euler_active_query_v1.py`. The runner refuses a stale source lock and does not overwrite an existing raw capture.
