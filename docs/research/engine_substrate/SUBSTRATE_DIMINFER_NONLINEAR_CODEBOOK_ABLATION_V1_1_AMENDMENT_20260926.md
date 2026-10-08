# Full-seed nonlinear DimInfer codebook ablation v1.1 amendment

The first harness launch completed all 72 scheduled workers but every worker failed before inference because the runner called `run_rules()` on the Python graph adapter. The production call site used by the existing full-seed measurements is the native facade returned by `reflective_faculty._native_eval2`; rule closure must be invoked as `native.run_rules()`.

The v1 raw failure record is retained. V1.1 changes only this harness call and the corresponding runner/provenance lock paths. The same 72-cell design, transform fixtures, scoring criteria, and analysis gates remain unchanged. No result from the failed launch is treated as a measurement.
