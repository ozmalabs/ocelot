# Spectral primitive I/O oracle v1.6 — current-source replay results

**Result:** all 12 current-source cases pass the amended independent analysis.

Six `spectral_value` forward cases (two faculty-key arms × three replicates) build and install the registered Term tree. The amended analyzer evaluates each captured Term natively on three fixed length-32 signals and compares all 17 frequency-bin outputs per signal against an independently calculated direct-DFT log-magnitude oracle. Across the six forward cases, all 18 signal checks (three signals per case) pass within `1e-6`. Six magnitude-only `recover_signal` requests produce no accepted Term or installed recovery primitive and instead return a `PrimitiveRequest`. The separate non-identifiability witness uses two distinct signals whose one-sided magnitude spectra differ by at most `9.77e-15`.

The replay uses a fresh graph for every case through the source-locked v1.5 execution helper. The raw capture has 12 distinct arm/case records, and all execution sources other than the corrected analyzer remain identical to the v1.6 pre-run lock. The first analysis attempt failed on a validator defect: it treated a graph-local `codebook_epoch` of zero as a globally unique graph identity. The raw capture was retained unchanged; the [analysis amendment](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_ANALYSIS_AMENDMENT_20261001.md) records the correction. The corrected analyzer separately hashes the amendment and itself and confirms the captured execution-source lock before evaluating outcomes.

This validates the current captured implementation for one fixed registered construction. It does not show that the substrate inferred the spectral formula: `substrate_extension.py` selects one named recipe and supplies both its Term tree and fake control. The source audit still finds one registered construction family. Selection among multiple learned constructions, an independent second recipe, and naturally occurring task utility remain unmeasured.

## Artifacts

- [Preregistration](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_PREREG_20261001.md)
- [Analysis amendment](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_6_ANALYSIS_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/spectral_io_oracle_v1_6.py)
- [Amended analyzer](../../../evaluation/substrate_capability/analyze_spectral_io_oracle_v1_6.py)
- [Execution lock](../../../evaluation/substrate_capability/spectral_io_oracle_v1_6_lock_20261001.json)
- [Analysis lock](../../../evaluation/substrate_capability/spectral_io_oracle_v1_6_analysis_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/spectral_io_oracle_v1_6_raw_20261001.json)
- [Independent analysis](../../../evaluation/reports/spectral_io_oracle_v1_6_analysis_20261001.json)
