# Thoughtexperiment recurrence parallel scale v1 preregistration

Extend the established recurrence-repair parallel-wave workload from 100,000 to 1,000,000 linked unrelated nodes. Each worker runs both sequential and eight-thread branch waves on the same 64-candidate recurrence task. Cross native full-copy/shared-graph-pages backends with three fresh-process repetitions per backend (six workers total); alternate sequential-first and concurrent-first order by repetition.

Each branch restores the authored negative-existence guard, emits exactly one offer for each of 64 candidates, reaches a zero-progress fixed point, and agrees across execution mode/backend. The primary graph counts, revision, and complete rule vector must remain unchanged. Record wall time, experiments per second, sampled PSS/RSS, and source/native provenance. The independent analyzer checks six unique workers, complete cell coverage, 64/64 branch outcomes per wave, backend/mode parity, host isolation, and stable sources.

This is a single recurrence family, one synthetic linked-noise topology, one host, fanout eight, and a 10 ms PSS sampler. It measures simultaneous branch waves with serialized Python-level fork calls and concurrent native closure; it does not measure autonomous candidate discovery, natural workload throughput, or general scaling. Stop before a worker if available host memory is below 12 GiB.
