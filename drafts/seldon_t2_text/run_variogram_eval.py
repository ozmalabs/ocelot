"""
run_variogram_eval — PHASE 2 measurement.

Per the PHASE12_PREREG:
  * builds both arms (independent, joint) from the SAME as-of panel,
  * hand-makes a realized joint vector with GENUINE co-movement (common-factor
    model, betas on a shared shock, model-independent seed),
  * scores BOTH arms with the REAL reference scorer via --realized,
  * reports the three raw components (marginal, joint variogram, tail) + composite.

The realized generation uses a seed DISTINCT from the model seed and does NOT
reuse the model's estimated covariance — the joint arm is not handed its answer.
Repeats over several realized seeds and reports the distribution.

Usage:
  PYTHONPATH=<track2> python run_variogram_eval.py --units <dir> --track2-repo <dir> \
     --select F3 --realized-seeds 0,1,2,3,4 --n-draws 1000
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from t2_adapter import (  # noqa: E402
    CardSpec, read_card, load_panels, asset_series,
    IndependentDrawEngine, JointDrawEngine, write_outputs,
)

# The REAL scorer's composite is exactly crps.crps_composite(samples, y, ...)
# on the flattened (n_draws, cell_count) matrix (scoring.py _score, line ~485,
# verified). We import the SAME crps module the scorer imports and call it
# in-process — identical math, no per-call subprocess startup. One arm is also
# cross-checked through the CLI to prove the in-process path matches.
from qfbench2_common.scoring import crps  # noqa: E402


def flatten_samples(samples: np.ndarray) -> np.ndarray:
    """(n_draws, n_assets, n_horizons) -> (n_draws, cell_count), asset-major
    horizon-minor in declared order (grid.py GridSpec.cells order)."""
    n_draws, n_a, n_h = samples.shape
    return samples.reshape(n_draws, n_a * n_h)


def flatten_realized_vec(realized: pd.DataFrame, assets, horizons) -> np.ndarray:
    """Flatten realized (asset,horizon,value) to the same asset-major order."""
    idx = {(a, int(h)): None for a in assets for h in horizons}
    lut = {(r.asset, int(r.horizon)): float(r.value)
           for r in realized.itertuples()}
    vec = []
    for a in assets:
        for h in horizons:
            vec.append(lut[(a, int(h))])
    return np.asarray(vec, dtype=float)


def _econ_signs(assets: list[str]) -> np.ndarray:
    """Economically-motivated co-movement SIGNS for the common factor, set from
    asset-class priors that are INDEPENDENT of the panel-estimated correlation
    (so the joint arm is not handed its own answer):
      * yields/rates (UST_*) all load +1 (a curve level shock moves all tenors
        the same way);
      * USD-value crosses: majors that strengthen together get +1, classic
        risk/safe-haven opposites get -1. We use a fixed, small prior table;
        anything unknown defaults to +1.
    This lets the FX units carry a realistic SIGNED co-movement so the variogram
    test is not rigged toward positive-only moves. It is a coarse prior, stated
    as such — not a fit to the data."""
    # safe-haven / funding currencies tend to move OPPOSITE risk currencies.
    safe = {"JPY", "CHF", "USD"}
    risk = {"AUD", "NZD", "CAD", "NOK", "SEK", "BRL", "INR", "ZAR", "MXN",
            "TRY", "ZAR", "GBP", "EUR", "DKK", "CNH", "KRW"}
    signs = []
    for a in assets:
        if a.startswith("UST_") or a.startswith("DGS"):
            signs.append(1.0)
        elif a in safe:
            signs.append(-1.0)
        elif a in risk:
            signs.append(1.0)
        else:
            signs.append(1.0)
    return np.asarray(signs, dtype=float)


def make_realized(card: CardSpec, panel: pd.DataFrame, seed: int,
                  k: float = 1.0, mode: str = "positive") -> pd.DataFrame:
    """Hand-made realized with a common-factor co-movement structure.

    y[a,h] = last_obs[a] + sign[a]*beta[a]*S_h + idio[a,h]
    S_h ~ N(0,(k*h_scale)^2), beta tapering, idio small.
    mode='positive': all signs +1 (realistic for a yield curve).
    mode='signed':   signs from _econ_signs (asset-class prior; realistic for FX
                     where safe-haven and risk crosses move oppositely).
    Model-independent: signs are an economic prior, NOT the panel correlation.
    Returns columns (asset, horizon, value)."""
    rng = np.random.default_rng(1_000_000 + seed)  # distinct from model seeds
    assets = card.asset_ids
    horizons = card.horizons
    n_a = len(assets)
    last = {}
    for a in assets:
        x = asset_series(panel, a)
        last[a] = float(x[-1]) if len(x) else 0.0
    betas = np.linspace(1.0, 0.6, n_a)
    signs = _econ_signs(assets) if mode == "signed" else np.ones(n_a)
    base_x = asset_series(panel, assets[0])
    daily = float(np.median(np.abs(np.diff(base_x)))) if len(base_x) > 2 else 0.05
    daily = daily or 0.05

    rows = []
    for hi, h in enumerate(horizons):
        h_scale = daily * np.sqrt(h)
        S_h = rng.normal(0.0, k * h_scale)
        for ai, a in enumerate(assets):
            idio = rng.normal(0.0, 0.15 * k * h_scale)
            y = last[a] + signs[ai] * betas[ai] * S_h + idio
            rows.append({"asset": a, "horizon": int(h), "value": float(y)})
    return pd.DataFrame(rows)


def make_realized_text_aware(
        card: CardSpec, panel: pd.DataFrame, seed: int,
        gold_dir: dict[str, float], p_signal: float, e: float,
        k: float = 1.0, mode: str = "positive") -> pd.DataFrame:
    """DIRECTION-AWARE sibling of make_realized (H2_RESOLUTION_PREREG §fix.1).

    Byte-for-byte reuses make_realized's SYMMETRIC common-factor proxy as the
    base draw (same seed, same co-movement), then, for a `p_signal` fraction of
    the (asset, horizon) cells that carry a real ToM gold direction, NUDGES the
    realized outcome in that gold direction by a fixed effect size `e` (in
    cell-sigma) ON TOP OF the co-movement. This makes the realized correlate
    with the text ONLY to the degree the corpus informs it — the honest upper
    structure, p_signal/e swept, never hand-fit.

    Parameters
    ----------
    gold_dir : {asset -> +1|-1|0}
        The GOLD (correct) band direction per asset — the direction the corpus
        genuinely implies for that cell. +1 = realized nudged UP, -1 = DOWN,
        0/absent = no signal on that asset (cell keeps the symmetric proxy).
    p_signal : float in [0,1]
        Fraction of signalled cells (assets with gold_dir != 0) whose realized
        is actually nudged. The remaining (1 - p_signal) fraction of signalled
        cells KEEP the unchanged symmetric proxy — the typer's real error/abstain
        rate. p_signal = 0 => text carries nothing (H2c empty-signal case).
    e : float
        Effect size of the gold-direction nudge, in units of that cell's OWN
        proxy sigma (the per-cell scale make_realized draws at). e in cell-sigma.

    Deterministic given `seed` (the signalled-cell selection uses a seed-derived
    RNG distinct from the proxy's draw RNG, so which cells carry signal is fixed
    per seed and does not perturb the base draw). Still a PROXY, not the sealed
    outcome: RAW_UNRANKABLE, direction-SENSITIVE but not the organizer board.
    """
    # 1. the UNCHANGED symmetric proxy is the base (identical draw to make_realized).
    base = make_realized(card, panel, seed, k=k, mode=mode)
    if p_signal <= 0.0 or e == 0.0 or not gold_dir:
        return base

    assets = card.asset_ids
    horizons = card.horizons

    # per-cell proxy sigma: the scale make_realized draws each cell at is
    # dominated by the common factor sign[a]*beta[a]*S_h plus idio. We recover
    # the SAME daily scale make_realized uses so the nudge `e` is genuinely in
    # cell-sigma (matched to the proxy's own dispersion), not an arbitrary unit.
    base_x = asset_series(panel, assets[0])
    daily = float(np.median(np.abs(np.diff(base_x)))) if len(base_x) > 2 else 0.05
    daily = daily or 0.05
    n_a = len(assets)
    betas = np.linspace(1.0, 0.6, n_a)

    # 2. decide WHICH signalled cells actually carry the nudge (a p_signal
    #    fraction), deterministically per seed, with an RNG DISTINCT from the
    #    proxy draw RNG so the base draw is untouched.
    sel_rng = np.random.default_rng(2_000_000 + seed)

    lut = {(r.asset, int(r.horizon)): float(r.value) for r in base.itertuples()}
    rows = []
    for hi, h in enumerate(horizons):
        h_scale = daily * np.sqrt(h)
        for ai, a in enumerate(assets):
            v = lut[(a, int(h))]
            gd = float(gold_dir.get(a, 0.0))
            # cell sigma matched to the proxy's per-cell dispersion at this
            # (asset, horizon): the common-factor component scale.
            cell_sigma = abs(betas[ai]) * h_scale
            if gd != 0.0 and sel_rng.random() < p_signal:
                v = v + gd * e * cell_sigma
            # else: no signal on this asset, OR an abstain draw -> UNCHANGED proxy.
            rows.append({"asset": a, "horizon": int(h), "value": float(v)})
    return pd.DataFrame(rows)


def score_with_realized(track2_repo: str, card_path: Path, forecast_path: Path,
                        realized_path: Path) -> dict:
    full_env = dict(os.environ)
    full_env["PYTHONPATH"] = track2_repo
    cmd = [sys.executable, "-m", "qfbench2_track_forecasting.scoring", "score",
           "--card", str(card_path), "--forecast", str(forecast_path),
           "--realized", str(realized_path)]
    p = subprocess.run(cmd, capture_output=True, text=True, env=full_env)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"admissible": False, "error": (p.stdout + p.stderr)[:400]}


def is_multi_asset(card: CardSpec) -> bool:
    return len(set(card.asset_ids)) >= 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--track2-repo", required=True)
    ap.add_argument("--select", default="F3")
    ap.add_argument("--realized-seeds", default="0,1,2,3,4")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--model-seed", type=int, default=0)
    ap.add_argument("--out-root", default="/tmp/t2_vario")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--realized-mode", default="positive",
                    choices=["positive", "signed"])
    args = ap.parse_args()

    units_dir = Path(args.units)
    out_root = Path(args.out_root)
    subs = [s.strip() for s in args.select.split(",") if s.strip()]
    seeds = [int(s) for s in args.realized_seeds.split(",")]

    unit_dirs = sorted([d for d in units_dir.iterdir()
                        if d.is_dir() and (d / "card.toml").exists()
                        and any(s in d.name for s in subs)])

    records = []
    for ud in unit_dirs:
        try:
            card = read_card(ud / "card.toml")
        except Exception as e:
            print(f"SKIP {ud.name}: card {e}")
            continue
        if not is_multi_asset(card):
            print(f"SKIP {ud.name}: single-asset ({card.asset_ids}) — variogram=0")
            continue
        try:
            panel = load_panels(ud, card.asof)
        except Exception as e:
            print(f"SKIP {ud.name}: panel {e}")
            continue
        try:
            engines = {
                "independent": IndependentDrawEngine().build(card, panel),
                "joint": JointDrawEngine().build(card, panel),
            }
        except Exception as e:
            print(f"SKIP {ud.name}: build {e}")
            continue

        # produce both arms once (draws fixed by model seed)
        arm_samples = {}
        for name, eng in engines.items():
            samples = eng.sample_matrix(args.n_draws, seed=args.model_seed)
            arm_samples[name] = samples
            od = out_root / ud.name / name
            write_outputs(od, card, samples, eng.name)

        flat = {n: flatten_samples(s) for n, s in arm_samples.items()}
        weights = (card.weights["marginal"], card.weights["joint"],
                   card.weights["tail"])
        tail_levels = tuple(card.tail_levels)

        for seed in seeds:
            realized = make_realized(card, panel, seed, mode=args.realized_mode)
            y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
            for name in ("independent", "joint"):
                out = crps.crps_composite(
                    flat[name], y, weights=weights,
                    tail_levels=tail_levels, joint=card.joint_kind)
                records.append({
                    "unit": ud.name, "arm": name, "seed": seed,
                    "cells": card.cell_count, "n_draws": args.n_draws,
                    "marginal": out["marginal"],
                    "joint": out["joint"],
                    "tail": out["tail"],
                    "composite": out["composite"],
                })

    df = pd.DataFrame(records)
    if df.empty:
        print("NO RECORDS")
        return 1

    # ---- CLI cross-check: prove in-process crps_composite == reference CLI ----
    # Re-score the FIRST unit's joint arm, seed 0, through the real scorer CLI
    # with a written realized.parquet, and compare the joint variogram number.
    try:
        first = df.iloc[0]["unit"]
        ud = units_dir / first
        card = read_card(ud / "card.toml")
        panel = load_panels(ud, card.asof)
        eng = JointDrawEngine().build(card, panel)
        samples = eng.sample_matrix(args.n_draws, seed=args.model_seed)
        od = out_root / first / "joint"
        write_outputs(od, card, samples, "joint")
        realized = make_realized(card, panel, 0, mode=args.realized_mode)
        rp = out_root / first / "realized_seed0.parquet"
        realized.to_parquet(rp, index=False)
        cli = score_with_realized(args.track2_repo, ud / "card.toml",
                                  od / "forecast.parquet", rp)
        inproc = df[(df.unit == first) & (df.arm == "joint") & (df.seed == 0)].iloc[0]
        print("\n=== CLI cross-check (in-process vs reference scorer CLI) ===")
        print(f"  unit={first} arm=joint seed=0")
        print(f"  in-process joint variogram = {inproc['joint']:.6f}")
        print(f"  reference CLI joint variogram = {cli.get('joint_variogram')}")
        print(f"  in-process composite = {inproc['composite']:.6f}  "
              f"CLI composite = {cli.get('composite_score')}")
    except Exception as e:
        print(f"CLI cross-check skipped: {e}")

    # per (unit,seed) paired comparison
    piv = df.pivot_table(index=["unit", "seed"], columns="arm",
                         values=["marginal", "joint", "tail", "composite"])
    print("\n=== PAIRED per (unit, seed): joint − independent ===")
    for comp in ("marginal", "joint", "tail", "composite"):
        diff = piv[(comp, "joint")] - piv[(comp, "independent")]
        win = (diff < 0).mean()
        print(f"  {comp:10s}: mean(joint−indep)={diff.mean():+.5f}  "
              f"median={diff.median():+.5f}  joint-better fraction={win:.2%}")

    print("\n=== AGGREGATE means by arm ===")
    agg = df.groupby("arm")[["marginal", "joint", "tail", "composite"]].mean()
    print(agg.to_string())

    print("\n=== per-unit mean joint variogram (over seeds) ===")
    pu = df.pivot_table(index="unit", columns="arm", values="joint", aggfunc="mean")
    pu["delta"] = pu["joint"] - pu["independent"]
    pu["joint_better"] = pu["delta"] < 0
    print(pu.to_string())

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(records, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
