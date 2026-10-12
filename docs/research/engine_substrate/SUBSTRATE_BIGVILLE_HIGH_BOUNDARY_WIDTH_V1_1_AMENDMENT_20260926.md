# Bigville high-boundary-width v1.1 amendment (2026-09-26)

This amendment reruns the existing high-boundary-width design with the shared benchmark manifest and durable parent-process logs. It does not change graph topologies, sizes, boundary dimensions, seeds, case order, solver, ground truth, quality checks, or analysis thresholds from the [v1 preregistration](SUBSTRATE_BIGVILLE_HIGH_BOUNDARY_WIDTH_PREREG_20260926.md). The v1 report and its initial-undercoverage failure remain immutable.

## Provenance changes

- Use `scripts/substrate_run_manifest.py` to record the shared v1 manifest, including source/native identity, explicit input hashes, hardware/toolchain, command/environment, dirty-state summary, timing, and exit status.
- Tee parent-process stdout/stderr to a content-hashed file under `evaluation/run_logs/`. Worker stdout is parsed as structured worker data and retained in the raw report; worker stderr is retained per worker.
- Write a new v1.1 lock and raw report; do not overwrite v1 artifacts.
- Any missing log, input, or provenance field is a failed provenance gate.

## Claim boundary

This remains controlled offline inference evidence. It does not establish native frame scheduling, natural task boundary prevalence, or general cheap-cut tractability. The update is provenance-only; the original v1 outcome remains the result for the original lock.
