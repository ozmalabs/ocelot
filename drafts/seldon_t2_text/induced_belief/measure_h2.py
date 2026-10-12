"""measure_h2 — H2: does the GROUNDING-WEIGHTED band shift stay calibrated vs
the Phase-5 flat 0.1 sigma shift?

Preregistered decision rule (INDUCED_BELIEF_PREREG.md H2): shifting the band by
`base_shift x grounding_weight` (the transitive grounding read, NOT a flat
weight) keeps magnitude calibrated vs the flat 0.1 sigma shift. Measure
randomised-PIT KS and the scorer's tail penalty on the F3-shaped units,
grounding-weighted arm vs flat arm, HAND-MADE realized proxy (sealed outcomes
unavailable -> RAW_UNRANKABLE, stated). NEUTRAL-OR-BETTER iff KS not worse AND
tail within the Phase-5 5% tolerance.

REUSE: the exact Phase-5 randomised-PIT / KS / tail machinery
(run_calibration_eval) and the exact Phase-2 hand-made realized proxy
(run_variogram_eval.make_realized) and the REAL reference scorer
(qfbench2_common.scoring.crps). This file only adds the two SHIFT POLICIES and
compares them; it invents no new metric.

RAW_UNRANKABLE: the realized here is the hand-made common-factor proxy, NOT the
sealed organizer outcome. All numbers are RELATIVE calibration instruments.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_T2 = _HERE.parent
sys.path.insert(0, str(_T2))

from t2_adapter import read_card, load_panels, JointDrawEngine  # noqa: E402
from run_variogram_eval import make_realized, flatten_realized_vec  # noqa: E402
from run_calibration_eval import randomised_pit, ks_uniform, collect_pit  # noqa: E402
from qfbench2_common.scoring import crps  # noqa: E402


def apply_band_shift(samples: np.ndarray, signed_shift_sigma: float) -> np.ndarray:
    """Shift every cell's draws by `signed_shift_sigma` x that cell's own draw
    std (a directional band shift in units of the cell's predictive sigma).
    Contract-preserving: pure per-cell additive translation, so finiteness, cell
    occupancy, and cross-asset correlation (translation-invariant) are all
    unchanged — the same discipline run_calibration_eval.scale_dispersion uses,
    applied to the mean instead of the spread."""
    if signed_shift_sigma == 0.0:
        return samples
    sd = samples.std(axis=0, keepdims=True)
    return samples + signed_shift_sigma * sd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--select", default="F3")
    ap.add_argument("--realized-seeds", default="0,1,2,3,4,5,6,7")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--model-seed", type=int, default=0)
    ap.add_argument("--flat-shift", type=float, default=0.1,
                    help="the Phase-5 flat band shift, in sigma")
    ap.add_argument("--grounding-weight", type=float, default=0.333,
                    help="the arm's grounding weight for a grounded single-hit "
                         "read (1/(1+hops-1) with hops=3 -> 1/3); the "
                         "grounding-weighted shift is base_shift(=flat) x this")
    ap.add_argument("--realized-mode", default="signed",
                    choices=["positive", "signed"])
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    units_dir = Path(args.units)
    subs = [s.strip() for s in args.select.split(",") if s.strip()]
    seeds = [int(s) for s in args.realized_seeds.split(",")]

    unit_dirs = sorted([d for d in units_dir.iterdir()
                        if d.is_dir() and (d / "card.toml").exists()
                        and any(s in d.name for s in subs)])

    built = []
    for ud in unit_dirs:
        try:
            card = read_card(ud / "card.toml")
            panel = load_panels(ud, card.asof)
            eng = JointDrawEngine().build(card, panel)
            base = eng.sample_matrix(args.n_draws, seed=args.model_seed)
        except Exception as e:
            print(f"SKIP {ud.name}: {e}")
            continue
        built.append((ud, card, panel, base))

    if not built:
        print("NO UNITS BUILT")
        return 1
    print(f"built {len(built)} F3-shaped units; realized seeds={seeds}; "
          f"n_draws={args.n_draws}")
    print(f"flat shift={args.flat_shift} sigma; grounding-weighted shift="
          f"{args.flat_shift * args.grounding_weight:.4f} sigma "
          f"(= {args.flat_shift} x gw {args.grounding_weight})\n")

    # Two arms, both shifting in the SAME (arbitrary but fixed) direction so the
    # ONLY difference is the MAGNITUDE POLICY (flat vs grounding-weighted). The
    # direction sign is averaged over MANY random direction assignments (dir_seed)
    # so the verdict is not an artifact of one particular +/- pattern interacting
    # with the symmetric hand-made proxy — a single hash pattern can spuriously
    # favour whichever magnitude happens to shift toward the proxy mean.
    def unit_dir(name: str, dir_seed: int) -> float:
        r = np.random.default_rng(abs(hash((name, dir_seed))) % (2**32))
        return 1.0 if r.random() < 0.5 else -1.0

    DIR_SEEDS = list(range(8))

    def arm_shift(policy: str, ud, dir_seed: int) -> float:
        d = unit_dir(ud.name, dir_seed)
        if policy == "no_shift":
            return 0.0
        if policy == "flat_0.1sigma":
            return d * args.flat_shift
        if policy == "grounding_weighted":
            return d * args.flat_shift * args.grounding_weight
        return 0.0

    records = {}
    for arm_name in ("no_shift", "flat_0.1sigma", "grounding_weighted"):
        pit_pool, tails, comps, margs = [], [], [], []
        for dir_seed in DIR_SEEDS:
            for (ud, card, panel, base) in built:
                samples = apply_band_shift(base, arm_shift(arm_name, ud, dir_seed))
                flat_s = samples.reshape(samples.shape[0], -1)
                weights = (card.weights["marginal"], card.weights["joint"],
                           card.weights["tail"])
                tl = tuple(card.tail_levels)
                for seed in seeds:
                    realized = make_realized(card, panel, seed, mode=args.realized_mode)
                    y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
                    rng = np.random.default_rng(7_000 + seed)
                    pit_pool.append(collect_pit(samples, y, rng))
                    out = crps.crps_composite(flat_s, y, weights=weights,
                                              tail_levels=tl, joint=card.joint_kind)
                    comps.append(out["composite"]); margs.append(out["marginal"])
                    tails.append(out["tail"])
        pit = np.concatenate(pit_pool)
        ks = ks_uniform(pit)
        rec = {"ks": ks, "pit_mean": float(pit.mean()), "pit_std": float(pit.std()),
               "n_pit": int(pit.size), "tail": float(np.mean(tails)),
               "marginal": float(np.mean(margs)),
               "composite": float(np.mean(comps))}
        records[arm_name] = rec
        print(f"  {arm_name:20s}  KS={ks:.4f}  PIT mean={pit.mean():.3f} "
              f"std={pit.std():.3f}  tail={rec['tail']:.4f} "
              f"marg={rec['marginal']:.4f} comp={rec['composite']:.4f}")

    base = records["no_shift"]
    flat = records["flat_0.1sigma"]
    gw = records["grounding_weighted"]
    tail_tol = 0.05 * abs(flat["tail"])
    verdict = {
        "ks_not_worse_than_flat": gw["ks"] <= flat["ks"] + 1e-9,
        "tail_within_flat_5pct_tol": gw["tail"] <= flat["tail"] + tail_tol,
        "ks_vs_flat_delta": gw["ks"] - flat["ks"],
        "tail_vs_flat_delta": gw["tail"] - flat["tail"],
        "tail_tolerance": tail_tol,
    }
    verdict["NEUTRAL_OR_BETTER"] = bool(
        verdict["ks_not_worse_than_flat"] and verdict["tail_within_flat_5pct_tol"])
    print("\n=== H2 verdict (grounding-weighted vs flat 0.1 sigma) ===")
    print(f"  KS: flat={flat['ks']:.4f}  grounding_weighted={gw['ks']:.4f}  "
          f"delta={verdict['ks_vs_flat_delta']:+.4f}  "
          f"(not worse: {verdict['ks_not_worse_than_flat']})")
    print(f"  tail: flat={flat['tail']:.4f}  grounding_weighted={gw['tail']:.4f}  "
          f"delta={verdict['tail_vs_flat_delta']:+.5f}  tol={tail_tol:.5f}  "
          f"(within tol: {verdict['tail_within_flat_5pct_tol']})")
    print(f"  NEUTRAL-OR-BETTER: {verdict['NEUTRAL_OR_BETTER']}")
    print("  RAW_UNRANKABLE: realized is the hand-made common-factor proxy, "
          "NOT the sealed outcome.")

    out = {"arms": records, "verdict": verdict, "n_units": len(built),
           "flat_shift_sigma": args.flat_shift,
           "grounding_weight": args.grounding_weight,
           "RAW_UNRANKABLE": True}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
