# CAN Stage A fallback envelope preregistration

## Question

On the existing authored CAN rule workload, what share of Stage-A-derivable drains trigger the runtime overlap fallback, and what execution-time cost/results arise when Stage A is enabled?

## Workload and design

Reuse the exact seed-loader and deterministic graph-construction functions from `scripts/substrate_can_structure_envelope.py`. Measure N=16 and 32 on path, banded-2, and complete coupling graphs in 3-state mode at weight granularity 0.25, with three independent seeds/repeats. For each case construct fresh identical substrates and run three arms: ordinary closure, compare-only (which records the number and divergence of Stage-A-derivable drains without changing committed execution), and Stage A enabled (which records proposals, excluded drains, and overlap fallback count). Setup is excluded from run wall/CPU time.

The fallback rate denominator is the compare-only `compared_drains` count; the numerator is enabled-arm `conflict_fallbacks`. If the denominator is zero, report the rate as undefined and report the eligibility share as zero when the enabled arm also records only excluded drains. These are matched workload runs, not a simultaneous per-drain join. Also report proposal and exclusion counts. Compare exact whole graph state, progress count, terminal probe, vocabulary, and the workload's independent local fixed-point residual between ordinary and Stage-A-enabled runs. Report timing descriptively; instrumentation and separate fresh runs prevent claiming a causal speedup from this small envelope.

## Gates and provenance

Three fresh worker processes must cover all six size/topology cells once each. Each run must lock the protocol, runner, shared workload builder, CAN seed manifest, Rust source files, native extension/build manifest, and commit at worker start and end. Every arm must settle under the budget and pass the independent fixed-point predicate; ordinary and Stage-A-enabled arms must have exact graph/progress parity. Counts must be nonnegative. Where derivable drains exist, fallback count cannot exceed compare-only drain count; when none exist, report Stage A as inapplicable to that measured rule workload rather than treating an undefined fallback rate as zero.

## Claim boundary

This measures authored CAN rule execution on synthetic path, banded, and complete topologies. It does not estimate natural task prevalence, establish Stage A correctness beyond the matched cases, or demonstrate speedup. `compared_drains` and enabled fallback counts are aggregate matched-run counts, not a per-drain paired trace.
