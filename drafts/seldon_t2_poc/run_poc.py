"""
End-to-end PoC runner for the Seldon-manifold-with-confidence T2 forecasting
experiment. Single command:

    python3 drafts/seldon_t2_poc/run_poc.py

Does, in order:
  0. Runs the CRPS correctness gate (aborts if it fails — no trusting numbers
     from an unverified scorer).
  1. Generates a regime-switching integer panel + timestamped text corpus.
  2. Builds a rolling-origin evaluation: at each of several cutoffs, forecast
     every entity at horizons h=1..H, score by CRPS against the realised value.
  3. Scores: climatology, Gaussian-AR(1), Seldon-no-text, Seldon-with-text.
  4. Calibration (randomised PIT) for the Seldon forecaster.
  5. Text-uplift ablation: Seldon-with-text vs Seldon-no-text, same everything.
  6. Prints a results table and a paired bootstrap CI on the text uplift.

Everything is seeded. Prints REAL numbers.
"""

from __future__ import annotations

import sys
import numpy as np

from crps import crps_stepped
from data import generate_panel
from forecasters import (
    climatology_forecast,
    gaussian_ar1_forecast,
    SeldonConfidenceForecaster,
)
from calibration import pit_values, pit_histogram, calibration_error, ascii_histogram


def run_crps_gate():
    import subprocess, os
    here = os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, os.path.join(here, "test_crps.py")],
                       capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr)
        print("ABORT: CRPS correctness gate failed; refusing to report numbers.")
        sys.exit(1)


def evaluate(seed=0, n_entities=60, T=320, H=5, n_cutoffs=6):
    panel = generate_panel(n_entities=n_entities, T=T, seed=seed)

    # rolling-origin cutoffs, leaving room for horizon H and >100 steps history
    first = 140
    last = T - H - 2
    cutoffs = np.linspace(first, last, n_cutoffs).astype(int)

    # per-method: collect per-(cutoff,entity,horizon) CRPS, and store forecasts
    methods = ["climatology", "gauss_ar1", "seldon_notext", "seldon_text"]
    crps = {m: [] for m in methods}
    # for calibration + paired uplift, keep aligned lists
    seldon_notext_fc, seldon_text_fc, outcomes = [], [], []
    # paired CRPS arrays aligned by (cutoff,entity,horizon)
    paired = {m: [] for m in methods}

    for cutoff in cutoffs:
        seldon = SeldonConfidenceForecaster(panel, cutoff)
        for e in range(panel.E):
            hist = panel.series[e, : cutoff + 1]
            for h in range(1, H + 1):
                y = int(panel.series[e, cutoff + h])

                cv, cm = climatology_forecast(hist, h)
                gv, gm = gaussian_ar1_forecast(hist, h)
                sv, sm = seldon.forecast(e, h, use_text=False)
                tv, tm = seldon.forecast(e, h, use_text=True)

                c_clim = crps_stepped(cv, cm, y)
                c_gar = crps_stepped(gv, gm, y)
                c_snt = crps_stepped(sv, sm, y)
                c_stx = crps_stepped(tv, tm, y)

                crps["climatology"].append(c_clim)
                crps["gauss_ar1"].append(c_gar)
                crps["seldon_notext"].append(c_snt)
                crps["seldon_text"].append(c_stx)

                paired["climatology"].append(c_clim)
                paired["gauss_ar1"].append(c_gar)
                paired["seldon_notext"].append(c_snt)
                paired["seldon_text"].append(c_stx)

                seldon_notext_fc.append((sv, sm))
                seldon_text_fc.append((tv, tm))
                outcomes.append(y)

    for m in methods:
        crps[m] = np.array(crps[m])
        paired[m] = np.array(paired[m])

    return panel, crps, paired, seldon_notext_fc, seldon_text_fc, outcomes


def paired_bootstrap_ci(a, b, n_boot=5000, seed=0):
    """Mean of (a - b) with a percentile bootstrap CI. Positive = a worse than b
    (i.e. b improves over a) when a=text-blind, b=text."""
    rng = np.random.default_rng(seed)
    d = a - b
    n = len(d)
    means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        means[i] = d[idx].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi)


def main():
    print("=" * 72)
    print("Seldon-manifold-with-confidence — T2 forecasting viability PoC")
    print("=" * 72)
    print("\n[0] CRPS correctness gate")
    run_crps_gate()

    print("\n[1] Generating panel + running rolling-origin CRPS evaluation ...")
    panel, crps, paired, snt_fc, stx_fc, outcomes = evaluate(seed=0)
    n = len(outcomes)
    print(f"    {panel.E} entities, T={panel.T}, integer range "
          f"[{panel.series.min()},{panel.series.max()}], "
          f"{len(panel.tokens)} text tokens")
    print(f"    scored {n} (cutoff,entity,horizon) forecasts per method")

    print("\n[2] Mean CRPS by method (lower is better)")
    print(f"    {'method':<22}{'mean CRPS':>12}{'vs clim':>12}")
    base = crps["climatology"].mean()
    for m in ["climatology", "gauss_ar1", "seldon_notext", "seldon_text"]:
        mu = crps[m].mean()
        rel = (mu - base) / base * 100
        print(f"    {m:<22}{mu:>12.4f}{rel:>11.1f}%")

    print("\n[3] Calibration (randomised PIT) — Seldon text-blind")
    pits = pit_values(snt_fc, outcomes, seed=1)
    counts, _ = pit_histogram(pits, n_bins=10)
    print(ascii_histogram(counts))
    ce = calibration_error(pits)
    print(f"    calibration error (KS vs uniform): {ce:.4f}   "
          f"(flat histogram / low value == calibrated)")

    print("\n[3b] Calibration (randomised PIT) — Seldon text-informed")
    pits_t = pit_values(stx_fc, outcomes, seed=1)
    counts_t, _ = pit_histogram(pits_t, n_bins=10)
    print(ascii_histogram(counts_t))
    ce_t = calibration_error(pits_t)
    print(f"    calibration error (KS vs uniform): {ce_t:.4f}")

    print("\n[4] Text-uplift ablation (paired, same forecaster, text on vs off)")
    a = paired["seldon_notext"]
    b = paired["seldon_text"]
    mean_d, lo, hi = paired_bootstrap_ci(a, b, seed=2)
    pct = mean_d / a.mean() * 100
    print(f"    mean CRPS  text-blind : {a.mean():.4f}")
    print(f"    mean CRPS  text-informed: {b.mean():.4f}")
    print(f"    mean CRPS reduction (blind - text): {mean_d:.4f}  "
          f"({pct:.1f}% of text-blind CRPS)")
    print(f"    95% paired bootstrap CI on reduction: "
          f"[{lo:.4f}, {hi:.4f}]  ({lo/a.mean()*100:.1f}%, {hi/a.mean()*100:.1f}%)")
    verdict = "UPLIFT (CI excludes 0)" if lo > 0 else \
              ("NULL/AMBIGUOUS (CI includes 0)" if hi > 0 else "TEXT HURTS")
    print(f"    verdict: {verdict}")

    print("\n[5] Where the uplift lives — CRPS by horizon (text-blind vs text)")
    # recompute per-horizon means from the paired arrays (they are in
    # cutoff-major, entity, horizon order; reconstruct horizon index)
    H = 5
    a2 = a.reshape(-1, H)
    b2 = b.reshape(-1, H)
    print(f"    {'horizon':<10}{'blind':>10}{'text':>10}{'reduction':>12}")
    for hidx in range(H):
        av = a2[:, hidx].mean()
        bv = b2[:, hidx].mean()
        print(f"    h={hidx+1:<8}{av:>10.4f}{bv:>10.4f}{av-bv:>12.4f}")

    print("\n" + "=" * 72)
    print("Done. See REPORT.md for interpretation and the honest verdict.")
    print("=" * 72)


if __name__ == "__main__":
    main()
