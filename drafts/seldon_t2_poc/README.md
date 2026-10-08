# seldon_t2_poc — reachable-set-plus-confidence forecasting PoC

Standalone empirical PoC probing whether Agenthon 2026 Track T2 (Forecasting)
can be implemented as a "Seldon manifold with a confidence dimension". Pure
Python + numpy; does **not** touch `substrate_rs`, the main tree, or the test
suite.

**Read `REPORT.md` for findings and the honest verdict.** This is a
synthetic-data mechanism study, not evidence of benchmark value.

## Run

```bash
cd drafts/seldon_t2_poc
python3 test_crps.py     # CRPS correctness gate (8 checks)
python3 run_poc.py       # end-to-end: CRPS table, calibration, text-uplift ablation
python3 multiseed.py     # 10-seed robustness sweep
python3 data.py          # inspect the synthetic panel
```

Requires: `python3`, `numpy`. No `scipy`, no Rust build.

## Files

- `crps.py` — closed-form CRPS for stepped `(value,mass)` distributions (+ energy-score cross-check). Load-bearing correctness module.
- `test_crps.py` — correctness gate; `run_poc.py` aborts if it fails.
- `data.py` — regime-switching AR(1) integer panel + timestamped text corpus with genuine advance signal.
- `forecasters.py` — `SeldonConfidenceForecaster` + climatology + Gaussian-AR(1) baselines.
- `calibration.py` — randomised-PIT calibration for discrete predictive CDFs.
- `run_poc.py` — single-command end-to-end runner.
- `multiseed.py` — robustness across seeds.

## One-line result

Valid, CRPS-scorable, out-of-the-box-calibrated forecast object; text
conditioning gives a real ~6% CRPS reduction (95% CI [3.6%, 10.1%], 10/10 seeds)
on synthetic data where text carries signal; the reachable-set framing itself
earned ~nothing over a plain AR baseline text-blind. Not benchmark value.
