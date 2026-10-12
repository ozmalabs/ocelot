# Typed rule-run report overhead pilot

**Status:** exploratory paired API microbenchmark; no general engine-performance claim.

## Question and method

What is the caller-visible cost of requesting the structured Python dictionary from `run_rules_report` instead of the legacy integer from `run_rules`? Both methods use the same Rust rule loop. The run compared them on identical two-node, two-rule toggle cycles with a progress budget of 2, where each call applies two progressing rewrites and leaves the same graph state. Scale audit was disabled. Each of seven repeats warmed both paths, then timed 5,000 calls per path. Call order alternated by repeat. Semantic output and final graph state were compared after each timed block.

Raw source/build/protocol hashes and all timings are in [the pilot JSON](../../../evaluation/reports/substrate_rule_run_report_overhead_20260924.json); rerun with `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_rule_run_report_overhead.py`.

## Results

| API path | Median wall time per call | Range across repeat medians |
|---|---:|---:|
| Legacy integer | 2.28 µs | 2.10–2.58 µs |
| Typed dictionary | 5.93 µs | 5.45–6.80 µs |

Median typed/legacy ratios were 2.72× for wall time and 2.71× for process CPU time; the wall-ratio range was 2.11–2.95×. All seven pairs matched progress counts and final graph states, and the typed path reported `progress_budget_reached` as expected. These timings include the PyO3 return conversion and Python dictionary construction for the typed path. They do not isolate the small Rust `RuleRunReport` construction, which both paths now share.

The absolute difference was about 3.65 µs per call for this micro-workload. The relative cost is high because the underlying rule run is very short; this comparison alone does not show a material end-to-end penalty at normal tick rates. Conversely, it should not be extrapolated to other rule workloads or large call counts without measurement.

## Limits and next step

The pilot uses one deterministic, audit-disabled cycle and seven repeats in one local environment. It does not compare the pre-report Rust implementation, compiled-out instrumentation, or representative substrate workloads. It measures the Python-visible report conversion, not common internal report construction. If typed outcomes are used at high call volume, compare JSON-to-Python conversion with a direct PyDict/tuple/native result, then measure both on closure and a representative active workload. Keep the legacy integer path for call sites that do not need termination status.
