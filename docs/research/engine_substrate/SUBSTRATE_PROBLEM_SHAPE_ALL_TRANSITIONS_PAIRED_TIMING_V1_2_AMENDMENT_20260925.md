# V1.2 amendment: correct six-pair aggregate validation

The balanced six-pair run completed all six baseline/candidate pairs. Every pair record says complete and semantically valid, all 12 recorded PIDs are unique, and the execution order contains three baseline-first and three candidate-first pairs. The runner's top-level `all_checks_pass` is false solely because its copied final predicate still required `len(pairs)==3`; this is a coordinator aggregation bug, not a worker or semantic failure.

Preserve the original raw artifact unchanged. Independently revalidate each pair, PIDs, and balance from raw worker records, and compute the six-pair summary. Record the exact coordinator script hash after the run because its hash was omitted from the pre-run lock. The worker runners, protocol, seeds, and native binary were locked before execution. Do not change worker outputs or exclude any pair. This correction does not upgrade the study beyond six exploratory pairs on one workload.
