# Shape-decoding concurrency profile v3 — binding scope amendment

The targeted GIL-release intervention includes all three experimental fork bindings and the aperture-scope binding. The wrapper eligibility checks still run with the GIL held; the native `Arc` is cloned before release; native locking and fork semantics are unchanged. This tests whether allowing Python worker threads to reach independent branch work during native setup is sufficient to improve the complete rehearsal wave. It is not a native orchestration implementation and does not change the primary `Substrate` state.
