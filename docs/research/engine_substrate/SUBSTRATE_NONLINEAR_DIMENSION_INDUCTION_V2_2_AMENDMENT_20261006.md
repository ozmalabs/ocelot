# Bounded quadratic GenInfer v2.2 evaluation amendment

This amendment is frozen before creating the v2.2 source/native lock. The
fixture, learner, worker conditions, and 320-worker schedule from v2.1 are
unchanged.

## Launcher and failure capture

The first v2.1 launch produced no batch marker or raw report before it was
stopped. A direct run of the first scheduled worker then completed in under a
second, showing that the isolated worker path itself could finish; the original
launcher did not expose enough progress to locate its stall. The v2.1 lock is
`nonlinear_quadratic_geninfer_v2_1_lock_20261006.json` (SHA-256
`31ab9b1b59c8af2510cdef1c0ad8a243de3ab74a80970ef262ffb31251a3f950`). No v2.1
raw file was produced. Those launches are diagnostic failures and are not
confirmation data.

The v2.2 launcher prints each worker's latest stage, enforces a 300-second
worker timeout, and atomically checkpoints every completed row before starting
the next worker. If a worker times out or fails, it records the worker ID,
elapsed limit, and last heartbeat stage, finalizes an explicitly incomplete
raw report, and stops. An incomplete report fails admission and must be
preserved. Source or binary drift also fails the capture. The full schedule is
still 320 fresh processes and fresh substrates, including 160 audit-off clean
workers and their 160 audit-on semantic-parity matches.

No v2.1 or v2.2 complete raw capture existed when this amendment was written.
