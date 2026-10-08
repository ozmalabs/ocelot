# Full-seed nonlinear DimInfer codebook ablation v1.2.1 analysis amendment

The locked v1.2 capture completed without worker failures. Its first independent analysis reported only `independent_input_reconstruction=false`: the analyzer rebuilt expected coordinates as Python tuples and compared them directly with the raw JSON arrays at the top-level expected-target field. The per-arm target comparison already converted coordinates into relation lists and passed, as did route, control, balance, provenance, and complete-record checks.

The amended analyzer normalizes the independently reconstructed top-level expected target to JSON list form before comparison. No raw values, workload, scoring criteria, or thresholds changed. The initial v1.2 analysis is preserved; v1.2.1 is the authoritative analysis.
