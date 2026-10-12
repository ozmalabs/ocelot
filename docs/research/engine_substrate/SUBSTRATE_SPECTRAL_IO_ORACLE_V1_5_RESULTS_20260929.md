# Spectral primitive I/O guard replication v1.5 results (2026-09-29)

## Result

The 12-call, fresh-graph source-locked replication passed its fixture and pre/post-lock gates. All six valid forward `signal`→`spectrum` cases built and were accepted; all six matched the independent direct DFT oracle across three length-32 signals (maximum absolute error `2.22e-16`). All six magnitude-only `magnitude_spectrum`→`recovered_signal` cases returned a `PrimitiveRequest(recover_signal)`, with no term tree and no installed `recover_signal` primitive. The inverse non-identifiability witness again passed: two different signals had one-sided magnitude difference `9.77e-15`.

The extension's spectral constructor selection now checks that the requested primitive and declared ports match the registered forward spectral-value construction. This closes the measured false-acceptance path while preserving the tested forward behavior. Evidence is limited to this alias and these deterministic inputs: it does not establish soundness for other primitive families, all port naming conventions, natural task rates, or the capability of a future inverse primitive with additional phase/side information.

## Provenance

- Protocol: [`SUBSTRATE_SPECTRAL_IO_ORACLE_V1_5_PREREG_20260929.md`](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_5_PREREG_20260929.md)
- Runner and source lock: [`spectral_io_oracle_v1_5.py`](../../../evaluation/substrate_capability/spectral_io_oracle_v1_5.py), [`lock`](../../../evaluation/substrate_capability/spectral_io_oracle_v1_5_lock_20260929.json)
- Raw capture and analysis: [`capture.json`](../../../evaluation/reports/spectral_io_oracle_v1_5/capture.json), [`analysis.json`](../../../evaluation/reports/spectral_io_oracle_v1_5/analysis.json)

