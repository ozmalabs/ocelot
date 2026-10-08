# Generated hypothesis-pool streaming scale v1 — preregistration

## Question

Does streaming candidate registration reduce peak memory or total cost for bounded version-space construction without changing the hypotheses, completion status, or held-out target coverage? This measures the rung-three search workload that supports active query selection; it is not a measure of autonomous task or grammar invention.

## Design

Use the existing `domains.generator.synthesize` version-space mode on the triangular-number function. The target is `n(n+1)/2`, with one labeled anchor `(n=1, output=1)`, fixed operators `Plus`, `Times`, `Minus`, `Div`, fixed constants `{0,1,2,-1}`, and `include_output_constants=False`. Probe environments are unlabeled integer inputs from the prefix `n=0..p-1`, with `p ∈ {4,8,12}`. Cross this with expression-size caps `{5,6,7}` and both `stream_cohort=False` (batch control) and `stream_cohort=True` (streaming treatment). Use three fresh-process replicates per cell, a 15-second wall cap, a 10,000-hypothesis cap, and no beam or saturation stop. Randomize cell order within each replicate using a frozen seed. The four held-out target inputs are `13,17,23,31`; their labels are never passed to synthesis and are used only to measure pool coverage after search ends.

Each process records synthesis wall/CPU time, process peak RSS, explored terms, distinct behaviors, hypothesis count and digest, stop reason, completeness, approximate retained hypothesis-object heap, target-hypothesis presence, held-out exact behaviors, and source/native provenance. Timing includes candidate construction inside `synthesize`, not Python startup. `ru_maxrss` is process-wide peak RSS, including interpreter/native setup; it is a coarse memory measure. The approximate heap field is supplementary and excludes Rust allocations.

## Gates and interpretation

The 10 independent analysis gates require: (1) exact source/native provenance and a current engine; (2) complete, unique factorial coverage of 54 fresh-process rows; (3) batch/stream equivalence of stop reason, explored/distinct counts, and ordered hypothesis digest for every paired cell; (4) identical target-presence and held-out coverage within pairs; (5) valid, finite resource measurements; (6) target outputs are never included among labeled examples; (7) every pool member is training-consistent; (8) completion is reported only for `max_size` termination, while timeout/solution-cap are retained as incomplete outcomes; (9) no hypothesis or probe cap is silently exceeded; and (10) source stability through each worker.

Report cost ratios and completion/target-coverage by size and probe count. Do not call a timed-out or solution-limited pool complete. A streaming win in memory with a wall-time penalty is a tradeoff, not an overall tractability win. The study uses one arithmetic family and three fixed anchors/search sizes; it makes no claim about general hypothesis-class learnability or all substrate workloads.

## Reproduction

Run `python3 evaluation/substrate_capability/substrate_generator_stream_scale_v1.py --lock`, then `--capture`, then `python3 evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1.py`.
