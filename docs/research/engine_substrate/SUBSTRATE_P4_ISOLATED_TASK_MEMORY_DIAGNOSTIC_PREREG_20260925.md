# Isolated per-task P4 acquisition memory diagnostic

**Status:** diagnostic replication of an already inspected family, not confirmatory capability evidence.

## Question and procedure

Repeat the 18 contrast-string P4 acquisitions with one new OS process per task. Each worker imports the locked current substrate/P4 code, boots a fresh substrate, and runs exactly one task from `tests/fixtures/substrate_string_pbe_contrast/tasks.json` in fixture order. The worker reports current RSS after imports, after boot, immediately before and after route acquisition, and after optional correctness scoring; process peak RSS is isolated to that worker. Python `tracemalloc` starts after boot and captures route-window current/peak deltas. It does not include Rust allocator memory. Record TermArena length and graph node count before/after route, status, route wall/CPU, and seven-row correctness for accepted IRs.

The parent orchestrator runs each worker sequentially, requires one valid JSON record per requested task, and fails on worker exit or provenance mismatch. No retries or route changes are permitted. Lock the runner, task family, P4 boot, synthesis/retrieval adapters, seed, preregistration, and native extension before starting workers.

## Interpretation

Fresh processes isolate process high-water RSS by task and remove allocator carry-over between tasks; they still include interpreter/native import and boot costs, so route-attributable memory is approximated by stage differences. `tracemalloc` measures Python allocations only. This known task family and its outcomes have already been inspected, so success rates and timings are descriptive. The run is not a scaling curve, natural-distribution estimate, or evidence about general induction.
