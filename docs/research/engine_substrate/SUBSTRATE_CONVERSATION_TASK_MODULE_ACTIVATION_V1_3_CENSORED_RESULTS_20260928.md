# Conversation task module activation v1.3 — censored capture

**Protocol:** [v1.3 preregistration](SUBSTRATE_CONVERSATION_TASK_MODULE_ACTIVATION_V1_3_PREREG_20260928.md).  
**Evidence:** [partial raw capture](../../../evaluation/reports/conversation_task_module_activation_v1_3_20260928.json), [independent analysis](../../../evaluation/reports/conversation_task_module_activation_v1_3_analysis_20260928.json), [source lock](../../../evaluation/substrate_capability/conversation_task_module_activation_v1_3_lock_20260928.json), [runner](../../../scripts/substrate_conversation_task_module_activation_v1_3.py), [analyzer](../../../scripts/analyze_substrate_conversation_task_module_activation_v1_3.py).

## Censor reason

The capture ran while `substrate/world_adapter.py` was changing. Its SHA-256 was `a5df84271c12709806b6c014f22cee64edafa0f9059d6bc0a00208df8ecdd733` at lock time and `062b51b1274d248e54edcee3d3c8c0caad8db7276128e81a888b63128b309bcb` by the end. Two workers completed with stable inputs; the third worker detected intra-worker drift; the remaining seven workers refused the stale parent lock. The capture is marked censored and the independent analyzer fails the required completeness/source-stability gates.

The profiler recognized exactly one conversation extent in each of the three completed workers, so the v1.3 wrapper-aware root detector worked. The first two task oracles pass on their stable per-worker source snapshots; the third result is excluded because its source changed during the worker. No aggregate outcome, repeatability, timing, or module comparison is admissible from this partial run. Preserve all three records for audit and do not pool them with v1.1 or v1.2.

## Consequence

V1.2 remains a valid locked snapshot and its source/map crosswalk remains a valid statement about that snapshot's 40 observed domain modules. It is no longer the latest `substrate/world_adapter.py` source state. A fresh current-route panel needs a source snapshot that remains unchanged for all workers; meanwhile, a separately gated static source census can refresh file hashes and map coverage. The repeated mid-panel drift is a measurement constraint, not evidence of a capability change.

## Static source refresh and task-module join

The separate v1.3 Python source census completed with stable pre/post source, seed, and capability-map hashes. It reports 69/833 directly linked files (8.3%), 247/833 files statically import-reachable, and 248/833 reachable after declared profile loads. A seven-check join of the complete v1.2 task capture to this current census finds all 40 observed Python domain modules directly linked and all 40 per-file source hashes unchanged since the task run. The changed file is the adapter, `substrate/world_adapter.py`, outside the domain-module set; therefore module-level Python activation remains source-consistent while the v1.2 task route itself is not a current adapter result ([source census](SUBSTRATE_PYTHON_SOURCE_COVERAGE_AUDIT_V1_3_RESULTS_20260928.md), [crosswalk](../../../evaluation/reports/conversation_task_module_source_crosswalk_v1_3_20260928.json)).
