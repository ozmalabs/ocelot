# Conversation-profile runtime import observation v1 results

Date: 2026-09-28  
Status: all source, replication, profile, and import-observation gates pass.

## Capture

Three fresh worker processes ran `load_conversation_seed_profile()` under the source lock. Each loaded the same 74 seed IDs without reported loader failures and ended with 2,100 graph nodes and 1,390 edges. The source lock hashes all 833 Python files in the audited roots, all 838 loader-discovered seed manifests, the Rust source fingerprint, native extension/build record, and capture scripts/protocol. Inputs matched at each worker's start and finish and before/after the full capture.

The explicit profile declares 65 unique module loads. The wrapper observed all 65 `importlib.import_module` calls in the declared order, all resolving to the locked in-repository Python files. None of the 65 targets was already in `sys.modules` before profile loading. The profile added 86 `domains.*` modules total: the 65 declared targets plus transitive imports. All 86 were in the v1.1 declared runtime-reachability set. The import observer found one `domains.*` module already loaded before profile invocation, attributable to the provenance/setup path.

The raw per-worker capture is [here](../../../evaluation/reports/profile_runtime_import_observation_v1_20260928.json), the independent gate summary is [here](../../../evaluation/reports/profile_runtime_import_observation_v1_analysis_20260928.json), and the full input hashes are [here](../../../evaluation/substrate_capability/profile_runtime_import_observation_v1_lock_20260928.json). The [preregistration](SUBSTRATE_PROFILE_RUNTIME_IMPORT_OBSERVATION_V1_PREREG_20260928.md) defines the scope and gates.

The exact locked source/native/seed inputs are also preserved in [the replay source bundle](../../../evaluation/substrate_capability/source_bundles/profile_runtime_import_observation_v1_20260928.tar.zst), SHA-256 `efc81107025cc19f402024b13bc2dcbaf175cb7d90b813ff8aa2f0ffd295aa4d` (1,778 files). The bundle is verified against the captured per-file hashes before creation and against the Rust/native fingerprints; its compressed archive passes `zstd -t`. The bundle creation helper is [here](../../../scripts/archive_profile_runtime_import_source_v1.py).

## Cost observations

Instrumented profile call time was 2,797 ms, 558 ms, and 571 ms across the three processes (median 571 ms). Peak process RSS was approximately 386 MiB, 127 MiB, and 127 MiB. The first process was much slower and larger than the next two; process count is too small to estimate a stable cost distribution, and OS page-cache state was not controlled. The wrapper and import tracing add unmeasured overhead. These measurements include profile seed selection/loading and module preloads; they are not per-turn inference costs or commodity-scale claims.

## Interpretation and next gate

The explicit preload list corresponds to actual import calls, and the profile's observed module delta fits within the static-plus-declared reachability census. This supports the inventory's usefulness as a code navigation map while showing that a single profile loads 86 domain modules at boot. It does not show that any particular module is needed by each task or that importing it exercises its capability.

Next instrument actual separately selected task families after profile boot, record per-turn module activation and call-path evidence, and connect those modules to independent task oracles. Then classify the remaining unlinked modules instead of treating import reachability as capability coverage.
