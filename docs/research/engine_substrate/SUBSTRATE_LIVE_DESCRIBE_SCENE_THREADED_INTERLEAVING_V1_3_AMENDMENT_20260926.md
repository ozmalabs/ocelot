# Live describe-scene threaded interleaving v1.3 amendment

**Amendment before capture.** V1.2 establishes that the per-adapter lock serializes two live describe-scene calls and that both Goal-bound lifecycles complete. It does not attribute the work performed by the production event writer, `_record_live_goal_event`.

V1.3 repeats the exact two-thread schedule and semantic oracles from v1.2. A wrapper resets and enables native scale counters immediately around each production lifecycle helper call, records its elapsed time, global counters, and per-rule counters, then disables instrumentation before returning to the unchanged action path. It requires six helper calls per worker (selection, execution, result for each Goal), counter conservation, and exact candidate/Term work replication across the three workers. The existing exact reply, identity, lifecycle, and lock-serialization gates remain unchanged.

The new capture remains one scene vocabulary, one instruction text, one adapter, and one serialized schedule. Counter mode is scoped to helper calls and its timing includes helper event setup plus native closure. No cost ratio, natural-task distribution, general concurrency guarantee, or unlocked-control comparison will be claimed. The analyzer and all source dependencies are included in the fresh content-hash lock.
