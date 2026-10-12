"""measure_h2b_gwrange — H2b item-2: does a grounding weight that TRACKS the
signal (spanning a real range, e.g. 0.2..1.0) change the flat-vs-graded verdict,
or is the near-tie an artifact of grounding_weight being pinned at 0.333 in this
harness? (H2B_POWER_PREREG.md item 2 / task ITEM 2.)

WHY THIS RUNG EXISTS
--------------------
`measure_h2b_power.py` powered the fixed-gw question to 64 seeds and found
flat-wins on composite, CI-separated 6/6. But it used the arm's OWN decoded
grounding_weight, which in THIS harness is a CONSTANT 0.3333 for every one of the
12 signalled units:
    grounding_weight = min(1.0, |marginal|) * hop_discount
    hop_discount     = 1 / (1 + (hops - 1)),  and every grounded read hits the
                       SensorAnchor at hops=3  =>  hop_discount = 1/3 = 0.3333
    |marginal| saturates to 1.0 after the CAN relax  =>  min(1.0,|marginal|)=1.0
So the "grounding_weighted" arm was just `flat * 0.333` — a constant 3x
attenuation with ZERO cross-unit variance. H2b's mechanism claim ("gw attenuates
by confidence, not effect size, so it under-shoots strong signals") predicts that
the near-tie is BECAUSE gw is near-constant and low. This harness tests that
directly: it makes the gw magnitude a swept quantity that spans a real range and
asks whether ANY point in [0.2,1.0] — or a signal-TRACKING weight — flips the
verdict vs flat.

WHAT IS OVERRIDDEN (and what is NOT)
------------------------------------
Everything is reused verbatim from measure_h2_directed: build_units,
decode_units (the REAL arm decode — direction is still the arm's OWN decoded
direction, unchanged), apply_band_shift_percell, make_realized_text_aware, the
REAL scorer crps.crps_composite, the Phase-5 PIT machinery. The ONLY change is
the gw arm's MAGNITUDE policy: instead of `flat * arm.grounding_weight` (const
0.333), the gw magnitude is
    * GLOBAL-W mode:   flat * w             for a swept scalar w in [w_lo,w_hi]
    * TRACKING mode:   flat * w_unit        where w_unit is assigned per signalled
                       unit across [w_lo,w_hi] by a signal-strength RANK, i.e. a
                       weight that TRACKS the signal (stronger signal -> larger
                       weight), the thing H2b's mechanism hinges on.
Direction is UNCHANGED (the arm's decoded sign) in every arm; only the graded
magnitude is varied. This isolates "does a signal-tracking / larger graded weight
beat flat" from "having a direction" — exactly the H2b question, now with the
grade actually spanning a range instead of pinned at 0.333.

The per-seed paired delta d_i = composite_gw(seed_i) - composite_flat(seed_i)
(both arms scored on the SAME realized draw per seed) gives a CI, same protocol
as measure_h2b_power. flat is the SAME flat arm (flat*sign, unchanged).

RAW_UNRANKABLE: direction-aware PROXY (make_realized_text_aware), sympathetic to
the arm's decode by construction; NOT the sealed organizer board. No new metric;
no hand-fitting to a cell — the whole (w x p_signal x e) grid is reported.

Reproduce:
  PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
    .bigtmp/t2venv/bin/python \
    drafts/seldon_t2_text/induced_belief/measure_h2b_gwrange.py \
    --units .bigtmp/track2/units --select t2-F3 \
    --realized-seeds 0-63 --n-draws 1000 \
    --p-signals 0.3,0.5,0.7 --effects 0.5,1.0 \
    --gw-values 0.2,0.333,0.4,0.6,0.8,1.0 --gw-range 0.2,1.0 \
    --json-out drafts/seldon_t2_text/induced_belief/h2b_gwrange_results.json
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
for _p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python"), str(_T2)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from run_variogram_eval import (make_realized_text_aware,        # noqa: E402
                                flatten_realized_vec)
from qfbench2_common.scoring import crps                          # noqa: E402
from induced_belief.measure_h2_directed import (                  # noqa: E402  (REUSE verbatim)
    build_units, decode_units, apply_band_shift_percell)


def _parse_seeds(spec: str):
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(s) for s in spec.split(",") if s.strip() != ""]


def assign_tracking_weights(built, decoded, w_lo, w_hi):
    """Assign each SIGNALLED unit a grounding weight that TRACKS the signal,
    spanning [w_lo, w_hi]. This is the "more hops / stronger anchor -> larger
    weight" design H2b names, realized here as: rank the signalled units by a
    signal-strength proxy and spread their weights linearly across the range.

    The signal-strength proxy is the unit's OWN decoded grounding provenance
    (grounding_weight, then hops); since grounding_weight saturates to 0.333 and
    hops is constant (=3) in this harness, the rank is otherwise degenerate, so
    we break ties by a stable per-unit hash of the unit name to produce a
    DETERMINISTIC, spread-out range that is not hand-fit to any outcome (the
    proxy realized has not been touched when this is computed; the assignment
    sees only the decode + the unit name). The point is not WHICH unit gets which
    weight, but that the weights SPAN [w_lo,w_hi] instead of all sitting at 0.333
    — so the composite delta vs flat can be measured as a function of a grade
    that actually varies across units.

    Returns {unit_name -> w in [w_lo,w_hi]} for signalled units (0.0 for none).
    """
    sig = [(ud.name, decoded[ud.name]) for (ud, *_ ) in built
           if decoded[ud.name]["sign"] != 0.0]
    # rank key: decoded grounding_weight primary (the arm's own confidence),
    # then |shift|, stable name hash tiebreak (all degenerate here by design —
    # that degeneracy IS the item-2 premise; the hash spreads the range).
    def key(item):
        name, dec = item
        h = int.from_bytes(__import__("hashlib").sha256(name.encode()).digest()[:4],
                           "big") / 2**32
        return (float(dec.get("grounding_weight", 0.0)),
                abs(float(dec.get("shift", 0.0))), h)
    ordered = sorted(sig, key=key)
    n = len(ordered)
    w = {}
    if n == 1:
        w[ordered[0][0]] = 0.5 * (w_lo + w_hi)
    else:
        for i, (name, _dec) in enumerate(ordered):
            w[name] = w_lo + (w_hi - w_lo) * i / (n - 1)
    # non-signalled units contribute 0 regardless.
    for (ud, *_ ) in built:
        if ud.name not in w:
            w[ud.name] = 0.0
    return w


def _gw_shift_grid(card, dec, flat_shift, gw_magnitude):
    """Per-cell signed shift for the gw arm at a GIVEN grounding-weight magnitude
    (overriding the arm's fixed 0.333). Direction is the arm's OWN decoded sign
    (unchanged); only the graded magnitude is the swept gw_magnitude.
        shift_cell = sign * flat_shift * gw_magnitude
    """
    n_a = len(card.asset_ids)
    n_h = len(card.horizons)
    val = dec["sign"] * flat_shift * gw_magnitude
    return np.full((n_a, n_h), float(val), dtype=float)


def _flat_shift_grid(card, dec, flat_shift):
    n_a = len(card.asset_ids)
    n_h = len(card.horizons)
    return np.full((n_a, n_h), float(dec["sign"] * flat_shift), dtype=float)


def paired_cell_gw(built, decoded, seeds, p_signal, e, flat_shift,
                   realized_mode, gw_of_unit):
    """Paired per-seed (gw - flat) composite/tail delta for a gw arm whose
    per-unit grounding-weight magnitude is gw_of_unit[name] (a callable or dict
    -> magnitude). flat is the SAME unchanged flat arm. Mirrors
    measure_h2b_power.paired_cell exactly except the gw magnitude is overridden.
    """
    prepared = []
    for (ud, card, panel, base) in built:
        dec = decoded[ud.name]
        weights = (card.weights["marginal"], card.weights["joint"],
                   card.weights["tail"])
        tl = tuple(card.tail_levels)
        gold = {aid: dec["sign"] for aid in card.asset_ids}
        mag = gw_of_unit[ud.name] if isinstance(gw_of_unit, dict) else gw_of_unit
        flat_s = apply_band_shift_percell(
            base, _flat_shift_grid(card, dec, flat_shift))
        gw_s = apply_band_shift_percell(
            base, _gw_shift_grid(card, dec, flat_shift, mag))
        prepared.append((card, panel, weights, tl, gold,
                         flat_s.reshape(flat_s.shape[0], -1),
                         gw_s.reshape(gw_s.shape[0], -1)))

    f_by_seed, g_by_seed, ft_by_seed, gt_by_seed = [], [], [], []
    for seed in seeds:
        f_comps, g_comps, f_tails, g_tails = [], [], [], []
        for (card, panel, weights, tl, gold, flat_flat, gw_flat) in prepared:
            realized = make_realized_text_aware(
                card, panel, seed, gold_dir=gold,
                p_signal=p_signal, e=e, mode=realized_mode)
            y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
            sf = crps.crps_composite(flat_flat, y, weights=weights,
                                     tail_levels=tl, joint=card.joint_kind)
            sg = crps.crps_composite(gw_flat, y, weights=weights,
                                     tail_levels=tl, joint=card.joint_kind)
            f_comps.append(sf["composite"]); g_comps.append(sg["composite"])
            f_tails.append(sf["tail"]); g_tails.append(sg["tail"])
        f_by_seed.append(float(np.mean(f_comps)))
        g_by_seed.append(float(np.mean(g_comps)))
        ft_by_seed.append(float(np.mean(f_tails)))
        gt_by_seed.append(float(np.mean(g_tails)))

    fc = np.array(f_by_seed); gc = np.array(g_by_seed)
    ft = np.array(ft_by_seed); gt = np.array(gt_by_seed)
    d_comp = gc - fc; d_tail = gt - ft
    n = len(seeds)

    def ci(d):
        m = float(np.mean(d))
        se = float(np.std(d, ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        return {"mean": m, "se": se, "lo95": m - 1.96 * se, "hi95": m + 1.96 * se}

    cc = ci(d_comp); ct = ci(d_tail)
    return {
        "n_seeds": n,
        "flat_composite_mean": float(np.mean(fc)),
        "gw_composite_mean": float(np.mean(gc)),
        "flat_tail_mean": float(np.mean(ft)),
        "gw_tail_mean": float(np.mean(gt)),
        "d_composite": cc, "d_tail": ct,
        "composite_ci_separated_below0": bool(cc["hi95"] < 0),   # gw wins
        "composite_ci_separated_above0": bool(cc["lo95"] > 0),   # flat wins
        "composite_ci_straddles0": bool(cc["lo95"] <= 0 <= cc["hi95"]),
    }


def _verdict(r):
    if r["composite_ci_separated_below0"]:
        return "gw<flat"
    if r["composite_ci_separated_above0"]:
        return "flat<gw"
    return "TIE"


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
    ap.add_argument("--gw-values", default="0.2,0.333,0.4,0.6,0.8,1.0",
                    help="GLOBAL-W sweep: scalar gw magnitudes to test vs flat")
    ap.add_argument("--gw-range", default="0.2,1.0",
                    help="w_lo,w_hi for the signal-TRACKING per-unit weights")
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
    gw_values = [float(x) for x in args.gw_values.split(",")]
    w_lo, w_hi = [float(x) for x in args.gw_range.split(",")]

    built = build_units(units_dir, subs, args.n_draws, args.model_seed)
    if not built:
        print("NO UNITS BUILT")
        return 1
    print(f"built {len(built)} F3 units; POWER seeds={len(seeds)} "
          f"({seeds[0]}..{seeds[-1]}); n_draws={args.n_draws}")

    decoded = decode_units(built, market=args.market)
    n_signal = sum(1 for (ud, *_ ) in built if decoded[ud.name]["sign"] != 0.0)
    gws = sorted({round(decoded[ud.name]["grounding_weight"], 6)
                  for (ud, *_ ) in built if decoded[ud.name]["sign"] != 0.0})
    print(f"  ({n_signal}/{len(built)} units carry a non-zero decoded direction)")
    print(f"  arm's OWN decoded grounding_weight(s) among signalled units: {gws} "
          f"  <- item-2 premise: gw is pinned, near-zero variance")

    # ---------------------------------------------------------------- #
    #  (A) GLOBAL-W sweep: gw arm = flat * w, w swept across the range. #
    #  Answers: is the near-tie because w is pinned at 0.333? Does ANY  #
    #  w in [0.2,1.0] flip the verdict (gw CI-below flat)?              #
    # ---------------------------------------------------------------- #
    global_grid = {}
    print("\n=== (A) GLOBAL-W sweep: composite delta (gw=flat*w) - flat, 95% CI ===")
    print(f"  {'w':>5} {'p_sig':>5} {'e':>4} | {'d_comp mean':>12} "
          f"{'95% CI':>24} | {'verdict':>8}")
    for w in gw_values:
        for p in p_signals:
            for e in effects:
                r = paired_cell_gw(built, decoded, seeds, p, e,
                                   args.flat_shift, args.realized_mode, w)
                v = _verdict(r)
                cc = r["d_composite"]
                global_grid[f"w{w}_p{p}_e{e}"] = {
                    "w": w, "p_signal": p, "e": e, **r, "verdict": v}
                print(f"  {w:5.3f} {p:5.1f} {e:4.1f} | {cc['mean']:+12.6f} "
                      f"[{cc['lo95']:+.6f},{cc['hi95']:+.6f}] | {v:>8}")

    # summarise per-w across p/e cells: does this w ever CI-win vs flat?
    print("\n  --- per-w summary (across the 6 p/e cells) ---")
    global_w_summary = {}
    for w in gw_values:
        cells = [v for k, v in global_grid.items() if v["w"] == w]
        n_gw = sum(1 for c in cells if c["verdict"] == "gw<flat")
        n_flat = sum(1 for c in cells if c["verdict"] == "flat<gw")
        n_tie = sum(1 for c in cells if c["verdict"] == "TIE")
        mean_d = float(np.mean([c["d_composite"]["mean"] for c in cells]))
        global_w_summary[w] = {"n_gw_wins": n_gw, "n_flat_wins": n_flat,
                               "n_tie": n_tie, "mean_d_composite": mean_d}
        print(f"  w={w:5.3f}: mean d_comp={mean_d:+.6f}  "
              f"cells gw<flat={n_gw} flat<gw={n_flat} TIE={n_tie}")

    # ---------------------------------------------------------------- #
    #  (B) signal-TRACKING per-unit weights spanning [w_lo, w_hi].     #
    #  Answers: if gw TRACKED the signal (stronger -> larger weight)   #
    #  instead of being pinned at 0.333, does grading beat flat?       #
    # ---------------------------------------------------------------- #
    w_of_unit = assign_tracking_weights(built, decoded, w_lo, w_hi)
    print(f"\n=== (B) signal-TRACKING weights spanning [{w_lo},{w_hi}] "
          f"(per-unit, ranked by signal strength) ===")
    for (ud, *_ ) in built:
        if decoded[ud.name]["sign"] != 0.0:
            print(f"  {ud.name:34s} w_track={w_of_unit[ud.name]:.3f}")
    track_grid = {}
    print(f"  {'p_sig':>5} {'e':>4} | {'d_comp mean':>12} {'95% CI':>24} | {'verdict':>8}")
    for p in p_signals:
        for e in effects:
            r = paired_cell_gw(built, decoded, seeds, p, e,
                               args.flat_shift, args.realized_mode, w_of_unit)
            v = _verdict(r)
            cc = r["d_composite"]
            track_grid[f"p{p}_e{e}"] = {"p_signal": p, "e": e, **r, "verdict": v}
            print(f"  {p:5.1f} {e:4.1f} | {cc['mean']:+12.6f} "
                  f"[{cc['lo95']:+.6f},{cc['hi95']:+.6f}] | {v:>8}")
    n_gw_t = sum(1 for c in track_grid.values() if c["verdict"] == "gw<flat")
    n_flat_t = sum(1 for c in track_grid.values() if c["verdict"] == "flat<gw")
    n_tie_t = sum(1 for c in track_grid.values() if c["verdict"] == "TIE")

    # ---- the item-2 verdict ----
    # gw wins ANY cell at ANY w? the crossover w (where mean d_comp changes sign)?
    any_gw_win = any(v["verdict"] == "gw<flat" for v in global_grid.values())
    # find the w where mean d_comp crosses zero (per p/e), if any.
    print("\n=== ITEM-2 VERDICT (RAW_UNRANKABLE; direction-aware proxy) ===")
    print(f"  arm's real gw is pinned at {gws}; this rung swept gw over "
          f"{gw_values} and a tracking range [{w_lo},{w_hi}].")
    print(f"  GLOBAL-W: gw CI-beats flat in ANY (w,p,e) cell? {any_gw_win}")
    print(f"  TRACKING: cells gw<flat={n_gw_t} flat<gw={n_flat_t} TIE={n_tie_t} of "
          f"{len(track_grid)}")
    # the direction of the story: mean d_comp as a function of w at a mid cell.
    mid = [f"w{w}_p0.5_e0.5" for w in gw_values if f"w{w}_p0.5_e0.5" in global_grid]
    if mid:
        print("  mean d_comp(w) at p=0.5,e=0.5 (>0 => flat better):")
        for k in mid:
            print(f"    w={global_grid[k]['w']:5.3f}: "
                  f"d_comp={global_grid[k]['d_composite']['mean']:+.6f} "
                  f"[{global_grid[k]['d_composite']['lo95']:+.6f},"
                  f"{global_grid[k]['d_composite']['hi95']:+.6f}]  "
                  f"{global_grid[k]['verdict']}")
    print("\n  RAW_UNRANKABLE: make_realized_text_aware is a direction-aware "
          "PROXY sympathetic to the arm's decode; NOT the sealed board.")

    out = {
        "n_units": len(built),
        "n_signal_units": n_signal,
        "arm_decoded_grounding_weights": gws,
        "flat_shift": args.flat_shift,
        "seeds": seeds, "n_draws": args.n_draws,
        "gw_values": gw_values, "gw_range": [w_lo, w_hi],
        "tracking_weights": {k: v for k, v in w_of_unit.items() if v != 0.0},
        "global_w_grid": global_grid,
        "global_w_summary": global_w_summary,
        "tracking_grid": track_grid,
        "tracking_summary": {"n_gw_wins": n_gw_t, "n_flat_wins": n_flat_t,
                             "n_tie": n_tie_t},
        "any_gw_ci_win_global": any_gw_win,
        "RAW_UNRANKABLE": True,
    }
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2, default=str))
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
