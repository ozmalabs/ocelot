# Preregistration: scoped fallback for deferred NetCollapse updates

**Question.** Does the scoped pending-work flag plus full-closure fallback preserve a deferred `NetCollapse` update, including its writes to graph-resident weight tensors, compared with ordinary full closure?

**Why this queue.** `NetCollapse` is a distinct deferred path from `TrackIdentity`: it queues numerical input/target/learning-rate values, then updates a `NetworkAssemblage`'s `WeightTensor.data` and a `ReflexNet.surprise` attribute. This tests queue signaling and fallback parity for numerical model state, not identity attributes.

**Frozen matrix.** One, two, or four independent reflex-net/observation pairs, each assigned to a distinct consumer frame; all observations are owned by a single controller Microtheory whose scoped rule can enqueue them. Each net has a deterministic one-input/one-output assemblage with a single ReLU step, fixed `W1=1`, `b1=0`, zero `W2` and `b2`, input `[1]`, target `[1]`, and `eta=0.1`. Three fresh-process arms are run twice per size: ordinary `full`, `scoped_only` with progress budget 1, and `scoped_fallback`, which runs global closure only after the scoped pending flag appears.

**Gates.** The scoped arms must expose both pending queue and budget exit. Full and fallback closure must settle; a final global probe is zero-work. Fallback must reproduce the full arm's exact per-net `W2`, `b2`, surprise, observation status, and controller status. Scoped-only is retained as a negative control and must leave some queued model updates unflushed. Fresh PIDs and locked hashes are required.

**Claim boundary.** This measures one simple deterministic network geometry and one deferred update per observation, not learning quality, nontrivial network scaling, queue interactions with other effects, or natural frame prevalence. No cost claim is made.
