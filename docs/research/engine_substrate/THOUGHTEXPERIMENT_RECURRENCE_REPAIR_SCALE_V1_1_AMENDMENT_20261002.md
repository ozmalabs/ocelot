# Recurrence repair scale v1.1 amendment — explicit branch release

The v1 scale runner reused `thoughtexperiment_recurrence_repair_memory_v1.worker`. Source inspection after capture found that the helper binds `bn = branch._inner` and later deletes only `branch`; the `bn` alias keeps the native branch alive during the purported after-drop sample. Therefore v1 peak deltas and task/isolation gates remain valid, but its `after_drop_bytes` values are retained-branch measurements and cannot be interpreted as reclamation.

V1.1 keeps the one-million-node fixture, recurrence repair semantics, two backends, three fresh processes per backend, and 10 ms sampler. It independently implements the worker lifecycle and deletes both wrapper and inner-substrate references before collecting and sampling after drop. It preserves v1 artifacts and uses a new source lock and capture. This amendment changes no semantic task gate; it corrects only branch lifetime accounting.
