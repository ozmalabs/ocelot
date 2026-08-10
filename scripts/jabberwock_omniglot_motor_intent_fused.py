#!/usr/bin/env python3
"""jabberwock_omniglot_motor_intent_fused.py — proper motor-intent verdict stack.

PRIMARY (program inference + AbS render-compare on extracted intent):
  (a) intent       — AbS topology: realize noise → inverse plan → render-compare segs
  (b) intent_abs   — AbS arrangement: render candidate in query plan frame
  (c) program_intent — per-stroke program inference on plan-frame strokes

BASELINES:
  (d) arrangement  — raw canvas outcome compare (failure mode)
  (e) program_raw  — per-stroke program on raw canvas (diagnostic)
  (f) sctps_diag   — whole-figure SC+TPS blob warp (DIAGNOSTIC ONLY — false confidence)

Run:
  PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_omniglot_motor_intent_fused.py
  PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_omniglot_motor_intent_fused.py --quick
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from domains import motor_intent as mi
from domains import omniglot_world as ow
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for

SEP = "=" * 92
WAY = 20
SEED = 42
EVAL_ALPHABETS = ["Angelic", "Atemayar_Qelisayer", "Atlantean", "Aurek-Besh"]
EPISODES_PER_ALPHABET = 20
RESULT_PATH = os.path.join(ROOT, "results", "omniglot_motor_intent_fused.json")

PRIMARY_ARMS = ("intent", "intent_abs", "program_intent")
BASELINE_ARMS = ("arrangement", "program_raw", "sctps_diag")
ALL_ARMS = PRIMARY_ARMS + BASELINE_ARMS


def boot():
    s, ag = boot_core()
    native = s._inner
    native.load_seed_manifest(manifest_for("motor_intent_core"), ag)
    return s, ag, native


def _strokes(path: str) -> list[list]:
    return [st.tolist() for st in ow.load_strokes(path, drop_degenerate=True)]


def _run_test(native, alphabets: list[str], way: int, episodes_per: int,
              rng: np.random.Generator) -> dict:
    preds = {a: [] for a in ALL_ARMS}
    trues = []
    per_alph = {a: {arm: [] for arm in ALL_ARMS} for a in alphabets}
    skipped = []
    n_ep = 0

    for alph in alphabets:
        chars = sorted(ow.characters(alph, "evaluation"))
        if len(chars) < way:
            skipped.append((alph, f"only {len(chars)} chars"))
            continue
        chars = chars[:way]
        drawer_files = [ow.drawings(cd) for cd in chars]
        n_drawers = min(len(fl) for fl in drawer_files)
        ex_drawer = int(rng.integers(n_drawers))
        exemplars = [_strokes(drawer_files[ci][ex_drawer]) for ci in range(way)]

        for qi in range(min(episodes_per, way)):
            q_drawer = int(rng.integers(n_drawers))
            while q_drawer == ex_drawer:
                q_drawer = int(rng.integers(n_drawers))
            query = _strokes(drawer_files[qi][q_drawer])
            for arm in ALL_ARMS:
                res = mi.fused_motor_verdict(native, query, exemplars, mode=arm)
                w = res.get("winner")
                if arm == "arrangement":
                    w = w if w is not None else -1
                else:
                    w = int(w) if w is not None else -1
                preds[arm].append(w)
                per_alph[alph][arm].append(w == qi)
            trues.append(qi)
            n_ep += 1

    def _acc(p, t):
        return float(np.mean([a == b for a, b in zip(p, t)])) if t else 0.0

    shuf = list(trues)
    rng.shuffle(shuf)
    chance = 1.0 / way

    out = {
        "n_episodes": n_ep,
        "skipped_alphabets": skipped,
        "chance": chance,
        "primary_arms": list(PRIMARY_ARMS),
        "baseline_arms": list(BASELINE_ARMS),
        "note": "sctps_diag is diagnostic only — holistic blob warp, false confidence",
    }
    for arm in ALL_ARMS:
        out[f"acc_{arm}"] = _acc(preds[arm], trues)
        out[f"acc_{arm}_shuffled"] = _acc(preds[arm], shuf)
        out[f"per_alph_{arm}"] = {
            a: float(np.mean(per_alph[a][arm])) if per_alph[a][arm] else 0.0
            for a in per_alph
        }

    best_primary = max(PRIMARY_ARMS, key=lambda a: out[f"acc_{a}"])
    out["best_primary_arm"] = best_primary
    out["acc_best_primary"] = out[f"acc_{best_primary}"]
    out["delta_best_primary_minus_arrangement_pp"] = 100 * (
        out["acc_best_primary"] - out["acc_arrangement"])
    out["delta_best_primary_minus_sctps_diag_pp"] = 100 * (
        out["acc_best_primary"] - out["acc_sctps_diag"])
    out["delta_program_intent_minus_raw_pp"] = 100 * (
        out["acc_program_intent"] - out["acc_program_raw"])
    out["delta_intent_abs_minus_intent_pp"] = 100 * (
        out["acc_intent_abs"] - out["acc_intent"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--alphabets", nargs="*", default=None)
    args = ap.parse_args()

    if not mi.stroke_quantize_live():
        print("SKIP: StrokeQuantize not built")
        return 0
    if not mi.stroke_render_live():
        print("SKIP: StrokeRender not built (AbS intent arms need it)")
        return 0
    if not ow.have_data("evaluation"):
        print(f"WALL: no evaluation data under {ow.DATA}")
        return 1

    alphabets = args.alphabets or (EVAL_ALPHABETS[:1] if args.quick else EVAL_ALPHABETS)
    episodes = 10 if args.quick else EPISODES_PER_ALPHABET

    print(SEP)
    print("OMNIGLOT MOTOR-INTENT — program inference + AbS render-compare (SC+TPS diagnostic)")
    print(f"  alphabets={alphabets}  episodes/alphabet={episodes}  seed={SEED}")
    print(SEP)

    t0 = time.time()
    _, _, native = boot()
    rep = _run_test(native, alphabets, WAY, episodes, np.random.default_rng(SEED))
    rep["elapsed_s"] = round(time.time() - t0, 2)
    rep["alphabets"] = alphabets

    print(f"\n  episodes: {rep['n_episodes']}  elapsed: {rep['elapsed_s']}s")
    print(f"\n  PRIMARY (proper verdict stack):")
    labels = {
        "intent": "AbS intent topology",
        "intent_abs": "AbS intent arrangement",
        "program_intent": "per-stroke program (plan)",
    }
    print(f"  {'ARM':<28} {'ACC':>7}  {'shuf':>7}")
    for arm in PRIMARY_ARMS:
        print(f"  {labels[arm]:<28} {100*rep[f'acc_{arm}']:6.1f}%  "
              f"{100*rep[f'acc_{arm}_shuffled']:6.1f}%")

    print(f"\n  BASELINES + diagnostic:")
    blabels = {
        "arrangement": "raw canvas arrangement",
        "program_raw": "per-stroke program (raw)",
        "sctps_diag": "SC+TPS blob warp (DIAG)",
    }
    for arm in BASELINE_ARMS:
        print(f"  {blabels[arm]:<28} {100*rep[f'acc_{arm}']:6.1f}%  "
              f"{100*rep[f'acc_{arm}_shuffled']:6.1f}%")

    print(f"\n  best primary: {rep['best_primary_arm']} ({100*rep['acc_best_primary']:.1f}%)")
    print(f"  delta best-primary vs arrangement: {rep['delta_best_primary_minus_arrangement_pp']:+.1f}pp")
    print(f"  delta best-primary vs sctps_diag:    {rep['delta_best_primary_minus_sctps_diag_pp']:+.1f}pp")
    print(f"  delta program intent-raw:            {rep['delta_program_intent_minus_raw_pp']:+.1f}pp")
    print(f"  delta intent_abs vs intent:          {rep['delta_intent_abs_minus_intent_pp']:+.1f}pp")

    rep["pass_best_primary_beats_arrangement"] = rep["acc_best_primary"] > rep["acc_arrangement"]
    rep["pass_above_chance"] = rep["acc_best_primary"] > rep["chance"]

    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"\nwrote {RESULT_PATH}")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
