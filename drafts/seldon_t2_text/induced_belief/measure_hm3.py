"""measure_hm3 — H-M3: does a correctly-typed macro SURPRISE, applied as a
graded band shift, lower composite vs no_shift on macro-carrying units?

Same instrument as H2a (H2_RESOLUTION): the direction-aware proxy
`make_realized_text_aware` (REUSED verbatim), the REAL reference scorer
`qfbench2_common.scoring.crps.crps_composite`, and the per-cell additive shift
`apply_band_shift_percell` (REUSED). The ONLY differences from
measure_h2_directed are: (1) the per-unit direction/shift comes from the
MACRO-SURPRISE decode (`macro_surprise.decode_macro_surprise` on the unit's
macro_release doc + its macro panel), not the ToM speech-act decode; (2)
single-asset macro units are ALLOWED (macro units are single-asset NFP/CPI or a
rates target), so the ≥2-asset F3 filter is dropped.

Arms (contract-preserving, same base draws):
  no_shift     — text-blind base (the floor)
  macro_shift  — shift each signalled cell by the macro decode's OWN graded
                 `shift` (= sign x grounding_weight), scaled into the flat band.

CONFIRMED iff composite(macro_shift) < composite(no_shift) across the
p_signal/e sweep (MACRO_SURPRISE_PREREG H-M3). RAW_UNRANKABLE: every number is
on the direction-aware PROXY, sympathetic to the decode's direction by
construction; it is NOT the sealed organizer outcome.

Reproduce:
  PYTHONPATH=runners/dsl/python:.bigtmp/track2 .bigtmp/t2venv/bin/python \
    drafts/seldon_t2_text/induced_belief/measure_hm3.py \
    --units .bigtmp/track2/units \
    --realized-seeds 0,1,2,3,4,5,6,7 --n-draws 1000 \
    --p-signals 0.0,0.3,0.5,0.7 --effects 0.5,1.0 \
    --json-out drafts/seldon_t2_text/induced_belief/hm3_results.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_T2 = _HERE.parent
_ROOT = _T2.parent.parent
for p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python"), str(_T2)):
    if p not in sys.path:
        sys.path.insert(0, p)

from t2_adapter import read_card, load_panels, JointDrawEngine  # noqa: E402
from run_variogram_eval import (make_realized_text_aware,        # noqa: E402
                                flatten_realized_vec, asset_series)
from run_calibration_eval import collect_pit, ks_uniform         # noqa: E402
from qfbench2_common.scoring import crps                         # noqa: E402
from induced_belief.measure_h2_directed import (                 # noqa: E402  (REUSE)
    apply_band_shift_percell)

_DIR_SIGN = {"up": 1.0, "down": -1.0, "none": 0.0}
_MACRO_DOC_TYPES = {"macro_release"}


def _asof(unit_dir: Path):
    try:
        c = tomllib.loads((unit_dir / "card.toml").read_text())
        return (c.get("provenance", {}).get("data_cutoff")
                or c.get("task", {}).get("asof"))
    except Exception:
        return None


def _macro_docs(unit_dir: Path):
    """Return the unit's macro_release doc texts (via corpus_index doc_type).
    Mechanical host I/O."""
    tdir = unit_dir / "text"
    idx = tdir / "corpus_index.json"
    out = []
    if idx.exists():
        try:
            for d in json.loads(idx.read_text()).get("documents", []):
                if d.get("doc_type") in _MACRO_DOC_TYPES:
                    fp = tdir / d["file"]
                    if fp.exists():
                        out.append(fp.read_text(errors="ignore"))
        except Exception:
            pass
    return out


def build_macro_units(units_dir: Path):
    """Select units that carry a macro_release doc AND build cleanly. Includes
    single-asset units (macro units are single-asset)."""
    built = []
    for ud in sorted(units_dir.iterdir()):
        if not (ud.is_dir() and (ud / "card.toml").exists()):
            continue
        macro_texts = _macro_docs(ud)
        if not macro_texts:
            continue
        try:
            card = read_card(ud / "card.toml")
            panel = load_panels(ud, card.asof)
            eng = JointDrawEngine().build(card, panel)
            base = eng.sample_matrix(1000, seed=0)
        except Exception as e:
            print(f"SKIP {ud.name}: {e}")
            continue
        built.append((ud, card, panel, base, macro_texts))
    return built


def decode_macro_units(built):
    """Boot the arm+macro ONCE; decode each unit's macro doc(s) -> the macro
    decode's OWN (direction, grounding_weight, shift). Graph-native; Python
    reads values off. Most-recent macro doc wins (index order)."""
    from substrate.world_adapter import WorldAdapter
    from induced_belief import arm
    from induced_belief import macro_surprise as ms

    a = WorldAdapter()
    mk = arm.boot(a)
    ms.boot_macro(a)
    decoded = {}
    for (ud, card, panel, base, macro_texts) in built:
        last = {"direction": "none", "sign": 0.0, "grounding_weight": 0.0,
                "shift": 0.0, "reached": False, "hops": None, "source": None}
        for txt in macro_texts:
            arm.reset_beliefs(a, mk)
            r = ms.decode_macro_surprise(a, txt, mk, panel=panel)
            if r["direction"] != "none":
                last = {"direction": r["direction"],
                        "sign": _DIR_SIGN.get(r["direction"], 0.0),
                        "grounding_weight": float(r["grounding_weight"]),
                        "shift": float(r["shift"]),
                        "reached": bool(r["reached"]), "hops": r["hops"],
                        "source": r["surprise"]["source"]}
        decoded[ud.name] = last
    return decoded


def cell_shift_grid(card, dec, policy: str, flat_shift: float) -> np.ndarray:
    n_a = len(card.asset_ids)
    n_h = len(card.horizons)
    if policy == "no_shift":
        val = 0.0
    elif policy == "macro_shift":
        # dec['shift'] = sign * grounding_weight (the macro decode's graph
        # output); scaled into the flat band, exactly like grounding_weighted
        # in measure_h2_directed.
        val = flat_shift * dec["shift"]
    else:
        val = 0.0
    return np.full((n_a, n_h), float(val), dtype=float)


def measure_cell(built, decoded, seeds, p_signal, e, flat_shift, realized_mode):
    arms = ("no_shift", "macro_shift")
    out = {}
    for arm_name in arms:
        pit_pool, comps, margs, tails, jnts = [], [], [], [], []
        for (ud, card, panel, base, macro_texts) in built:
            dec = decoded[ud.name]
            shift_grid = cell_shift_grid(card, dec, arm_name, flat_shift)
            samples = apply_band_shift_percell(base, shift_grid)
            flat_s = samples.reshape(samples.shape[0], -1)
            weights = (card.weights["marginal"], card.weights["joint"],
                       card.weights["tail"])
            tl = tuple(card.tail_levels)
            gold = {aid: dec["sign"] for aid in card.asset_ids}
            for seed in seeds:
                realized = make_realized_text_aware(
                    card, panel, seed, gold_dir=gold,
                    p_signal=p_signal, e=e, mode=realized_mode)
                y = flatten_realized_vec(realized, card.asset_ids, card.horizons)
                rng = np.random.default_rng(7_000 + seed)
                pit_pool.append(collect_pit(samples, y, rng))
                sc = crps.crps_composite(flat_s, y, weights=weights,
                                         tail_levels=tl, joint=card.joint_kind)
                comps.append(sc["composite"]); margs.append(sc["marginal"])
                tails.append(sc["tail"]); jnts.append(sc["joint"])
        pit = np.concatenate(pit_pool)
        out[arm_name] = {
            "ks": ks_uniform(pit), "pit_mean": float(pit.mean()),
            "n_pit": int(pit.size),
            "marginal": float(np.mean(margs)), "joint": float(np.mean(jnts)),
            "tail": float(np.mean(tails)), "composite": float(np.mean(comps)),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--realized-seeds", default="0,1,2,3,4,5,6,7")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--flat-shift", type=float, default=0.1)
    ap.add_argument("--p-signals", default="0.0,0.3,0.5,0.7")
    ap.add_argument("--effects", default="0.5,1.0")
    ap.add_argument("--realized-mode", default="signed",
                    choices=["positive", "signed"])
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    units_dir = Path(args.units)
    seeds = [int(s) for s in args.realized_seeds.split(",")]
    p_signals = [float(x) for x in args.p_signals.split(",")]
    effects = [float(x) for x in args.effects.split(",")]

    built = build_macro_units(units_dir)
    if not built:
        print("NO MACRO UNITS BUILT")
        return 1
    print(f"built {len(built)} macro-carrying units; seeds={seeds}; "
          f"n_draws={args.n_draws}; flat_shift={args.flat_shift}sigma")

    decoded = decode_macro_units(built)
    print("\n=== per-unit MACRO decode (graph-native) ===")
    n_signal = 0
    for (ud, card, panel, base, macro_texts) in built:
        d = decoded[ud.name]
        if d["sign"] != 0.0:
            n_signal += 1
        print(f"  {ud.name:34s} dir={d['direction']:4s} "
              f"gw={d['grounding_weight']:.3f} shift={d['shift']:+.3f} "
              f"src={d['source']} assets={card.asset_ids}")
    print(f"  ({n_signal}/{len(built)} units carry a non-zero macro direction)")

    grid = {}
    print("\n=== GRID: p_signal x e, no_shift vs macro_shift "
          "(composite / tail / KS) ===")
    print(f"  {'p_sig':>5s} {'e':>4s} | {'ns comp':>10s} {'macro comp':>11s} "
          f"| {'d comp':>10s} | {'ns tail':>8s} {'macro tail':>10s}")
    for p in p_signals:
        for e in effects:
            cell = measure_cell(built, decoded, seeds, p, e,
                                args.flat_shift, args.realized_mode)
            ns = cell["no_shift"]; msh = cell["macro_shift"]
            dcomp = msh["composite"] - ns["composite"]
            grid[f"p{p}_e{e}"] = {
                "p_signal": p, "e": e, "cell": cell,
                "macro_minus_noshift_composite": dcomp,
                "macro_minus_noshift_tail": msh["tail"] - ns["tail"],
                "hm3_macro_lt_noshift": bool(msh["composite"] < ns["composite"]),
            }
            print(f"  {p:5.1f} {e:4.1f} | {ns['composite']:10.5f} "
                  f"{msh['composite']:11.5f} | {dcomp:+10.6f} | "
                  f"{ns['tail']:8.5f} {msh['tail']:10.5f}")

    signalled = [v for k, v in grid.items() if v["p_signal"] > 0.0]
    n_better = sum(1 for v in signalled if v["hm3_macro_lt_noshift"])
    empty = [v for k, v in grid.items() if v["p_signal"] == 0.0]
    # empty-signal delta per e (the direction-INDEPENDENT shift artifact): the
    # band shift moves mass on the symmetric proxy regardless of gold. The
    # DIRECTION-ATTRIBUTABLE gain strips it: signalled_delta - empty_delta(same e).
    empty_by_e = {}
    for v in empty:
        empty_by_e[v["e"]] = v["macro_minus_noshift_composite"]
    dir_only = []
    for v in signalled:
        base = empty_by_e.get(v["e"], 0.0)
        d = v["macro_minus_noshift_composite"] - base
        v["direction_only_composite_gain"] = d
        dir_only.append(d)
    summary = {
        "n_units": len(built),
        "n_signalled_cells": len(signalled),
        "n_macro_lt_noshift": n_better,
        "H_M3_literal_confirmed": bool(signalled and n_better == len(signalled)),
        "mean_signalled_delta_composite":
            float(np.mean([v["macro_minus_noshift_composite"] for v in signalled]))
            if signalled else None,
        "empty_signal_abs_delta_composite":
            float(np.mean([abs(v["macro_minus_noshift_composite"]) for v in empty]))
            if empty else None,
        # the confound flag + the honest direction-only measure.
        "shift_artifact_confound": bool(
            empty and signalled and
            abs(np.mean([v["macro_minus_noshift_composite"] for v in empty]))
            > 0.5 * abs(np.mean([v["macro_minus_noshift_composite"]
                                 for v in signalled]))),
        "mean_direction_only_gain":
            float(np.mean(dir_only)) if dir_only else None,
        "direction_only_all_negative":
            bool(dir_only and all(d < 0 for d in dir_only)),
        "direction_only_monotone_in_p_and_e": None,  # inspected in the doc
    }
    print("\n=== H-M3 SUMMARY (RAW_UNRANKABLE; direction-aware proxy) ===")
    print(f"  macro_shift < no_shift in {n_better}/{len(signalled)} "
          f"signalled cells (LITERAL criterion)")
    print(f"  H-M3 literal confirmed: {summary['H_M3_literal_confirmed']}")
    print(f"  shift-artifact confound (empty-signal delta ~ signalled delta): "
          f"{summary['shift_artifact_confound']}")
    print(f"  mean DIRECTION-ONLY composite gain (signalled - empty): "
          f"{summary['mean_direction_only_gain']}")
    print(f"  direction-only gain all negative: "
          f"{summary['direction_only_all_negative']}")

    out = {"summary": summary, "grid": grid, "decoded": decoded,
           "seeds": seeds, "n_draws": args.n_draws,
           "flat_shift": args.flat_shift}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=2, default=str))
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
