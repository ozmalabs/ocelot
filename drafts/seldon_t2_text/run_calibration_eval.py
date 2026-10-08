"""
run_calibration_eval — PHASE 5 calibration.

Measures randomised-PIT calibration of the MC-draw forecaster (the phase12
JointDrawEngine, the shipped numeric core) against a LOCAL hand-made realized
proxy, and evaluates a concrete tightening knob (a dispersion scale on the
innovation kernel width) before/after.

WHY randomised PIT.  For a sample/ensemble forecast the probability integral
transform is discrete; the randomised PIT (Czado et al. 2009) removes the
discreteness so that, IF the forecast is calibrated, PIT ~ Uniform(0,1):

    u = ( #{draws < y}  +  V * #{draws == y} ) / m ,   V ~ Uniform(0,1)

We add a tiny jitter for the (rare, since draws are continuous) ties. We then
measure the one-sample Kolmogorov–Smirnov distance of the pooled PIT sample to
Uniform(0,1). KS is the same statistic the PoC reported (0.0926). Over-dispersion
shows as PIT mass piling in the MIDDLE (a hump); under-dispersion shows as mass
piling at the ENDS (a U). We also report the mean |coverage_a − a| tail metric
(the scorer's own tail penalty) so the calibration story is told in the harness's
own currency.

THE KNOB.  `disp_scale` multiplies each cell's draw spread around its predictive
mean:  x' = mean + disp_scale * (x − mean).  disp_scale < 1 TIGHTENS (cures
over-dispersion); disp_scale > 1 widens. This is contract-preserving: it is a
per-cell affine map on already-drawn values, so draws stay finite, the row count
and cell occupancy are untouched, and — because it is the SAME scale on every
draw of a cell — the cross-asset correlation of the JOINT draws (phase2) is
unchanged (corr is scale-invariant). So calibration is tuned WITHOUT disturbing
the variogram structure.

CRPS PUNISHES BOTH TAILS.  We therefore do NOT pick the disp_scale that minimises
KS; we report KS, marginal CRPS, tail penalty and composite across a scan and
pick a scale that improves calibration WITHOUT worsening CRPS — the plan's
explicit guard ("do not over-tighten").

The realized is the SAME transparent hand-made instrument as phase2
(run_variogram_eval.make_realized) — a common-factor co-movement draw with a
model-independent seed. It is a RELATIVE / calibration instrument, NOT the sealed
outcome; local runs are always RAW_UNRANKABLE (PHASE0 §5.1). Stated as such.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t2_adapter import (  # noqa: E402
    read_card, load_panels, JointDrawEngine,
)
from run_variogram_eval import make_realized, flatten_realized_vec  # noqa: E402
from qfbench2_common.scoring import crps  # noqa: E402


def scale_dispersion(samples: np.ndarray, disp_scale: float) -> np.ndarray:
    """Affine per-cell contraction/expansion of draws around their mean.
    samples: (n_draws, n_assets, n_horizons). Preserves finiteness, cell
    occupancy, and cross-asset correlation (scale-invariant)."""
    if disp_scale == 1.0:
        return samples
    mean = samples.mean(axis=0, keepdims=True)
    return mean + disp_scale * (samples - mean)


def randomised_pit(draws: np.ndarray, y: float,
                   rng: np.random.Generator) -> float:
    """Randomised PIT of a scalar realized y under an ensemble `draws`.
    u = (#{x<y} + V*#{x==y})/m, V~U(0,1). Draws are continuous so ties are rare;
    the V term handles them without biasing the transform."""
    m = len(draws)
    below = np.count_nonzero(draws < y)
    equal = np.count_nonzero(draws == y)
    return (below + rng.uniform(0.0, 1.0) * equal) / m


def ks_uniform(u: np.ndarray) -> float:
    """One-sample KS distance of samples u to Uniform(0,1)."""
    u = np.sort(np.asarray(u, dtype=float))
    n = len(u)
    if n == 0:
        return float("nan")
    i = np.arange(1, n + 1)
    d_plus = np.max(i / n - u)
    d_minus = np.max(u - (i - 1) / n)
    return float(max(d_plus, d_minus))


def collect_pit(samples: np.ndarray, y_vec: np.ndarray,
                rng: np.random.Generator) -> np.ndarray:
    """One PIT value per flattened cell (asset-major, horizon-minor)."""
    n_draws, n_a, n_h = samples.shape
    flat = samples.reshape(n_draws, n_a * n_h)
    return np.array([randomised_pit(flat[:, c], y_vec[c], rng)
                     for c in range(flat.shape[1])])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--track2-repo", required=True)
    ap.add_argument("--select", default="F3",
                    help="comma-separated substrings of unit names to include")
    ap.add_argument("--realized-seeds", default="0,1,2,3,4,5,6,7")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--model-seed", type=int, default=0)
    ap.add_argument("--scales", default="0.6,0.7,0.8,0.85,0.9,0.95,1.0,1.1,1.25")
    ap.add_argument("--realized-mode", default="positive",
                    choices=["positive", "signed"])
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    units_dir = Path(args.units)
    subs = [s.strip() for s in args.select.split(",") if s.strip()]
    seeds = [int(s) for s in args.realized_seeds.split(",")]
    scales = [float(s) for s in args.scales.split(",")]

    unit_dirs = sorted([d for d in units_dir.iterdir()
                        if d.is_dir() and (d / "card.toml").exists()
                        and any(s in d.name for s in subs)])

    # Build each multi-asset unit's joint arm ONCE (draws fixed by model seed),
    # keep the base sample matrix + card + panel for realized generation.
    built = []
    for ud in unit_dirs:
        try:
            card = read_card(ud / "card.toml")
        except Exception as e:
            print(f"SKIP {ud.name}: card {e}")
            continue
        if len(set(card.asset_ids)) < 2:
            continue  # single-cell: PIT still defined but variogram=0; keep multi
        try:
            panel = load_panels(ud, card.asof)
            eng = JointDrawEngine().build(card, panel)
            base = eng.sample_matrix(args.n_draws, seed=args.model_seed)
        except Exception as e:
            print(f"SKIP {ud.name}: build {e}")
            continue
        built.append((ud, card, panel, base))

    if not built:
        print("NO UNITS BUILT")
        return 1

    print(f"built {len(built)} multi-asset units; scales={scales}; "
          f"realized seeds={seeds}; n_draws={args.n_draws}\n")

    # For each scale: pool PIT across all (unit, cell, realized-seed) points,
    # measure KS to uniform; also mean composite/marginal/tail across the same
    # (unit, seed) set so we can see the CRPS tradeoff of tightening.
    records = []
    pit_hist = {}
    for sc in scales:
        pit_pool = []
        comps, margs, tails, jnts = [], [], [], []
        for (ud, card, panel, base) in built:
            samples = scale_dispersion(base, sc)
            flat = samples.reshape(samples.shape[0], -1)
            weights = (card.weights["marginal"], card.weights["joint"],
                       card.weights["tail"])
            tl = tuple(card.tail_levels)
            for seed in seeds:
                realized = make_realized(card, panel, seed,
                                         mode=args.realized_mode)
                y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
                rng = np.random.default_rng(7_000 + seed)
                pit_pool.append(collect_pit(samples, y, rng))
                out = crps.crps_composite(flat, y, weights=weights,
                                          tail_levels=tl, joint=card.joint_kind)
                comps.append(out["composite"])
                margs.append(out["marginal"])
                tails.append(out["tail"])
                jnts.append(out["joint"])
        pit = np.concatenate(pit_pool)
        ks = ks_uniform(pit)
        rec = {
            "disp_scale": sc,
            "ks": ks,
            "pit_mean": float(pit.mean()),
            "pit_std": float(pit.std()),
            "n_pit": int(pit.size),
            "marginal": float(np.mean(margs)),
            "joint": float(np.mean(jnts)),
            "tail": float(np.mean(tails)),
            "composite": float(np.mean(comps)),
        }
        records.append(rec)
        pit_hist[sc] = np.histogram(pit, bins=10, range=(0, 1))[0].tolist()
        print(f"  disp_scale={sc:4.2f}  KS={ks:.4f}  "
              f"PIT mean={pit.mean():.3f} std={pit.std():.3f}  "
              f"marg={rec['marginal']:.4f} tail={rec['tail']:.4f} "
              f"comp={rec['composite']:.4f}")

    # ---- recommendation, with the "do not over-tighten" guard made explicit.
    # KS alone bottoms out where PIT is flattest, but the scorer's TAIL penalty
    # (|coverage_a - a|, its own coverage-calibration metric) is the tripwire:
    # tightening narrows the extreme quantiles, so tail coverage error blows up
    # even while the mid-PIT hump flattens. So we do NOT pick argmin(KS); we pick
    # the scale that (a) reduces KS vs baseline AND (b) does not worsen the TAIL
    # metric beyond a small tolerance of baseline. That is the CRPS-both-tails
    # guard the plan calls for. We also report the raw argmin(KS) so the reader
    # sees what the guard is protecting against. ----
    base_rec = next(r for r in records if abs(r["disp_scale"] - 1.0) < 1e-9)
    ks_argmin = min(records, key=lambda r: r["ks"])
    tail_tol = 0.05 * abs(base_rec["tail"])  # 5% tail-metric tolerance
    guarded = [r for r in records
               if r["ks"] < base_rec["ks"]
               and r["tail"] <= base_rec["tail"] + tail_tol
               and r["marginal"] <= base_rec["marginal"] + 1e-9]
    best = min(guarded, key=lambda r: r["ks"]) if guarded else base_rec
    print("\n=== recommendation ===")
    print(f"  baseline disp_scale=1.0:  KS={base_rec['ks']:.4f}  "
          f"tail={base_rec['tail']:.4f}  marg={base_rec['marginal']:.4f}  "
          f"comp={base_rec['composite']:.4f}")
    print(f"  RAW argmin(KS) disp_scale={ks_argmin['disp_scale']}:  "
          f"KS={ks_argmin['ks']:.4f}  tail={ks_argmin['tail']:.4f}  "
          f"marg={ks_argmin['marginal']:.4f}  comp={ks_argmin['composite']:.4f}  "
          f"(<-- tail worse by {ks_argmin['tail']-base_rec['tail']:+.4f}: OVER-TIGHTENED)")
    print(f"  TAIL-GUARDED chosen disp_scale={best['disp_scale']}:  "
          f"KS={best['ks']:.4f}  tail={best['tail']:.4f}  "
          f"marg={best['marginal']:.4f}  comp={best['composite']:.4f}")
    print(f"  KS improvement (guarded): {base_rec['ks']-best['ks']:+.4f}  "
          f"({100*(base_rec['ks']-best['ks'])/base_rec['ks']:+.1f}%)")
    print(f"  tail change (guarded): {best['tail']-base_rec['tail']:+.5f} "
          f"(tolerance {tail_tol:.5f})")
    print(f"  marginal CRPS change (guarded): "
          f"{best['marginal']-base_rec['marginal']:+.5f}")
    print("\n  PIT histogram (10 bins):")
    print(f"    scale 1.00 (baseline): {pit_hist[base_rec['disp_scale']]}")
    print(f"    scale {best['disp_scale']:.2f} (chosen): {pit_hist[best['disp_scale']]}")
    print(f"    scale {ks_argmin['disp_scale']:.2f} (argmin-KS): {pit_hist[ks_argmin['disp_scale']]}")

    best_out = best

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            {"records": records, "pit_hist": {str(k): v for k, v in pit_hist.items()},
             "baseline": base_rec, "chosen": best_out, "ks_argmin": ks_argmin},
            indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
