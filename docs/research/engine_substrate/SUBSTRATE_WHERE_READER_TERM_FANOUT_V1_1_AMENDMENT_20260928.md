# Where-reader Term/fan-out v1.1 amendment

V1's semantic and candidate-count gates passed, but its audit snapshot began only after batch deletion. As a result, its `ReachableFrom` interior-work count described the empty post-delete graph and was zero; it did not measure the nonempty initial traversal. The v1 raw, analysis, and lock are retained as `substrate_where_reader_term_fanout_v1_initial_20260928.json`, `substrate_where_reader_term_fanout_v1_initial_analysis_20260928.json`, and `where_reader_term_fanout_v1_initial_lock_20260928.json`.

V1.1 changes only audit placement and artifact paths: it snapshots counters for both initial closure and post-delete closure, resetting between phases. Workload cells, graph fixtures, rules, mutation operation, and semantic gates are unchanged. The new report separates `ReachableFrom` traversal units from candidate and Term invocation counts.
