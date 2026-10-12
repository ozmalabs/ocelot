# Scoped snapshot clone cost results

**Protocol:** [`SUBSTRATE_SCOPED_SNAPSHOT_CLONE_COST_PREREG_20260926.md`](SUBSTRATE_SCOPED_SNAPSHOT_CLONE_COST_PREREG_20260926.md)  
**Runner:** [`substrate_scoped_snapshot_clone_cost_v1.py`](../../../scripts/substrate_scoped_snapshot_clone_cost_v1.py)  
**Independent analysis:** [`substrate_scoped_snapshot_clone_cost_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_snapshot_clone_cost_v1_20260926_analysis.json)

All 60 cells pass source/native/build integrity and semantic checks. The Rust diagnostic cloned exactly the reported number of active rule slots per iteration; scoped calls reached fixed points with unchanged graph/rules and zero candidate, Term, or audit work. Both timings were measured on the same fixture/build, with five fresh repeats.

The measured snapshot filter/clone/allocation/drop takes 10.6–142.0 μs per iteration across the matrix. Against scoped no-match API medians of 12.3–152.2 μs/call, the paired diagnostic median is 86–95% of the full call, depending on rule shape/count. This is a descriptive fraction: the diagnostic repeatedly drops snapshots in its own loop, while a production snapshot lives through reference construction and matching; it also excludes ownership discovery and includes loop overhead.

Paired effects-axis contrast (one versus eight effects/rule) is especially diagnostic: the snapshot-only increment is 4.1, 18.6, and 36.4 μs at 64, 256, and 512 rules, compared with same-build end-to-end increments of 4.2, 16.6, and 37.5 μs. At 256/512 rules these increments closely track; at 64 both are small. For match edges, snapshot increments are 0.5, 3.3, and 4.3 μs, versus end-to-end increments −0.1, 0.4, and 4.3 μs; the smaller differences are noisy. Thus copied active-rule payload plausibly explains much of the effect-size slope; added pattern size is less clearly a bottleneck in this fixture. This is still not an instruction-level attribution or evidence that caching will pay off after invalidation costs.

The cache feasibility audit finds that `Substrate::rules` is public and is mutated outside the core API: `cognitive_cycle.rs` and `wave_stencil.rs` temporarily toggle `active` directly. Core paths also add, tombstone, swap in patched rules, and update metadata/pushdown plans. A retained clone cache cannot be trusted without first encapsulating all external mutations and routing them through invalidation-aware methods.

**Next:** prototype a borrow-based scoped runner that holds immutable references to live active rules while mutably borrowing disjoint graph/Term/concept fields. This removes the per-call clone without a retained cache or invalidation protocol. Verify exact event/full parity, counter conservation/original indices, and audit-on/off behavior across active-rule mutation and tombstone fixtures. No natural workload distribution or system-scale claim follows from this synthetic probe.
