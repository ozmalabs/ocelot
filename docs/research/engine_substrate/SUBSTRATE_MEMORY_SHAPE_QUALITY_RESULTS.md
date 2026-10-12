# Durable memory shape-recall quality pilot

**Run date:** 2026-09-25  
**Runner:** [substrate_memory_shape_quality_pilot.py](../../../scripts/substrate_memory_shape_quality_pilot.py)  
**Independent analyzer:** [analyze_substrate_memory_shape_quality_pilot.py](../../../scripts/analyze_substrate_memory_shape_quality_pilot.py)  
**Preregistration:** [SUBSTRATE_MEMORY_SHAPE_QUALITY_PREREG_20260925.md](SUBSTRATE_MEMORY_SHAPE_QUALITY_PREREG_20260925.md)  
**Lock:** [memory_shape_quality_lock_20260925.json](../../../evaluation/substrate_capability/memory_shape_quality_lock_20260925.json)  
**Raw report:** [substrate_memory_shape_quality_pilot_20260925.json](../../../evaluation/reports/substrate_memory_shape_quality_pilot_20260925.json)  
**Independent analysis:** [substrate_memory_shape_quality_analysis_20260925.json](../../../evaluation/reports/substrate_memory_shape_quality_analysis_20260925.json)

## Method

The fixture stores 36 records in six ordinal-rank clusters. Each cluster contains three “low” and three “high” magnitude records; the values in each cluster share their rank ordering under positive scaling and offset. Twelve fresh-process queries cover every rank class at both magnitudes. The writer pages all six clusters out before readers launch. Each query is read through both shape recall and exact-key lookup.

## Results

All 12 readers indexed all 36 durable records without duplicate or skipped records. The writer evicted all six clusters and left zero memory records resident. Shape recall returned six records for every query, with 100% precision on the rank label and 50% precision on the magnitude label. Exact-key lookup returned the requested record on all 12 controls.

Median reader index-rebuild time was 1.30 ms for the shape arm and 1.32 ms for the exact-key arm. Median shape lookup was 0.085 ms; exact-key lookup was 0.084 ms. These are adapter-level timings over 36 tiny files and exclude interpreter startup; they are not service-level or large-store performance estimates.

The independent analyzer confirms six fixture classes with six records each, a balanced 3/3 magnitude mix, the expected cluster ID for all 12 queries, and agreement between the fixture-derived class precision and the raw aggregate metrics. The raw artifact records the exact-key correctness boolean but omits its returned key string and the shape candidate key lists; the independent analyzer therefore cannot independently verify every individual paged record identity.

## Interpretation and limits

This is a controlled retrieval mechanism result. It confirms the claimed ordinal-rank invariance for positive scale changes on an aligned synthetic feature task, while demonstrating a sharp information boundary: records that share the same rank but differ in absolute magnitude are merged into one six-record drawer. Exact-key recall can recover a known key, but does not solve query-to-key identification.

The rank-class label is intentionally aligned with the index representation, and the magnitude label is intentionally not. Neither is learned task semantics or a natural workload. This does not establish that the memory system improves task performance, selects useful memories under interference, or generalizes to other feature signatures. Next measure task-linked retrieval with realistic records, distractors and interference, then compare memory, reset-memory, and no-memory performance under a frozen task split. Preserve the candidate-identity logging gap in any follow-up protocol.

The first invocation exposed two harness-only API assumptions (shuffle metadata shape and node-ID attribute access); both are recorded in the preregistration amendment. No retrieval outcome was scored in that invocation; the amended lock predates the scored rerun.
