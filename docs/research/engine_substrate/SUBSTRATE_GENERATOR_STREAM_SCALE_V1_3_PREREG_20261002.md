# Generated hypothesis-pool stress scale v1.3 — preregistration

## Question

At size 11, does the version-space generator complete within bounded time and address space, and does streaming preserve the batch pool while reducing memory use? V1.2 completed size 9 with 88,069 explored terms; this protocol tests the next syntactically productive size while containing cohort-construction risk.

## Design and resource controls

Keep the same single-anchor triangular task, fixed `Plus/Times/Minus/Div` grammar, constants `{0,1,2,-1}`, 12 unlabeled probes `n=0..11`, four held-out values `13,17,23,31`, 10,000 fitting-hypothesis cap, and batch/stream arms. Cross size caps 9 and 11, both modes, and three fresh-process replicates (12 workers total) in randomized order. Use a 12-second internal generator timeout and a 16-second parent subprocess timeout. Each worker applies a 2 GiB `RLIMIT_AS` address-space ceiling before synthesis; this is an address-space cap, not a physical RSS limit. No timed-out, memory-limited, or errored worker is retried or replaced.

The size-9 arm controls for host/runtime variation against v1.2 and confirms the resource-limited wrapper itself does not change the completed result. Synthesis receives exactly one labeled example `(n=1, output=1)`. The held-out labels are evaluated only after a pool returns. Parent timeouts, memory-limit failures, worker errors, internal timeouts, and completed but incomplete pools are kept distinct. Parent-timeout rows have no in-worker synthesis metrics; do not impute them.

## Analysis gates

The 10 checks require: (1) pre/post source and native provenance match; (2) all 12 scheduled outcomes appear once; (3) every run has an explicit status; (4) complete search pairs have identical ordered pool digests and counts; (5) complete pairs have identical held-out exact-pool results; (6) the fixed training/probe setup is respected; (7) all returned hypotheses fit the single anchor; (8) only `max_size` is called complete; (9) completed worker measurements are finite and record the 2 GiB limit; and (10) timeouts, memory-limit failures, and worker errors remain explicit and non-retried.

Report completion, internal timeout, parent timeout, address-space failure, and worker-error counts by mode and size. If size 9 fails under the new resource wrapper, size-11 outcomes remain descriptive and the implementation difference must be investigated before comparing to v1.2. This one-family, one-anchor panel is not a general synthesis complexity result.

## Reproduction

Run `python3 evaluation/substrate_capability/substrate_generator_stream_scale_v1_3.py --lock`, then `--capture`, then `python3 evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_4.py`.
