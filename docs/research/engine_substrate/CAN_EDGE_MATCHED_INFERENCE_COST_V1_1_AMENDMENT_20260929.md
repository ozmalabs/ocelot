# Edge-matched inference cost v1.1 harness amendment (2026-09-29)

The initial v1 locked invocation stopped before MAP evaluation because the generated elimination certificate used abstract fixture ids, while the live substrate assigns node ids after its Microtheory node. No inference result capture was produced. The v1 lock is retained.

V1.1 translates fixture ids to the actual graph node ids through the handles returned by native node creation, then maps extracted factors back to fixture ids for the independent oracle. Workload, factors, oracle, elimination orders, metrics, and gates are unchanged. A new lock and capture path are used.

