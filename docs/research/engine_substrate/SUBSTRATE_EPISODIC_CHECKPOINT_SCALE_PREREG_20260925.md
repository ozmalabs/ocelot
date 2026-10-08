# Preregistration: episodic graph-checkpoint scale envelope

**Question.** How do full `WorldAdapter.save/load` checkpoint size, write/read latency, memory use, and exact episodic recall cost change as graph-resident episode count grows across a small synthetic range?

**Workload and process boundaries.** Test N = 6, 24, 78, and 192 observed route episodes; run two independent writer/reader process pairs per size. Each writer boots the episodic seed, creates N events with unique exact cues and linked context/schema records, runs binding closure once, verifies N Episode nodes, and saves the complete adapter checkpoint. Each fresh reader loads the checkpoint and queries all N keys once in ascending order. Every writer and reader is a distinct PID. No durable LongTermMemory store is used.

**Frozen correctness criteria.** Each writer must bind exactly N episodes. Each reader must restore exactly N Episode nodes and retrieve all N exact expected summaries with one candidate, `recalled` provenance, and `not_observed` status. All checkpoint loads and closes must complete without error. If any criterion fails, retain the raw results and mark the size unsuccessful; do not replace failed cases.

**Measures.** Writer boot, closure, and save time; checkpoint bytes; reader load time; per-key retrieval tick latency (median, p95, and maximum); total query time; node count; writer/reader peak RSS; process IDs; and exact-recall rate. Timings remain descriptive for this synthetic workload. Do not infer complexity order from four sizes or two repeats.

**Claim boundary.** This is a scale envelope for the current authored episodic graph checkpoint and exact symbolic cues over N≤192. It is not evidence for long-term JSON record-index scale, natural-task retrieval, semantic cue matching, crash consistency, corruption integrity, or commodity-CPU performance at millions of nodes. The sizes and criteria are fixed before the scored run; no exploratory worker is run beforehand.
