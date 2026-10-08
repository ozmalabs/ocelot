# Query Index Branch Reuse v1.1 Amendment

The v1 capture and its original analyzer are preserved. The initial analyzer required every selected hidden target to become the sole survivor. Review showed that this requirement is stronger than the configured CEGIS numeric tolerance: distinct exact floating signatures can remain mutually consistent within `1e-9` after every available query. The raw capture records these as non-singleton survivors in both cached and uncached arms; no cached/uncached query-sequence or survivor mismatch occurred.

The amended analysis uses the appropriate invariant for an oracle-consistent branch: the hidden target must remain in the final survivor set, cached and uncached branch outputs must match exactly, and unique-recovery rate must be reported separately. It does not relabel ambiguous branches as successful identification. The query family has 13 candidates as defined by the source; the Euler active-query protocol's prose and `max_queries` metadata said 12, but no v1.1 policy used more than nine queries, so that mismatch did not affect this captured run. Future protocols must derive the limit from the source family and enforce it in the runner.

This amendment changes only the analysis gate; it does not alter or rerun the v1 branch workload. Its analyzer records its own source hash alongside the unchanged runner lock and raw-capture hash.
