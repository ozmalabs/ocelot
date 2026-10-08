# Production treewidth gate relabelling v1.1 harness amendment (2026-09-29)

The initial v1 locked invocation stopped in worker 1 before calling the production solver: the state-snapshot helper passed integer graph IDs to a native API requiring `NodeID` handles. No solver decision or result capture was produced. The v1 lock is retained.

V1.1 snapshots attributes through the original handles returned by node creation. This changes only measurement bookkeeping; graph generation, randomized insertion orders, solver calls, oracle, dimensions, and gates are unchanged. A fresh v1.1 lock and capture path are used.

