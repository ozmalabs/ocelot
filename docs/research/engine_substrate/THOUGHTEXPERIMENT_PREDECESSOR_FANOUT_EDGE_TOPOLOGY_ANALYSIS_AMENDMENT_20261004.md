# Edge-topology analysis amendment — 2026-10-04

The preregistered v1.1 analyzer executed after capture but stopped before
writing an analysis because it indexed a JSON-decoded integer-keyed summary
with an integer instead of the serialized string key. The raw 24-worker capture
and preregistered runner/analyzer sources were not changed. The amended
independent analyzer `analyze_thoughtexperiment_predecessor_fanout_edge_topology_v1_1_1.py`
uses the JSON string key, reruns every declared source, schedule, semantic,
size, instrumentation, and setup-time check, and writes the analysis artifact.
Its SHA-256 is recorded in that artifact. No worker was rerun, removed, or
reordered. The correction changes only analysis execution, not the protocol,
capture, or metric definitions.
