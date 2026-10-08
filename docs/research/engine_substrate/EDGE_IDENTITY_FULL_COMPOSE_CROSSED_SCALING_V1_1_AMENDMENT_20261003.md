# Edge identity crossed scaling v1.1 amendment (2026-10-03)

The v1 capture is retained as diagnostic: its composer outcome was correct,
but its post-call materialization count inspected the caller graph while the
composer materializes `EditSite` nodes in a private graph copy. Its independent
analyzer correctly rejected the inconsistent count. No v1 result is treated
as valid evidence.

Version 1.1 counts sites by invoking the same `_ensure_edge_identity_sites`
materializer on the input graph before composition, recording the newly
materialized target-site count and preparation time. The composer then clones
that graph and repeats the materializer idempotently in the actual selection
path. The exact selected site reported by the composer is the selection
oracle; the prior attempt to inspect the private selected node from the caller
graph is removed. Candidate enumeration, synthetic field design, graph sizes,
trial counts, and candidate caps remain as preregistered. This change improves
instrumentation visibility; it does not change the measured compose path or
the held-out oracle.
