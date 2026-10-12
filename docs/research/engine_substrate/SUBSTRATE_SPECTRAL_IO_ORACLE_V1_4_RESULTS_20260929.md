# Spectral primitive independent I/O oracle v1.4 results (2026-09-29)

## Result

The 12-call, fresh-graph panel passed its lock-integrity and fixture-count gates. All six forward `signal`→`spectrum` artifacts matched an independent direct complex-exponential DFT oracle on three length-32 signals (maximum absolute error `2.22e-16`). The two distinct signals in the magnitude-only inverse witness had one-sided magnitude difference `9.77e-15`, below the `1e-10` threshold. In all six inverse cases, the extension returned the same forward log-magnitude term as the valid forward fixture, yet accepted it as `recover_signal`. These are six false acceptances on the preregistered cases.

This is a constructed counterexample, not an estimate of semantic error prevalence. It shows that the previous tone-peak verifier did not bind acceptance to declared input/output roles and could not establish unique recovery from magnitude-only input.

## Provenance

- Protocol: [`SUBSTRATE_SPECTRAL_IO_ORACLE_V1_4_PREREG_20260929.md`](SUBSTRATE_SPECTRAL_IO_ORACLE_V1_4_PREREG_20260929.md)
- Runner and source lock: [`spectral_io_oracle_v1_4.py`](../../../evaluation/substrate_capability/spectral_io_oracle_v1_4.py), [`lock`](../../../evaluation/substrate_capability/spectral_io_oracle_v1_4_lock_20260929.json)
- Raw capture and analysis: [`capture.json`](../../../evaluation/reports/spectral_io_oracle_v1_4/capture.json), [`analysis.json`](../../../evaluation/reports/spectral_io_oracle_v1_4/analysis.json)

