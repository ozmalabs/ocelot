# Grounded concern-dispatch probe v1.1 amendment

The v1.0 capture completed four fresh worker processes, but all workers exited while JSON-serializing the action result because the returned `goal` field is a native `NodeID`. No worker outcomes or timings were captured. Preserve the v1.0 lock, partial raw output, and runner as failed-harness artifacts.

V1.1 fixes only serialization: node handles are recorded by integer `.value` where available. It uses a fresh lock and raw path. The conditions, setup, action call, and oracles remain unchanged. See the v1.1 preregistration for the executable design.
