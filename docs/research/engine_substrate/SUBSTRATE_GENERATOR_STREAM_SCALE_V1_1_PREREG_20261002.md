# Generated hypothesis-pool streaming scale v1.1 — preregistration

## Amendment and validity boundary

The v1 run did not produce a raw capture. Its worker's audit code assumed numeric signatures were scalar, while `domains.generator` represents them as tagged pairs such as `('num', 1.0)`. The process stopped during integrity extraction before writing the capture. Some earlier scheduled workers may have completed their deterministic held-out calculations, but no held-out result was displayed or retained, no model was selected from those outputs, and the v1 artifact is excluded. V1.1 fixes the signature parser and keeps the experimental design unchanged. This amend-and-relock is disclosed to preserve the failed attempt.

## Question

Does streaming candidate registration reduce peak memory or total cost for bounded version-space construction without changing the hypotheses, completion status, or held-out target coverage? This measures the rung-three search workload that supports active query selection; it is not a measure of autonomous task or grammar invention.

## Design

Use `domains.generator.synthesize` version-space mode on the triangular-number function. The target is `n(n+1)/2`, with one labeled anchor `(n=1, output=1)`, fixed operators `Plus`, `Times`, `Minus`, `Div`, fixed constants `{0,1,2,-1}`, and `include_output_constants=False`. Probe environments are unlabeled integer inputs `n=0..p-1`, for `p ∈ {4,8,12}`. Cross this with expression-size caps `{5,6,7}` and both `stream_cohort=False` (batch control) and `stream_cohort=True` (streaming treatment). Use three fresh-process replicates per cell, a 15-second wall cap, a 10,000-hypothesis cap, and no beam or saturation stop. Randomize cell order within each replicate using the frozen seed. The four held-out target inputs are `13,17,23,31`; their labels are never passed to synthesis and are used only to measure pool coverage after search ends.

Each process records synthesis wall/CPU time, process peak RSS, explored terms, distinct behaviors, hypothesis count and digest, stop reason, completeness, approximate retained hypothesis-object heap, target-hypothesis presence, held-out exact behaviors, and source/native provenance. Timing includes candidate construction inside `synthesize`, not Python startup. `ru_maxrss` is process-wide peak RSS, including interpreter/native setup; it is a coarse memory measure. The approximate heap field is supplementary and excludes Rust allocations.

## Gates and interpretation

The 10 analysis gates require: (1) exact source/native provenance and a current engine; (2) complete, unique coverage of 54 fresh-process rows; (3) batch/stream equivalence of stop reason, explored/distinct counts, training-consistent pool size, and ordered hypothesis digest for every pair; (4) identical target presence and held-out exact-pool coverage within each pair; (5) finite resource measurements; (6) the single fixed labeled anchor in every row; (7) every returned hypothesis fits that anchor; (8) only `max_size` termination is called complete, while timeout/solution-cap remain incomplete outcomes; (9) no hypothesis or probe cap is silently exceeded; and (10) source stability through each worker.

Report cost ratios and completion/target coverage by size and probe count. Do not call a timed-out or solution-limited pool complete. A streaming win in memory with a wall-time penalty is a tradeoff, not an overall tractability win. The study uses one arithmetic family and three search sizes; it makes no claim about general hypothesis-class learnability or all substrate workloads.

## Reproduction

Run `python3 evaluation/substrate_capability/substrate_generator_stream_scale_v1_1.py --lock`, then `--capture`, then `python3 evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_1.py`.
