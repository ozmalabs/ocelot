# Public remove-node scale v1.1 amendment

All v1 worker node/edge and sample oracles pass, and worker/source locks are stable. The aggregate runner failed only because JSON decoding represents the recorded `(node_id, type)` hook tuple as a list, while the parent oracle compared it to a tuple. V1.1 retains the v1 capture and changes the expected serialized hook to `[0, "Hub"]`; no engine, workload, timing, or graph-state criteria change. V1.1 uses fresh lock and raw paths.
