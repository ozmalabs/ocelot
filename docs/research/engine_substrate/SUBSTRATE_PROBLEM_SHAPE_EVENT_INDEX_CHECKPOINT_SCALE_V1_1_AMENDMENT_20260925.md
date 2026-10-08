# V1.1 amendment: time the load operation itself

All four writer/reader size cells passed state and fixed-point checks, but review found the reader's `load_wall_ns` timer started after `WorldAdapter.load()` and therefore captured projection checking rather than deserialization. Preserve that raw run as a diagnostic and rerun the four size cells with a timer around `WorldAdapter.load()` itself. Record projection-check time separately. No state, workload, size, arm, or semantic check changes.
