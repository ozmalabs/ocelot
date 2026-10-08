# Full P4 route diagnostic note (2026-09-25)

**Run state:** discovery diagnostic, not confirmatory. This run reuses the 22-task list-transform family from [`SUBSTRATE_LIST_PBE_PREREG_20260925.md`](SUBSTRATE_LIST_PBE_PREREG_20260925.md), whose direct enumerator outcomes have already been inspected. It therefore cannot serve as an independent or blinded generalization result.

## Question and path

Measure how the existing `domains.prog_synthesis.synthesize_from_request` pipeline handles these list tasks from request text and four revealed examples through the full P4 ladder. Use the main configured codebook and learned statistics as installed by `scripts/prog_synthesis_battery.py::boot(False)`. No policy, seed, grammar, task, or search-budget changes are made. Each task receives a fresh substrate. Request wording is fixed in the harness before this diagnostic and describes the intended transformation; held-out rows are passed only to the external scoring layer.

Record each task's outcome, selected/active rungs, gap reason, residual tokens, enumeration detail, candidate count where reported, route wall time, setup time, and held-out verdict. Total process RSS is a process high-water mark. The run uses the harness's built-in request cues and ladder; no retries or manually selected alternative prompts are allowed.

The first instrumentation pass completed, but its summary omitted the `retrieval` and `construction` read-back already returned by `read_goal`, so its non-null rung counts are incomplete. The preserved initial raw record is [`substrate_list_pbe_pipeline_pilot_20260925.json`](../../../evaluation/reports/substrate_list_pbe_pipeline_pilot_20260925.json). A corrected harness adds these fields and performs one deterministic instrumented repeat, with its own provenance, in [`substrate_list_pbe_pipeline_instrumented_replication_20260925.json`](../../../evaluation/reports/substrate_list_pbe_pipeline_instrumented_replication_20260925.json). The initial result is not overwritten; the corrected report is the source for route classification. Because outcomes were already observed, this correction and repeat remain discovery-only.

## Interpretation boundary

The task family and its direct-search outcomes were visible before this diagnostic. Any result is useful for locating routing and instrumentation gaps and comparing route behavior with the direct-search mechanism envelope, but not for estimating new-task generalization or prevalence. The endpoint also does not test source-level minting/adoption, reuse across tasks, or transfer. A future confirmatory run requires a new, independently frozen family, prompts, split, harness and budget before outcomes are inspected.
