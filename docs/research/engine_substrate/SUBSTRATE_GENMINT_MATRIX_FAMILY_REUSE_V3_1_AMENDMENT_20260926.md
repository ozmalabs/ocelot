# GenMint matrix-family reuse v3.1 analysis amendment

The v3 preregistered run and raw capture are unchanged. Its independent v3 analyzer failed the `independent_input_reconstruction` gate because it reused the randomized schedule seed (20260926) when reconstructing the 16 held-out bases. The runner intentionally retained the v2 held-out geometry seed (20260930); these are separate design seeds. The amended analyzer now uses the locked held-out seed for geometry reconstruction and the preregistered schedule seed only for worker-order reconstruction.

No workload, raw record, outcome, metric, or acceptance criterion changed. The initial v3 analysis is preserved. The amended v3.1 analysis passes all 16 checks, including exact schedule reconstruction, independent inputs, full cell balance, unique workers, locked source/native provenance, and repeat determinism. The authoritative independent analyzer is `scripts/analyze_genmint_matrix_family_reuse_probe_v3_1.py`.
