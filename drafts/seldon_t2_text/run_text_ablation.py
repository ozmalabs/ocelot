"""
run_text_ablation — PHASE 5 text ablation (in-harness H1 uplift).

Runs the SHIPPED forecaster two ways on each unit and reports the composite-score
delta between them:

  * FULL   : the real pipeline — numeric JointDrawEngine draws + the PHASE 3
             rules text arm (type each corpus doc -> link via the alias index ->
             bounded 0.5σ confidence-mass shift, preserving the joint corr).
  * BLANK  : the SAME numeric draws with the corpus replaced by an EMPTY corpus
             (no text signal -> text-blind). This is the ablation.

Because both arms share the SAME base draws and SAME calibration (disp_scale),
the ONLY difference is whether the text signal is applied — so the composite
delta is the in-harness analogue of the PoC's H1 text uplift, measured in the
REAL scorer's own composite (crps.crps_composite, the exact function scoring.py
calls; cross-checked to the reference CLI in PHASE 2).

REALIZED IS HAND-MADE — stated plainly. The sealed outcomes are NOT available
(PHASE0 §7/§11), so we score against the transparent common-factor realized used
throughout (run_variogram_eval.make_realized). Two flavours are reported:

  * neutral realized (make_realized, common-factor, no text-truth): a text signal
    that shifts the band can only help if it happens to point the right way; on a
    text-agnostic realized the EXPECTED uplift is ~0. This is the honest null and
    the first thing to report.
  * text-consistent realized: the realized is nudged in the SAME direction the
    corpus signals (a controlled DGP where the text IS informative). This is the
    UPPER-BOUND uplift — what the arm buys IF the text is right, isolating the
    apply-mechanism from the typing accuracy (which PHASE 3 measured separately at
    0.71 usable directional recall on real prose).

We do NOT claim a leaderboard uplift: local runs are RAW_UNRANKABLE (PHASE0 §5.1)
and the realized is a probe, not the sealed truth. The number that matters for the
real board is (typing recall from PHASE 3) × (this apply-mechanism upside),
gated on the live house endpoint for the non-FOMC sources.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "phase3_derisk"))

from t2_adapter import (  # noqa: E402
    read_card, load_panels, JointDrawEngine, DEFAULT_DISP_SCALE,
)
from forecast_cli import derive_text_signal, apply_text_shift  # noqa: E402
from run_variogram_eval import make_realized, flatten_realized_vec  # noqa: E402
from qfbench2_common.scoring import crps  # noqa: E402


def flatten(samples: np.ndarray) -> np.ndarray:
    n_draws, n_a, n_h = samples.shape
    return samples.reshape(n_draws, n_a * n_h)


def text_consistent_realized(card, panel, base_realized: pd.DataFrame,
                             signal: dict[str, int], panel_daily_frac=0.5):
    """Nudge a base realized in the direction the corpus signals, by a fraction
    of the per-asset daily scale, so the text IS informative. Isolates the
    apply-mechanism upside from typing accuracy (upper bound)."""
    from t2_adapter import asset_series
    out = base_realized.copy()
    for a, sgn in signal.items():
        if sgn == 0:
            continue
        x = asset_series(panel, a)
        daily = float(np.median(np.abs(np.diff(x)))) if len(x) > 2 else 0.05
        daily = daily or 0.05
        mask = out["asset"] == a
        # nudge proportional to sqrt(h) like the realized's own h-scaling
        for i in out[mask].index:
            h = int(out.at[i, "horizon"])
            out.at[i, "value"] = out.at[i, "value"] + sgn * panel_daily_frac * daily * np.sqrt(h)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--track2-repo", required=True)
    ap.add_argument("--select", default="EXAMPLE,F1,F3",
                    help="unit-name substrings to include")
    ap.add_argument("--realized-seeds", default="0,1,2,3,4,5,6,7")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--model-seed", type=int, default=0)
    ap.add_argument("--disp-scale", type=float, default=DEFAULT_DISP_SCALE)
    ap.add_argument("--realized-mode", default="positive",
                    choices=["positive", "signed"])
    ap.add_argument("--shift-fracs", default="0.5",
                    help="comma-separated text-shift fractions to sweep "
                         "(apply_text_shift shift_frac); default 0.5")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    units_dir = Path(args.units)
    subs = [s.strip() for s in args.select.split(",") if s.strip()]
    seeds = [int(s) for s in args.realized_seeds.split(",")]
    shift_fracs = [float(s) for s in args.shift_fracs.split(",")]

    unit_dirs = sorted([d for d in units_dir.iterdir()
                        if d.is_dir() and (d / "card.toml").exists()
                        and any(s in d.name for s in subs)])

    records = []
    n_with_signal = 0
    for ud in unit_dirs:
        try:
            card = read_card(ud / "card.toml")
            panel = load_panels(ud, card.asof)
            eng = JointDrawEngine().build(card, panel)
            base = eng.sample_matrix(args.n_draws, seed=args.model_seed,
                                     disp_scale=args.disp_scale)
        except Exception as e:
            print(f"SKIP {ud.name}: {e}")
            continue

        # derive the text signal from the REAL corpus (rules arm) once
        text_dir = ud / "text"
        try:
            ts = derive_text_signal(text_dir, card, arm="rules")
            signal = ts["signal"]
        except Exception as e:
            signal = {}
            print(f"  {ud.name}: text signal error {e}")

        full = apply_text_shift(base, card, signal) if signal else base
        blank = base  # empty corpus == text-blind
        has_sig = bool(signal)
        n_with_signal += int(has_sig)

        weights = (card.weights["marginal"], card.weights["joint"],
                   card.weights["tail"])
        tl = tuple(card.tail_levels)
        f_blank = flatten(blank)
        # precompute FULL draws per shift fraction
        full_by_frac = {sf: flatten(apply_text_shift(base, card, signal,
                                                      shift_frac=sf) if signal
                                    else base)
                        for sf in shift_fracs}

        for seed in seeds:
            base_realized = make_realized(card, panel, seed,
                                          mode=args.realized_mode)
            for real_flavour in ("neutral", "text_consistent"):
                if real_flavour == "neutral":
                    realized = base_realized
                else:
                    if not signal:
                        continue  # no signal -> text-consistent == neutral
                    realized = text_consistent_realized(card, panel,
                                                        base_realized, signal)
                y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
                o_blank = crps.crps_composite(f_blank, y, weights=weights,
                                              tail_levels=tl, joint=card.joint_kind)
                for sf in shift_fracs:
                    o_full = crps.crps_composite(full_by_frac[sf], y,
                                                 weights=weights, tail_levels=tl,
                                                 joint=card.joint_kind)
                    records.append({
                        "unit": ud.name, "seed": seed, "realized": real_flavour,
                        "shift_frac": sf,
                        "has_signal": has_sig, "signal": dict(signal),
                        "cells": card.cell_count,
                        "full_composite": o_full["composite"],
                        "blank_composite": o_blank["composite"],
                        "delta_composite": o_full["composite"] - o_blank["composite"],
                        "full_marginal": o_full["marginal"],
                        "blank_marginal": o_blank["marginal"],
                        "full_tail": o_full["tail"],
                        "blank_tail": o_blank["tail"],
                    })

    df = pd.DataFrame(records)
    if df.empty:
        print("NO RECORDS")
        return 1

    print(f"\nunits evaluated: {df['unit'].nunique()}  "
          f"(with a usable text signal: {n_with_signal})\n")

    for sf in shift_fracs:
        dfsf = df[df["shift_frac"] == sf]
        print(f"################## shift_frac = {sf} ##################")
        for flavour in ("neutral", "text_consistent"):
            sub = dfsf[dfsf["realized"] == flavour]
            if sub.empty:
                continue
            d = sub["delta_composite"]
            print(f"=== realized={flavour}  (delta = full − blank; "
                  f"negative = text HELPS) ===")
            print(f"  n = {len(sub)} (unit×seed)   units with signal = "
                  f"{sub[sub.has_signal]['unit'].nunique()}")
            print(f"  mean delta_composite   = {d.mean():+.5f}")
            print(f"  median delta_composite = {d.median():+.5f}")
            print(f"  text-helps fraction    = {(d < 0).mean():.2%}")
            print(f"  text-hurts fraction    = {(d > 0).mean():.2%}")
        print()

    print("=== per-unit mean delta_composite (neutral realized, "
          f"shift_frac={shift_fracs[0]}) ===")
    pu = (df[(df.realized == "neutral") & (df.shift_frac == shift_fracs[0])]
          .groupby("unit")
          .agg(delta=("delta_composite", "mean"),
               has_signal=("has_signal", "first")))
    print(pu.to_string())

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(records, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
