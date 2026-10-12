"""measure_h2b_power — power the H2b (grounding_weighted vs flat_0.1sigma)
question above the 8-seed noise floor (H2B_POWER_PREREG.md).

REUSES measure_h2_directed's machinery VERBATIM (build_units, decode_units,
cell_shift_grid, apply_band_shift_percell) + make_realized_text_aware + the REAL
scorer crps.crps_composite. The ONLY additions vs measure_h2_directed are:
  (1) many more realized seeds (default 0..63);
  (2) PAIRED per-seed deltas d_i = composite_gw(seed_i) - composite_flat(seed_i)
      (both arms scored on the SAME realized draw for a seed), so a CI on the
      gw-flat difference is computable. Both arms use the SAME base draws and
      the SAME realized per seed, so d_i is a proper paired sample and its
      across-seed spread is the noise floor.

No new metric; no hand-fitting. RAW_UNRANKABLE: direction-aware PROXY, not the
sealed board.

Reproduce:
  PYTHONPATH=runners/dsl/python:.bigtmp/track2 .bigtmp/t2venv/bin/python \
    drafts/seldon_t2_text/induced_belief/measure_h2b_power.py \
    --units .bigtmp/track2/units --select t2-F3 \
    --realized-seeds 0-63 --n-draws 1000 \
    --p-signals 0.3,0.5,0.7 --effects 0.5,1.0 \
    --json-out drafts/seldon_t2_text/induced_belief/h2b_power_results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_T2 = _HERE.parent
_ROOT = _T2.parent.parent
for p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python"), str(_T2)):
    if p not in sys.path:
        sys.path.insert(0, p)

from run_variogram_eval import (make_realized_text_aware,        # noqa: E402
                                flatten_realized_vec)
from run_calibration_eval import collect_pit, ks_uniform          # noqa: E402
from qfbench2_common.scoring import crps                          # noqa: E402
from induced_belief.measure_h2_directed import (                  # noqa: E402  (REUSE)
    build_units, decode_units, cell_shift_grid, apply_band_shift_percell)


def _parse_seeds(spec: str):
    """Accept '0-63' range shorthand or an explicit comma list."""
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(s) for s in spec.split(",") if s.strip() != ""]


def paired_cell(built, decoded, seeds, p_signal, e, flat_shift, realized_mode):
    """Compute, per realized seed, the MEAN-over-units composite (and tail) for
    flat and gw arms on the SAME realized draw, then the paired delta d =
    gw - flat per seed. Returns arrays of per-seed composites + the paired
    deltas so a CI is computable.

    This is measure_h2_directed.measure_cell's exact inner computation, but kept
    at SEED granularity (not pooled) so the across-seed spread is preserved.
    """
    flat_comp_by_seed, gw_comp_by_seed = [], []
    flat_tail_by_seed, gw_tail_by_seed = [], []
    # precompute per-arm per-unit shifted samples + weights (arm-invariant part).
    prepared = []
    for (ud, card, panel, base) in built:
        dec = decoded[ud.name]
        weights = (card.weights["marginal"], card.weights["joint"],
                   card.weights["tail"])
        tl = tuple(card.tail_levels)
        gold = {aid: dec["sign"] for aid in card.asset_ids}
        arms = {}
        for arm_name in ("flat_0.1sigma", "grounding_weighted"):
            grid = cell_shift_grid(card, dec, arm_name, flat_shift)
            s = apply_band_shift_percell(base, grid)
            arms[arm_name] = s.reshape(s.shape[0], -1)
        prepared.append((card, panel, weights, tl, gold, arms))

    for seed in seeds:
        f_comps, g_comps, f_tails, g_tails = [], [], [], []
        for (card, panel, weights, tl, gold, arms) in prepared:
            # SAME realized draw for both arms at this seed (paired).
            realized = make_realized_text_aware(
                card, panel, seed, gold_dir=gold,
                p_signal=p_signal, e=e, mode=realized_mode)
            y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
            sf = crps.crps_composite(arms["flat_0.1sigma"], y, weights=weights,
                                     tail_levels=tl, joint=card.joint_kind)
            sg = crps.crps_composite(arms["grounding_weighted"], y,
                                     weights=weights, tail_levels=tl,
                                     joint=card.joint_kind)
            f_comps.append(sf["composite"]); g_comps.append(sg["composite"])
            f_tails.append(sf["tail"]); g_tails.append(sg["tail"])
        flat_comp_by_seed.append(float(np.mean(f_comps)))
        gw_comp_by_seed.append(float(np.mean(g_comps)))
        flat_tail_by_seed.append(float(np.mean(f_tails)))
        gw_tail_by_seed.append(float(np.mean(g_tails)))

    fc = np.array(flat_comp_by_seed); gc = np.array(gw_comp_by_seed)
    ft = np.array(flat_tail_by_seed); gt = np.array(gw_tail_by_seed)
    d_comp = gc - fc            # paired per-seed gw-flat composite delta
    d_tail = gt - ft
    n = len(seeds)

    def ci(d):
        m = float(np.mean(d))
        se = float(np.std(d, ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        return {"mean": m, "se": se, "lo95": m - 1.96 * se,
                "hi95": m + 1.96 * se}

    cc = ci(d_comp); ct = ci(d_tail)
    return {
        "n_seeds": n,
        "flat_composite_mean": float(np.mean(fc)),
        "gw_composite_mean": float(np.mean(gc)),
        "flat_tail_mean": float(np.mean(ft)),
        "gw_tail_mean": float(np.mean(gt)),
        "d_composite": cc, "d_tail": ct,
        "composite_ci_separated_below0": bool(cc["hi95"] < 0),
        "composite_ci_separated_above0": bool(cc["lo95"] > 0),
        "composite_ci_straddles0": bool(cc["lo95"] <= 0 <= cc["hi95"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--select", default="t2-F3")
    ap.add_argument("--realized-seeds", default="0-63")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--model-seed", type=int, default=0)
    ap.add_argument("--flat-shift", type=float, default=0.1)
    ap.add_argument("--p-signals", default="0.3,0.5,0.7")
    ap.add_argument("--effects", default="0.5,1.0")
    ap.add_argument("--realized-mode", default="signed",
                    choices=["positive", "signed"])
    ap.add_argument("--market", default=None)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    units_dir = Path(args.units)
    subs = [s.strip() for s in args.select.split(",") if s.strip()]
    seeds = _parse_seeds(args.realized_seeds)
    p_signals = [float(x) for x in args.p_signals.split(",")]
    effects = [float(x) for x in args.effects.split(",")]

    built = build_units(units_dir, subs, args.n_draws, args.model_seed)
    if not built:
        print("NO UNITS BUILT")
        return 1
    print(f"built {len(built)} F3 units; POWER seeds={len(seeds)} "
          f"({seeds[0]}..{seeds[-1]}); n_draws={args.n_draws}")

    decoded = decode_units(built, market=args.market)
    n_signal = sum(1 for (ud, *_ ) in built if decoded[ud.name]["sign"] != 0.0)
    print(f"  ({n_signal}/{len(built)} units carry a non-zero decoded direction)")

    grid = {}
    print("\n=== H2b POWER: paired gw-flat composite delta 95% CI per cell ===")
    print(f"  {'p_sig':>5} {'e':>4} | {'gw comp':>10} {'flat comp':>10} | "
          f"{'d_comp mean':>12} {'95% CI':>22} | {'verdict':>10}")
    for p in p_signals:
        for e in effects:
            r = paired_cell(built, decoded, seeds, p, e,
                            args.flat_shift, args.realized_mode)
            cc = r["d_composite"]
            if r["composite_ci_separated_below0"]:
                verdict = "gw<flat"
            elif r["composite_ci_separated_above0"]:
                verdict = "flat<gw"
            else:
                verdict = "TIE"
            grid[f"p{p}_e{e}"] = {"p_signal": p, "e": e, **r, "verdict": verdict}
            print(f"  {p:5.1f} {e:4.1f} | {r['gw_composite_mean']:10.5f} "
                  f"{r['flat_composite_mean']:10.5f} | {cc['mean']:+12.6f} "
                  f"[{cc['lo95']:+.6f},{cc['hi95']:+.6f}] | {verdict:>10}")

    # aggregate H2b-POWER verdict across signalled cells (majority rule).
    verdicts = [v["verdict"] for v in grid.values()]
    n_cells = len(verdicts)
    n_tie = verdicts.count("TIE")
    n_gw = verdicts.count("gw<flat")
    n_flat = verdicts.count("flat<gw")
    if n_tie > n_cells / 2:
        overall = "genuine-tie"
    elif n_gw > n_cells / 2:
        overall = "gw-wins"
    elif n_flat > n_cells / 2:
        overall = "flat-wins"
    else:
        overall = "no-majority (mixed even under power)"

    # e-crossover check: does the tail-vs-composite crossover survive power?
    e_split = {}
    for e in effects:
        cells_e = [v for v in grid.values() if v["e"] == e]
        e_split[e] = {
            "mean_d_composite": float(np.mean([v["d_composite"]["mean"] for v in cells_e])),
            "mean_d_tail": float(np.mean([v["d_tail"]["mean"] for v in cells_e])),
            "composite_verdicts": [v["verdict"] for v in cells_e],
        }

    summary = {
        "n_signalled_cells": n_cells, "n_tie": n_tie, "n_gw_wins": n_gw,
        "n_flat_wins": n_flat, "H2b_POWER_verdict": overall,
        "n_seeds": len(seeds), "e_split": e_split,
    }
    print("\n=== H2b-POWER VERDICT (RAW_UNRANKABLE; direction-aware proxy) ===")
    print(f"  cells: TIE={n_tie} gw<flat={n_gw} flat<gw={n_flat} of {n_cells}")
    print(f"  overall: {overall}")
    for e in effects:
        print(f"  e={e}: mean d_composite={e_split[e]['mean_d_composite']:+.6f} "
              f"mean d_tail={e_split[e]['mean_d_tail']:+.6f} "
              f"verdicts={e_split[e]['composite_verdicts']}")

    out = {"summary": summary, "grid": grid, "seeds": seeds,
           "n_draws": args.n_draws, "flat_shift": args.flat_shift}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2, default=str))
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
