# Task-graph structural census v1.2 amendment

Date: 2026-10-03

The v1.1 capture completed all 78 planned graph snapshots and passed its runner checks. Its independent analyzer stopped on an upstream edge whose endpoint was absent from the corresponding node table. The runner had excluded such endpoints from its simple undirected projection; the analyzer's min-fill certificate check had not. V1.2 retains the v1.1 lock, capture, analyzer, and amendment as provenance, and updates the independent analyzer to filter endpoints to the graph's declared node set before verifying the width certificate. No input selection, planned observation, or metric definition changes. The v1.2 source lock covers the analyzer change; only v1.2 analysis can support the census result.
