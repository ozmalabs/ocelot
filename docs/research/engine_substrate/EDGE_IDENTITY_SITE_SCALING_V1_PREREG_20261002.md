# Edge identity site extraction scaling v1 preregistration

This microbenchmark tests the candidate-extraction part of the edge-identity structural composer. It uses synthetic rules whose fresh node has `m` direct fields, each copied from a bound `Attr` term. It measures `find_edge_identity_sites` only; it does not measure graph materialization, native Term selection, complete composition, memory use, or task accuracy.

The locked field counts are 1, 2, 4, 8, 16, 32, 64, 128, and 256. Each point receives two warmups and seven `perf_counter_ns` trials; the reported value is the median. The expected number of attribute sites is `m + choose(m,2) + 1[m>2]`; one relation-only site is also expected. The runner and `domains/edit_ops.py` hashes, Python version, and platform are captured in the lock. This is a single-host diagnostic, not a cross-machine performance claim.

The implementation is considered count-correct when the observed attribute-site count matches that formula at every point. Timings characterize this extraction function under the specified synthetic input only. Extrapolations to full thoughtexperiment composition require separate measurements.

- Runner: [measure_edge_identity_site_scaling_v1.py](../../../evaluation/substrate_capability/measure_edge_identity_site_scaling_v1.py)
- Lock: [edge_identity_site_scaling_v1_lock_20261002.json](../../../evaluation/substrate_capability/edge_identity_site_scaling_v1_lock_20261002.json)
- Results: [edge_identity_site_scaling_v1_20261002.json](../../../evaluation/reports/edge_identity_site_scaling_v1_20261002.json)
